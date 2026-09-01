"""writer 라우터의 /generate, /send-to-naver 엔드포인트 테스트.

특히 send-to-naver는 "미리보기에서 사용자가 고친 내용"이 실제로 네이버 자동화 함수에
전달되는지 검증한다 - 이걸 안 하면 화면에서 아무리 고쳐도 서버에 저장된 원본 초안이
그대로 나가버리는 버그가 생긴다 (실제로 있었음).

"공식 블로그"라는 별도 역할은 없다 - 직원으로 등록해둔 블로그가 그대로 글쓰기 계정
후보가 되고, 예전에 만들어진 "공식 블로그"(company role) 데이터도 하위호환으로
계속 지원한다.
"""
from app.services import naver_browser


def _make_draft(**kwargs):
    """client 픽스처가 이미 초기화해둔 같은 엔진에 직접 Draft를 하나 넣는다.

    generate()는 OpenAI 호출이 필요해 테스트에서 쓰기 번거로우므로, send-to-naver만
    검증할 때는 draft를 직접 만든다.
    """
    from app import models
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        draft = models.Draft(**kwargs)
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft.id
    finally:
        db.close()


def test_send_to_naver_requires_existing_draft(client):
    r = client.post("/api/writer/send-to-naver", json={"draft_id": 999, "content": "본문"})
    assert r.status_code == 404


def test_send_to_naver_uses_edited_content_not_original_draft(client, monkeypatch):
    client.post(
        "/api/blogs",
        json={"name": "직원", "blog_url": "https://blog.naver.com/mystaff", "role": "staff"},
    )
    draft_id = _make_draft(title="원본 제목", content="원본 내용입니다", hashtags="#태그1,#태그2")

    captured = {}

    async def fake_open_write_draft(blog_id, title, content_html):
        captured["blog_id"] = blog_id
        captured["title"] = title
        captured["content_html"] = content_html

    monkeypatch.setattr(naver_browser, "open_write_draft", fake_open_write_draft)

    r = client.post(
        "/api/writer/send-to-naver",
        json={"draft_id": draft_id, "content": "사용자가 미리보기에서 고친 최종 내용"},
    )
    assert r.status_code == 200
    assert r.json()["success"] is True

    assert captured["blog_id"] == "mystaff"
    assert "사용자가 미리보기에서 고친 최종 내용" in captured["content_html"]
    assert "원본 내용입니다" not in captured["content_html"]
    assert "#태그1" in captured["content_html"]  # 해시태그는 그대로 뒤에 붙는다


def test_send_to_naver_works_with_legacy_company_role_blog(client, monkeypatch):
    """예전에 "공식 블로그"로 등록해둔 데이터가 있는 사용자도 계속 정상 동작해야 한다."""
    client.post(
        "/api/blogs",
        json={"name": "예전 공식블로그", "blog_url": "https://blog.naver.com/legacy_company", "role": "company"},
    )
    draft_id = _make_draft(title="제목", content="내용")

    captured = {}

    async def fake_open_write_draft(blog_id, title, content_html):
        captured["blog_id"] = blog_id

    monkeypatch.setattr(naver_browser, "open_write_draft", fake_open_write_draft)

    r = client.post("/api/writer/send-to-naver", json={"draft_id": draft_id, "content": "내용"})
    assert r.status_code == 200
    assert captured["blog_id"] == "legacy_company"


def test_send_to_naver_without_any_account_returns_400(client):
    draft_id = _make_draft(title="제목", content="내용")

    r = client.post("/api/writer/send-to-naver", json={"draft_id": draft_id, "content": "내용"})
    assert r.status_code == 400
    assert "글쓰기 계정" in r.json()["detail"]


def test_send_to_naver_uses_chosen_writer_blog_id_when_multiple_registered(client, monkeypatch):
    """직원 계정을 2개 이상 등록했을 때, writer_blog_id로 지정한 계정으로 정확히
    보내지는지 확인한다 - 지정 안 하면 등록 순서상 첫 번째로 가는 기존 동작과 헷갈리면
    안 된다."""
    client.post(
        "/api/blogs",
        json={"name": "본계정", "blog_url": "https://blog.naver.com/main_account", "role": "staff"},
    )
    r2 = client.post(
        "/api/blogs",
        json={"name": "부계정", "blog_url": "https://blog.naver.com/sub_account", "role": "staff"},
    )
    sub_account_pk = r2.json()["id"]
    draft_id = _make_draft(title="제목", content="내용")

    captured = {}

    async def fake_open_write_draft(blog_id, title, content_html):
        captured["blog_id"] = blog_id

    monkeypatch.setattr(naver_browser, "open_write_draft", fake_open_write_draft)

    r = client.post(
        "/api/writer/send-to-naver",
        json={"draft_id": draft_id, "content": "내용", "writer_blog_id": sub_account_pk},
    )
    assert r.status_code == 200
    assert captured["blog_id"] == "sub_account"


def test_send_to_naver_remembers_last_used_account_as_default_next_time(client, monkeypatch):
    """실제 요구사항: 로그인/전송했던 계정이 다음번 기본 글쓰기 계정이 돼야 한다 -
    매번 다시 고를 필요가 없어야 한다."""
    client.post(
        "/api/blogs",
        json={"name": "본계정", "blog_url": "https://blog.naver.com/main_account", "role": "staff"},
    )
    r2 = client.post(
        "/api/blogs",
        json={"name": "부계정", "blog_url": "https://blog.naver.com/sub_account", "role": "staff"},
    )
    sub_account_pk = r2.json()["id"]

    async def fake_open_write_draft(blog_id, title, content_html):
        pass

    monkeypatch.setattr(naver_browser, "open_write_draft", fake_open_write_draft)

    draft_id = _make_draft(title="제목", content="내용")
    client.post(
        "/api/writer/send-to-naver",
        json={"draft_id": draft_id, "content": "내용", "writer_blog_id": sub_account_pk},
    )

    # 이번엔 계정을 따로 지정하지 않는다 - 방금 썼던 부계정이 그대로 기본값이어야 한다.
    captured = {}

    async def fake_open_write_draft2(blog_id, title, content_html):
        captured["blog_id"] = blog_id

    monkeypatch.setattr(naver_browser, "open_write_draft", fake_open_write_draft2)

    draft_id2 = _make_draft(title="제목2", content="내용2")
    r = client.post("/api/writer/send-to-naver", json={"draft_id": draft_id2, "content": "내용2"})
    assert r.status_code == 200
    assert captured["blog_id"] == "sub_account"


def test_send_to_naver_rejects_empty_content(client):
    client.post(
        "/api/blogs",
        json={"name": "직원", "blog_url": "https://blog.naver.com/mystaff", "role": "staff"},
    )
    draft_id = _make_draft(title="제목", content="")

    r = client.post("/api/writer/send-to-naver", json={"draft_id": draft_id, "content": "   "})
    assert r.status_code == 400
