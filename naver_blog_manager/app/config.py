"""환경설정 로드.

.env 파일 값 + (설정 화면에서 저장한) DB의 Setting 레코드를 함께 사용한다.
.env는 "최초 기본값"이고, 실제 운영 중 값은 DB(Setting 테이블)가 우선한다.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# 테스트에서 격리된 DB를 쓰기 위해 NBM_DATA_DIR로 재정의 가능 (평소엔 신경 쓸 필요 없음)
DATA_DIR = Path(os.getenv("NBM_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

DB_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

NAVER_STATE_PATH = DATA_DIR / "naver_state.json"
# 계정을 여러 개 등록해 쓸 때(계정 전환), 공식 블로그별로 로그인 세션을 따로 저장하는 곳.
# 아무 계정도 특정 블로그에 지정해 로그인하지 않았으면 위 NAVER_STATE_PATH(기본 세션)를
# 그대로 쓴다 - PC 1대에 계정 1개만 쓰는 기존 사용자는 아무것도 안 바뀐다.
NAVER_SESSIONS_DIR = DATA_DIR / "naver_sessions"
NAVER_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv("PORT", "8000"))
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NAVER_USER_AGENT = os.getenv(
    "NAVER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)

# 순위 체크 관련 기본값
DEFAULT_RANK_CHECK_INTERVAL_HOURS = 24
TOP_N = 7  # 요구사항: TOP7 고정
MIN_REQUEST_DELAY_SEC = 3.0
MAX_REQUEST_DELAY_SEC = 8.0

# 글쓰기 SEO 기본 가이드
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
SEO_MIN_LENGTH = 1700
SEO_MAX_LENGTH = 2500
SEO_MIN_KEYWORD_COUNT = 5
SEO_MAX_KEYWORD_COUNT = 10
