from app.models import ContentMatch, ContentMatchDecision, Ownership, RankCheck, RankResult
from app.services import content_match_service
from app.services.naver_rank import RankItem


def _item(title, url, ownership="other", blog_id="reviewer1"):
    return RankItem(
        position=1, content_type="blog", url=url, blog_id=blog_id, title=title, ownership=ownership
    )


def test_apply_content_matches_creates_pending_candidate(db_session):
    items = [_item("OO PT샵 다녀온 후기", "https://blog.naver.com/reviewer1/1")]

    content_match_service.apply_content_matches(db_session, items, watch_names=["OO PT샵"])
    db_session.commit()

    assert items[0].ownership == Ownership.PENDING_EXPERIENCE.value
    saved = db_session.query(ContentMatch).one()
    assert saved.decision == ContentMatchDecision.PENDING.value
    assert saved.matched_text == "OO PT샵"


def test_apply_content_matches_ignores_non_matching_titles(db_session):
    items = [_item("전혀 관련없는 이야기", "https://blog.naver.com/reviewer1/2")]

    content_match_service.apply_content_matches(db_session, items, watch_names=["OO PT샵"])
    db_session.commit()

    assert items[0].ownership == "other"
    assert db_session.query(ContentMatch).count() == 0


def test_apply_content_matches_skips_already_registered_blogs(db_session):
    # 이미 등록된 블로그로 판정된(ownership != other) 항목은 이름 매칭 대상이 아니다
    items = [_item("OO PT샵 소식", "https://blog.naver.com/staffblog/3", ownership=Ownership.OURS_STAFF.value)]

    content_match_service.apply_content_matches(db_session, items, watch_names=["OO PT샵"])
    db_session.commit()

    assert items[0].ownership == Ownership.OURS_STAFF.value
    assert db_session.query(ContentMatch).count() == 0


def test_confirmed_decision_persists_across_reappearance(db_session):
    """이탈 알림 시나리오: 확정해둔 글이 검색결과에서 사라졌다 다시 나타나도 같은 판정이 적용된다."""
    url = "https://blog.naver.com/reviewer1/1"

    # 1차 조회: 후보로 걸림
    round1 = [_item("OO PT샵 후기", url)]
    content_match_service.apply_content_matches(db_session, round1, watch_names=["OO PT샵"])
    db_session.commit()
    match = db_session.query(ContentMatch).one()

    # 사람이 확정
    content_match_service.decide(db_session, match, ContentMatchDecision.CONFIRMED.value)

    # 2차 조회 (한동안 안 보이다가) 다시 같은 글이 나타남 - 다시 물어보지 않고 바로 확정 적용
    round2 = [_item("OO PT샵 후기", url)]
    content_match_service.apply_content_matches(db_session, round2, watch_names=["OO PT샵"])

    assert round2[0].ownership == Ownership.OURS_EXPERIENCE.value
    assert db_session.query(ContentMatch).count() == 1  # 새 후보로 중복 생성되지 않음


def test_decide_updates_existing_rank_results_immediately(db_session):
    from datetime import datetime

    from app.models import Keyword

    keyword = Keyword(keyword="서상동PT")
    db_session.add(keyword)
    db_session.flush()

    check = RankCheck(keyword_id=keyword.id, checked_at=datetime.utcnow())
    db_session.add(check)
    db_session.flush()

    url = "https://blog.naver.com/reviewer1/1"
    result = RankResult(
        rank_check_id=check.id,
        position=3,
        content_type="blog",
        url=url,
        blog_id="reviewer1",
        title="OO PT샵 후기",
        ownership=Ownership.PENDING_EXPERIENCE.value,
    )
    db_session.add(result)

    match = ContentMatch(post_key="blog:reviewer1:1", url=url, title="OO PT샵 후기", matched_text="OO PT샵")
    db_session.add(match)
    db_session.commit()

    content_match_service.decide(db_session, match, ContentMatchDecision.CONFIRMED.value)

    db_session.refresh(result)
    assert result.ownership == Ownership.OURS_EXPERIENCE.value


def test_manual_set_confirms_a_post_that_auto_detection_never_flagged(db_session):
    """체험단이 제목에 업체명/직원 이름을 안 써서 자동 감지 후보로도 안 걸린 글을,
    사람이 대시보드에서 직접 "우리 체험단 맞음"으로 지정하는 경로."""
    url = "https://blog.naver.com/reviewer2/9"

    match = content_match_service.manual_set(
        db_session, url, "그냥 동네 헬스장 다녀온 후기", ContentMatchDecision.CONFIRMED.value
    )
    db_session.commit()

    assert match.decision == ContentMatchDecision.CONFIRMED.value
    assert match.matched_text == "수동 확인"
    assert match.post_key == "blog:reviewer2:9"


def test_manual_set_updates_existing_content_match(db_session):
    """이미 자동 감지로 만들어진 pending 후보를, 수동 확정 경로로도 그대로 결정할 수 있다."""
    url = "https://blog.naver.com/reviewer1/1"
    existing = ContentMatch(post_key="blog:reviewer1:1", url=url, title="옛 제목", matched_text="OO PT샵")
    db_session.add(existing)
    db_session.commit()

    content_match_service.manual_set(db_session, url, "새 제목", ContentMatchDecision.REJECTED.value)
    db_session.commit()

    assert db_session.query(ContentMatch).count() == 1
    refreshed = db_session.query(ContentMatch).filter_by(post_key="blog:reviewer1:1").one()
    assert refreshed.decision == ContentMatchDecision.REJECTED.value
    assert refreshed.title == "새 제목"


class _FakeRegisteredBlog:
    def __init__(self, name):
        self.name = name


def test_apply_content_matches_still_checks_title_even_for_a_known_registered_identity(db_session):
    """실제로 있었던 문제: 체험단/경쟁업체로 등록해둔 같은 블로그 계정이 이 키워드에는
    우리 업체 이야기를, 다른 키워드에는 완전히 다른 업체 이야기를 쓰는 경우가 흔하다.
    그래서 item.matched_blog가 있어도(=신원이 등록된 계정) "이 계정 = 항상 이 판정"으로
    미리 건너뛰면 안 되고, 이 글의 제목은 그대로 검사해서 후보로 올려야 한다 - 신원 표시와
    이 글의 실제 판정은 별개다."""
    item = _item("OO PT샵 근처 헬스장 이야기", "https://blog.naver.com/rival_trainer/1")
    item.matched_blog = _FakeRegisteredBlog("김민수 헬스타이거")

    content_match_service.apply_content_matches(db_session, [item], watch_names=["OO PT샵"])
    db_session.commit()

    assert item.ownership == Ownership.PENDING_EXPERIENCE.value
    assert db_session.query(ContentMatch).count() == 1


def test_apply_content_matches_skips_cafe_posts():
    """등록 안 된 카페 글이 인기글에 섞여 들어와도, 체험단/직원은 개인 블로그에 글을 쓰지
    카페에 쓰지 않으므로 자동으로 체험단 후보 판정에서 제외돼야 한다."""
    item = RankItem(
        position=1,
        content_type="cafe",
        url="https://cafe.naver.com/somecafe/1",
        blog_id="somecafe",
        title="OO PT샵 이야기가 나온 카페 글",
        ownership="other",
    )

    content_match_service.apply_content_matches(None, [item], watch_names=["OO PT샵"])

    assert item.ownership == "other"


def test_manual_set_raises_when_post_key_cannot_be_extracted():
    import pytest

    with pytest.raises(ValueError):
        content_match_service.manual_set(None, "", "제목", "confirmed")
