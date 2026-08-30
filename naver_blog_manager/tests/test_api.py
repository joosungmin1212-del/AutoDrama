"""FastAPI 라우트 통합 테스트. 외부 서비스(OpenAI/네이버)는 monkeypatch로 대체한다."""
from app.services import openai_writer


def test_keyword_crud(client):
    r = client.get("/api/keywords")
    assert r.status_code == 200
    assert r.json() == []

    r = client.post("/api/keywords", json={"keyword": "서상동PT", "category": "메인"})
    assert r.status_code == 200
    kw_id = r.json()["id"]

    r = client.post("/api/keywords", json={"keyword": "서상동PT"})
    assert r.status_code == 400  # 중복 키워드 거절

    r = client.get("/api/keywords")
    assert len(r.json()) == 1

    r = client.delete(f"/api/keywords/{kw_id}")
    assert r.status_code == 200
    assert client.get("/api/keywords").json() == []


def test_blog_crud_and_invalid_url(client):
    r = client.post(
        "/api/blogs",
        json={"name": "원장", "blog_url": "https://blog.naver.com/wonjang_pt", "role": "staff"},
    )
    assert r.status_code == 200
    assert r.json()["blog_id"] == "wonjang_pt"

    r = client.post(
        "/api/blogs", json={"name": "이상함", "blog_url": "https://example.com/nope", "role": "staff"}
    )
    assert r.status_code == 400


def test_dashboard_summary_shape(client):
    client.post("/api/keywords", json={"keyword": "서상동PT", "category": "메인"})
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["monitored_keywords"] == 1
    assert body["stats"]["pending_content_match_count"] == 0
    assert len(body["keywords"]) == 1
    assert len(body["keywords"][0]["slots"]) == 7
    assert body["keywords"][0]["our_count"] == 0
    assert body["keywords"][0]["staff_presence"] == []
    assert body["keywords"][0]["experience_confirmed_count"] == 0
    assert body["keywords"][0]["experience_pending_count"] == 0


def test_dashboard_shows_staff_presence(client):
    client.post(
        "/api/blogs",
        json={"name": "원장", "blog_url": "https://blog.naver.com/wonjang_pt", "role": "staff"},
    )
    client.post("/api/keywords", json={"keyword": "서상동PT"})

    body = client.get("/api/dashboard/summary").json()
    assert body["keywords"][0]["staff_presence"] == [{"id": 1, "name": "원장", "present": False}]


def test_keyword_reorder(client):
    id_a = client.post("/api/keywords", json={"keyword": "키워드A"}).json()["id"]
    id_b = client.post("/api/keywords", json={"keyword": "키워드B"}).json()["id"]

    r = client.post("/api/keywords/reorder", json={"order": [id_b, id_a]})
    assert r.status_code == 200

    ordered = [k["keyword"] for k in client.get("/api/dashboard/summary").json()["keywords"]]
    assert ordered == ["키워드B", "키워드A"]


def test_content_match_flow(client):
    client.put("/api/settings", json={"business_name": "OO PT샵", "openai_api_key": "", "rank_check_interval_hours": 24})

    # 순위조회 없이 직접 API로는 content-match가 안 생기니, 서비스 계층 없이 라우트만 검증한다
    r = client.get("/api/content-matches?status=pending")
    assert r.status_code == 200
    assert r.json() == []

    r = client.post("/api/content-matches/999/decide", json={"decision": "confirmed"})
    assert r.status_code == 404

    r = client.post("/api/content-matches/1/decide", json={"decision": "invalid-value"})
    assert r.status_code == 422


def test_settings_masks_api_key(client):
    r = client.put(
        "/api/settings",
        json={
            "business_name": "OO PT샵",
            "openai_api_key": "sk-secret-key",
            "openai_model": "gpt-4o-mini",
            "rank_check_interval_hours": 12,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["openai_api_key"] == ""
    assert body["openai_api_key_set"] is True
    assert body["business_name"] == "OO PT샵"

    # 빈 값으로 다시 PUT하면 기존 키가 유지되어야 한다
    r = client.put(
        "/api/settings",
        json={"business_name": "OO PT샵 2", "openai_api_key": "", "rank_check_interval_hours": 12},
    )
    assert r.json()["openai_api_key_set"] is True


def test_writer_generate_uses_settings_profile(client, monkeypatch):
    client.put(
        "/api/settings",
        json={
            "business_name": "OO PT샵",
            "openai_api_key": "sk-test",
            "openai_model": "gpt-4o-mini",
            "rank_check_interval_hours": 24,
        },
    )

    def fake_generate_post(api_key, model, title, keyword, extra_request, profile):
        assert api_key == "sk-test"
        assert profile.business_name == "OO PT샵"
        return openai_writer.GeneratedPost(
            content="## 소제목\n" + "서상동PT " * 6 + "가" * 1700, hashtags=["#서상동PT", "#PT"]
        )

    monkeypatch.setattr(openai_writer, "generate_post", fake_generate_post)

    r = client.post(
        "/api/writer/generate",
        json={"title": "서상동PT 이야기", "keyword": "서상동PT", "extra_request": ""},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["hashtags"] == ["#서상동PT", "#PT"]
    assert body["seo_check"]["keyword_count"] == 6


def test_writer_generate_without_api_key_returns_400(client):
    r = client.post("/api/writer/generate", json={"title": "제목만 있음"})
    assert r.status_code == 400
