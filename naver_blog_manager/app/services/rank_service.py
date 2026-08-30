"""순위 조회 결과를 DB에 저장하고, 이탈(Alert)을 감지하는 오케스트레이션 레이어.

naver_rank.py(순수 조회/파싱)와 DB 모델을 이어붙이는 역할만 한다.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime

from sqlalchemy.orm import Session

from .. import config, models
from . import naver_rank


def _load_previous_items(db: Session, keyword_id: int) -> list[naver_rank.RankItem]:
    previous_check = (
        db.query(models.RankCheck)
        .filter(models.RankCheck.keyword_id == keyword_id)
        .order_by(models.RankCheck.checked_at.desc())
        .first()
    )
    if not previous_check:
        return []
    return [
        naver_rank.RankItem(
            position=r.position,
            content_type=r.content_type,
            url=r.url,
            blog_id=r.blog_id,
            title=r.title,
            ownership=r.ownership,
        )
        for r in previous_check.results
    ]


async def run_rank_check_async(db: Session, keyword: models.Keyword) -> models.RankCheck:
    registered_blogs = db.query(models.RegisteredBlog).all()
    previous_items = _load_previous_items(db, keyword.id)

    items = await naver_rank.check_keyword_rank(keyword.keyword, registered_blogs)

    rank_check = models.RankCheck(keyword_id=keyword.id, checked_at=datetime.utcnow())
    db.add(rank_check)
    db.flush()

    for item in items:
        matched_id = getattr(item.matched_blog, "id", None) if item.matched_blog else None
        db.add(
            models.RankResult(
                rank_check_id=rank_check.id,
                position=item.position,
                content_type=item.content_type,
                url=item.url,
                blog_id=item.blog_id,
                title=item.title,
                matched_blog_id_fk=matched_id,
                ownership=item.ownership,
            )
        )

    dropped = naver_rank.detect_dropouts(previous_items, items)
    blog_by_id = {rb.blog_id.lower(): rb for rb in registered_blogs if rb.blog_id}
    for d in dropped:
        matched_blog = blog_by_id.get(d.blog_id.lower())
        db.add(
            models.Alert(
                keyword_id=keyword.id,
                matched_blog_id_fk=getattr(matched_blog, "id", None),
                previous_position=d.position,
                detected_at=datetime.utcnow(),
            )
        )

    db.commit()
    db.refresh(rank_check)
    return rank_check


def run_rank_check_sync(db: Session, keyword: models.Keyword) -> models.RankCheck:
    return asyncio.run(run_rank_check_async(db, keyword))


async def run_all_active_checks(db: Session) -> list[models.RankCheck]:
    keywords = db.query(models.Keyword).filter(models.Keyword.active.is_(True)).all()
    checks: list[models.RankCheck] = []
    for idx, kw in enumerate(keywords):
        if idx > 0:
            await asyncio.sleep(
                random.uniform(config.MIN_REQUEST_DELAY_SEC, config.MAX_REQUEST_DELAY_SEC)
            )
        checks.append(await run_rank_check_async(db, kw))
    return checks


def run_all_active_checks_sync(db: Session) -> list[models.RankCheck]:
    return asyncio.run(run_all_active_checks(db))
