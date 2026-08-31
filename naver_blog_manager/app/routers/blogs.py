from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import matcher

router = APIRouter(prefix="/api/blogs", tags=["blogs"])


def _apply_new_registration_to_existing_results(db: Session, blog: models.RegisteredBlog) -> None:
    """새로 등록한 블로그와 같은 계정으로 이미 저장돼있던 지난 순위 결과에도 즉시 반영한다.

    안 하면, 예를 들어 대시보드에서 "경쟁업체로 등록"을 눌러도 다음 순위 갱신 전까지는
    화면에 이미 떠 있던 TOP7 스냅샷이 등록 전 상태 그대로 남아있어서 "등록했는데 왜
    아무 변화가 없지"처럼 보인다.
    """
    results = (
        db.query(models.RankResult).filter(models.RankResult.blog_id == blog.blog_id).all()
    )
    if not results:
        return

    for r in results:
        r.matched_blog_id_fk = blog.id
        # 체험단(EXPERIENCE)은 계정 단위로 ownership을 못 박으면 안 된다 - 다른 키워드에서
        # 완전히 다른 업체 글을 썼을 수 있어서, 이미 저장된 ownership(예: 사람이 직접 확정한
        # ours_experience)을 되돌리면 안 된다. 신원 표시(matched_blog_id_fk)만 붙여준다.
        if blog.role != models.BlogRole.EXPERIENCE.value:
            ownership, _ = matcher.match_ownership(blog.blog_id, [blog])
            r.ownership = ownership
    db.commit()


@router.get("", response_model=list[schemas.RegisteredBlogOut])
def list_blogs(db: Session = Depends(get_db)):
    return db.query(models.RegisteredBlog).order_by(models.RegisteredBlog.created_at.desc()).all()


@router.post("", response_model=schemas.RegisteredBlogOut)
def create_blog(payload: schemas.RegisteredBlogIn, db: Session = Depends(get_db)):
    blog_id = matcher.extract_identifier(payload.blog_url)
    if not blog_id:
        raise HTTPException(
            status_code=400,
            detail="블로그 주소에서 블로그ID를 인식하지 못했습니다. blog.naver.com/아이디 형태인지 확인해주세요.",
        )
    blog = models.RegisteredBlog(
        name=payload.name.strip(),
        blog_url=payload.blog_url.strip(),
        blog_id=blog_id,
        role=payload.role,
        memo=payload.memo,
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)

    _apply_new_registration_to_existing_results(db, blog)
    return blog


@router.delete("/{blog_pk}")
def delete_blog(blog_pk: int, db: Session = Depends(get_db)):
    blog = db.get(models.RegisteredBlog, blog_pk)
    if not blog:
        raise HTTPException(status_code=404, detail="블로그를 찾을 수 없습니다.")
    db.delete(blog)
    db.commit()
    return {"success": True}
