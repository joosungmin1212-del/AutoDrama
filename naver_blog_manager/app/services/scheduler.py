"""APScheduler로 주기적 순위 체크를 등록한다."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .. import config
from ..db import session_scope
from . import rank_service

logger = logging.getLogger("naver_blog_manager.scheduler")

_scheduler: BackgroundScheduler | None = None


def _job_check_all_keywords() -> None:
    try:
        with session_scope() as db:
            checks = rank_service.run_all_active_checks_sync(db)
            logger.info("정기 순위 체크 완료: %d개 키워드", len(checks))
    except Exception:  # noqa: BLE001
        logger.exception("정기 순위 체크 중 오류 발생")


def start_scheduler(interval_hours: int = config.DEFAULT_RANK_CHECK_INTERVAL_HOURS) -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    # IntervalTrigger는 기본적으로 "지금부터 interval 뒤"에 첫 실행되므로 서버 기동 직후
    # 곧바로 순위 체크가 돌지 않는다 (즉시 확인이 필요하면 대시보드의 수동 갱신 버튼 사용).
    scheduler.add_job(
        _job_check_all_keywords,
        "interval",
        hours=interval_hours,
        id="rank_check_all",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("스케줄러 시작 (매 %d시간마다 전체 키워드 순위 체크)", interval_hours)
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
