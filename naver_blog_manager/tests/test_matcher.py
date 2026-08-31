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
    blogs = [FakeBlog("MyBlog", BlogRole.COMPANY.value, "공식블로그")]
    ownership, matched = matcher.match_ownership("myblog", blogs)
    assert ownership == Ownership.OURS_COMPANY.value
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


def test_match_ownership_does_not_blanket_match_competitor_or_experience():
    """실제로 있었던 문제: 체험단/경쟁업체로 등록해둔 같은 블로그 계정이 키워드마다
    완전히 다른 업체 글을 쓰는 경우가 흔한데, match_ownership이 계정 단위로 ownership을
    자동 확정해버리면 그 계정의 아무 글이나 항상 "우리 것"/"항상 타업체"로 잘못 집계된다.
    그래서 이 두 역할은 match_ownership에서 아예 안 잡혀야 하고(글 단위 판정은
    content_match_service가 따로 함), 대신 find_known_identity로 신원만 표시한다."""
    blogs = [
        FakeBlog("rival_trainer", BlogRole.COMPETITOR.value, "김민수 헬스타이거"),
        FakeBlog("freelance_reviewer", BlogRole.EXPERIENCE.value, "체험단A"),
    ]

    for blog_id in ("rival_trainer", "freelance_reviewer"):
        ownership, matched = matcher.match_ownership(blog_id, blogs)
        assert ownership == Ownership.OTHER.value
        assert matched is None


def test_find_known_identity_finds_competitor_and_experience_regardless_of_role():
    """match_ownership과 달리, find_known_identity는 신원 표시 용도로 역할 상관없이
    등록된 블로그를 찾아준다 - ownership 판정에는 관여하지 않는다."""
    blogs = [FakeBlog("rival_trainer", BlogRole.COMPETITOR.value, "김민수 헬스타이거")]
    matched = matcher.find_known_identity("rival_trainer", blogs)
    assert matched is not None
    assert matched.name == "김민수 헬스타이거"

    assert matcher.find_known_identity("unknown_blog", blogs) is None
    assert matcher.find_known_identity("", blogs) is None
