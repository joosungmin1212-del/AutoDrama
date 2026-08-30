"""FastAPI 앱 조립."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db
from .routers import blogs, dashboard, keywords, naver_auth, writer
from .routers import settings as settings_router
from .services import scheduler as scheduler_service

BASE_DIR = Path(__file__).resolve().parent


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
