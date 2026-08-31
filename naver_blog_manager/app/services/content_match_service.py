"""등록되지 않은 블로그(주로 체험단)가 쓴 글을, 제목에 우리 업체명/직원 이름이 있으면
"우리 글일 수 있다"고 자동으로 걸러내고, 사람이 한 번 확정하면 계속 기억하는 로직.

체험단 블로거는 여러 업체를 옮겨 다니며 글을 쓰기 때문에 "이 블로그 = 우리 것"으로 미리
등록해두는 방식이 안 맞는다. 그래서 블로그 단위가 아니라 "그 글 하나(post_key)" 단위로
판정을 저장한다 - 순위가 오르내리거나 한동안 TOP7에서 빠졌다 다시 나타나도 같은 글이면
같은 판정이 그대로 적용된다.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .. import models
from . import matcher
from .naver_rank import RankItem


def get_watch_names(db: Session) -> list[str]:
    """제목 매칭에 쓸 "우리 이름" 목록: 업체명 + 등록된 직원/공식블로그 이름.

    직원 이름은 이미 "블로그 관리"에 등록돼 있으므로 따로 입력받지 않고 그대로 재사용한다.
    """
    names: list[str] = []

    setting = db.get(models.Setting, 1)
    if setting and setting.business_name.strip():
        names.append(setting.business_name.strip())

    blogs = (
        db.query(models.RegisteredBlog)
        .filter(
            models.RegisteredBlog.role.in_(
                [models.BlogRole.STAFF.value, models.BlogRole.COMPANY.value]
            )
        )
        .all()
    )
    names.extend(b.name.strip() for b in blogs if b.name.strip())
    return names


def apply_content_matches(db: Session, items: list[RankItem], watch_names: list[str]) -> None:
    """items를 제자리에서 갱신한다.

    아직 등록된 블로그로 판정되지 않은(ownership == "other") 항목 중 제목에 우리 이름이
    보이는 게 있으면, 이전에 확정/거절해둔 기록이 있는지 찾아보고 있으면 그대로 적용하고,
    없으면 새 후보로 등록해서 "확인 필요" 상태로 표시한다.

    item.matched_blog가 있어도(체험단/경쟁업체로 등록해둔 계정) 여기서는 건너뛰지 않는다 -
    같은 체험단 블로거가 이 키워드에는 우리 글을, 다른 키워드에는 완전히 다른 업체 글을
    쓰는 경우가 흔해서, "이 계정 = 항상 이런 판정"으로 미리 못 박으면 안 되고 글(URL)
    하나하나를 그대로 판정해야 하기 때문이다. matched_blog는 그저 "이 계정이 누구로
    등록돼 있는지" 표시용일 뿐이다.

    카페(cafe.naver.com) 글만 예외로 애초에 체험단 후보로 보지 않는다 - 등록 안 된 카페
    글이 인기글에 가끔 섞이는데, 체험단/직원은 개인 블로그에 글을 쓰지 카페에 쓰지
    않으므로 자동으로 "타업체"로 둔다. (우리가 직접 운영하는 카페를 공식/직원 블로그로
    등록해둔 경우는 이 로직 이전에 이미 매칭되므로 영향받지 않는다.)
    """
    if not watch_names:
        return

    for item in items:
        if item.ownership != models.Ownership.OTHER.value:
            continue
        if item.content_type == "cafe":
            continue

        matched_name = matcher.find_name_match(item.title, watch_names)
        if not matched_name:
            continue

        post_key = matcher.extract_post_key(item.url)
        if not post_key:
            continue

        content_match = db.query(models.ContentMatch).filter_by(post_key=post_key).first()
        if content_match is None:
            content_match = models.ContentMatch(
                post_key=post_key,
                url=item.url,
                title=item.title,
                matched_text=matched_name,
                decision=models.ContentMatchDecision.PENDING.value,
            )
            db.add(content_match)
            db.flush()
        else:
            # 판정 자체는 안 건드리고, 제목/URL만 최신 정보로 갱신 (글이 수정됐을 수 있음)
            content_match.title = item.title
            content_match.url = item.url

        if content_match.decision == models.ContentMatchDecision.CONFIRMED.value:
            item.ownership = models.Ownership.OURS_EXPERIENCE.value
        elif content_match.decision == models.ContentMatchDecision.REJECTED.value:
            item.ownership = models.Ownership.OTHER.value
        else:
            item.ownership = models.Ownership.PENDING_EXPERIENCE.value


def manual_set(db: Session, url: str, title: str, decision: str) -> models.ContentMatch:
    """대시보드에서 TOP7 글 하나를 사람이 직접 "우리 체험단 맞음/아님"으로 지정할 때 쓴다.

    제목에 업체명/직원 이름이 없어서 자동 감지(watch_names 매칭)에 걸리지 않은 글도
    이걸로 확정할 수 있다 - 체험단 블로거가 우리 이름을 안 쓰고 글을 쓰는 경우가 실제로
    있어서, 자동 감지만으로는 놓치는 글이 생긴다. post_key로 판정을 저장하는 방식은
    자동 감지와 동일해서, 이후 같은 글이 다시 나와도 판정이 계속 적용된다.
    """
    post_key = matcher.extract_post_key(url)
    if not post_key:
        raise ValueError("이 글의 식별자를 알아내지 못해 저장할 수 없습니다.")

    content_match = db.query(models.ContentMatch).filter_by(post_key=post_key).first()
    if content_match is None:
        content_match = models.ContentMatch(
            post_key=post_key,
            url=url,
            title=title,
            matched_text="수동 확인",
            decision=models.ContentMatchDecision.PENDING.value,
        )
        db.add(content_match)
        db.flush()
    else:
        content_match.title = title
        content_match.url = url

    return decide(db, content_match, decision)


def decide(db: Session, content_match: models.ContentMatch, decision: str) -> models.ContentMatch:
    """확정/거절 처리 + 이미 저장된 최근 결과에도 즉시 반영 (다음 갱신을 기다리지 않도록)."""
    content_match.decision = decision
    content_match.decided_at = datetime.utcnow()

    new_ownership = (
        models.Ownership.OURS_EXPERIENCE.value
        if decision == models.ContentMatchDecision.CONFIRMED.value
        else models.Ownership.OTHER.value
    )
    db.query(models.RankResult).filter(models.RankResult.url == content_match.url).update(
        {"ownership": new_ownership}
    )

    db.commit()
    db.refresh(content_match)
    return content_match
