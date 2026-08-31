"""네이버 로그인이 안 되어 있으면 페이지 대신 /login으로 보내는 게이트 테스트.

다른 테스트들은 NBM_DISABLE_AUTH=1로 이 검사를 건너뛰므로, 이 파일은 인증을 켠 상태로
app.main을 다시 로드해서 실제 동작을 확인한다. 끝나면 반드시 원래 상태로 복구한다.
"""
import importlib

from fastapi.testclient import TestClient


def test_page_redirects_to_login_when_no_naver_session(monkeypatch):
    monkeypatch.delenv("NBM_DISABLE_AUTH", raising=False)

    import app.main as main_module

    importlib.reload(main_module)
    try:
        with TestClient(main_module.app, follow_redirects=False) as client:
            r = client.get(f"/?token={main_module.APP_TOKEN}")
            assert r.status_code in (302, 307)
            assert r.headers["location"] == "/login"

            # /login 자체는 게이트 대상이 아니라서 그대로 보여야 한다
            r = client.get(f"/login?token={main_module.APP_TOKEN}")
            assert r.status_code == 200
    finally:
        monkeypatch.setenv("NBM_DISABLE_AUTH", "1")
        importlib.reload(main_module)


def test_page_not_redirected_when_session_exists(monkeypatch, tmp_path):
    monkeypatch.delenv("NBM_DISABLE_AUTH", raising=False)

    import app.main as main_module
    from app.services import naver_browser

    importlib.reload(main_module)
    try:
        state_path = tmp_path / "naver_state.json"
        state_path.write_text("dummy", encoding="utf-8")
        monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", state_path)

        with TestClient(main_module.app, follow_redirects=False) as client:
            r = client.get(f"/?token={main_module.APP_TOKEN}")
            assert r.status_code == 200
    finally:
        monkeypatch.setenv("NBM_DISABLE_AUTH", "1")
        importlib.reload(main_module)
