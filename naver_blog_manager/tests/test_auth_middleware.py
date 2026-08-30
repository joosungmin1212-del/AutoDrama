"""로컬호스트 토큰 인증 미들웨어 테스트.

다른 테스트들은 NBM_DISABLE_AUTH=1로 이 검사를 건너뛰지만, 이 파일은 실제로 인증이
켜졌을 때 동작을 검증하기 위해 일부러 app.main을 인증 활성 상태로 다시 로드한다.
테스트가 끝나면 다른 테스트에 영향이 없도록 반드시 원래 상태(인증 비활성)로 복구한다.
"""
import importlib

from fastapi.testclient import TestClient


def test_api_requires_token_when_auth_enabled(monkeypatch):
    monkeypatch.delenv("NBM_DISABLE_AUTH", raising=False)

    import app.main as main_module

    importlib.reload(main_module)
    try:
        with TestClient(main_module.app) as client:
            r = client.get("/api/keywords")
            assert r.status_code == 401

            r = client.get(f"/api/keywords?token={main_module.APP_TOKEN}")
            assert r.status_code == 200

            r = client.get("/api/keywords", headers={"X-App-Token": main_module.APP_TOKEN})
            assert r.status_code == 200

            r = client.get("/api/keywords", headers={"X-App-Token": "wrong-token"})
            assert r.status_code == 401
    finally:
        monkeypatch.setenv("NBM_DISABLE_AUTH", "1")
        importlib.reload(main_module)
