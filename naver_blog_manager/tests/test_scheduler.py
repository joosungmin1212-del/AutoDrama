"""스케줄러 주기 설정 테스트.

예전에는 설정 화면에서 저장한 "순위 자동 체크 주기"가 실제로는 전혀 쓰이지 않고,
서버가 항상 기본값(24시간)으로만 스케줄러를 띄우는 버그가 있었다. 여기서는
1) 서버 기동 시 DB에 저장된 값을 실제로 읽어오는지, 2) 스케줄러가 떠 있는 동안
설정을 바꾸면 재시작 없이 반영되는지를 검증한다.
"""
from app.services import scheduler


def test_reschedule_is_noop_when_scheduler_not_started(monkeypatch):
    monkeypatch.setattr(scheduler, "_scheduler", None)
    scheduler.reschedule(6)  # 예외 없이 조용히 무시되어야 한다


def test_reschedule_updates_running_job():
    try:
        scheduler.start_scheduler(interval_hours=24)
        job = scheduler._scheduler.get_job("rank_check_all")
        assert job.trigger.interval.total_seconds() == 24 * 3600

        scheduler.reschedule(6)
        job = scheduler._scheduler.get_job("rank_check_all")
        assert job.trigger.interval.total_seconds() == 6 * 3600
    finally:
        scheduler.shutdown_scheduler()


def test_load_configured_interval_hours_reads_db_setting(client):
    """main.py의 _load_configured_interval_hours가 DB에 저장된 값을 실제로 읽어오는지 확인.

    client 픽스처가 앱을 한 번 띄우면서 이미 기본 Setting(24시간)을 만들어두므로,
    값을 바꾼 뒤 같은 함수를 다시 호출해 새 값이 반영되는지 본다.
    """
    from app.main import _load_configured_interval_hours

    assert _load_configured_interval_hours() == 24

    client.put("/api/settings/ai", json={"rank_check_interval_hours": 9})
    assert _load_configured_interval_hours() == 9
