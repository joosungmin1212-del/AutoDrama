import pytest

from app.services import naver_rank


def test_detect_block_true_on_captcha_page():
    html = "<html><body>비정상적인 접근이 감지되어 자동입력 방지를 위해 보안문자를 입력해주세요</body></html>"
    assert naver_rank.detect_block(html) is True


def test_detect_block_false_on_normal_page():
    html = "<html><body><div id='main_pack'><a href='https://blog.naver.com/x/1'>글</a></div></body></html>"
    assert naver_rank.detect_block(html) is False


def test_detect_block_ignores_generic_phrases_when_results_found():
    # 실제로 있었던 오탐 케이스: 정상적으로 결과가 있는 페이지인데 어딘가의 광고/위젯에
    # "잠시 후 다시 시도" 같은 흔한 문구가 들어있어도, 결과가 있으면 차단으로 보면 안 된다.
    html = "<html><body>일시적인 오류입니다. 잠시 후 다시 시도해주세요 (무관한 위젯 문구)</body></html>"
    assert naver_rank.detect_block(html, items_found=3) is False


def test_detect_block_true_only_when_no_results_and_indicator_present():
    html = "<html><body>자동입력 방지를 위해 보안문자를 입력해주세요</body></html>"
    assert naver_rank.detect_block(html, items_found=0) is True


@pytest.mark.asyncio
async def test_check_keyword_rank_raises_on_block(monkeypatch):
    async def fake_fetch(keyword, page=None, timeout_ms=15000):
        return "<html>자동입력 방지 문자를 입력해주세요</html>"

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    with pytest.raises(naver_rank.NaverBlockError):
        await naver_rank.check_keyword_rank("서상동PT", registered_blogs=[])


@pytest.mark.asyncio
async def test_check_keyword_rank_succeeds_on_normal_page(monkeypatch):
    async def fake_fetch(keyword, page=None, timeout_ms=15000):
        return (
            "<html><body><div id='main_pack'>"
            "<a href='https://blog.naver.com/mytrainer/1'>제목1</a>"
            "</div></body></html>"
        )

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    items = await naver_rank.check_keyword_rank("서상동PT", registered_blogs=[])
    assert len(items) == 1
    assert items[0].blog_id == "mytrainer"


@pytest.mark.asyncio
async def test_check_keyword_rank_does_not_false_positive_on_unrelated_widget_text(monkeypatch):
    """실사용자가 겪은 오탐 재현: 정상 결과가 있는데도 차단으로 잘못 판단해서 실패했던 버그."""

    async def fake_fetch(keyword, page=None, timeout_ms=15000):
        return (
            "<html><body>"
            "<div id='main_pack'><a href='https://blog.naver.com/mytrainer/1'>서상동PT 후기</a></div>"
            "<div class='unrelated-widget'>일시적인 오류입니다. 잠시 후 다시 시도해주세요.</div>"
            "</body></html>"
        )

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    items = await naver_rank.check_keyword_rank("서상동pt", registered_blogs=[])
    assert len(items) == 1
