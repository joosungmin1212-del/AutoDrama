"""이탈 알림(Alert) 생성 -> 자동 해소 흐름 전체 테스트.

예전에는 한 번 뜬 이탈 알림을 다시 resolved=True로 되돌리는 코드가 어디에도 없어서,
문제가 실제로 해결(글이 TOP7에 다시 나타남)된 뒤에도 알림이 영원히 "열린" 상태로
남아 대시보드의 알림 카운트가 계속 쌓이기만 하는 버그가 있었다.
"""
import pytest

from app import models
from app.services import naver_rank, rank_service
from app.services.naver_rank import RankItem


def _item(position, ownership, blog_id):
    return RankItem(
        position=position,
        content_type="blog",
        url=f"https://blog.naver.com/{blog_id}/{position}",
        blog_id=blog_id,
        title=f"글 {position}",
        ownership=ownership,
    )


@pytest.mark.asyncio
async def test_alert_created_on_dropout_and_auto_resolved_on_recovery(db_session, monkeypatch):
    keyword = models.Keyword(keyword="서상동PT")
    db_session.add(keyword)
    db_session.flush()

    call_results = [
        [_item(1, "ours_staff", "staffblog")],  # 1차: 있음
        [_item(1, "other", "someone")],  # 2차: 이탈 (staffblog가 안 보임)
        [_item(2, "ours_staff", "staffblog")],  # 3차: 다시 나타남 (순위는 바뀜)
    ]

    async def fake_check(keyword_str, registered_blogs, top_n=7, page=None):
        return call_results.pop(0)

    monkeypatch.setattr(naver_rank, "check_keyword_rank", fake_check)

    await rank_service.run_rank_check_async(db_session, keyword)
    assert db_session.query(models.Alert).count() == 0  # 1차는 이탈이 없으니 알림도 없음

    await rank_service.run_rank_check_async(db_session, keyword)
    alerts = db_session.query(models.Alert).all()
    assert len(alerts) == 1
    assert alerts[0].resolved is False
    assert alerts[0].blog_id == "staffblog"
    assert alerts[0].previous_position == 1

    await rank_service.run_rank_check_async(db_session, keyword)
    db_session.refresh(alerts[0])
    assert alerts[0].resolved is True  # 다시 나타났으니 자동으로 해소되어야 한다
    assert alerts[0].resolved_at is not None


@pytest.mark.asyncio
async def test_alert_stays_open_while_blog_is_still_missing(db_session, monkeypatch):
    keyword = models.Keyword(keyword="서상동PT")
    db_session.add(keyword)
    db_session.flush()

    call_results = [
        [_item(1, "ours_staff", "staffblog")],
        [_item(1, "other", "someone")],  # 이탈
        [_item(1, "other", "someone2")],  # 여전히 없음 (다른 타업체가 그 자리에)
    ]

    async def fake_check(keyword_str, registered_blogs, top_n=7, page=None):
        return call_results.pop(0)

    monkeypatch.setattr(naver_rank, "check_keyword_rank", fake_check)

    await rank_service.run_rank_check_async(db_session, keyword)
    await rank_service.run_rank_check_async(db_session, keyword)
    await rank_service.run_rank_check_async(db_session, keyword)

    alert = db_session.query(models.Alert).one()
    assert alert.resolved is False  # 아직 안 돌아왔으니 계속 열려있어야 한다
