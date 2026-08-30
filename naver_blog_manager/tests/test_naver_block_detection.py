import pytest

from app.services import naver_rank


def test_detect_block_true_on_captcha_page():
    html = "<html><body>비정상적인 접근이 감지되어 자동입력 방지를 위해 보안문자를 입력해주세요</body></html>"
    assert naver_rank.detect_block(html) is True


def test_detect_block_false_on_normal_page():
    html = "<html><body><div id='main_pack'><a href='https://blog.naver.com/x/1'>글</a></div></body></html>"
    assert naver_rank.detect_block(html) is False


@pytest.mark.asyncio
async def test_check_keyword_rank_raises_on_block(monkeypatch):
    async def fake_fetch(keyword, timeout_ms=15000):
        return "<html>자동입력 방지 문자를 입력해주세요</html>"

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    with pytest.raises(naver_rank.NaverBlockError):
        await naver_rank.check_keyword_rank("서상동PT", registered_blogs=[])


@pytest.mark.asyncio
async def test_check_keyword_rank_succeeds_on_normal_page(monkeypatch):
    async def fake_fetch(keyword, timeout_ms=15000):
        return (
            "<html><body><div id='main_pack'>"
            "<a href='https://blog.naver.com/mytrainer/1'>제목1</a>"
            "</div></body></html>"
        )

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    items = await naver_rank.check_keyword_rank("서상동PT", registered_blogs=[])
    assert len(items) == 1
    assert items[0].blog_id == "mytrainer"
