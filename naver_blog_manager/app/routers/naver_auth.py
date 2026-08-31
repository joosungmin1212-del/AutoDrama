from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import naver_browser

router = APIRouter(prefix="/api/naver-auth", tags=["naver-auth"])


@router.get("/status", response_model=schemas.NaverAuthStatus)
async def status(blog_id: str | None = None):
    """blog_id를 안 주면 기본 세션(최초 로그인 계정) 상태를 확인한다 - 로그인 게이트/설정
    화면의 기존 단일 계정 흐름은 이 방식 그대로 계속 동작한다."""
    try:
        logged_in = await naver_browser.check_login_status(blog_id)
        return schemas.NaverAuthStatus(logged_in=logged_in, checked_at=datetime.utcnow())
    except Exception as exc:  # noqa: BLE001
        return schemas.NaverAuthStatus(
            logged_in=False, checked_at=datetime.utcnow(), message=str(exc)
        )


@router.get("/accounts", response_model=list[schemas.NaverAccountOut])
async def list_accounts(db: Session = Depends(get_db)):
    """등록된 공식 블로그마다 로그인 상태를 보여준다 (블로그 관리 화면의 계정 전환 UI용)."""
    company_blogs = (
        db.query(models.RegisteredBlog)
        .filter(models.RegisteredBlog.role == models.BlogRole.COMPANY.value)
        .order_by(models.RegisteredBlog.created_at.asc())
        .all()
    )
    accounts = []
    for b in company_blogs:
        has_dedicated = naver_browser.has_saved_session(b.blog_id)
        logged_in = await naver_browser.check_login_status(b.blog_id)
        accounts.append(
            schemas.NaverAccountOut(
                blog_pk=b.id,
                name=b.name,
                blog_id=b.blog_id,
                logged_in=logged_in,
                has_dedicated_session=has_dedicated,
            )
        )
    return accounts


@router.post("/login", response_model=schemas.NaverAuthStatus)
async def login(blog_id: str | None = None):
    """실제 브라우저 창을 띄워 사용자가 직접 로그인하도록 한다. PT샵 PC에서 실행되어야 한다.

    blog_id를 주면 그 공식 블로그 전용 계정으로 저장된다(계정 전환용) - 여러 공식 블로그를
    등록해 여러 네이버 계정을 오갈 때, 블로그 관리 화면에서 계정별로 로그인할 수 있게 한다.
    안 주면 기본 세션으로 저장된다(최초 설정 화면의 로그인).
    """
    try:
        await naver_browser.login_interactive(blog_id=blog_id)
        return schemas.NaverAuthStatus(
            logged_in=True, checked_at=datetime.utcnow(), message="로그인 성공"
        )
    except naver_browser.NaverAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {exc}")


@router.post("/logout")
def logout(blog_id: str | None = None):
    naver_browser.clear_saved_session(blog_id)
    return {"success": True}
