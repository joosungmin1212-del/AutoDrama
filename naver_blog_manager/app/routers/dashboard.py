from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

TREND_DAYS = 14


def _keyword_summary(db: Session, keyword: models.Keyword, staff_blogs: list) -> dict:
    latest_check = (
        db.query(models.RankCheck)
        .filter(models.RankCheck.keyword_id == keyword.id)
        .order_by(models.RankCheck.checked_at.desc())
        .first()
    )
    results = latest_check.results if latest_check else []
    slots = dashboard_service.build_slots(results)
    our_count = dashboard_service.count_ours(slots)
    has_open_alert = (
        db.query(models.Alert)
        .filter(models.Alert.keyword_id == keyword.id, models.Alert.resolved.is_(False))
        .first()
        is not None
    )
    return {
        "id": keyword.id,
        "keyword": keyword.keyword,
        "category": keyword.category,
        "memo": keyword.memo,
        "active": keyword.active,
        "sort_order": keyword.sort_order,
        "last_checked_at": latest_check.checked_at if latest_check else None,
        "our_count": our_count,
        "total_slots": len(slots),
        "slots": slots,
        "has_open_alert": has_open_alert,
        "staff_presence": dashboard_service.build_staff_presence(slots, staff_blogs),
        "experience_confirmed_count": dashboard_service.count_by_ownership(
            slots, models.Ownership.OURS_EXPERIENCE.value
        ),
        "experience_pending_count": dashboard_service.count_by_ownership(
            slots, models.Ownership.PENDING_EXPERIENCE.value
        ),
    }


@router.get("/summary", response_model=schemas.DashboardResponse)
def get_summary(db: Session = Depends(get_db)):
    keywords = (
        db.query(models.Keyword)
        .filter(models.Keyword.active.is_(True))
        .order_by(models.Keyword.sort_order.asc(), models.Keyword.created_at.asc())
        .all()
    )
    staff_blogs = (
        db.query(models.RegisteredBlog)
        .filter(models.RegisteredBlog.role == models.BlogRole.STAFF.value)
        .all()
    )
    summaries = [_keyword_summary(db, k, staff_blogs) for k in keywords]
    open_alert_count = sum(1 for s in summaries if s["has_open_alert"])
    pending_content_match_count = (
        db.query(models.ContentMatch)
        .filter(models.ContentMatch.decision == models.ContentMatchDecision.PENDING.value)
        .count()
    )
    stats = dashboard_service.aggregate_stats(summaries, open_alert_count, pending_content_match_count)

    since = datetime.utcnow() - timedelta(days=TREND_DAYS - 1)
    keyword_ids = [k.id for k in keywords]
    checks = (
        db.query(models.RankCheck)
        .filter(models.RankCheck.keyword_id.in_(keyword_ids), models.RankCheck.checked_at >= since)
        .all()
        if keyword_ids
        else []
    )
    trend = dashboard_service.build_trend_series(checks, days=TREND_DAYS)

    return schemas.DashboardResponse(stats=stats, keywords=summaries, trend=trend)
