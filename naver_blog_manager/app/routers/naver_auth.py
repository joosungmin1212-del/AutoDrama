from datetime import datetime

from fastapi import APIRouter, HTTPException

from .. import schemas
from ..services import naver_browser

router = APIRouter(prefix="/api/naver-auth", tags=["naver-auth"])


@router.get("/status", response_model=schemas.NaverAuthStatus)
async def status():
    try:
        logged_in = await naver_browser.check_login_status()
        return schemas.NaverAuthStatus(logged_in=logged_in, checked_at=datetime.utcnow())
    except Exception as exc:  # noqa: BLE001
        return schemas.NaverAuthStatus(
            logged_in=False, checked_at=datetime.utcnow(), message=str(exc)
        )


@router.post("/login", response_model=schemas.NaverAuthStatus)
async def login():
    """실제 브라우저 창을 띄워 사용자가 직접 로그인하도록 한다. PT샵 PC에서 실행되어야 한다."""
    try:
        await naver_browser.login_interactive()
        return schemas.NaverAuthStatus(
            logged_in=True, checked_at=datetime.utcnow(), message="로그인 성공"
        )
    except naver_browser.NaverAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"로그인 중 오류가 발생했습니다: {exc}")


@router.post("/logout")
def logout():
    naver_browser.clear_saved_session()
    return {"success": True}
