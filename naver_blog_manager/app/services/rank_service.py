"""순위 조회 결과를 DB에 저장하고, 이탈(Alert)을 감지하는 오케스트레이션 레이어.

naver_rank.py(순수 조회/파싱)와 DB 모델을 이어붙이는 역할만 한다.
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime

from sqlalchemy.orm import Session

from .. import config, models
from . import content_match_service, naver_rank


def _resolve_recovered_alerts(db: Session, keyword_id: int, current_items: list) -> None:
    """이탈 알림이 떴던 글(블로그)이 다시 TOP7에 나타나면 그 알림을 자동으로 해소한다.

    예전에는 이걸 하는 코드가 아예 없어서, 한 번 뜬 "이탈 알림"이 문제가 해결된 뒤에도
    영원히 열려있는 상태로 남아 대시보드 배너의 카운트가 계속 쌓이기만 하는 버그가 있었다.
    """
    recovered_blog_ids = {
        item.blog_id.lower() for item in current_items if item.blog_id and item.ownership.startswith("ours_")
    }
    if not recovered_blog_ids:
        return

    open_alerts = (
        db.query(models.Alert)
        .filter(models.Alert.keyword_id == keyword_id, models.Alert.resolved.is_(False))
        .all()
    )
    for alert in open_alerts:
        if alert.blog_id and alert.blog_id.lower() in recovered_blog_ids:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()


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


async def run_rank_check_async(
    db: Session, keyword: models.Keyword, page=None
) -> models.RankCheck:
    registered_blogs = db.query(models.RegisteredBlog).all()
    previous_items = _load_previous_items(db, keyword.id)

    items = await naver_rank.check_keyword_rank(keyword.keyword, registered_blogs, page=page)

    # 등록된 블로그로 안 잡힌(주로 체험단) 글 중 제목에 우리 이름이 보이는 게 있으면
    # "확인 필요" 후보로 걸거나, 이전에 확정/거절해둔 판정을 그대로 적용한다.
    watch_names = content_match_service.get_watch_names(db)
    content_match_service.apply_content_matches(db, items, watch_names)

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

    _resolve_recovered_alerts(db, keyword.id, items)

    dropped = naver_rank.detect_dropouts(previous_items, items)
    blog_by_id = {rb.blog_id.lower(): rb for rb in registered_blogs if rb.blog_id}
    for d in dropped:
        matched_blog = blog_by_id.get(d.blog_id.lower())
        db.add(
            models.Alert(
                keyword_id=keyword.id,
                matched_blog_id_fk=getattr(matched_blog, "id", None),
                blog_id=d.blog_id,
                previous_position=d.position,
                detected_at=datetime.utcnow(),
            )
        )

    db.commit()
    db.refresh(rank_check)
    return rank_check


def run_rank_check_sync(db: Session, keyword: models.Keyword) -> models.RankCheck:
    return asyncio.run(run_rank_check_async(db, keyword))


async def run_all_active_checks(db: Session, on_progress=None, on_error=None) -> list[models.RankCheck]:
    """등록된 키워드를 전부 순서대로 조회한다.

    브라우저는 배치 전체에서 딱 1개만 켜서 재사용한다 (키워드마다 새로 켰다 끄던 예전 방식은
    브라우저 실행 자체의 오버헤드가 커서, 키워드가 많을수록 불필요하게 느려졌다). 키워드
    사이의 딜레이는 그대로 유지한다 - 이건 속도 문제가 아니라 네이버가 짧은 시간에 몰아치는
    요청을 자동화로 의심하지 않게 하기 위한 것이라, 없애면 오히려 전체가 차단될 위험이 커진다.

    한 키워드가 실패해도(예: 일시적 차단 의심) 배치 전체를 멈추지 않고 나머지는 계속
    진행한다 - 실패는 on_error로 기록해서 나중에 요약해 보여준다.
    on_progress(done, total, current_keyword)는 매 키워드가 끝날 때마다 호출된다
    (진행률 표시용).
    """
    keywords = db.query(models.Keyword).filter(models.Keyword.active.is_(True)).all()
    checks: list[models.RankCheck] = []
    total = len(keywords)
    if not keywords:
        return checks

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=config.NAVER_USER_AGENT)
            for idx, kw in enumerate(keywords):
                if idx > 0:
                    await asyncio.sleep(
                        random.uniform(config.MIN_REQUEST_DELAY_SEC, config.MAX_REQUEST_DELAY_SEC)
                    )
                try:
                    checks.append(await run_rank_check_async(db, kw, page=page))
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    if on_error:
                        on_error(kw.keyword, str(exc))
                finally:
                    if on_progress:
                        on_progress(idx + 1, total, kw.keyword)
        finally:
            await browser.close()
    return checks


def run_all_active_checks_sync(db: Session) -> list[models.RankCheck]:
    return asyncio.run(run_all_active_checks(db))
