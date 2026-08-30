"""로컬 서버 실행 엔트리포인트.

사용법:
    pip install -r requirements.txt
    playwright install chromium
    python run.py

실행 후 브라우저에서 http://127.0.0.1:8000 접속.
"""
from __future__ import annotations

import uvicorn

from app import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=config.PORT, reload=False)
