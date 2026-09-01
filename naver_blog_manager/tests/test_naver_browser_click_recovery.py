"""_click_with_recovery() / _persist_session_state() 유닛 테스트.

실제로 있었던 문제: 사용자가 "네이버로 보내기"를 두 번 시도했는데, 둘 다 팝업(먼저
"작성 중인 글이 있습니다" 확인창, 그 다음 "도움말" 안내 패널)에 화면이 가려 자동
클릭이 막혔고, 그때마다 선택자 기반 팝업닫기 시도가 top-level page를 뒤졌지만 실제
팝업은 iframe 문서 안에 있어서 실패했다(근본 수정은 _dismiss_editor_popups 참고) -
결국 사용자가 직접 "취소"를 눌러야 했다. 이 헬퍼는 그와는 별개로, 그래도 뭔가로
클릭이 막힐 때를 대비한 선택자 무관 최종 안전망이다: 일반
클릭 -> Escape 두 번 후 재시도 -> 그래도 안 되면 `.focus()`로 강제 포커스. (처음엔
`click(force=True)`를 마지막 단계로 썼는데, 로컬 HTML 실험으로 force=True도 실제
화면 좌표의 진짜 클릭이라 팝업이 여전히 가로챈다는 걸 확인하고 `.focus()`로
바꿨다 - `.focus()`는 화면에 뭐가 덮여 있든 상관없이 그 DOM 요소에 직접 포커스를
준다.) 아래 테스트는 실제 Playwright 브라우저 없이 가짜(duck-typed) 객체로 이
3단계 흐름을 검증한다.
"""
import pytest

from app.services.naver_browser import _click_with_recovery, _persist_session_state


class _FakeLocator:
    def __init__(self, click_impl, focus_impl=None):
        self._click_impl = click_impl
        self._focus_impl = focus_impl
        self.focus_calls: list[int | None] = []

    @property
    def first(self):
        return self

    async def click(self, timeout=None, force=False):
        await self._click_impl(timeout=timeout, force=force)

    async def focus(self, timeout=None):
        self.focus_calls.append(timeout)
        if self._focus_impl is not None:
            await self._focus_impl(timeout=timeout)


class _FakeFrame:
    def __init__(self, click_impl, focus_impl=None):
        self.locator_calls: list[str] = []
        self._click_impl = click_impl
        self._focus_impl = focus_impl
        self._locator = None

    def locator(self, selector):
        self.locator_calls.append(selector)
        # 매번 같은 인스턴스를 돌려줘서 테스트에서 focus_calls를 확인할 수 있게 한다
        if self._locator is None:
            self._locator = _FakeLocator(self._click_impl, self._focus_impl)
        return self._locator


class _FakePage:
    def __init__(self):
        self.escape_presses = 0

    class _Keyboard:
        def __init__(self, outer):
            self._outer = outer

        async def press(self, key):
            if key == "Escape":
                self._outer.escape_presses += 1

    @property
    def keyboard(self):
        return self._Keyboard(self)


@pytest.mark.asyncio
async def test_click_with_recovery_succeeds_on_first_try_without_escape_or_focus():
    calls = []

    async def click_impl(timeout, force):
        calls.append((timeout, force))

    page = _FakePage()
    frame = _FakeFrame(click_impl)
    await _click_with_recovery(page, frame, ".se-title-text")

    assert calls == [(6000, False)]
    assert page.escape_presses == 0


@pytest.mark.asyncio
async def test_click_with_recovery_presses_escape_and_retries_when_first_click_fails():
    calls = []
    attempt = {"n": 0}

    async def click_impl(timeout, force):
        attempt["n"] += 1
        calls.append((timeout, force))
        if attempt["n"] == 1:
            raise TimeoutError("subtree intercepts pointer events")
        # 두 번째 시도(Escape 이후)는 성공

    page = _FakePage()
    frame = _FakeFrame(click_impl)
    await _click_with_recovery(page, frame, ".se-main-container")

    assert calls == [(6000, False), (4000, False)]
    assert page.escape_presses == 2  # Escape를 두 번 누른다


@pytest.mark.asyncio
async def test_click_with_recovery_focuses_as_last_resort_not_force_click():
    """일반 클릭도, Escape 후 재시도도 실패하면 마지막엔 `.focus()`로 강제 포커스를
    준다 - `click(force=True)`가 아니다. 로컬 HTML 실험으로 force=True는 실제
    화면 좌표의 진짜 클릭이라 팝업이 여전히 그 클릭을 가로채지만, `.focus()`는
    화면에 뭐가 덮여 있든 상관없이 그 DOM 요소에 직접 포커스를 준다는 걸 확인했다."""
    click_calls = []

    async def click_impl(timeout, force):
        click_calls.append((timeout, force))
        raise TimeoutError("subtree intercepts pointer events")  # 클릭은 항상 실패

    page = _FakePage()
    frame = _FakeFrame(click_impl)
    await _click_with_recovery(page, frame, ".se-main-container")

    # 클릭은 두 번(일반 + Escape 후 재시도)만 시도되고, force=True로는 절대 안 부른다
    assert click_calls == [(6000, False), (4000, False)]
    assert all(force is False for _, force in click_calls)
    assert page.escape_presses == 2
    assert frame._locator.focus_calls == [5000]


@pytest.mark.asyncio
async def test_click_with_recovery_propagates_error_when_even_focus_fails():
    """세 단계 다 실패하면(정말 뭔가 크게 잘못된 상황) 예외를 그대로 던져서 호출부가
    "자동 입력 실패" 에러로 사용자에게 알릴 수 있어야 한다 - 조용히 삼키면 안 된다."""

    async def click_impl(timeout, force):
        raise TimeoutError("여전히 실패")

    async def focus_impl(timeout):
        raise TimeoutError("포커스도 실패")

    page = _FakePage()
    frame = _FakeFrame(click_impl, focus_impl)

    with pytest.raises(TimeoutError):
        await _click_with_recovery(page, frame, ".se-main-container")


@pytest.mark.asyncio
async def test_persist_session_state_saves_updated_state(monkeypatch):
    saved = {}

    def fake_save_state(state, blog_id):
        saved["state"] = state
        saved["blog_id"] = blog_id

    monkeypatch.setattr("app.services.naver_browser._save_state", fake_save_state)

    class _FakeContext:
        async def storage_state(self):
            return {"cookies": [{"name": "NID_AUT", "value": "x"}], "origins": []}

    await _persist_session_state(_FakeContext(), "sm_main")

    assert saved == {
        "state": {"cookies": [{"name": "NID_AUT", "value": "x"}], "origins": []},
        "blog_id": "sm_main",
    }


@pytest.mark.asyncio
async def test_persist_session_state_swallows_error():
    """저장 중 뭔가 실패해도(디스크 문제 등) 조용히 넘어가야 한다 - 로그인 자체는
    이미 별도로 저장돼 있어 이건 부가적인 개선일 뿐 필수가 아니므로."""

    class _FakeContext:
        async def storage_state(self):
            raise RuntimeError("boom")

    await _persist_session_state(_FakeContext(), "sm_main")  # 예외 없이 조용히 리턴하면 통과
