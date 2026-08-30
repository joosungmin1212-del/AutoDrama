import pytest

from app.services import naver_rank


class FakePage:
    """Playwright Page 흉내 - fetch_view_html(page=...)가 새 브라우저를 켜지 않고
    넘겨받은 page를 그대로 재사용하는지 확인하기 위한 더블."""

    def __init__(self, html: str):
        self._html = html
        self.goto_calls: list[str] = []

    async def goto(self, url, wait_until=None, timeout=None):
        self.goto_calls.append(url)

    async def wait_for_selector(self, selector, timeout=None):
        raise TimeoutError("no selector in fake page - should be swallowed")

    async def content(self) -> str:
        return self._html


@pytest.mark.asyncio
async def test_fetch_view_html_reuses_given_page_without_launching_browser():
    fake_page = FakePage("<html><body><div id='main_pack'></div></body></html>")

    html = await naver_rank.fetch_view_html("서상동PT", page=fake_page)

    assert html == "<html><body><div id='main_pack'></div></body></html>"
    assert len(fake_page.goto_calls) == 1
    assert "서상동PT" in fake_page.goto_calls[0] or "%EC" in fake_page.goto_calls[0]


@pytest.mark.asyncio
async def test_check_keyword_rank_passes_page_through(monkeypatch):
    fake_page = FakePage("<html><body><div id='main_pack'></div></body></html>")
    seen = {}

    async def fake_fetch(keyword, page=None, timeout_ms=20000):
        seen["page"] = page
        return "<html><body><div id='main_pack'></div></body></html>"

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    await naver_rank.check_keyword_rank("서상동PT", registered_blogs=[], page=fake_page)

    assert seen["page"] is fake_page
