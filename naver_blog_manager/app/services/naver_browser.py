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
import re
from datetime import datetime
from pathlib import Path

from .. import config
from . import secure_storage

logger = logging.getLogger("naver_blog_manager.naver_browser")

WRITE_URL_TMPL = "https://blog.naver.com/{blog_id}?Redirect=Write"
LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# 스마트에디터 ONE 기준 선택자 (네이버가 마크업을 바꾸면 여기만 수정)
EDITOR_IFRAME_SELECTOR = "iframe#mainFrame"
TITLE_SELECTOR = ".se-title-text, .se-placeholder.__se-placeholder"
BODY_SELECTOR = ".se-main-container"

# "작성 중인 글이 있습니다"/"도움말" 팝업을 iframe(#mainFrame) 문서 "안"에서 텍스트로
# 찾아 닫는 JS. 처음엔 이 팝업들을 top-level page에서 CSS class로 찾으려 했다가 두
# 차례 실패했다 - 실제로는 iframe 문서 안에 있어서 page.locator()로는 애초에 보이지
# 않았다. 다른 개발자가 실제로 검증한 오픈소스 구현(MIT: csh1668/naver-blog-automation,
# app/src/main/assets/editor_bridge.js)을 참고해, class 이름 대신 "정확한 버튼
# 텍스트 + 팝업 컨테이너(role=dialog 또는 layer/popup/modal/dialog 클래스) 안에서만"
# 찾는 방식으로 재작성했다 - 네이버가 class 이름을 바꿔도 텍스트("취소"/"닫기")는
# 잘 안 바뀌므로 이쪽이 훨씬 오래간다.
_DISMISS_POPUPS_JS = r"""
() => {
  function className(n) {
    var c = n && n.className;
    if (c && typeof c === 'object' && 'baseVal' in c) c = c.baseVal;
    return String(c || '').toLowerCase();
  }
  function visible(n) {
    try { var r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; } catch (e) { return false; }
  }
  function inToolbar(n) {
    for (var p = n; p; p = p.parentElement) {
      if (/toolbar/.test(className(p)) || /toolbar/.test(String(p.id || '').toLowerCase())) return true;
    }
    return false;
  }
  function isLayerContainer(n) {
    return !!n && (/layer|popup|modal|dialog/.test(className(n)) || (n.getAttribute && n.getAttribute('role') === 'dialog'));
  }
  function popupContainer(node) {
    for (var p = node.parentElement, i = 0; p && i < 8; p = p.parentElement, i++) {
      if (isLayerContainer(p)) return p;
    }
    return null;
  }
  function clickInside(container, label) {
    if (!container) return false;
    var nodes = Array.prototype.slice.call(container.querySelectorAll('button, a, [role="button"]'));
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if ((n.innerText || n.textContent || '').trim() !== label) continue;
      if (!visible(n) || inToolbar(n)) continue;
      n.click();
      return true;
    }
    return false;
  }
  function dismissDraftDialog(doc) {
    var roots = doc.querySelectorAll('[role="dialog"], .se-popup, .__se-pop-layer');
    for (var i = 0; i < roots.length; i++) {
      var root = roots[i];
      if (!visible(root)) continue;
      if ((root.textContent || '').indexOf('작성 중인 글이 있습니다') === -1) continue;
      if (clickInside(root, '취소')) return true;
    }
    return false;
  }
  var frame = document.querySelector('iframe#mainFrame');
  var doc = frame && frame.contentWindow && frame.contentWindow.document;
  if (!doc) return 0;
  var count = 0;
  if (dismissDraftDialog(doc)) count++;
  var nodes = Array.prototype.slice.call(doc.querySelectorAll('button, a, [role="button"]'));
  nodes.forEach(function (n) {
    if ((n.innerText || n.textContent || '').trim() !== '닫기') return;
    if (!visible(n) || inToolbar(n)) return;
    if (!isLayerContainer(popupContainer(n))) return;
    n.click();
    count++;
  });
  return count;
}
"""


class NaverAuthError(RuntimeError):
    pass


async def _dismiss_editor_popups(page) -> int:
    """"작성 중인 글이 있습니다" 확인창의 "취소"와, "도움말" 등 안내 레이어의
    "닫기" 버튼을 iframe(#mainFrame) 문서 안에서 찾아 자동으로 닫는다.

    "이어서 작성"(확인)을 누르면 예전 내용 위에 새로 생성한 글이 덧붙여져
    뒤죽박죽되므로, 항상 "취소"를 눌러 빈 글로 새로 시작한다. 팝업이 없으면
    아무 일도 안 하고 0을 반환한다 - 페이지마다 뜨거나 안 뜨거나 하므로 정상이다.
    """
    try:
        return await page.evaluate(_DISMISS_POPUPS_JS)
    except Exception:  # noqa: BLE001
        return 0


