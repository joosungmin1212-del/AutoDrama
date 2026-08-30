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
    ]
    assert dashboard_service.count_ours(slots) == 3


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
    stats = dashboard_service.aggregate_stats(summaries, open_alert_count=1)
    assert stats["monitored_keywords"] == 2
    assert stats["our_total"] == 3
    assert stats["our_slots_total"] == 14
    assert stats["staff_breakdown"] == {"원장": 2}
    assert stats["experience_breakdown"] == {"미니": 1}
    assert stats["staff_exposure_count"] == 2
    assert stats["experience_exposure_count"] == 1
    assert stats["open_alert_count"] == 1
