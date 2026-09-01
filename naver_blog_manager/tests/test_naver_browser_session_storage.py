import asyncio

import pytest

from app.services import naver_browser


@pytest.mark.asyncio
async def test_watch_and_cleanup_does_not_close_browser_while_still_in_use():
    """실제로 있었던 심각한 버그 재현: Playwright의 Browser 객체엔 wait_for_event()가
    없는데(Page/BrowserContext에만 있음) _watch_and_cleanup이 그걸 호출하고 있었다.
    그래서 AttributeError가 즉시 발생 -> 조용히 삼켜짐 -> playwright.stop()이 곧바로
    실행되어, "네이버로 보내기"가 글쓰기 화면을 열기도 전에 브라우저가 닫혀버리는
    문제가 있었다("Target page, context or browser has been closed"). 목(mock)이 아닌
    실제 Playwright 브라우저로, cleanup 백그라운드 태스크가 떠 있는 동안에도 브라우저가
    멀쩡히 계속 쓰일 수 있는지 확인한다 - 몽키패치로는 이 버그를 잡을 수 없다(실제
    Browser 객체의 실제 메서드 존재 여부가 핵심이라서)."""
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=True)
    except Exception as exc:  # noqa: BLE001
        await playwright.stop()
        pytest.skip(f"이 환경에 pip playwright 버전과 맞는 Chromium이 설치돼 있지 않음: {exc}")

    cleanup_task = asyncio.ensure_future(naver_browser._watch_and_cleanup(playwright, browser))

    # cleanup 태스크가 스케줄되어 한 번 돌 시간을 준다 - 버그가 있었다면 바로 이 시점에
    # playwright.stop()이 이미 실행돼서 브라우저를 못 쓰게 됐을 것이다.
    await asyncio.sleep(0.3)

    # 고쳐졌다면 브라우저는 여전히 멀쩡해야 한다 - 실제 open_write_draft()가 하는 것과
    # 똑같이 new_context()를 호출해본다.
    context = await browser.new_context()
    await context.close()

    await browser.close()
    await asyncio.wait_for(cleanup_task, timeout=5)


def test_session_state_is_not_stored_as_plaintext_json(tmp_path, monkeypatch):
    state_path = tmp_path / "naver_state.json"
    monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", state_path)

    fake_state = {"cookies": [{"name": "NID_AUT", "value": "secret-session-value"}]}
    naver_browser._save_state(fake_state)

    raw = state_path.read_text(encoding="utf-8")
    assert "secret-session-value" not in raw  # 평문으로 남으면 안 된다

    loaded = naver_browser._load_state()
    assert loaded == fake_state


def test_has_and_clear_saved_session(tmp_path, monkeypatch):
    state_path = tmp_path / "naver_state.json"
    monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", state_path)

    assert naver_browser.has_saved_session() is False
    naver_browser._save_state({"cookies": []})
    assert naver_browser.has_saved_session() is True

    naver_browser.clear_saved_session()
    assert naver_browser.has_saved_session() is False


def _isolate_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", tmp_path / "naver_state.json")
    sessions_dir = tmp_path / "naver_sessions"
    sessions_dir.mkdir()
    monkeypatch.setattr(naver_browser.config, "NAVER_SESSIONS_DIR", sessions_dir)


def test_per_blog_session_is_isolated_from_default_and_other_accounts(tmp_path, monkeypatch):
    """계정을 여러 개 등록해 쓸 때: 계정 A 전용으로 저장한 세션은 계정 B나 기본 세션과
    섞이면 안 된다 - 계정 전환의 핵심 전제조건."""
    _isolate_sessions(tmp_path, monkeypatch)

    naver_browser._save_state({"cookies": [{"name": "A"}]}, blog_id="account_a")
    naver_browser._save_state({"cookies": [{"name": "B"}]}, blog_id="account_b")

    assert naver_browser.has_saved_session("account_a") is True
    assert naver_browser.has_saved_session("account_b") is True
    assert naver_browser.has_saved_session("account_c") is False  # 등록한 적 없는 계정
    assert naver_browser.has_saved_session() is False  # 기본 세션은 따로 저장한 적 없음

    assert naver_browser._load_state("account_a") == {"cookies": [{"name": "A"}]}
    assert naver_browser._load_state("account_b") == {"cookies": [{"name": "B"}]}

    naver_browser.clear_saved_session("account_a")
    assert naver_browser.has_saved_session("account_a") is False
    assert naver_browser.has_saved_session("account_b") is True  # 다른 계정은 안 지워짐


def test_saved_session_file_permissions_are_restricted_to_owner(tmp_path, monkeypatch):
    """access_token/.secret.key처럼, 로그인 세션 파일도 소유자만 읽을 수 있어야 한다 -
    가장 민감한 파일인데 정작 권한 제한이 빠져있던 문제."""
    import stat
    import sys

    if sys.platform == "win32":
        return  # chmod가 의미 없는 플랫폼 - Windows에서는 DPAPI가 내용을 계정에 묶어줌

    _isolate_sessions(tmp_path, monkeypatch)

    naver_browser._save_state({"cookies": []}, blog_id="account_a")
    mode = stat.S_IMODE(naver_browser._session_path("account_a").stat().st_mode)
    assert mode == 0o600


def test_resolve_session_blog_id_falls_back_to_default_when_no_dedicated_session(tmp_path, monkeypatch):
    """실제로 요구된 동작: 특정 계정 전용으로 따로 로그인해둔 적이 없으면(계정 1개만
    쓰는 기존 사용자), 처음 로그인했을 때의 계정(기본 세션)을 그대로 쓴다."""
    _isolate_sessions(tmp_path, monkeypatch)

    # 아직 아무 계정도 전용으로 로그인 안 함 -> 기본 세션으로 폴백(None)
    assert naver_browser._resolve_session_blog_id("some_blog") is None

    # "some_blog" 전용으로 로그인해두면 -> 그 계정 그대로 씀
    naver_browser._save_state({"cookies": []}, blog_id="some_blog")
    assert naver_browser._resolve_session_blog_id("some_blog") == "some_blog"

    # 다른(전용 세션 없는) 계정은 여전히 기본 세션으로 폴백
    assert naver_browser._resolve_session_blog_id("other_blog") is None
