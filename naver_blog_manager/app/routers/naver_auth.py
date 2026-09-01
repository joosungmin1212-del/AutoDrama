from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services import naver_browser, writer_account

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
    """등록된 글쓰기 계정(직원으로 등록한 블로그)마다 로그인 상태를 보여준다
    (블로그 관리 화면의 계정 전환 UI + 글쓰기 화면의 계정 선택 목록용).

    "공식 블로그"라는 별도 역할은 더 이상 요구하지 않는다 - 실제로 로그인해서 쓰는
    계정은 이미 "직원"으로 등록해둔 블로그 그 자체이기 때문이다.
    """
    accounts_rows = writer_account.list_writer_accounts(db)
    accounts = []
    for b in accounts_rows:
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
async def login(blog_id: str | None = None, db: Session = Depends(get_db)):
    """실제 브라우저 창을 띄워 사용자가 직접 로그인하도록 한다. PT샵 PC에서 실행되어야 한다.

    blog_id를 주면 그 계정 전용 세션으로 저장된다(계정 전환용) - 여러 계정을 등록해
    여러 네이버 계정을 오갈 때, 블로그 관리 화면에서 계정별로 로그인할 수 있게 한다.
    안 주면 기본 세션으로 저장된다(최초 설정 화면의 로그인).

    로그인에 성공하면, 그 계정이 곧바로 "지금 쓸 글쓰기 계정"이 된다("로그인했던 계정이
    글쓰기 계정" 요구사항) - 매번 따로 골라줄 필요 없이 방금 로그인한 계정으로 바로
    "네이버로 보내기"가 동작한다.
    """
    try:
        await naver_browser.login_interactive(blog_id=blog_id)
        if blog_id:
            setting = db.get(models.Setting, 1)
            if not setting:
                setting = models.Setting(id=1)
                db.add(setting)
            setting.active_writer_blog_id = blog_id
            db.commit()
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
