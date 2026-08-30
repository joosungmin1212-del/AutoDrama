from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import matcher

router = APIRouter(prefix="/api/blogs", tags=["blogs"])


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
    return blog


@router.delete("/{blog_pk}")
def delete_blog(blog_pk: int, db: Session = Depends(get_db)):
    blog = db.get(models.RegisteredBlog, blog_pk)
    if not blog:
        raise HTTPException(status_code=404, detail="블로그를 찾을 수 없습니다.")
    db.delete(blog)
    db.commit()
    return {"success": True}
