from app.services import rank_progress, rank_service


def test_refresh_all_with_no_keywords_returns_zero(client):
    r = client.post("/api/keywords/refresh-all")
    assert r.status_code == 200
    assert r.json() == {"success": True, "total": 0}


def test_refresh_all_reports_progress_and_survives_partial_failure(client, monkeypatch):
    client.post("/api/keywords", json={"keyword": "키워드A"})
    client.post("/api/keywords", json={"keyword": "키워드B"})

    async def fake_run_all_active_checks(db, on_progress=None, on_error=None):
        if on_error:
            on_error("키워드A", "네이버 차단 의심")
        if on_progress:
            on_progress(1, 2, "키워드A")
        if on_progress:
            on_progress(2, 2, "키워드B")
        return []

    monkeypatch.setattr(rank_service, "run_all_active_checks", fake_run_all_active_checks)

    r = client.post("/api/keywords/refresh-all")
    assert r.status_code == 200
    assert r.json()["total"] == 2

    status = client.get("/api/keywords/refresh-all/status").json()
    assert status["running"] is False
    assert status["done"] == 2
    assert status["total"] == 2
    assert status["errors"] == [{"keyword": "키워드A", "message": "네이버 차단 의심"}]


def test_refresh_all_rejects_concurrent_run(client, monkeypatch):
    client.post("/api/keywords", json={"keyword": "키워드A"})
    rank_progress.reset(1)  # 이미 진행 중인 상태를 흉내낸다
    try:
        r = client.post("/api/keywords/refresh-all")
        assert r.status_code == 409
    finally:
        rank_progress.finish()
