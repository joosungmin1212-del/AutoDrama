"""네이버 로그인 세션 관리 + 블로그 글쓰기 에디터에 초안을 채워넣는 브라우저 자동화.

중요한 설계 원칙:
  - 로그인은 절대 아이디/비밀번호를 코드로 자동 입력하지 않는다. 실제 브라우저 창을 띄워
    사용자가 직접 로그인하게 하고, 로그인 성공 후 세션(storage_state)만 저장해 재사용한다.
  - 저장되는 세션 파일은 평문이 아니라 secure_storage로 암호화한다 (Windows는 DPAPI로
    로그인 계정에 묶임 - 파일만 복사해가도 다른 PC/계정에서는 못 연다).
  - 글쓰기 자동화는 "초안을 채워넣는 것"까지만 한다. 발행 버튼은 절대 자동 클릭하지 않는다.
  - 네이버 스마트에디터는 iframe + contenteditable 구조라 DOM이 자주 바뀔 수 있다.
    선택자는 이 파일의 상단 상수에 모아뒀으니, 문제가 생기면 여기만 고치면 된다.
  - "발행은 직접" 요구사항 때문에 브라우저 창은 자동화가 끝나도 사용자가 닫을 때까지
    열어둔다. 그렇다고 Playwright 드라이버 프로세스까지 영원히 떠 있으면 안 되므로,
    브라우저가 실제로 닫히는 시점에 맞춰 드라이버도 함께 정리한다 (_watch_and_cleanup).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

from .. import config
from . import secure_storage

logger = logging.getLogger("naver_blog_manager.naver_browser")

WRITE_URL_TMPL = "https://blog.naver.com/{blog_id}?Redirect=Write"
LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# 스마트에디터 ONE 기준 선택자 (네이버가 마크업을 바꾸면 여기만 수정)
EDITOR_IFRAME_SELECTOR = "iframe#mainFrame"
TITLE_SELECTOR = ".se-title-text, .se-placeholder.__se-placeholder"
BODY_SELECTOR = ".se-main-container"
POPUP_CLOSE_SELECTOR = ".se-popup-button-cancel, button.se-help-panel-close-button"


class NaverAuthError(RuntimeError):
    pass


def _session_path(blog_id: str | None):
    """blog_id를 지정하면 그 계정 전용 세션 파일을, 안 지정하면(None) 기본 세션 파일을 쓴다.

    PC 1대에 네이버 계정 1개만 쓰는 기존 방식(공식 블로그도 1개)에서는 항상 기본 세션
    파일 하나만 쓰이므로 아무것도 안 바뀐다. 계정을 여러 개 등록한 경우에만, 블로그 관리
    화면에서 그 블로그에 지정해 로그인한 계정별 파일이 따로 쓰인다.
    """
    if not blog_id:
        return config.NAVER_STATE_PATH
    return config.NAVER_SESSIONS_DIR / f"{blog_id.lower()}.json"


def has_saved_session(blog_id: str | None = None) -> bool:
    return _session_path(blog_id).exists()


def clear_saved_session(blog_id: str | None = None) -> None:
    path = _session_path(blog_id)
    if path.exists():
        path.unlink()


def _save_state(state: dict, blog_id: str | None = None) -> None:
    encrypted = secure_storage.protect(json.dumps(state, ensure_ascii=False))
    path = _session_path(blog_id)
    path.write_text(encrypted, encoding="utf-8")
    # .access_token/.secret.key와 마찬가지로 소유자만 읽을 수 있게 잠근다 - 로그인 세션
    # 쿠키는 이 중 가장 민감한 파일인데 정작 권한 제한이 빠져있었다. Windows에서는
    # DPAPI가 내용 자체를 현재 계정에 묶어주지만, 파일 권한도 같이 잠가두는 게 안전하다
    # (chmod가 의미 없는 Windows에서는 조용히 무시됨).
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _load_state(blog_id: str | None = None) -> dict:
    raw = _session_path(blog_id).read_text(encoding="utf-8")
    return json.loads(secure_storage.unprotect(raw))


def _resolve_session_blog_id(blog_id: str | None) -> str | None:
    """실제 글쓰기/상태확인에 쓸 세션을 고른다: 이 블로그 전용으로 로그인해둔 세션이
    있으면 그걸 쓰고, 없으면 기본 세션(가장 처음 로그인한 계정)으로 자동 대체한다 -
    계정을 하나만 쓰는 사용자는 매번 지정 안 해도 항상 그 계정으로 동작한다."""
    if blog_id and has_saved_session(blog_id):
        return blog_id
    return None


async def _watch_and_cleanup(playwright, browser) -> None:
    """브라우저 창이 실제로 닫히면(사용자가 닫거나, 발행 후 닫거나) 드라이버 프로세스를 정리한다.

    "네이버로 보내기"는 창을 열어둔 채로 함수가 먼저 리턴해야 하므로, 정리는 백그라운드
    태스크로 분리해서 fire-and-forget 한다.

    실제로 있었던 심각한 버그: Playwright의 Browser 객체에는 wait_for_event()라는
    메서드가 아예 없다(Page/BrowserContext에만 있음). 그런데도 이 코드가
    `browser.wait_for_event(...)`를 호출하고 있어서 AttributeError가 즉시(대기 없이)
    발생했고, 그걸 `except Exception: pass`가 조용히 삼킨 뒤 곧바로
    `playwright.stop()`으로 드라이버를 꺼버렸다 - 그 결과 "네이버로 보내기"가
    실행되자마자(글쓰기 화면을 열기도 전에) 브라우저/드라이버가 닫혀버려서
    "Browser.new_context: Target page, context or browser has been closed" 오류로
    항상 실패했다. Browser는 on()/once()로 이벤트를 등록하는 방식만 지원하므로,
    asyncio.Event를 이용해 "disconnected" 이벤트가 실제로 발생할 때까지 올바르게
    기다리도록 고쳤다.
    """
    disconnected = asyncio.Event()
    browser.once("disconnected", lambda _b=None: disconnected.set())
    try:
        await disconnected.wait()
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            await playwright.stop()
        except Exception:  # noqa: BLE001
            logger.debug("playwright 정리 중 오류(무시 가능)", exc_info=True)


async def login_interactive(timeout_ms: int = 180_000, blog_id: str | None = None) -> bool:
    """실제 브라우저 창을 열어 사용자가 직접 로그인하도록 하고, 세션을 암호화해 저장한다.

    PT샵 PC(화면이 있는 환경)에서 실행되어야 한다. 클라우드/헤드리스 서버에서는 동작하지 않는다.
    blog_id를 지정하면 그 공식 블로그 전용 계정으로 저장되어(계정 전환용), 나중에
    open_write_draft(blog_id=...)가 이 세션을 우선 사용한다. 지정하지 않으면(최초
    설정 화면의 기본 로그인) 계정을 하나만 쓰는 사용자가 계속 쓰게 될 기본 세션으로 저장된다.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            context = await browser.new_context(user_agent=config.NAVER_USER_AGENT)
            page = await context.new_page()
            await page.goto(LOGIN_URL)

            # 사용자가 직접 로그인 완료(로그인 페이지를 벗어나 naver.com 도메인으로 이동)할 때까지 대기
            try:
                await page.wait_for_url(
                    lambda url: "nidlogin" not in url and "nid.naver.com" not in url,
                    timeout=timeout_ms,
                )
            except Exception as exc:  # noqa: BLE001
                raise NaverAuthError(
                    "로그인 대기 시간이 초과되었습니다. 다시 시도해주세요."
                ) from exc

            state = await context.storage_state()
            _save_state(state, blog_id)
            return True
        finally:
            await browser.close()


