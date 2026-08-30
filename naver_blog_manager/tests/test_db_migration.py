"""기존에 설치되어 데이터가 들어있는 사용자의 DB(예: sort_order 컬럼이 없는 옛날 스키마)가
업데이트 후 init_db()를 다시 돌려도 깨지지 않는지 확인한다."""
import sqlalchemy as sa

from app.db import Base, _apply_column_migrations, init_db


def test_init_db_adds_missing_column_to_legacy_table(tmp_path):
    db_path = tmp_path / "legacy.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")

    # sort_order 컬럼이 없는 옛날 버전의 keywords 테이블을 흉내낸다
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE keywords ("
                "id INTEGER PRIMARY KEY, keyword VARCHAR(200) UNIQUE, "
                "category VARCHAR(50), active BOOLEAN, memo VARCHAR(300), "
                "created_at DATETIME)"
            )
        )
        conn.execute(sa.text("INSERT INTO keywords (id, keyword) VALUES (1, '서상동PT')"))

    import app.db as db_module

    original_engine = db_module.engine
    db_module.engine = engine
    try:
        Base.metadata.create_all(bind=engine)  # keywords는 이미 있으니 새 테이블만 생김
        _apply_column_migrations()

        with engine.connect() as conn:
            columns = {row[1] for row in conn.execute(sa.text("PRAGMA table_info(keywords)"))}
            assert "sort_order" in columns

            row = conn.execute(sa.text("SELECT keyword FROM keywords WHERE id = 1")).fetchone()
            assert row[0] == "서상동PT"  # 기존 데이터가 안 날아갔는지 확인
    finally:
        db_module.engine = original_engine


def test_apply_column_migrations_is_idempotent(db_session):
    # 이미 최신 스키마인 상태에서 두 번 돌려도 에러 없이 통과해야 한다
    _apply_column_migrations()
    _apply_column_migrations()
