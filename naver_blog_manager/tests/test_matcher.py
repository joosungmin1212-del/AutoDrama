from app.models import BlogRole, Ownership
from app.services import matcher


class FakeBlog:
    def __init__(self, blog_id: str, role: str, name: str = "test"):
        self.blog_id = blog_id
        self.role = role
        self.name = name


def test_extract_identifier_blog_url():
    assert matcher.extract_identifier("https://blog.naver.com/abcd1234") == "abcd1234"
    assert matcher.extract_identifier("https://blog.naver.com/abcd1234/223456789") == "abcd1234"
    assert matcher.extract_identifier("https://m.blog.naver.com/AbcD1234") == "abcd1234"


def test_extract_identifier_postview_query_param():
    url = "https://blog.naver.com/PostView.naver?blogId=abcd1234&logNo=223456789"
    assert matcher.extract_identifier(url) == "abcd1234"


def test_extract_identifier_cafe_url():
    assert matcher.extract_identifier("https://cafe.naver.com/somecafe/9876") == "somecafe"
    assert (
        matcher.extract_identifier("https://cafe.naver.com/ca-fe/cafes/12345/articles/9")
        == "12345"
    )


def test_extract_identifier_empty_for_unrelated_url():
    assert matcher.extract_identifier("https://www.google.com") == ""
    assert matcher.extract_identifier("") == ""


def test_match_ownership_staff():
    blogs = [FakeBlog("wonjang_pt", BlogRole.STAFF.value, "원장")]
    ownership, matched = matcher.match_ownership("wonjang_pt", blogs)
    assert ownership == Ownership.OURS_STAFF.value
    assert matched.name == "원장"


def test_match_ownership_case_insensitive():
    blogs = [FakeBlog("MyBlog", BlogRole.EXPERIENCE.value, "체험단A")]
    ownership, matched = matcher.match_ownership("myblog", blogs)
    assert ownership == Ownership.OURS_EXPERIENCE.value
    assert matched is not None


def test_match_ownership_no_match_is_other():
    blogs = [FakeBlog("wonjang_pt", BlogRole.STAFF.value)]
    ownership, matched = matcher.match_ownership("unknown_blog", blogs)
    assert ownership == Ownership.OTHER.value
    assert matched is None


def test_match_ownership_empty_identifier():
    ownership, matched = matcher.match_ownership("", [FakeBlog("x", BlogRole.STAFF.value)])
    assert ownership == Ownership.OTHER.value
    assert matched is None
