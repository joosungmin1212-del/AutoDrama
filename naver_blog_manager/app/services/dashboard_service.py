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
            "owner_blog_id": None,
            "owner_role": None,
            "blog_id": "",
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
            owner_blog_id = r.get("owner_blog_id")
            owner_role = r.get("owner_role")
            ownership = r.get("ownership", "other")
            blog_id = r.get("blog_id", "")
            title = r.get("title", "")
            url = r.get("url", "")
            content_type = r.get("content_type", "")
        else:
            matched = getattr(r, "matched_blog", None)
            owner_name = getattr(matched, "name", None) if matched else None
            owner_blog_id = getattr(matched, "id", None) if matched else None
            # matched_blog가 있다고 해서 ownership이 항상 "우리 것"인 건 아니다 - 체험단/
            # 경쟁업체로 등록해둔 계정은 신원 표시용으로만 붙어있고(owner_role 참고),
            # 실제 소유 판정은 글(URL) 단위로 따로 결정된다.
            owner_role = getattr(matched, "role", None) if matched else None
            ownership = r.ownership
            blog_id = r.blog_id
            title = r.title
            url = r.url
            content_type = r.content_type

        slots[pos - 1] = {
            "position": pos,
            "ownership": ownership,
            "owner_name": owner_name,
            "owner_blog_id": owner_blog_id,
            "owner_role": owner_role,
            "blog_id": blog_id,
            "title": title,
            "url": url,
            "content_type": content_type,
        }

    return slots


def count_ours(slots: list[dict]) -> int:
    return sum(1 for s in slots if s["ownership"].startswith("ours_"))


def count_by_ownership(slots: list[dict], ownership: str) -> int:
    return sum(1 for s in slots if s["ownership"] == ownership)


def build_staff_presence(slots: list[dict], staff_blogs: list) -> list[dict]:
    """등록된 직원(또는 공식블로그) 각각이 이 키워드의 TOP7 안에 있는지 여부.

    예: 서상동PT (4/7) -> 원장(v) 이수석(v) 박재활(x) 처럼 대시보드에 바로 쓰인다.
    """
    present_ids = {s["owner_blog_id"] for s in slots if s.get("owner_blog_id")}
    presence = []
    for b in staff_blogs:
        blog_id, name = (b["id"], b["name"]) if isinstance(b, dict) else (b.id, b.name)
        presence.append({"id": blog_id, "name": name, "present": blog_id in present_ids})
    return presence


def aggregate_stats(
    keyword_summaries: list[dict], open_alert_count: int, pending_content_match_count: int = 0
) -> dict:
    monitored = len(keyword_summaries)
    our_total = sum(k["our_count"] for k in keyword_summaries)
    our_slots_total = monitored * config.TOP_N

    staff_breakdown: dict[str, int] = {}
    experience_breakdown: dict[str, int] = {}
    staff_exposure_count = 0
    experience_exposure_count = 0
    for k in keyword_summaries:
        for slot in k["slots"]:
            if slot["ownership"] == Ownership.OURS_STAFF.value:
                staff_exposure_count += 1
                if slot["owner_name"]:
                    staff_breakdown[slot["owner_name"]] = (
                        staff_breakdown.get(slot["owner_name"], 0) + 1
                    )
            elif slot["ownership"] == Ownership.OURS_EXPERIENCE.value:
                experience_exposure_count += 1
                # 자동 감지(제목 매칭)로 확정된 체험단 글은 등록된 블로그가 아니라서
                # owner_name이 없을 수 있다 - 그래도 전체 개수(experience_exposure_count)에는
                # 포함하고, 이름별 분해(experience_breakdown)에만 못 넣는 것.
                if slot["owner_name"]:
                    experience_breakdown[slot["owner_name"]] = (
                        experience_breakdown.get(slot["owner_name"], 0) + 1
                    )

    return {
        "monitored_keywords": monitored,
        "our_total": our_total,
        "our_slots_total": our_slots_total,
        "staff_exposure_count": staff_exposure_count,
        "experience_exposure_count": experience_exposure_count,
        "staff_breakdown": staff_breakdown,
        "experience_breakdown": experience_breakdown,
        "open_alert_count": open_alert_count,
        "pending_content_match_count": pending_content_match_count,
    }