async def check_login_status(blog_id: str | None = None) -> bool:
    """저장된 세션이 실제로 아직 유효한지 headless로 확인.

    blog_id 전용 세션이 없으면 기본 세션으로 자동 대체해서 확인한다(_resolve_session_blog_id).
    """
    session_blog_id = _resolve_session_blog_id(blog_id)
    if not has_saved_session(session_blog_id):
        return False

    from playwright.async_api import async_playwright

    try:
        state = _load_state(session_blog_id)
    except Exception:  # noqa: BLE001
        # 세션 파일이 깨졌거나(예: 다른 PC에서 복사해온 DPAPI 암호문) 복호화할 수 없으면
        # 로그인 안 된 것으로 취급한다.
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                storage_state=state,
                user_agent=config.NAVER_USER_AGENT,
            )
            page = await context.new_page()
            await page.goto("https://www.naver.com", wait_until="domcontentloaded")
            cookies = await context.cookies("https://www.naver.com")
            return any(c["name"] == "NID_AUT" for c in cookies)
        finally:
            await browser.close()


async def open_write_draft(blog_id: str, title: str, content_html: str) -> None:
    """네이버 블로그 글쓰기 화면을 열고 제목/본문을 채워넣는다. 발행은 자동으로 누르지 않는다.

    사용자 PC(화면이 있는 환경)에서 실행되어야 하며, 자동화가 끝나면 브라우저 창은
    사용자가 검토/발행할 수 있도록 열린 채로 남겨둔다(자동으로 닫지 않음). 다만 그 창이
    나중에 닫히면 백그라운드에서 Playwright 드라이버도 함께 정리된다.

    이 blog_id 전용으로 로그인해둔 계정이 있으면 그 계정으로, 없으면 기본 계정(가장
    처음 로그인한 계정)으로 자동 전송한다 - 계정을 하나만 쓰는 사용자는 신경 쓸 필요 없다.
    """
    session_blog_id = _resolve_session_blog_id(blog_id)
    if not has_saved_session(session_blog_id):
        raise NaverAuthError("네이버 로그인이 먼저 필요합니다. 설정 화면에서 로그인해주세요.")

    try:
        state = _load_state(session_blog_id)
    except Exception as exc:  # noqa: BLE001
        raise NaverAuthError(
            "저장된 네이버 로그인 세션을 읽을 수 없습니다. 설정 화면에서 다시 로그인해주세요."
        ) from exc

    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=False)
    except Exception:
        await playwright.stop()
        raise

    # 브라우저가 (자동화 성공/실패와 무관하게) 나중에 닫히면 드라이버를 정리하도록 예약해둔다.
    asyncio.ensure_future(_watch_and_cleanup(playwright, browser))

    context = await browser.new_context(
        storage_state=state,
        user_agent=config.NAVER_USER_AGENT,
    )
    page = await context.new_page()
    await page.goto(WRITE_URL_TMPL.format(blog_id=blog_id), wait_until="domcontentloaded")

    # 새 글쓰기 진입 시 뜨는 "이어쓰기/취소" 등 팝업 처리 (있으면 닫고, 없으면 무시)
    try:
        await page.locator(POPUP_CLOSE_SELECTOR).first.click(timeout=3000)
    except Exception:  # noqa: BLE001
        pass

    frame = page.frame_locator(EDITOR_IFRAME_SELECTOR)

    try:
        await frame.locator(TITLE_SELECTOR).first.click(timeout=10000)
        await page.keyboard.type(title, delay=15)
        await page.keyboard.press("Tab")
        await frame.locator(BODY_SELECTOR).first.click(timeout=10000)
        for line in content_html.split("\n"):
            await page.keyboard.type(line, delay=5)
            await page.keyboard.press("Enter")
    except Exception as exc:  # noqa: BLE001
        # 자동 입력이 실패해도 브라우저 창은 열어둔다 - 사용자가 직접 복사/붙여넣기 하도록.
        # (창을 닫으면 위에서 예약해둔 _watch_and_cleanup이 알아서 드라이버를 정리한다)
        raise NaverAuthError(
            "네이버 에디터 자동 입력에 실패했습니다. 브라우저 창에 직접 붙여넣어주세요. "
            f"(상세: {exc})"
        )

    # 브라우저/컨텍스트는 의도적으로 닫지 않음 - 사용자가 검토 후 직접 발행하도록 둔다.
