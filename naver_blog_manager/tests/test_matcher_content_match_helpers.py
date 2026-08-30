from app.services import matcher


def test_extract_post_key_blog_post():
    assert matcher.extract_post_key("https://blog.naver.com/mytrainer/223456789") == "blog:mytrainer:223456789"


def test_extract_post_key_stable_across_query_string_changes():
    # 같은 글인데 쿼리스트링(예: 추적용 파라미터)만 다른 경우에도 같은 키가 나와야 한다
    a = matcher.extract_post_key("https://blog.naver.com/mytrainer/223456789?from=search")
    b = matcher.extract_post_key("https://blog.naver.com/mytrainer/223456789")
    assert a == b


def test_extract_post_key_postview_query_param():
    url = "https://blog.naver.com/PostView.naver?blogId=mytrainer&logNo=223456789"
    assert matcher.extract_post_key(url) == "blog:mytrainer:223456789"


def test_extract_post_key_cafe_new_format():
    url = "https://cafe.naver.com/ca-fe/cafes/12345/articles/987"
    assert matcher.extract_post_key(url) == "cafe:12345:987"


def test_extract_post_key_cafe_old_format():
    assert matcher.extract_post_key("https://cafe.naver.com/somecafe/555") == "cafe:somecafe:555"


def test_extract_post_key_empty_for_empty_url():
    assert matcher.extract_post_key("") == ""


def test_find_name_match_returns_matched_name():
    watch_names = ["OO PT샵", "원장", "이수석"]
    assert matcher.find_name_match("원장이 알려주는 서상동PT 팁", watch_names) == "원장"


def test_find_name_match_case_insensitive():
    assert matcher.find_name_match("OO pt샵 다녀왔어요", ["OO PT샵"]) == "OO PT샵"


def test_find_name_match_none_when_nothing_matches():
    assert matcher.find_name_match("전혀 관련없는 글입니다", ["OO PT샵", "원장"]) is None


def test_find_name_match_empty_title_or_names():
    assert matcher.find_name_match("", ["원장"]) is None
    assert matcher.find_name_match("원장이 최고", []) is None
