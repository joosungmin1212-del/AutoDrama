"""/api/alerts 라우터 테스트 (목록 조회 + 수동 확인 처리)."""
from datetime import datetime

from app import models
from app.db import SessionLocal


def _make_alert(**kwargs):
    db = SessionLocal()
    try:
        keyword = db.query(models.Keyword).filter_by(keyword="서상동PT").first()
        if not keyword:
            keyword = models.Keyword(keyword="서상동PT")
            db.add(keyword)
            db.flush()
        alert = models.Alert(keyword_id=keyword.id, detected_at=datetime.utcnow(), **kwargs)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert.id
    finally:
        db.close()


def test_list_alerts_defaults_to_open_only(client):
    open_id = _make_alert(blog_id="staffblog", previous_position=1)
    resolved_id = _make_alert(blog_id="otherblog", previous_position=3, resolved=True)

    r = client.get("/api/alerts")
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()]
    assert open_id in ids
    assert resolved_id not in ids

    r = client.get("/api/alerts?status=resolved")
    ids = [a["id"] for a in r.json()]
    assert resolved_id in ids
    assert open_id not in ids

    r = client.get("/api/alerts?status=all")
    assert len(r.json()) == 2


def test_list_alerts_filters_by_keyword(client):
    id1 = _make_alert(blog_id="a", previous_position=1)

    db = SessionLocal()
    other_kw = models.Keyword(keyword="다른키워드")
    db.add(other_kw)
    db.commit()
    db.refresh(other_kw)
    kw_id = other_kw.id
    db.close()

    db = SessionLocal()
    db.add(models.Alert(keyword_id=kw_id, blog_id="b", previous_position=2, detected_at=datetime.utcnow()))
    db.commit()
    db.close()

    r = client.get(f"/api/alerts?keyword_id={kw_id}")
    assert len(r.json()) == 1
    assert r.json()[0]["blog_id"] == "b"


def test_resolve_alert(client):
    alert_id = _make_alert(blog_id="staffblog", previous_position=1)

    r = client.post(f"/api/alerts/{alert_id}/resolve")
    assert r.status_code == 200
    assert r.json()["resolved"] is True

    r = client.get("/api/alerts?status=open")
    assert r.json() == []


def test_resolve_missing_alert_404(client):
    r = client.post("/api/alerts/999/resolve")
    assert r.status_code == 404
