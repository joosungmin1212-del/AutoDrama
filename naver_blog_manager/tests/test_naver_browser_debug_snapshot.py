"""_save_debug_snapshot() 유닛 테스트.

지금까지 "도움말"/"작성 중인 글" 팝업 문제를 세 차례 고쳐봤는데도 재현됐고, 매번
사용자에게 개발자도구로 직접 캡처해 보내달라고 부탁했다가 엉뚱한 요소(우리 앱 자체의
토스트 등)를 캡처해 오는 시행착오가 있었다. 그래서 실패하는 바로 그 순간의 화면
캡처 + 실제 페이지/iframe HTML을 자동으로 남기도록 만들었다 - 이 테스트는 가짜
Page로 (1) 정상적으로 세 파일이 저장되는지, (2) 일부가 실패해도(예: iframe이 없어
None을 리턴) 나머지는 저장되고 원래 에러를 가리지 않는지 확인한다.
"""
import pytest

from app.services import naver_browser


class _FakePage:
    def __init__(self, iframe_html=None, fail_screenshot=False, fail_content=False):
        self._iframe_html = iframe_html
        self._fail_screenshot = fail_screenshot
        self._fail_content = fail_content
        self.screenshot_calls = []

    async def screenshot(self, path, full_page=False):
        if self._fail_screenshot:
            raise RuntimeError("스크린샷 실패")
        self.screenshot_calls.append((path, full_page))
        with open(path, "wb") as f:
            f.write(b"fake-png-bytes")

    async def content(self):
        if self._fail_content:
            raise RuntimeError("content 실패")
        return "<html><body>top page</body></html>"

    async def evaluate(self, js):
        return self._iframe_html


@pytest.mark.asyncio
async def test_save_debug_snapshot_writes_all_three_files(tmp_path, monkeypatch):
    monkeypatch.setattr(naver_browser.config, "NAVER_DEBUG_DIR", tmp_path)

    page = _FakePage(iframe_html="<html><body>iframe content</body></html>")
    base = await naver_browser._save_debug_snapshot(page, "write_failed")

    assert base is not None
    from pathlib import Path

    assert Path(base + ".png").read_bytes() == b"fake-png-bytes"
    assert "top page" in Path(base + "_top.html").read_text(encoding="utf-8")
    assert "iframe content" in Path(base + "_iframe.html").read_text(encoding="utf-8")
    assert "write_failed" in base


@pytest.mark.asyncio
async def test_save_debug_snapshot_skips_iframe_file_when_no_iframe_found(tmp_path, monkeypatch):
    """실패 시점에 iframe이 아예 없었다면(iframe_html이 None) 그 파일만 건너뛰고
    나머지(스크린샷, 최상위 페이지 HTML)는 정상적으로 저장돼야 한다."""
    monkeypatch.setattr(naver_browser.config, "NAVER_DEBUG_DIR", tmp_path)

    page = _FakePage(iframe_html=None)
    base = await naver_browser._save_debug_snapshot(page, "write_failed")

    from pathlib import Path

    assert base is not None
    assert Path(base + ".png").exists()
    assert Path(base + "_top.html").exists()
    assert not Path(base + "_iframe.html").exists()


@pytest.mark.asyncio
async def test_save_debug_snapshot_never_raises_even_if_everything_fails(tmp_path, monkeypatch):
    """진단 파일 저장 자체가 실패해도(디스크 문제 등) 원래 에러를 절대 가리면 안
    된다 - 호출부가 예외 없이 None을 받을 수 있어야 한다."""
    monkeypatch.setattr(naver_browser.config, "NAVER_DEBUG_DIR", tmp_path)

    page = _FakePage(fail_screenshot=True, fail_content=True, iframe_html=None)
    result = await naver_browser._save_debug_snapshot(page, "write_failed")
    # 스크린샷/HTML 저장이 전부 실패해도 예외 없이 (경로 문자열 또는 None) 리턴한다
    assert result is None or isinstance(result, str)
