from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import SessionLocal, get_db
from ..services import rank_progress, rank_service

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[schemas.KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return (
        db.query(models.Keyword)
        .order_by(models.Keyword.sort_order.asc(), models.Keyword.created_at.asc())
        .all()
    )


@router.post("", response_model=schemas.KeywordOut)
def create_keyword(payload: schemas.KeywordIn, db: Session = Depends(get_db)):
    max_order = db.query(func.max(models.Keyword.sort_order)).scalar() or 0
    keyword = models.Keyword(
        keyword=payload.keyword.strip(),
        category=payload.category.strip(),
        memo=payload.memo.strip(),
        sort_order=max_order + 1,
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


@router.post("/reorder")
def reorder_keywords(payload: schemas.KeywordReorderIn, db: Session = Depends(get_db)):
    """대시보드 드래그앤드롭으로 정한 순서를 저장한다. payload.order는 위에서부터 나열한 id 목록."""
    for index, keyword_id in enumerate(payload.order):
        db.query(models.Keyword).filter(models.Keyword.id == keyword_id).update(
            {"sort_order": index}
        )
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


async def _run_refresh_all_in_background() -> None:
    """백그라운드에서 실행되므로, 요청과 수명이 다른 별도 DB 세션을 새로 연다."""
    db = SessionLocal()
    try:
        await rank_service.run_all_active_checks(
            db, on_progress=rank_progress.set_current, on_error=rank_progress.add_error
        )
    except Exception as exc:  # noqa: BLE001
        rank_progress.add_error("(전체)", str(exc))
    finally:
        rank_progress.finish()
        db.close()


@router.post("/refresh-all")
def refresh_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if rank_progress.is_running():
        raise HTTPException(status_code=409, detail="이미 순위 갱신이 진행 중입니다. 잠시 후 다시 시도해주세요.")

    total = db.query(models.Keyword).filter(models.Keyword.active.is_(True)).count()
    if total == 0:
        return {"success": True, "total": 0}

    rank_progress.reset(total)
    background_tasks.add_task(_run_refresh_all_in_background)
    return {"success": True, "total": total}


@router.get("/refresh-all/status")
def refresh_all_status():
    """진행 중인 "전체 순위 갱신"의 진행 상태를 폴링용으로 반환한다."""
    return rank_progress.snapshot()
