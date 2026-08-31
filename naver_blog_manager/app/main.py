"""FastAPI 앱 조립."""
from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db
from .routers import blogs, content_matches, dashboard, keywords, naver_auth, writer
from .routers import settings as settings_router
from .services import access_token, naver_browser, scheduler as scheduler_service

BASE_DIR = Path(__file__).resolve().parent

# 이 서버는 127.0.0.1에만 열려 있지만, 같은 PC의 다른 Windows 계정/프로그램도 로컬호스트
# 포트에는 동일하게 접근할 수 있다. run.py가 브라우저를 직접 열어줄 때만 이 토큰이 쿠키로
# 심어지므로, 토큰을 모르는 다른 프로세스는 /api/*를 호출할 수 없다.
# 테스트(TestClient)에서는 NBM_DISABLE_AUTH=1로 이 검사를 건너뛴다.
APP_TOKEN = access_token.get_or_create_token()
TOKEN_COOKIE_NAME = "nbm_token"
_AUTH_DISABLED = os.getenv("NBM_DISABLE_AUTH") == "1"

# 네이버 로그인이 안 되어 있으면 이 페이지들 대신 /login으로 보낸다 (로그인이 앱의 첫 관문).
_LOGIN_GATED_PAGES = {"/", "/writer", "/blogs", "/settings"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler_service.start_scheduler()
    yield
    scheduler_service.shutdown_scheduler()


app = FastAPI(title="PT샵 네이버 블로그 매니저", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(dashboard.router)
app.include_router(keywords.router)
app.include_router(blogs.router)
app.include_router(writer.router)
app.include_router(naver_auth.router)
app.include_router(settings_router.router)
app.include_router(content_matches.router)


def _set_token_cookie(response):
    response.set_cookie(
        TOKEN_COOKIE_NAME, APP_TOKEN, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30
    )
    return response


@app.middleware("http")
async def local_token_guard(request: Request, call_next):
    """run.py가 열어준 브라우저인지 확인한다 (토큰 쿠키/헤더/쿼리스트링 중 하나로 인증)."""
    if _AUTH_DISABLED:
        return await call_next(request)

    supplied = (
        request.query_params.get("token")
        or request.cookies.get(TOKEN_COOKIE_NAME)
        or request.headers.get("X-App-Token")
        or ""
    )
    authorized = secrets.compare_digest(supplied, APP_TOKEN)

    if request.url.path.startswith("/api/") and not authorized:
        return JSONResponse(
            status_code=401,
            content={"detail": "인증이 필요합니다. run.py(2-start.bat)로 연 창에서 다시 접속해주세요."},
        )

    # 네이버 로그인 세션이 아예 없으면, 실제 페이지 대신 로그인 화면으로 먼저 보낸다.
    if (
        authorized
        and request.url.path in _LOGIN_GATED_PAGES
        and not naver_browser.has_saved_session()
    ):
        return _set_token_cookie(RedirectResponse(url="/login"))

    response = await call_next(request)

    # 정상 토큰으로 페이지에 처음 들어온 경우, 이후 요청부터는 쿼리스트링 없이도 되도록
    # 쿠키를 심어준다 (탭 안에서의 페이지 이동/새로고침에 계속 토큰을 붙일 필요가 없게).
    if authorized and not request.url.path.startswith("/api/"):
        _set_token_cookie(response)
    return response


@app.middleware("http")
async def no_cache_static_assets(request: Request, call_next):
    """정적 파일(JS/CSS)은 기본적으로 Last-Modified만 붙어서 브라우저가 한동안 서버에
    묻지도 않고 예전 캐시를 그대로 쓴다(휴리스틱 캐싱). 이 앱은 자주 업데이트되는데,
    파일을 새로 받아도 브라우저가 옛날 JS/CSS를 계속 쓰면 화면이 깨진 것처럼 보인다
    (실제로 새 화면 요소를 옛 JS가 못 찾아 오류가 나는 사례가 있었음). no-cache를 붙여
    매번 서버에 최신인지 확인하도록 강제한다 (내용이 그대로면 여전히 304로 빠르게 응답됨).
    인증 미들웨어보다 먼저 등록해서, 인증 켜짐/꺼짐 여부와 상관없이 항상 적용되게 한다."""
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"active_nav": ""})


@app.get("/")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active_nav": "dashboard"})


@app.get("/writer")
def writer_page(request: Request):
    return templates.TemplateResponse(request, "writer.html", {"active_nav": "writer"})


@app.get("/blogs")
def blogs_page(request: Request):
    return templates.TemplateResponse(request, "blogs.html", {"active_nav": "blogs"})


@app.get("/settings")
def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html", {"active_nav": "settings"})
