"""_try_close_popup() / _try_dismiss_resume_draft_dialog() 유닛 테스트.

실제 사용자가 겪은 문제: "도움말"(What's New) 안내 패널이 페이지 진입 직후가 아니라
제목을 입력하는 동안 뒤늦게 뜨면서, 팝업 닫기 시도가 한 번뿐이라 본문 클릭이 그 패널에
가려 타임아웃났다. 이 테스트는 실제 Playwright 브라우저 없이 가짜(duck-typed) Page로
_try_close_popup()이 (1) 팝업이 있을 때 실제로 클릭하고 (2) 없을 때(타임아웃/예외)도
예외를 삼키고 조용히 리턴하는지만 검증한다 - 여러 시점에서 다시 불러도 안전하다는 것.
실제 네이버 페이지에서 "언제 팝업이 뜨는지"까지는 이 샌드박스에서 검증할 수 없다
(README에 명시된 것처럼 실사이트 검증은 사용자 PC 몫).

_try_dismiss_resume_draft_dialog()는 실제 사용자가 겪은 두 번째 문제("작성 중인 글이
있습니다 - 이어서 작성하시겠습니까?" 확인창이 자동으로 안 닫혀서 화면 전체를 덮는
배경이 이후 모든 클릭을 막아버린 문제)를 재현/검증한다. 이 확인창의 실제 DOM 구조는
사용자가 캡처해준 오류 로그(data-group="popupLayer", data-name="se-popup-alert
se-popup-confirm")로 확인된 값이라 추측이 아니다.
"""
import pytest

from app.services.naver_browser import (
    RESUME_DRAFT_CANCEL_SELECTOR,
    _try_close_popup,
    _try_dismiss_resume_draft_dialog,
)


class _FakeLocator:
    def __init__(self, click_impl):
        self._click_impl = click_impl

    @property
    def first(self):
        return self

    async def click(self, timeout=None):
        await self._click_impl(timeout)


class _FakePage:
    def __init__(self, click_impl):
        self.locator_calls: list[str] = []
        self._click_impl = click_impl

    def locator(self, selector):
        self.locator_calls.append(selector)
        return _FakeLocator(self._click_impl)


@pytest.mark.asyncio
async def test_try_close_popup_clicks_when_popup_present():
    clicked = []

    async def click_impl(timeout):
        clicked.append(timeout)

    page = _FakePage(click_impl)
    await _try_close_popup(page)

    assert clicked == [1500]
    assert page.locator_calls == [
        ".se-popup-button-cancel, button.se-help-panel-close-button"
    ]


@pytest.mark.asyncio
async def test_try_close_popup_swallows_error_when_popup_absent():
    """팝업이 없어 클릭이 타임아웃/예외가 나도 예외를 밖으로 던지지 않아야 한다 -
    호출부가 매번 try/except 없이 안전하게 여러 번 부를 수 있어야 하므로."""

    async def click_impl(timeout):
        raise TimeoutError("no such element")

    page = _FakePage(click_impl)
    await _try_close_popup(page)  # 예외 없이 조용히 리턴하면 통과


@pytest.mark.asyncio
async def test_try_close_popup_can_be_called_multiple_times_safely():
    """실제 호출부(open_write_draft)가 페이지 진입 직후 + 본문 클릭 직전, 두 번
    부르므로 - 연달아 여러 번 불러도 매번 독립적으로 안전해야 한다."""
    calls = []

    async def click_impl(timeout):
        calls.append(timeout)

    page = _FakePage(click_impl)
    await _try_close_popup(page)
    await _try_close_popup(page)

    assert calls == [1500, 1500]


@pytest.mark.asyncio
async def test_try_dismiss_resume_draft_dialog_clicks_cancel_scoped_to_popup_layer():
    """항상 "취소"를 눌러 새 글로 시작해야 한다 - "확인"(이어서 작성)을 누르면 예전
    내용 위에 새 글이 덧붙여져 뒤죽박죽되므로. 선택자도 popupLayer 안으로 좁혀서
    엉뚱한 "취소" 버튼(다른 UI 요소)을 잘못 누르지 않게 한다."""
    clicked = []

    async def click_impl(timeout):
        clicked.append(timeout)

    page = _FakePage(click_impl)
    await _try_dismiss_resume_draft_dialog(page)

    assert clicked == [1500]
    assert page.locator_calls == [RESUME_DRAFT_CANCEL_SELECTOR]
    assert '[data-group="popupLayer"]' in RESUME_DRAFT_CANCEL_SELECTOR
    assert "취소" in RESUME_DRAFT_CANCEL_SELECTOR


@pytest.mark.asyncio
async def test_try_dismiss_resume_draft_dialog_swallows_error_when_absent():
    """대부분의 경우(쓰다 만 글이 없을 때)엔 이 확인창 자체가 안 뜨므로, 선택자가
    안 잡혀 예외가 나도 조용히 넘어가야 한다."""

    async def click_impl(timeout):
        raise TimeoutError("no such element")

    page = _FakePage(click_impl)
    await _try_dismiss_resume_draft_dialog(page)  # 예외 없이 조용히 리턴하면 통과
