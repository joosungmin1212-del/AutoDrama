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


def has_saved_session() -> bool:
    return config.NAVER_STATE_PATH.exists()


def clear_saved_session() -> None:
    if config.NAVER_STATE_PATH.exists():
        config.NAVER_STATE_PATH.unlink()


def _save_state(state: dict) -> None:
    encrypted = secure_storage.protect(json.dumps(state, ensure_ascii=False))
    config.NAVER_STATE_PATH.write_text(encrypted, encoding="utf-8")


def _load_state() -> dict:
    raw = config.NAVER_STATE_PATH.read_text(encoding="utf-8")
    return json.loads(secure_storage.unprotect(raw))


async def _watch_and_cleanup(playwright, browser) -> None:
    """브라우저 창이 실제로 닫히면(사용자가 닫거나, 발행 후 닫거나) 드라이버 프로세스를 정리한다.

    "네이버로 보내기"는 창을 열어둔 채로 함수가 먼저 리턴해야 하므로, 정리는 백그라운드
    태스크로 분리해서 fire-and-forget 한다.
    """
    try:
        await browser.wait_for_event("disconnected", timeout=0)
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            await playwright.stop()
        except Exception:  # noqa: BLE001
            logger.debug("playwright 정리 중 오류(무시 가능)", exc_info=True)


async def login_interactive(timeout_ms: int = 180_000) -> bool:
    """실제 브라우저 창을 열어 사용자가 직접 로그인하도록 하고, 세션을 암호화해 저장한다.

    PT샵 PC(화면이 있는 환경)에서 실행되어야 한다. 클라우드/헤드리스 서버에서는 동작하지 않는다.
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
            _save_state(state)
            return True
        finally:
            await browser.close()


async def check_login_status() -> bool:
    """저장된 세션이 실제로 아직 유효한지 headless로 확인."""
    if not has_saved_session():
        return False

    from playwright.async_api import async_playwright

    try:
        state = _load_state()
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
    """
    if not has_saved_session():
        raise NaverAuthError("네이버 로그인이 먼저 필요합니다. 설정 화면에서 로그인해주세요.")

    try:
        state = _load_state()
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
