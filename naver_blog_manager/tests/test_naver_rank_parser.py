import pytest

from app.services import naver_rank
from app.services.naver_rank import parse_view_html

# 실제 네이버 마크업을 그대로 흉내낸 것이 아니라, parse_view_html이 의존하는 "본문 영역 안의
# blog.naver.com/cafe.naver.com 링크를 순서대로, 중복 없이, 광고 영역은 제외하고" 뽑아내는
# 동작 자체를 검증하기 위한 대표 구조다. 실제 네이버 마크업이 바뀌면 naver_rank.py의 선택자만
# 조정하면 되고, 이 테스트의 기대값(등장 순서 유지/중복 제거/광고 제외)은 그대로 유효해야 한다.
FIXTURE_HTML = """
<html><body>
<div id="main_pack">
  <div class="power_link_area">
    <a href="https://blog.naver.com/adblog1/999">광고 블로그는 제외되어야 함</a>
  </div>
  <ul class="view_list">
    <li class="bx">
      <a href="https://blog.naver.com/wonjang_pt/223451"><img src="thumb1.jpg"/></a>
      <a href="https://blog.naver.com/wonjang_pt/223451">1위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/other_person/223452">2위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://cafe.naver.com/somecafe/555">3위 카페글 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/leesuseok_pt/223454">4위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/other2/223455">5위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/other3/223456">6위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/other4/223457">7위 포스팅 제목</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/other5/223458">8위 (TOP7 밖이라 제외되어야 함)</a>
    </li>
  </ul>
</div>
</body></html>
"""


def test_parse_view_html_returns_top_n_in_order():
    items = parse_view_html(FIXTURE_HTML, top_n=7)
    assert len(items) == 7
    assert [i.position for i in items] == [1, 2, 3, 4, 5, 6, 7]
    assert items[0].blog_id == "wonjang_pt"
    assert items[0].content_type == "blog"
    assert items[2].content_type == "cafe"
    assert items[2].blog_id == "somecafe"


def test_parse_view_html_excludes_ads():
    items = parse_view_html(FIXTURE_HTML, top_n=7)
    assert all(i.blog_id != "adblog1" for i in items)


def test_parse_view_html_dedupes_thumbnail_and_title_links():
    items = parse_view_html(FIXTURE_HTML, top_n=7)
    wonjang_items = [i for i in items if i.blog_id == "wonjang_pt"]
    assert len(wonjang_items) == 1


def test_parse_view_html_empty_html_returns_empty_list():
    assert parse_view_html("<html><body></body></html>") == []


# 실제로 보고된 버그: 네이버 결과 카드가 "썸네일(장식용) 앵커 + 진짜 제목 앵커" 순서로
# 나오는데, 장식용 앵커 안에 스크린리더용 안내문구("새 창 열림")가 텍스트로 들어있어서
# (화면엔 안 보이지만 get_text()엔 잡힘) 이걸 "제목 있는 링크"로 착각해 그 자리를
# 차지해버리고, 정작 진짜 제목이 있는 뒤의 앵커는 "이미 처리된 글"로 건너뛰어졌다.
# 그 결과 대시보드에 제목이 "새 창 열림"으로만 보이고, 등록된 블로그 매칭에도 실패했다.
NOISY_FIXTURE_HTML = """
<html><body>
<div id="main_pack">
  <ul class="view_list">
    <li class="bx">
      <a href="https://blog.naver.com/systempt_cw/223999001">
        <img src="thumb.jpg"/><span class="blind">새 창 열림</span>
      </a>
      <a href="https://blog.naver.com/systempt_cw/223999001">창원 의창구서상동 pt샵 견적문의</a>
    </li>
    <li class="bx">
      <a href="https://blog.naver.com/reviewer1/223999002">서상동PT헬스와피티를 꾸준히 하는데 왜 몸은 그대로일까<span class="blind">새 창 열림</span></a>
    </li>
  </ul>
</div>
</body></html>
"""


def test_parse_view_html_ignores_screen_reader_only_noise_text():
    items = parse_view_html(NOISY_FIXTURE_HTML, top_n=7)
    assert len(items) == 2
    assert items[0].title == "창원 의창구서상동 pt샵 견적문의"
    assert items[0].blog_id == "systempt_cw"
    assert items[1].title == "서상동PT헬스와피티를 꾸준히 하는데 왜 몸은 그대로일까"
    assert "새 창 열림" not in items[0].title
    assert "새 창 열림" not in items[1].title