_DEBUG_DUMP_IFRAME_JS = r"""
() => {
  var f = document.querySelector('iframe#mainFrame');
  var doc = f && f.contentDocument;
  return doc ? doc.documentElement.outerHTML : null;
}
"""


async def _save_debug_snapshot(page, label: str) -> str | None:
    """자동 입력이 실패한 순간의 화면 캡처 + 실제 페이지/iframe HTML을 저장해둔다.

    지금까지 "도움말"/"작성 중인 글" 팝업 문제를 세 차례 고쳐봤는데(선택자 추측 ->
    다른 오픈소스 참고 -> 그래도 재현), 매번 사용자에게 개발자도구로 직접 캡처해
    보내달라고 했다가 엉뚱한 요소(우리 앱 자체의 토스트 등)를 캡처해 오는 등 시행
    착오가 컸다. 실패하는 바로 그 순간의 실제 DOM을 자동으로 남겨두면, 사용자는
    이 폴더만 통째로 보내면 되고 추측 없이 정확한 원인을 알 수 있다.

    실패해도(디스크 문제 등) 원래 에러를 절대 가리면 안 되므로 전부 best-effort다.
    """
    try:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = config.NAVER_DEBUG_DIR / f"{ts}_{label}"

        try:
            await page.screenshot(path=str(base) + ".png", full_page=True)
        except Exception:  # noqa: BLE001
            pass

        try:
            top_html = await page.content()
            (Path(str(base) + "_top.html")).write_text(top_html, encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

        try:
            iframe_html = await page.evaluate(_DEBUG_DUMP_IFRAME_JS)
            if iframe_html:
                (Path(str(base) + "_iframe.html")).write_text(iframe_html, encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

        return str(base)
    except Exception:  # noqa: BLE001
        return None


async def _click_with_recovery(page, frame, selector: str) -> None:
    """에디터 안의 요소(제목/본문)를 클릭한다.

    실제로 있었던 문제: "작성 중인 글이 있습니다" 확인창이나 "도움말" 안내 패널을 CSS
    class 선택자로 top-level page에서 찾아 미리 닫아보려 했지만, 두 차례 다 실패했다
    (알고 보니 그 팝업들은 iframe 문서 안에 있었다 - _dismiss_editor_popups 참고).
    이 함수는 그 근본 수정과는 별개로, 그래도 뭔가 예상 못한 이유로 여전히 클릭이
    막힐 때를 대비한 **선택자에 의존하지 않는** 마지막 안전망이다:
      1) 일반 클릭 시도
      2) 실패하면 Escape를 두 번 눌러본다 - 웬만한 안내 패널/확인창은 Escape로
         닫히므로, 그 팝업이 무엇이든 상관없이 통한다
      3) 그래도 실패하면 `.focus()`로 그 요소에 강제로 포커스를 준다. (주의:
         `click(force=True)`는 액셔너빌리티 "체크"만 건너뛸 뿐, 실제 클릭은 여전히
         진짜 마우스 클릭처럼 그 좌표의 화면에 실제로 보이는 요소(예: 팝업 배경)에
         전달된다 - 로컬 HTML로 직접 실험해서 확인한 사실이다. 반면 `.focus()`는
         화면에 뭐가 덮여 있든 상관없이 DOM 요소에 직접 포커스를 주므로, 그 다음
         `page.keyboard.type()`이 확실히 원하는 요소에 입력된다 - 이것도 로컬
         HTML로 overlay가 덮은 contenteditable에 실제로 타이핑되는 것까지 확인했다.
    """
    try:
        await frame.locator(selector).first.click(timeout=6000)
        return
    except Exception:  # noqa: BLE001
        pass

    await page.keyboard.press("Escape")
    await page.keyboard.press("Escape")

    try:
        await frame.locator(selector).first.click(timeout=4000)
        return
    except Exception:  # noqa: BLE001
        pass

    await frame.locator(selector).first.focus(timeout=5000)


async def _persist_session_state(context, session_blog_id) -> None:
    """이번 세션에서 갱신된 쿠키/로컬스토리지를 다시 저장한다 (best-effort).

    네이버가 "도움말 봤음" 같은 걸 브라우저 로컬스토리지에 남겨두는 방식이라면,
    매번 로그인 시점의 옛 storage_state로 새 컨텍스트를 여는 지금 구조에서는 그
    기록이 이어지지 않아 같은 안내 패널이 매번 다시 뜰 수 있다. 세션이 끝날 때마다
    최신 상태를 다시 저장해두면, 시간이 지나면서 이런 패널 자체가 안 뜨게 될 수
    있다. 실패해도 무시한다 - 로그인 자체는 이미 별도로 저장돼 있어 필수는 아니다.
    """
    try:
        updated_state = await context.storage_state()
        _save_state(updated_state, session_blog_id)
    except Exception:  # noqa: BLE001
        pass


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def parse_markdown_line(line: str) -> list[tuple[str, bool]]:
    """openai_writer가 생성한 마크다운 한 줄을 (텍스트, 볼드여부) 조각 목록으로 바꾼다.

    네이버 스마트에디터는 붙여넣은 텍스트의 "## "나 "**...**" 마크다운 문법을 그대로
    글자로 인식해버려서(즉, 그대로 넣으면 사용자가 "## 소제목" 같은 글자가 그대로
    보이는 글을 받는다), 여기서 미리 문법을 걷어내고 실제 타이핑할 때 Ctrl+B 토글로
    굵게 처리할 부분을 알려준다. 호출부(open_write_draft)가 이 목록을 그대로 타이핑하며
    bold=True인 조각 앞뒤로 Control+B를 눌러 실제 굵게 서식을 적용한다.

    "## "로 시작하는 소제목 줄은 전체를 굵게 처리하고("**"가 안에 섞여 있으면 제거만),
    일반 줄은 "**...**"로 감싼 부분만 굵게, 나머지는 평문으로 나눈다.
    """
    if line.startswith("## "):
        heading_text = line[3:].replace("**", "")
        return [(heading_text, True)] if heading_text else []

    segments: list[tuple[str, bool]] = []
    pos = 0
    for m in _BOLD_RE.finditer(line):
        if m.start() > pos:
            segments.append((line[pos : m.start()], False))
        if m.group(1):
            segments.append((m.group(1), True))
        pos = m.end()
    if pos < len(line):
        segments.append((line[pos:], False))
    return segments


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

    # 새 글쓰기 진입 시 뜨는 "쓰다 만 글 이어서 작성" 확인창(있으면 "취소"로 새 글
    # 시작) + "도움말" 등 안내 레이어 처리 (있으면 닫고, 없으면 무시). 이어서 작성
    # 확인창은 화면 전체를 덮는 배경을 깔아 다른 클릭을 다 막아버리므로 먼저 처리한다.
    await _dismiss_editor_popups(page)

    frame = page.frame_locator(EDITOR_IFRAME_SELECTOR)

    try:
        # 제목/본문 클릭 모두, 위 _dismiss_editor_popups가 뭔가를 놓쳐도 뚫고
        # 지나가도록 Escape+강제포커스 안전망을 함께 쓴다 (_click_with_recovery 설명 참고).
        await _click_with_recovery(page, frame, TITLE_SELECTOR)
        await page.keyboard.type(title, delay=15)
        await page.keyboard.press("Tab")
        # 제목을 입력하는 동안 위 팝업들이 뒤늦게 뜨는 경우가 있어, 본문을 클릭하기
        # 직전에 한 번 더 시도한다 (위 주석 참고).
        await _dismiss_editor_popups(page)
        await _click_with_recovery(page, frame, BODY_SELECTOR)
        for line in content_html.split("\n"):
            for text, bold in parse_markdown_line(line):
                if not text:
                    continue
                if bold:
                    await page.keyboard.press("Control+B")
                    await page.keyboard.type(text, delay=5)
                    await page.keyboard.press("Control+B")
                else:
                    await page.keyboard.type(text, delay=5)
            await page.keyboard.press("Enter")
    except Exception as exc:  # noqa: BLE001
        # 자동 입력이 실패해도 브라우저 창은 열어둔다 - 사용자가 직접 복사/붙여넣기 하도록.
        # (창을 닫으면 위에서 예약해둔 _watch_and_cleanup이 알아서 드라이버를 정리한다)
        # 실패한 바로 그 순간의 화면 캡처 + 실제 페이지/iframe HTML을 자동으로 남겨서,
        # 다음에 또 실패하면 추측 없이 정확한 원인을 바로 알 수 있게 한다.
        debug_path = await _save_debug_snapshot(page, "write_failed")
        debug_note = (
            f" 진단용 파일이 저장됐습니다: {debug_path}.png / _top.html / _iframe.html "
            "(이 파일들을 보내주시면 원인을 정확히 알 수 있습니다.)"
            if debug_path
            else ""
        )
        raise NaverAuthError(
            "네이버 에디터 자동 입력에 실패했습니다. 브라우저 창에 직접 붙여넣어주세요. "
            f"(상세: {exc}){debug_note}"
        )
    finally:
        # 성공/실패와 무관하게, 이번에 갱신된 쿠키/로컬스토리지를 다시 저장해둔다
        # (위 _persist_session_state 설명 참고).
        await _persist_session_state(context, session_blog_id)

    # 브라우저/컨텍스트는 의도적으로 닫지 않음 - 사용자가 검토 후 직접 발행하도록 둔다.
