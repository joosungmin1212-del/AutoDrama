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


def test_keyword_update(client):
    """오타 수정 등을 위해 삭제 후 재등록(=이력 손실) 없이 그대로 고칠 수 있어야 한다."""
    kw_id = client.post("/api/keywords", json={"keyword": "서상둥PT", "category": "메인"}).json()["id"]

    r = client.put(f"/api/keywords/{kw_id}", json={"keyword": "서상동PT", "category": "핵심", "memo": "오타 수정"})
    assert r.status_code == 200
    body = r.json()
    assert body["keyword"] == "서상동PT"
    assert body["category"] == "핵심"
    assert body["memo"] == "오타 수정"

    r = client.put("/api/keywords/999", json={"keyword": "없음"})
    assert r.status_code == 404


def test_keyword_update_rejects_duplicate_name(client):
    client.post("/api/keywords", json={"keyword": "키워드A"})
    kw_b = client.post("/api/keywords", json={"keyword": "키워드B"}).json()["id"]

    r = client.put(f"/api/keywords/{kw_b}", json={"keyword": "키워드A"})
    assert r.status_code == 400


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


def test_registering_a_blog_immediately_updates_already_stored_rank_results(client):
    """실제로 있었던 문제: 대시보드 TOP7 상세보기에서 "경쟁업체로 등록"을 눌러도, 이미
    저장돼 있던 지난 순위 스냅샷은 다음 순위 갱신 전까지 그대로라 화면에 아무 변화가
    없는 것처럼 보였다. 새로 등록하는 즉시 같은 blog_id의 기존 결과에도 반영돼야 한다."""
    from datetime import datetime

    from app import models
    from app.db import SessionLocal

    kw_id = client.post("/api/keywords", json={"keyword": "서상동PT"}).json()["id"]

    db = SessionLocal()
    try:
        check = models.RankCheck(keyword_id=kw_id, checked_at=datetime.utcnow())
        db.add(check)
        db.flush()
        db.add(
            models.RankResult(
                rank_check_id=check.id,
                position=1,
                content_type="blog",
                url="https://blog.naver.com/rival_trainer/1",
                blog_id="rival_trainer",
                title="아무 상관없는 블로그 글",
                ownership="other",
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.post(
        "/api/blogs",
        json={
            "name": "김민수 헬스타이거",
            "blog_url": "https://blog.naver.com/rival_trainer",
            "role": "competitor",
        },
    )
    assert r.status_code == 200

    summary = client.get("/api/dashboard/summary").json()
    slot = summary["keywords"][0]["slots"][0]
    assert slot["ownership"] == "other"
    assert slot["owner_role"] == "competitor"
    assert slot["owner_name"] == "김민수 헬스타이거"


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
    assert body["trend"] == []  # 아직 순위체크 이력이 없으니 빈 배열
    assert body["stats"]["account_breakdown"] == []


def test_dashboard_summary_includes_trend_and_account_breakdown(client):
    """실제로 순위체크 이력이 쌓이면 /api/dashboard/summary가 추이(trend)와 계정별
    노출 현황(account_breakdown)을 정확히 계산해서 내려줘야 한다."""
    from datetime import datetime

    from app import models
    from app.db import SessionLocal

    kw_id = client.post("/api/keywords", json={"keyword": "서상동PT"}).json()["id"]
    blog = client.post(
        "/api/blogs",
        json={"name": "원장", "blog_url": "https://blog.naver.com/wonjang_pt", "role": "staff"},
    ).json()

    db = SessionLocal()
    try:
        check = models.RankCheck(keyword_id=kw_id, checked_at=datetime.utcnow())
        db.add(check)
        db.flush()
        db.add(
            models.RankResult(
                rank_check_id=check.id,
                position=1,
                content_type="blog",
                url="https://blog.naver.com/wonjang_pt/1",
                blog_id="wonjang_pt",
                title="원장 글",
                matched_blog_id_fk=blog["id"],
                ownership="ours_staff",
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()

    assert len(body["trend"]) == 1
    assert body["trend"][0]["our_total"] == 1

    assert body["stats"]["account_breakdown"] == [
        {"blog_id": blog["id"], "name": "원장", "count": 1}
    ]


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
    client.put("/api/settings/ai", json={"openai_api_key": "", "rank_check_interval_hours": 24})

    # 순위조회 없이 직접 API로는 content-match가 안 생기니, 서비스 계층 없이 라우트만 검증한다
    r = client.get("/api/content-matches?status=pending")
    assert r.status_code == 200
    assert r.json() == []

    r = client.post("/api/content-matches/999/decide", json={"decision": "confirmed"})
    assert r.status_code == 404

    r = client.post("/api/content-matches/1/decide", json={"decision": "invalid-value"})
    assert r.status_code == 422


def test_content_match_manual_endpoint_confirms_a_post_without_name_match(client):
    """대시보드 키워드 TOP7 상세보기에서, 자동 감지에 안 걸린 글도 직접 확정할 수 있다."""
    r = client.post(
        "/api/content-matches/manual",
        json={"url": "https://blog.naver.com/reviewer3/5", "title": "동네 헬스장 후기", "decision": "confirmed"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "confirmed"
    assert body["matched_text"] == "수동 확인"

    r = client.get("/api/content-matches?status=all")
    assert len(r.json()) == 1

    r = client.post("/api/content-matches/manual", json={"url": "", "title": "", "decision": "confirmed"})
    assert r.status_code == 400


def test_settings_profile_and_ai_are_independent(client):
    r = client.put("/api/settings/profile", json={"business_name": "OO PT샵"})
    assert r.status_code == 200
    assert r.json()["business_name"] == "OO PT샵"

    r = client.put(
        "/api/settings/ai",
        json={"openai_api_key": "sk-secret-key", "openai_model": "gpt-4o-mini", "rank_check_interval_hours": 12},
    )
    assert r.status_code == 200
    body = r.json()
    assert "openai_api_key" not in body  # 원문은 응답에 아예 없어야 한다
    assert body["openai_api_key_set"] is True
    assert body["business_name"] == "OO PT샵"  # AI 설정 저장이 프로필을 건드리면 안 됨

    # 빈 값으로 다시 PUT하면 기존 키가 유지되어야 한다
    r = client.put("/api/settings/ai", json={"openai_api_key": "", "rank_check_interval_hours": 12})
    assert r.json()["openai_api_key_set"] is True


def test_settings_ai_reschedules_scheduler_when_interval_changes(client, monkeypatch):
    """설정에서 순위 자동 체크 주기를 바꾸면, 실행 중인 스케줄러도 재시작 없이 반영돼야 한다.

    예전에는 이 값이 DB에 저장만 되고 실제 스케줄러는 항상 기본값(24시간)으로 고정 동작하는
    버그가 있었다."""
    from app.routers import settings as settings_router

    calls = []
    monkeypatch.setattr(settings_router.scheduler_service, "reschedule", lambda hours: calls.append(hours))

    # 기본값(24)과 같은 값으로 저장하면 재조정할 필요가 없다
    client.put("/api/settings/ai", json={"rank_check_interval_hours": 24})
    assert calls == []

    # 다른 값으로 바꾸면 reschedule이 호출돼야 한다
    r = client.put("/api/settings/ai", json={"rank_check_interval_hours": 6})
    assert r.status_code == 200
    assert calls == [6]


def test_settings_ai_rejects_non_positive_interval(client):
    r = client.put("/api/settings/ai", json={"rank_check_interval_hours": 0})
    assert r.status_code == 422


def test_settings_prompt_defaults_and_custom_persists(client):
    body = client.get("/api/settings").json()
    assert body["custom_prompt"] == body["default_prompt"]  # 커스텀 안 했으면 기본값이 그대로 보임
    assert len(body["default_prompt"]) > 0

    r = client.put("/api/settings/ai", json={"custom_prompt": "나만의 프롬프트입니다"})
    assert r.json()["custom_prompt"] == "나만의 프롬프트입니다"

    # 다시 조회해도 커스텀 값이 남아있어야 한다
    assert client.get("/api/settings").json()["custom_prompt"] == "나만의 프롬프트입니다"


def test_writer_generate_uses_settings_profile(client, monkeypatch):
    client.put("/api/settings/profile", json={"business_name": "OO PT샵"})
    client.put("/api/settings/ai", json={"openai_api_key": "sk-test", "openai_model": "gpt-4o-mini"})

    def fake_generate_post(api_key, model, title, keyword, extra_request, profile, system_prompt=None):
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
