"""대시보드에 필요한 집계 로직 (DB row 등가 객체/딕셔너리만 받아 처리 -> 유닛테스트 용이)."""
from __future__ import annotations

from .. import config
from ..models import Ownership


def build_slots(results: list) -> list[dict]:
    """TOP_N 길이의 슬롯 리스트를 만든다. 결과가 없는 자리는 ownership="empty"로 채운다.

    results 항목은 RankResult ORM 객체 또는 동일한 키를 가진 dict 모두 지원한다.
    """
    slots = [
        {
            "position": i,
            "ownership": "empty",
            "owner_name": None,
            "title": "",
            "url": "",
            "content_type": "",
        }
        for i in range(1, config.TOP_N + 1)
    ]

    for r in results:
        is_dict = isinstance(r, dict)
        pos = r["position"] if is_dict else r.position
        if not (1 <= pos <= config.TOP_N):
            continue

        if is_dict:
            owner_name = r.get("owner_name")
            ownership = r.get("ownership", "other")
            title = r.get("title", "")
            url = r.get("url", "")
            content_type = r.get("content_type", "")
        else:
            matched = getattr(r, "matched_blog", None)
            owner_name = getattr(matched, "name", None) if matched else None
            ownership = r.ownership
            title = r.title
            url = r.url
            content_type = r.content_type

        slots[pos - 1] = {
            "position": pos,
            "ownership": ownership,
            "owner_name": owner_name,
            "title": title,
            "url": url,
            "content_type": content_type,
        }

    return slots


def count_ours(slots: list[dict]) -> int:
    return sum(1 for s in slots if s["ownership"].startswith("ours_"))


def aggregate_stats(keyword_summaries: list[dict], open_alert_count: int) -> dict:
    monitored = len(keyword_summaries)
    our_total = sum(k["our_count"] for k in keyword_summaries)
    our_slots_total = monitored * config.TOP_N

    staff_breakdown: dict[str, int] = {}
    experience_breakdown: dict[str, int] = {}
    for k in keyword_summaries:
        for slot in k["slots"]:
            if not slot["owner_name"]:
                continue
            if slot["ownership"] == Ownership.OURS_STAFF.value:
                staff_breakdown[slot["owner_name"]] = staff_breakdown.get(slot["owner_name"], 0) + 1
            elif slot["ownership"] == Ownership.OURS_EXPERIENCE.value:
                experience_breakdown[slot["owner_name"]] = (
                    experience_breakdown.get(slot["owner_name"], 0) + 1
                )

    return {
        "monitored_keywords": monitored,
        "our_total": our_total,
        "our_slots_total": our_slots_total,
        "staff_exposure_count": sum(staff_breakdown.values()),
        "experience_exposure_count": sum(experience_breakdown.values()),
        "staff_breakdown": staff_breakdown,
        "experience_breakdown": experience_breakdown,
        "open_alert_count": open_alert_count,
    }
