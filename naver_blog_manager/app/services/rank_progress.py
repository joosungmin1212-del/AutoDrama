""""전체 순위 갱신"의 진행 상태를 담아두는 아주 단순한 인메모리 저장소.

이 앱은 한 PC에서 한 명이 쓰는 로컬 서버라 별도 큐/DB 없이 프로세스 메모리에 상태를
들고 있는 것으로 충분하다. 프론트엔드는 이 상태를 주기적으로 폴링해서 진행률(몇 개 중
몇 개 처리했는지)을 보여준다.
"""
from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class ErrorEntry(TypedDict):
    keyword: str
    message: str


_state = {
    "running": False,
    "total": 0,
    "done": 0,
    "current_keyword": "",
    "errors": [],  # type: list[ErrorEntry]
    "started_at": None,
    "finished_at": None,
}


def reset(total: int) -> None:
    _state.update(
        running=True,
        total=total,
        done=0,
        current_keyword="",
        errors=[],
        started_at=datetime.utcnow().isoformat(),
        finished_at=None,
    )


def set_current(done: int, total: int, current_keyword: str) -> None:
    """rank_service.run_all_active_checks의 on_progress(done, total, keyword) 콜백 형태에 맞춘다."""
    _state["done"] = done
    _state["total"] = total
    _state["current_keyword"] = current_keyword


def add_error(keyword: str, message: str) -> None:
    _state["errors"].append({"keyword": keyword, "message": message})


def finish() -> None:
    _state["running"] = False
    _state["current_keyword"] = ""
    _state["finished_at"] = datetime.utcnow().isoformat()


def snapshot() -> dict:
    return {**_state, "errors": list(_state["errors"])}


def is_running() -> bool:
    return bool(_state["running"])
