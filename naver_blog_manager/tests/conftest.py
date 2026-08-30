"""pytest 전역 설정.

app.config가 import되기 전에 테스트 전용 데이터 디렉터리를 지정해서, 실제 운영 DB
(data/app.db)를 절대 건드리지 않도록 격리한다. conftest.py는 pytest가 테스트 모듈보다
먼저 임포트하므로 여기서 환경변수를 세팅하면 이후 모든 `from app import config` 시점에
반영된다.
"""
import os
import tempfile

os.environ.setdefault("NBM_DATA_DIR", tempfile.mkdtemp(prefix="nbm_test_"))
# 로컬호스트 접근 토큰 검사는 실제 브라우저 흐름이 있어야 의미가 있으므로 테스트에서는 끈다
# (app/main.py의 local_token_guard 미들웨어 참고).
os.environ.setdefault("NBM_DISABLE_AUTH", "1")

import pytest  # noqa: E402


@pytest.fixture()
def db_session():
    """테스트마다 깨끗한 인메모리 상태의 DB 세션을 제공한다."""
    from app.db import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """FastAPI TestClient. 매 테스트마다 DB를 초기화한다."""
    from fastapi.testclient import TestClient

    from app.db import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
