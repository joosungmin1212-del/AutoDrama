"""SQLAlchemy 엔진 / 세션 관리."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from . import config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# create_all()은 "없는 테이블"만 새로 만들고, 이미 있는 테이블에 새 컬럼을 추가해주지는 않는다.
# 정식 마이그레이션 도구(Alembic) 없이도, 이미 설치돼서 데이터가 들어있는 사용자의 DB가
# 업데이트 후에도 깨지지 않도록 여기서 부족한 컬럼만 최소한으로 보충한다.
_COLUMN_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "keywords": [("sort_order", "INTEGER DEFAULT 0")],
    "settings": [
        ("custom_prompt", "TEXT DEFAULT ''"),
        ("custom_watch_keywords", "TEXT DEFAULT ''"),
    ],
    "alerts": [("blog_id", "VARCHAR(200) DEFAULT ''")],
}


def _apply_column_migrations() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _COLUMN_MIGRATIONS.items():
            if table not in existing_tables:
                continue  # 새로 설치한 경우면 create_all이 이미 최신 스키마로 만들어준다
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            for column_name, column_def in columns:
                if column_name not in existing_columns:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}"))


def init_db() -> None:
    # 모델을 등록하기 위해 import (순환참조 방지를 위해 함수 내부에서)
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_column_migrations()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends용 세션 제공자."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """스케줄러/서비스 코드 등 FastAPI 요청 밖에서 사용하는 세션 컨텍스트."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
