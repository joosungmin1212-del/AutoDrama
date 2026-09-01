"""'네이버로 보내기'가 어느 계정으로 보낼지 결정하는 로직.

예전에는 "공식 블로그"라는 별도 역할을 등록해야만 글쓰기가 됐는데, 실제로는 그냥
"로그인한 그 계정으로 쓰고 싶다"는 게 사용자 기대였다. 그런데 이미 "직원"으로
등록해둔 블로그를 또 "공식 블로그"로 중복 등록하는 경우가 생겼고, 그러면 같은
블로그ID를 가진 두 행 중 어느 게 매칭되느냐에 따라 대시보드 직원 체크리스트가
틀리게 표시되는 버그가 실제로 있었다(matcher.match_ownership이 먼저 찾은 행 하나만
씀). 그래서 "공식 블로그"라는 별도 역할 없이, 이미 추적용으로 등록해둔 "직원" 블로그
자체를 글쓰기 계정 후보로 그대로 쓴다. 예전에 만들어진 "공식 블로그" 데이터가 있는
사용자를 위해 role=company도 후보에 계속 포함한다(하위호환, 신규 등록만 막음).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .. import models

WRITER_ACCOUNT_ROLES = [models.BlogRole.STAFF.value, models.BlogRole.COMPANY.value]


def list_writer_accounts(db: Session) -> list[models.RegisteredBlog]:
    """글쓰기 계정 후보 목록. 같은 blog_id가 여러 role로 중복 등록돼 있어도 한 번만 보여준다.

    (먼저 등록된 행을 대표로 쓴다 - 어차피 블로그ID가 같으면 실제로 로그인/글쓰기 동작은
    동일하고, 표시 이름만 어느 걸 쓰느냐의 문제라 순서는 크게 중요하지 않다.)
    """
    rows = (
        db.query(models.RegisteredBlog)
        .filter(models.RegisteredBlog.role.in_(WRITER_ACCOUNT_ROLES))
        .order_by(models.RegisteredBlog.created_at.asc())
        .all()
    )
    seen: set[str] = set()
    unique: list[models.RegisteredBlog] = []
    for r in rows:
        key = (r.blog_id or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def resolve_writer_blog(
    db: Session, setting: models.Setting, requested_blog_pk: int | None = None
) -> models.RegisteredBlog | None:
    """실제로 글을 보낼 블로그 행을 고른다.

    1. 화면에서 명시적으로 계정을 골랐으면 그걸 최우선으로 쓴다.
    2. 아니면 마지막으로 사용(로그인 또는 전송)한 계정(Setting.active_writer_blog_id)을 쓴다.
    3. 그것도 없으면(맨 처음이라 아직 기록이 없음) 등록된 계정 중 가장 먼저 등록된 걸 쓴다.
    """
    accounts = list_writer_accounts(db)
    if not accounts:
        return None

    if requested_blog_pk:
        for a in accounts:
            if a.id == requested_blog_pk:
                return a

    if setting.active_writer_blog_id:
        for a in accounts:
            if a.blog_id.lower() == setting.active_writer_blog_id.lower():
                return a

    return accounts[0]