def test_parse_view_html_skips_anchor_with_only_noise_text():
    html = """
    <div id="main_pack">
      <a href="https://blog.naver.com/onlynoise/1"><span class="blind">새 창 열림</span></a>
    </div>
    """
    assert parse_view_html(html) == []


def test_parse_view_html_merges_same_path_anchors_despite_different_query_string():
    """같은 글을 가리키는 앵커라도 쿼리스트링(추적 파라미터 등)만 다를 수 있다 - 경로가
    같으면 같은 글로 묶여서, 장식용 앵커의 노이즈 텍스트 대신 실제 제목이 채택돼야 한다."""
    html = """
    <div id="main_pack">
      <a href="https://blog.naver.com/systempt_cw/223999001?frm=viewshelf"><span class="blind">새 창 열림</span></a>
      <a href="https://blog.naver.com/systempt_cw/223999001">진짜 제목입니다</a>
    </div>
    """
    items = parse_view_html(html)
    assert len(items) == 1
    assert "223999001" in items[0].url
    assert items[0].title == "진짜 제목입니다"


def test_parse_view_html_keeps_title_over_longer_snippet_link():
    """실제로 있었던 회귀 버그: 제목 링크와 본문 미리보기(snippet) 링크가 같은 글(URL)을
    공유할 때, "더 긴 텍스트를 우선"하는 방식으로 고치자 훨씬 긴 본문 미리보기 문단이
    "제목"으로 나와버렸다(제목이 본문 요약처럼 보임). 화면에 제목이 미리보기보다 먼저
    나오는 순서를 그대로 믿고, 먼저 나온 진짜 텍스트를 title로 써야 한다."""
    html = """
    <div id="main_pack">
      <a href="https://blog.naver.com/systempt_cw/223999001" class="title_link">진짜 짧은 제목</a>
      <a href="https://blog.naver.com/systempt_cw/223999001" class="dsc_link">
        여기는 훨씬 긴 본문 미리보기 문단입니다 실제 제목보다 글자 수가 훨씬 많고 검색결과
        스니펫으로 보여지는 부분이라 제목으로 쓰이면 안 됩니다.
      </a>
    </div>
    """
    items = parse_view_html(html)
    assert len(items) == 1
    assert items[0].title == "진짜 짧은 제목"


def test_parse_view_html_skips_author_profile_home_link():
    """실제로 사용자가 보내준 네이버 검색결과 원본 HTML에서 확인된 버그: 작성자
    프로필/닉네임 앵커가 글이 아니라 블로그 홈(글 번호 없음)으로 연결되는데, 이걸 별개의
    검색결과로 잘못 집계해서 "빅스짐 중동점 점장 변효성" 같은 사람 이름이 제목 자리를
    차지하며 TOP7 한 자리를 빼앗아갔다. 작성자 홈 링크는 결과에서 아예 제외돼야 하고,
    실제 글 앵커의 진짜 제목만 하나의 결과로 남아야 한다."""
    html = """
    <div id="main_pack">
      <div data-template-id="articleSource">
        <a href="https://blog.naver.com/bhy0565">
          <span>빅스짐 중동점 점장 변효성</span>
          <span class="blind">새 창 열림</span>
        </a>
      </div>
      <div>
        <a href="https://blog.naver.com/bhy0565/224380926951" class="title_link">
          <span>서상동PT 헬스와 피티를 꾸준히 하는데 왜 몸은 그대로일까</span>
          <span class="blind">새 창 열림</span>
        </a>
        <a href="https://blog.naver.com/bhy0565/224380926951" class="dsc_link">
          <span>프로그램입니다 운동을 시작해야겠다고 다짐한 회원님들을 위한 이야기...</span>
          <span class="blind">새 창 열림</span>
        </a>
      </div>
    </div>
    """
    items = parse_view_html(html)
    assert len(items) == 1
    assert items[0].blog_id == "bhy0565"
    assert items[0].title == "서상동PT 헬스와 피티를 꾸준히 하는데 왜 몸은 그대로일까"
    assert "변효성" not in items[0].title


