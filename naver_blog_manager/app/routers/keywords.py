from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import rank_service

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[schemas.KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return db.query(models.Keyword).order_by(models.Keyword.created_at.desc()).all()


@router.post("", response_model=schemas.KeywordOut)
def create_keyword(payload: schemas.KeywordIn, db: Session = Depends(get_db)):
    keyword = models.Keyword(
        keyword=payload.keyword.strip(), category=payload.category.strip(), memo=payload.memo.strip()
    )
    db.add(keyword)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="이미 등록된 키워드입니다.")
    db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.get(models.Keyword, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    db.delete(keyword)
    db.commit()
    return {"success": True}


def _to_rank_check_out(rank_check: models.RankCheck) -> schemas.RankCheckOut:
    return schemas.RankCheckOut(
        checked_at=rank_check.checked_at,
        results=[
            schemas.RankResultOut(
                position=r.position,
                content_type=r.content_type,
                url=r.url,
                blog_id=r.blog_id,
                title=r.title,
                ownership=r.ownership,
                matched_blog_name=r.matched_blog.name if r.matched_blog else None,
            )
            for r in rank_check.results
        ],
    )


@router.post("/{keyword_id}/refresh", response_model=schemas.RankCheckOut)
async def refresh_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.get(models.Keyword, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    try:
        rank_check = await rank_service.run_rank_check_async(db, keyword)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"네이버 순위 조회에 실패했습니다: {exc}")
    return _to_rank_check_out(rank_check)


@router.post("/refresh-all")
async def refresh_all(db: Session = Depends(get_db)):
    try:
        checks = await rank_service.run_all_active_checks(db)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"전체 순위 갱신 중 오류가 발생했습니다: {exc}")
    return {"success": True, "checked": len(checks)}
