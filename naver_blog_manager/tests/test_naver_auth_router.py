"""글쓰기 계정(직원으로 등록한 블로그)별 로그인 상태를 보여주는
/api/naver-auth/accounts 엔드포인트 테스트.

"공식 블로그"라는 별도 역할 없이, 이미 "직원"으로 등록해둔 블로그 자체가 계정
후보가 된다 - 계정을 여러 개 등록해 전환해 쓰는 기능의 핵심이다.
"""
from app.services import naver_browser


def test_list_accounts_empty_when_no_accounts_registered(client):
    r = client.get("/api/naver-auth/accounts")
    assert r.status_code == 200
    assert r.json() == []


def test_list_accounts_reports_per_blog_login_status(client, monkeypatch):
    client.post(
        "/api/blogs",
        json={"name": "본계정", "blog_url": "https://blog.naver.com/main_account", "role": "staff"},
    )
    client.post(
        "/api/blogs",
        json={"name": "부계정", "blog_url": "https://blog.naver.com/sub_account", "role": "staff"},
    )
    # 체험단/경쟁업체는 우리가 로그인해서 쓰는 계정이 아니므로 목록에 안 나와야 한다
    client.post(
        "/api/blogs",
        json={"name": "체험단", "blog_url": "https://blog.naver.com/reviewer", "role": "experience"},
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


def test_list_accounts_still_includes_legacy_company_role_for_backward_compat(client):
    """예전에 "공식 블로그"로 등록해둔 데이터가 있는 사용자도 계속 계정 목록에 나와야 한다
    (신규 등록만 막았지, 기존 데이터를 무시하면 안 된다)."""
    client.post(
        "/api/blogs",
        json={"name": "예전 공식블로그", "blog_url": "https://blog.naver.com/legacy_company", "role": "company"},
    )

    r = client.get("/api/naver-auth/accounts")
    assert r.status_code == 200
    assert [a["blog_id"] for a in r.json()] == ["legacy_company"]


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


def test_login_with_blog_id_sets_it_as_active_writer_account(client, monkeypatch):
    """실제 요구사항: 로그인했던 계정이 그대로 글쓰기 계정이 돼야 한다 - 별도로
    "공식 블로그"를 지정할 필요 없이, 로그인 성공 즉시 active_writer_blog_id가
    그 계정으로 갱신된다."""

    async def fake_login_interactive(timeout_ms=180_000, blog_id=None):
        return True

    monkeypatch.setattr(naver_browser, "login_interactive", fake_login_interactive)

    r = client.post("/api/naver-auth/login?blog_id=sm_main")
    assert r.status_code == 200

    settings = client.get("/api/settings").json()
    assert settings["active_writer_blog_id"] == "sm_main"


def test_login_without_blog_id_uses_default_session(client, monkeypatch):
    """기존 단일 계정 사용자의 흐름(로그인 화면의 "네이버 로그인하기") - blog_id 없이
    호출하면 기본 세션으로 저장되고, active_writer_blog_id는 안 건드린다(아직 어느
    블로그인지 모르니까 - 로그인 화면에서 이어서 등록할 때 따로 지정된다)."""
    captured = {}

    async def fake_login_interactive(timeout_ms=180_000, blog_id=None):
        captured["login_blog_id"] = blog_id
        return True

    monkeypatch.setattr(naver_browser, "login_interactive", fake_login_interactive)

    r = client.post("/api/naver-auth/login")
    assert r.status_code == 200
    assert captured["login_blog_id"] is None

    settings = client.get("/api/settings").json()
    assert settings["active_writer_blog_id"] == ""
