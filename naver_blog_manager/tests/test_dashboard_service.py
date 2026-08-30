from app.services import dashboard_service


def test_build_slots_fills_empty_for_missing_positions():
    results = [
        {"position": 1, "ownership": "ours_staff", "owner_name": "원장", "title": "t1", "url": "u1", "content_type": "blog"},
        {"position": 3, "ownership": "other", "owner_name": None, "title": "t3", "url": "u3", "content_type": "blog"},
    ]
    slots = dashboard_service.build_slots(results)
    assert len(slots) == 7
    assert slots[0]["ownership"] == "ours_staff"
    assert slots[1]["ownership"] == "empty"
    assert slots[2]["ownership"] == "other"
    assert slots[6]["ownership"] == "empty"


def test_count_ours_counts_only_ours_prefixed():
    slots = [
        {"ownership": "ours_staff"},
        {"ownership": "ours_experience"},
        {"ownership": "ours_company"},
        {"ownership": "other"},
        {"ownership": "empty"},
        {"ownership": "pending_experience"},  # 아직 확인 안 됐으니 우리 것으로 안 셈
    ]
    assert dashboard_service.count_ours(slots) == 3


def test_count_by_ownership():
    slots = [
        {"ownership": "pending_experience"},
        {"ownership": "pending_experience"},
        {"ownership": "ours_experience"},
    ]
    assert dashboard_service.count_by_ownership(slots, "pending_experience") == 2
    assert dashboard_service.count_by_ownership(slots, "ours_experience") == 1


def test_build_staff_presence_marks_present_by_blog_id():
    slots = [
        {"ownership": "ours_staff", "owner_blog_id": 1, "owner_name": "원장"},
        {"ownership": "empty", "owner_blog_id": None, "owner_name": None},
    ]
    staff_blogs = [{"id": 1, "name": "원장"}, {"id": 2, "name": "이수석"}]
    presence = dashboard_service.build_staff_presence(slots, staff_blogs)
    assert presence == [
        {"id": 1, "name": "원장", "present": True},
        {"id": 2, "name": "이수석", "present": False},
    ]


def test_aggregate_stats_breaks_down_by_owner_name():
    summaries = [
        {
            "our_count": 2,
            "slots": [
                {"ownership": "ours_staff", "owner_name": "원장"},
                {"ownership": "ours_experience", "owner_name": "미니"},
                {"ownership": "other", "owner_name": None},
            ],
        },
        {
            "our_count": 1,
            "slots": [
                {"ownership": "ours_staff", "owner_name": "원장"},
            ],
        },
    ]
    stats = dashboard_service.aggregate_stats(summaries, open_alert_count=1, pending_content_match_count=3)
    assert stats["monitored_keywords"] == 2
    assert stats["our_total"] == 3
    assert stats["our_slots_total"] == 14
    assert stats["staff_breakdown"] == {"원장": 2}
    assert stats["experience_breakdown"] == {"미니": 1}
    assert stats["staff_exposure_count"] == 2
    assert stats["experience_exposure_count"] == 1
    assert stats["open_alert_count"] == 1
    assert stats["pending_content_match_count"] == 3


def test_aggregate_stats_counts_nameless_experience_in_total_only():
    # 제목 매칭으로 자동 확정된 체험단 글은 등록된 블로그가 아니라 owner_name이 없을 수 있다.
    # 그래도 전체 개수(experience_exposure_count)에는 포함돼야 한다.
    summaries = [
        {
            "our_count": 1,
            "slots": [{"ownership": "ours_experience", "owner_name": None}],
        }
    ]
    stats = dashboard_service.aggregate_stats(summaries, open_alert_count=0)
    assert stats["experience_exposure_count"] == 1
    assert stats["experience_breakdown"] == {}
    assert stats["pending_content_match_count"] == 0
