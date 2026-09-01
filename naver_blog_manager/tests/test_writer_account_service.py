"""writer_account.py 테스트 - "공식 블로그" 역할 없이 실제 로그인한 계정이 글쓰기
계정이 되는 로직의 핵심.

실제로 있었던 버그: 같은 블로그를 "직원"과 "공식 블로그" 둘 다로 중복 등록하면,
matcher.match_ownership이 둘 중 먼저 찾은 행 하나만 매칭해서 대시보드 직원
체크리스트가 틀리게 표시됐다. list_writer_accounts()는 같은 blog_id가 여러 role로
중복 등록돼 있어도 한 번만 후보로 보여줘서, 그런 혼란을 애초에 만들지 않는다.
"""
from app import models
from app.services import writer_account


def _blog(db, name, blog_id, role):
    b = models.RegisteredBlog(name=name, blog_url=f"https://blog.naver.com/{blog_id}", blog_id=blog_id, role=role)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def test_list_writer_accounts_includes_staff_and_legacy_company(db_session):
    _blog(db_session, "직원A", "staff_a", "staff")
    _blog(db_session, "예전공식", "legacy_co", "company")
    _blog(db_session, "체험단", "reviewer", "experience")
    _blog(db_session, "경쟁업체", "rival", "competitor")

    accounts = writer_account.list_writer_accounts(db_session)
    assert {a.blog_id for a in accounts} == {"staff_a", "legacy_co"}


def test_list_writer_accounts_dedupes_same_blog_id_across_roles(db_session):
    """실제로 있었던 문제 재현: 같은 블로그를 직원으로도, 공식 블로그로도 중복 등록해도
    계정 후보 목록에는 한 번만 나와야 한다 - 안 그러면 글쓰기 화면 드롭다운에 같은
    계정이 두 줄로 뜨는 등 혼란이 생긴다."""
    staff_row = _blog(db_session, "성민본계정", "sm_main", "staff")
    _blog(db_session, "성민본계정(공식)", "sm_main", "company")

    accounts = writer_account.list_writer_accounts(db_session)
    assert len(accounts) == 1
    assert accounts[0].id == staff_row.id  # 먼저 등록된(직원) 쪽이 대표로 남는다


def test_resolve_writer_blog_returns_none_when_no_accounts(db_session):
    setting = models.Setting(id=1)
    assert writer_account.resolve_writer_blog(db_session, setting) is None


def test_resolve_writer_blog_prefers_explicit_request_over_active_setting(db_session):
    _blog(db_session, "본계정", "main_account", "staff")
    sub = _blog(db_session, "부계정", "sub_account", "staff")
    setting = models.Setting(id=1, active_writer_blog_id="main_account")

    resolved = writer_account.resolve_writer_blog(db_session, setting, requested_blog_pk=sub.id)
    assert resolved.blog_id == "sub_account"


def test_resolve_writer_blog_falls_back_to_active_writer_setting(db_session):
    _blog(db_session, "본계정", "main_account", "staff")
    _blog(db_session, "부계정", "sub_account", "staff")
    setting = models.Setting(id=1, active_writer_blog_id="sub_account")

    resolved = writer_account.resolve_writer_blog(db_session, setting)
    assert resolved.blog_id == "sub_account"


def test_resolve_writer_blog_falls_back_to_first_registered_when_nothing_else_set(db_session):
    """실제로 있었던 첫 사용 시나리오: 아직 한 번도 로그인/전송을 안 해서
    active_writer_blog_id가 비어있으면, 가장 먼저 등록된 계정을 그냥 쓴다."""
    first = _blog(db_session, "본계정", "main_account", "staff")
    _blog(db_session, "부계정", "sub_account", "staff")
    setting = models.Setting(id=1, active_writer_blog_id="")

    resolved = writer_account.resolve_writer_blog(db_session, setting)
    assert resolved.blog_id == first.blog_id
