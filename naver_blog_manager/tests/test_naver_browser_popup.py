"""_dismiss_editor_popups() 테스트.

실제로 있었던 문제: "작성 중인 글이 있습니다" 확인창과 "도움말" 안내 패널을 두 차례에
걸쳐 CSS class 선택자로 top-level page에서 찾아 닫으려 했지만 둘 다 실패했다 - 사용자가
결국 직접 "취소"를 눌러야 했다. 다른 개발자가 실제로 검증한 오픈소스 구현(MIT 라이선스:
csh1668/naver-blog-automation, app/src/main/assets/editor_bridge.js)을 참고해서 알아낸
사실: 이 팝업들은 top-level page가 아니라 iframe(#mainFrame) 문서 "안"에 있었다 -
page.locator()로는 애초에 보이지 않는 곳을 찾고 있었던 것. 그래서 class 이름 대신
"정확한 버튼 텍스트('취소'/'닫기') + 팝업 컨테이너(role=dialog 또는 layer/popup/modal/
dialog 클래스) 안에서만"이라는, iframe 문서를 직접 훑는 JS로 재작성했다.

아래는 (1) 순수 래�퍼 로직(page.evaluate 호출/예외 처리)을 가짜 page로 검증하는
유닛 테스트, (2) 실제 Playwright로 iframe#mainFrame 안에 두 팝업을 진짜로 만들어놓고
JS가 실제로 올바른 버튼만 골라 클릭하는지 확인하는 통합 테스트다.
"""
import pytest

from app.services.naver_browser import _dismiss_editor_popups


@pytest.mark.asyncio
async def test_dismiss_editor_popups_returns_evaluate_result():
    async def fake_evaluate(js):
        assert "작성 중인 글이 있습니다" in js
        assert "닫기" in js
        return 2

    class _FakePage:
        evaluate = staticmethod(fake_evaluate)

    assert await _dismiss_editor_popups(_FakePage()) == 2


@pytest.mark.asyncio
async def test_dismiss_editor_popups_swallows_error_and_returns_zero():
    class _FakePage:
        async def evaluate(self, js):
            raise RuntimeError("boom")

    assert await _dismiss_editor_popups(_FakePage()) == 0


@pytest.mark.asyncio
async def test_dismiss_editor_popups_real_browser_clicks_correct_buttons_only():
    """실제 Playwright + 실제 DOM으로, iframe#mainFrame 안에 두 팝업(작성 중인 글
    확인창 + 도움말 레이어)을 만들어두고, JS가 정확히 그 안의 "취소"/"닫기" 버튼만
    누르고 - 툴바에 있는 동명 버튼이나 다른 텍스트 버튼은 절대 안 누르는지 확인한다."""
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=True)
    except Exception as exc:  # noqa: BLE001
        await playwright.stop()
        pytest.skip(f"이 환경에 pip playwright 버전과 맞는 Chromium이 설치돼 있지 않음: {exc}")

    try:
        page = await browser.new_page()

        iframe_html = """
        <html><body>
          <div class="toolbar"><button>취소</button></div>

          <div role="dialog" class="se-popup-alert-confirm">
            <p>작성 중인 글이 있습니다. 이어서 작성하시겠습니까?</p>
            <button onclick="window.__confirmClicked=true">확인</button>
            <button onclick="window.__cancelClicked=true">취소</button>
          </div>

          <div class="se-help-panel-layer">
            <p>도움말</p>
            <button onclick="window.__closeClicked=true">닫기</button>
          </div>

          <div class="se-title-text" contenteditable="true"></div>
          <div class="se-main-container" contenteditable="true"></div>
        </body></html>
        """
        outer_html = (
            "<html><body>"
            f'<iframe id="mainFrame" srcdoc="{iframe_html.replace(chr(34), "&quot;")}"'
            ' style="width:900px;height:700px;border:none;"></iframe>'
            "</body></html>"
        )
        await page.set_content(outer_html)
        await page.wait_for_timeout(300)

        count = await _dismiss_editor_popups(page)
        assert count == 2  # 확인창의 취소 + 도움말의 닫기, 딱 둘

        frame = page.frame_locator("iframe#mainFrame")
        cancel_clicked = await frame.locator("body").evaluate("() => !!window.__cancelClicked")
        confirm_clicked = await frame.locator("body").evaluate("() => !!window.__confirmClicked")
        close_clicked = await frame.locator("body").evaluate("() => !!window.__closeClicked")

        assert cancel_clicked is True  # "이어서 작성"이 아니라 "취소"를 눌러야 함
        assert confirm_clicked is False
        assert close_clicked is True
    finally:
        await browser.close()
        await playwright.stop()