def test_parse_view_html_home_link_alone_produces_no_result():
    """글 번호 없는 작성자 홈 링크만 있고 실제 글 앵커가 아예 없으면(예: 파싱 못한 카드),
    가짜 결과를 만들지 말고 그냥 아무 것도 반환하지 않아야 한다."""
    html = """
    <div id="main_pack">
      <a href="https://blog.naver.com/bhy0565">작성자 닉네임</a>
    </div>
    """
    assert parse_view_html(html) == []


def test_parse_view_html_scopes_to_ugc_item_cards_when_present():
    """실제 네이버 VIEW 페이지에서는 인기글 카드 하나하나가
    [data-template-id="ugcItem"]로 감싸여 있다 - 이 컨테이너가 있으면 그 밖(연관검색어,
    "다른 사람들이 많이 찾는" 등)에 우연히 있는 blog/cafe 링크는 인기글 결과로 잡히면
    안 되고, 카드 안에서는 대표 글 하나만 결과가 돼야 한다."""
    html = """
    <div id="main_pack">
      <div class="related_srch">
        <a href="https://blog.naver.com/unrelated_widget/1">연관검색어 옆 위젯에 우연히 있는 블로그 링크</a>
      </div>
      <div data-template-id="ugcItem" data-template-type="searchBasic">
        <div data-template-id="articleSource">
          <a href="https://blog.naver.com/bhy0565">
            <span>작성자 닉네임</span>
          </a>
        </div>
        <div>
          <a href="https://blog.naver.com/bhy0565/224380926951" class="title_link">
            <span>진짜 인기글 제목 1</span>
          </a>
          <a href="https://blog.naver.com/bhy0565/224380926951" class="dsc_link">
            <span>훨씬 긴 본문 미리보기 문단...</span>
          </a>
        </div>
      </div>
      <div data-template-id="ugcItem" data-template-type="searchBasic">
        <a href="https://cafe.naver.com/somecafe/2">
          <span>진짜 인기글 제목 2</span>
        </a>
      </div>
    </div>
    """
    items = parse_view_html(html)
    assert len(items) == 2
    assert items[0].title == "진짜 인기글 제목 1"
    assert items[0].blog_id == "bhy0565"
    assert items[1].title == "진짜 인기글 제목 2"
    assert items[1].blog_id == "somecafe"
    assert all(i.blog_id != "unrelated_widget" for i in items)


def test_parse_view_html_falls_back_to_wide_scan_without_ugc_item_markers():
    """ugcItem 컨테이너가 없는(구버전/다른 마크업) 페이지에서는 예전처럼 본문 전체를
    넓게 훑는 방식으로 계속 동작해야 한다 - 기존 FIXTURE_HTML 테스트들이 이를 검증한다."""
    html = """
    <div id="main_pack">
      <a href="https://blog.naver.com/plainlist/1">ugcItem 없이도 잡혀야 하는 글</a>
    </div>
    """
    items = parse_view_html(html)
    assert len(items) == 1
    assert items[0].title == "ugcItem 없이도 잡혀야 하는 글"


class _FakeBlog:
    def __init__(self, blog_id, role):
        self.blog_id = blog_id
        self.role = role


@pytest.mark.asyncio
async def test_check_keyword_rank_matches_registered_blog_despite_noise_text(monkeypatch):
    """실제로 있었던 문제 재현: 등록해둔 블로그의 글이 검색결과에 실제로 있는데도,
    장식용 앵커의 "새 창 열림" 텍스트 때문에 대시보드에서 매칭 실패로 보이던 상황."""

    async def fake_fetch(keyword, page=None, timeout_ms=15000):
        return NOISY_FIXTURE_HTML

    monkeypatch.setattr(naver_rank, "fetch_view_html", fake_fetch)

    registered = [_FakeBlog("systempt_cw", "staff")]
    items = await naver_rank.check_keyword_rank("서상동PT", registered_blogs=registered)

    assert len(items) == 2
    matched = next(i for i in items if i.blog_id == "systempt_cw")
    assert matched.ownership == "ours_staff"
    assert matched.title == "창원 의창구서상동 pt샵 견적문의"
