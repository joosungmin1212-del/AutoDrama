"""체험단(등록 안 된 블로그) 자동 감지 후보 확인/확정 API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import content_match_service

router = APIRouter(prefix="/api/content-matches", tags=["content-matches"])


@router.get("", response_model=list[schemas.ContentMatchOut])
def list_content_matches(status: str = "pending", db: Session = Depends(get_db)):
    query = db.query(models.ContentMatch)
    if status != "all":
        query = query.filter(models.ContentMatch.decision == status)
    return query.order_by(models.ContentMatch.created_at.desc()).all()


@router.post("/{match_id}/decide", response_model=schemas.ContentMatchOut)
def decide_content_match(
    match_id: int, payload: schemas.ContentMatchDecisionIn, db: Session = Depends(get_db)
):
    match = db.get(models.ContentMatch, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    return content_match_service.decide(db, match, payload.decision)


@router.post("/manual", response_model=schemas.ContentMatchOut)
def decide_content_match_manual(payload: schemas.ContentMatchManualIn, db: Session = Depends(get_db)):
    """대시보드의 키워드 TOP7 상세보기에서, 자동 감지 후보로 안 걸린 글도 직접 확정/거절한다."""
    try:
        return content_match_service.manual_set(db, payload.url, payload.title, payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
