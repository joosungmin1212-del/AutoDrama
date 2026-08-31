"""URL/블로그ID로부터 소유자(우리 공식/직원/체험단/타업체)를 판정하는 순수 로직.

DB나 네트워크에 의존하지 않아 유닛테스트가 쉽다.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from ..models import BlogRole, Ownership

_BLOG_RE = re.compile(r"blog\.naver\.com/([a-zA-Z0-9_\-]+)", re.IGNORECASE)
_CAFE_NEW_RE = re.compile(r"cafe\.naver\.com/ca-fe/cafes/(\d+)", re.IGNORECASE)
_CAFE_OLD_RE = re.compile(r"cafe\.naver\.com/([a-zA-Z0-9_\-]+)(?:/\d+)?", re.IGNORECASE)

_BLOG_POST_RE = re.compile(r"blog\.naver\.com/([a-zA-Z0-9_\-]+)/(\d+)", re.IGNORECASE)
_CAFE_NEW_POST_RE = re.compile(r"cafe\.naver\.com/ca-fe/cafes/(\d+)/articles/(\d+)", re.IGNORECASE)
_CAFE_OLD_POST_RE = re.compile(r"cafe\.naver\.com/([a-zA-Z0-9_\-]+)/(\d+)", re.IGNORECASE)

_ROLE_TO_OWNERSHIP = {
    BlogRole.COMPANY.value: Ownership.OURS_COMPANY.value,
    BlogRole.STAFF.value: Ownership.OURS_STAFF.value,
}

# "이 블로그 계정 = 항상 우리 것"이라고 안전하게 확정할 수 있는 역할. 공식/직원 블로그는
# 계정 자체가 우리 소유라서 이 가정이 항상 맞는다.
_BLANKET_OURS_ROLES = {BlogRole.COMPANY.value, BlogRole.STAFF.value}

# "이 블로그 계정 = 항상 남의 것"이라고 안전하게 확정할 수 있는 역할. 경쟁업체(주변 다른
# 트레이너/PT샵의 본인 블로그)는 자기 업체 홍보가 계정의 존재 이유라서, 그 계정에서 우리
# 얘기가 나올 일은 사실상 없다 - 매번 재확인 없이 계정 단위로 "확인된 타업체"로 못 박아도
# 안전하다.
_BLANKET_OTHER_ROLES = {BlogRole.COMPETITOR.value}

# 체험단(BlogRole.EXPERIENCE)은 이 두 집합 어디에도 안 들어간다 - 같은 체험단 블로거가
# 이번 키워드에는 우리 글을, 다른 키워드에는 완전히 다른 업체 글을 쓰는 경우가 흔해서
# (실제로 사용자가 지적한 문제), 계정 단위로 "항상 우리 것"이라고 못 박으면 안 된다.
# 그래서 체험단은 블로그 등록을 해도 match_ownership()에서 안 잡히고, 글(URL) 하나하나를
# content_match_service의 post_key 기반 판정으로 따로 확인한다 - 등록은 신원 표시(이름)
# 용도로만 쓰인다. 자세한 내용은 match_ownership()/find_known_identity() 참고.


def extract_identifier(url: str) -> str:
    """블로그/카페 URL에서 매칭에 쓸 식별자(블로그ID 또는 카페 식별자)를 뽑아낸다.

    예)
      https://blog.naver.com/abcd1234/223456789      -> "abcd1234"
      https://m.blog.naver.com/abcd1234               -> "abcd1234"
      https://cafe.naver.com/ca-fe/cafes/12345/articles/9 -> "12345"
      https://cafe.naver.com/somecafe/9876             -> "somecafe"
      https://blog.naver.com/PostView.naver?blogId=abcd1234&... -> "abcd1234"
    """
    if not url:
        return ""

    match = _BLOG_RE.search(url)
    if match:
        candidate = match.group(1)
        # PostView.naver?blogId=... 형태는 블로그ID가 아니라 뷰어 페이지 경로이므로 건너뛰고
        # 아래 쿼리스트링(blogId) 파싱으로 넘어간다.
        if candidate.lower() != "postview":
            return candidate.lower()

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "blogId" in qs and qs["blogId"]:
        return qs["blogId"][0].lower()

    match = _CAFE_NEW_RE.search(url)
    if match:
        return match.group(1)

    match = _CAFE_OLD_RE.search(url)
    if match:
        return match.group(1).lower()

    return ""


def extract_post_key(url: str) -> str:
    """글 하나를 유일하게 식별하는 키를 만든다 ("이 글 자체"를 추적하기 위함).

    체험단 확인 여부는 순위/등장 여부와 무관하게 "그 글"에 계속 붙어있어야 한다 - 순위가
    바뀌거나 한동안 TOP7에서 안 보이다 다시 나타나도 같은 키가 나와야 다시 물어보지 않는다.
    blog_id/cafe_id + 글 번호 조합을 쓰고, 글 번호를 못 찾으면 URL 경로를 최후의 수단으로 쓴다.
    """
    if not url:
        return ""

    match = _BLOG_POST_RE.search(url)
    if match and match.group(1).lower() != "postview":
        return f"blog:{match.group(1).lower()}:{match.group(2)}"

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "blogId" in qs and qs["blogId"]:
        log_no = (qs.get("logNo") or [""])[0]
        if log_no:
            return f"blog:{qs['blogId'][0].lower()}:{log_no}"

    match = _CAFE_NEW_POST_RE.search(url)
    if match:
        return f"cafe:{match.group(1)}:{match.group(2)}"

    match = _CAFE_OLD_POST_RE.search(url)
    if match:
        return f"cafe:{match.group(1).lower()}:{match.group(2)}"

    return f"url:{parsed.netloc}{parsed.path.rstrip('/')}"


def find_name_match(title: str, watch_names: list[str]) -> str | None:
    """제목에 업체명/직원 이름 중 하나가 들어있으면 그 이름을 반환한다 (없으면 None).

    체험단처럼 미리 등록해둔 블로그가 아닌 글에서, 제목만 보고 "우리 이야기일 수 있다"고
    걸러내는 용도. 확정은 사람이 하고, 이건 그 후보를 찾아내는 역할만 한다.
    """
    if not title:
        return None
    lowered_title = title.lower()
    for name in watch_names:
        name = (name or "").strip()
        if name and name.lower() in lowered_title:
            return name
    return None


def match_ownership(identifier: str, registered_blogs: list) -> tuple[str, object | None]:
    """등록된 블로그 목록과 대조해 (ownership, matched_blog) 반환.

    공식/직원(_BLANKET_OURS_ROLES) 블로그는 계정 단위로 "ours_*"를 자동 확정하고,
    경쟁업체(_BLANKET_OTHER_ROLES)는 계정 단위로 "other"를 자동 확정한다(matched_blog는
    채워서 반환 - 대시보드 표시 및 체험단 후보 판정 제외에 쓰인다). 체험단으로 등록된
    블로그는 여기서 안 잡힌다 - 같은 계정이 키워드마다 다른 업체 글을 쓸 수 있어서, 계정
    단위로 "항상 우리 것"이라고 못 박으면 안 되기 때문이다 (find_known_identity()로 신원
    표시만 하고, 실제 판정은 글 단위로 함).

    registered_blogs: `.blog_id`, `.role` 속성을 가진 객체 리스트 (RegisteredBlog ORM 또는 동등한 dict-like).
    """
    if not identifier:
        return Ownership.OTHER.value, None

    for rb in registered_blogs:
        rb_id = getattr(rb, "blog_id", "") or ""
        role = getattr(rb, "role", "")
        if not (rb_id and rb_id.lower() == identifier.lower()):
            continue
        if role in _BLANKET_OURS_ROLES:
            return _ROLE_TO_OWNERSHIP.get(role, Ownership.OTHER.value), rb
        if role in _BLANKET_OTHER_ROLES:
            return Ownership.OTHER.value, rb

    return Ownership.OTHER.value, None


def find_known_identity(identifier: str, registered_blogs: list) -> object | None:
    """블로그ID로 등록된 블로그를 역할 상관없이 찾는다.

    match_ownership()이 이미 처리하는 공식/직원/경쟁업체는 여기서 다시 찾을 필요가
    없으므로(check_keyword_rank에서 match_ownership이 못 찾았을 때만 호출됨), 실질적으로는
    체험단(EXPERIENCE) 등록을 찾아내는 역할이다. ownership 판정에는 전혀 관여하지 않고,
    "이 계정이 등록해둔 누구인지"를 대시보드에 표시하기 위한 용도로만 쓰인다 - 아직 이
    글 자체는 우리 것인지 판정 전(ownership="other")이라도, 등록해둔 체험단 블로거의
    계정이라는 걸 미리 알려줘서 사람이 TOP7 상세보기에서 더 빨리 판단할 수 있게 돕는다.
    """
    if not identifier:
        return None
    for rb in registered_blogs:
        rb_id = getattr(rb, "blog_id", "") or ""
        if rb_id and rb_id.lower() == identifier.lower():
            return rb
    return None
