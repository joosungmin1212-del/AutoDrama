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

_ROLE_TO_OWNERSHIP = {
    BlogRole.COMPANY.value: Ownership.OURS_COMPANY.value,
    BlogRole.STAFF.value: Ownership.OURS_STAFF.value,
    BlogRole.EXPERIENCE.value: Ownership.OURS_EXPERIENCE.value,
}


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


def match_ownership(identifier: str, registered_blogs: list) -> tuple[str, object | None]:
    """등록된 블로그 목록과 대조해 (ownership, matched_blog) 반환.

    registered_blogs: `.blog_id`, `.role` 속성을 가진 객체 리스트 (RegisteredBlog ORM 또는 동등한 dict-like).
    """
    if not identifier:
        return Ownership.OTHER.value, None

    for rb in registered_blogs:
        rb_id = getattr(rb, "blog_id", "") or ""
        if rb_id and rb_id.lower() == identifier.lower():
            ownership = _ROLE_TO_OWNERSHIP.get(getattr(rb, "role", ""), Ownership.OTHER.value)
            return ownership, rb

    return Ownership.OTHER.value, None
