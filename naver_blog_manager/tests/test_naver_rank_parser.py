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
