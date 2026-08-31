"""공식 블로그(계정)별 로그인 상태를 보여주는 /api/naver-auth/accounts 엔드포인트 테스트.

계정을 여러 개 등록해 전환해 쓰는 기능의 핵심 - 계정마다 로그인 상태가 정확히
따로 표시돼야 계정 전환 UI(블로그 관리 화면)가 의미가 있다.
"""
from app.services import naver_browser


def test_list_accounts_empty_when_no_company_blogs(client):
    r = client.get("/api/naver-auth/accounts")
    assert r.status_code == 200
    assert r.json() == []


def test_list_accounts_reports_per_blog_login_status(client, monkeypatch):
    client.post(
        "/api/blogs",
        json={"name": "본계정", "blog_url": "https://blog.naver.com/main_account", "role": "company"},
    )
    client.post(
        "/api/blogs",
        json={"name": "부계정", "blog_url": "https://blog.naver.com/sub_account", "role": "company"},
    )
    # 직원 블로그는 공식 블로그가 아니므로 계정 목록에 안 나와야 한다
    client.post(
        "/api/blogs",
        json={"name": "직원", "blog_url": "https://blog.naver.com/staff_blog", "role": "staff"},
    )

    async def fake_check_login_status(blog_id=None):
        return blog_id == "main_account"

    def fake_has_saved_session(blog_id=None):
        return blog_id == "main_account"

    monkeypatch.setattr(naver_browser, "check_login_status", fake_check_login_status)
    monkeypatch.setattr(naver_browser, "has_saved_session", fake_has_saved_session)

    r = client.get("/api/naver-auth/accounts")
    assert r.status_code == 200
    accounts = {a["blog_id"]: a for a in r.json()}

    assert set(accounts.keys()) == {"main_account", "sub_account"}
    assert accounts["main_account"]["logged_in"] is True
    assert accounts["main_account"]["has_dedicated_session"] is True
    assert accounts["sub_account"]["logged_in"] is False
    assert accounts["sub_account"]["has_dedicated_session"] is False


def test_login_and_logout_pass_blog_id_through(client, monkeypatch):
    captured = {}

    async def fake_login_interactive(timeout_ms=180_000, blog_id=None):
        captured["login_blog_id"] = blog_id
        return True

    def fake_clear_saved_session(blog_id=None):
        captured["logout_blog_id"] = blog_id

    monkeypatch.setattr(naver_browser, "login_interactive", fake_login_interactive)
    monkeypatch.setattr(naver_browser, "clear_saved_session", fake_clear_saved_session)

    r = client.post("/api/naver-auth/login?blog_id=sub_account")
    assert r.status_code == 200
    assert captured["login_blog_id"] == "sub_account"

    r = client.post("/api/naver-auth/logout?blog_id=sub_account")
    assert r.status_code == 200
    assert captured["logout_blog_id"] == "sub_account"


def test_login_without_blog_id_uses_default_session(client, monkeypatch):
    """기존 단일 계정 사용자의 흐름(로그인 화면의 "네이버 로그인하기") - blog_id 없이
    호출하면 기본 세션으로 저장된다."""
    captured = {}

    async def fake_login_interactive(timeout_ms=180_000, blog_id=None):
        captured["login_blog_id"] = blog_id
        return True

    monkeypatch.setattr(naver_browser, "login_interactive", fake_login_interactive)

    r = client.post("/api/naver-auth/login")
    assert r.status_code == 200
    assert captured["login_blog_id"] is None
