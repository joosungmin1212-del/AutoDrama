from app.models import BlogRole, Ownership
from app.services import matcher


class FakeBlog:
    def __init__(self, blog_id: str, role: str, name: str = "test", id: int | None = None):
        self.blog_id = blog_id
        self.role = role
        self.name = name
        self.id = id


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


def test_match_ownership_blanket_matches_competitor_but_not_experience():
    """경쟁업체(주변 다른 트레이너/PT샵 본인 블로그)는 계정 자체가 자기 홍보용이라
    우리 얘기가 나올 일이 사실상 없으므로, match_ownership이 계정 단위로 "확인된
    타업체"를 자동 확정해도 안전하다 - 매번 재확인할 필요가 없다.

    반대로 체험단은 같은 블로거가 이 키워드에는 우리 글을, 다른 키워드에는 완전히
    다른 업체 글을 쓰는 경우가 흔해서(실제로 사용자가 지적한 문제), match_ownership이
    계정 단위로 못 박으면 안 된다 - 여기서 안 잡혀야 하고, 글 단위 판정은
    content_match_service가 따로 하며, 신원 표시만 find_known_identity가 해준다."""
    blogs = [
        FakeBlog("rival_trainer", BlogRole.COMPETITOR.value, "김민수 헬스타이거"),
        FakeBlog("freelance_reviewer", BlogRole.EXPERIENCE.value, "체험단A"),
    ]

    ownership, matched = matcher.match_ownership("rival_trainer", blogs)
    assert ownership == Ownership.OTHER.value
    assert matched is not None
    assert matched.name == "김민수 헬스타이거"

    ownership, matched = matcher.match_ownership("freelance_reviewer", blogs)
    assert ownership == Ownership.OTHER.value
    assert matched is None


def test_match_ownership_prefers_staff_row_when_same_blog_id_registered_twice():
    """실제로 사용자가 겪은 버그 재현: 같은 블로그를 "직원"과 (예전 방식인) "공식
    블로그" 둘 다로 중복 등록해두면, 대시보드 직원 체크리스트가 STAFF 행의 id로만
    "존재 여부"를 판정하기 때문에 하필 COMPANY 행이 먼저 매칭되면 실제로는 그 직원
    글이 맞는데도 체크리스트에 "없음(X)"으로 잘못 표시됐다. 등록 순서(리스트 순서)와
    무관하게 항상 STAFF 행이 매칭돼야 한다."""
    staff_row = FakeBlog("sm_main", BlogRole.STAFF.value, "성민본계정", id=1)
    company_row = FakeBlog("sm_main", BlogRole.COMPANY.value, "성민본계정(공식)", id=2)

    # COMPANY 행이 리스트에서 먼저 나오는 경우(예: DB 쿼리 순서가 그렇게 나온 경우)에도
    ownership, matched = matcher.match_ownership("sm_main", [company_row, staff_row])
    assert ownership == Ownership.OURS_STAFF.value
    assert matched.id == 1

    # 순서를 반대로 해도(STAFF가 먼저) 당연히 그대로 STAFF가 매칭돼야 한다.
    ownership, matched = matcher.match_ownership("sm_main", [staff_row, company_row])
    assert ownership == Ownership.OURS_STAFF.value
    assert matched.id == 1


def test_find_known_identity_finds_experience_for_display_only():
    """match_ownership과 달리, find_known_identity는 신원 표시 용도로 역할 상관없이
    등록된 블로그를 찾아준다 - ownership 판정에는 관여하지 않는다. (실제 호출 지점인
    naver_rank.check_keyword_rank는 match_ownership이 못 찾았을 때만 이걸 부르므로,
    실질적으로는 체험단 등록을 찾아내는 역할이다.)"""
    blogs = [FakeBlog("freelance_reviewer", BlogRole.EXPERIENCE.value, "체험단A")]
    matched = matcher.find_known_identity("freelance_reviewer", blogs)
    assert matched is not None
    assert matched.name == "체험단A"

    assert matcher.find_known_identity("unknown_blog", blogs) is None
    assert matcher.find_known_identity("", blogs) is None
