from app.services import naver_browser


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
