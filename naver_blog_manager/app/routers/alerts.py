"""이탈 알림(TOP7에서 우리 글이 사라짐) 조회/확인 API.

블로그가 다시 TOP7에 나타나면 rank_service가 자동으로 해소하지만, 사용자가 "봤다"고
직접 확인 처리하고 싶을 때(예: 자동 회복을 기다리지 않고 알림만 지우고 싶을 때)를 위해
수동 확인 엔드포인트도 함께 제공한다.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_out(alert: models.Alert) -> schemas.AlertOut:
    return schemas.AlertOut(
        id=alert.id,
        keyword_id=alert.keyword_id,
        keyword=alert.keyword.keyword if alert.keyword else "",
        matched_blog_name=alert.matched_blog.name if alert.matched_blog else None,
        blog_id=alert.blog_id,
        previous_position=alert.previous_position,
        detected_at=alert.detected_at,
        resolved=alert.resolved,
    )


@router.get("", response_model=list[schemas.AlertOut])
def list_alerts(status: str = "open", keyword_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Alert)
    if status == "open":
        query = query.filter(models.Alert.resolved.is_(False))
    elif status == "resolved":
        query = query.filter(models.Alert.resolved.is_(True))
    if keyword_id is not None:
        query = query.filter(models.Alert.keyword_id == keyword_id)
    return [_to_out(a) for a in query.order_by(models.Alert.detected_at.desc()).all()]


@router.post("/{alert_id}/resolve", response_model=schemas.AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(models.Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다.")
    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return _to_out(alert)
