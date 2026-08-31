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


def test_static_asset_urls_carry_a_cache_busting_version(client):
    """no-cache 헤더만으로는, 업데이트 전에 이미 브라우저에 캐시된 파일까지 즉시 재검증하게
    만들지는 못한다 - 실제로 이 문제로 설정 화면이 빈 값으로 보이는 오류가 있었다. 그래서
    HTML이 static 파일을 가리킬 때 항상 ?v=버전 을 붙여서, 업데이트마다 아예 다른 URL이
    되게 한다 (다른 URL은 브라우저가 캐시를 재사용할 수 없어 무조건 새로 받아온다)."""
    r = client.get("/")
    assert r.status_code == 200
    assert "/static/js/dashboard.js?v=" in r.text
    assert "/static/css/style.css?v=" in r.text


def test_static_assets_are_never_heuristically_cached(monkeypatch):
    """정적 JS/CSS가 브라우저에 오래 캐시되면, 앱을 업데이트해도 사용자가 옛 파일을
    계속 쓰게 되어 화면이 깨진 것처럼 보이는 문제가 실제로 있었다 (설정/키워드 화면
    오류). no-cache를 강제해서 매번 서버에 최신인지 재확인하도록 한다."""
    import app.main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as client:
        r = client.get("/static/js/dashboard.js")
        assert r.status_code == 200
        assert r.headers.get("cache-control") == "no-cache"
