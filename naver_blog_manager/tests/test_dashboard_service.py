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


def test_aggregate_stats_account_breakdown_groups_by_blog_id_not_name():
    """rank-dot 색상과 정확히 일치하는 계정 식별을 위해 owner_blog_id로 묶여야 한다 -
    이름이 같아도 blog_id가 다르면 별개 계정으로, 많이 나온 순으로 정렬된다."""
    summaries = [
        {
            "our_count": 3,
            "slots": [
                {"ownership": "ours_staff", "owner_blog_id": 1, "owner_name": "성민본계정"},
                {"ownership": "ours_staff", "owner_blog_id": 1, "owner_name": "성민본계정"},
                {"ownership": "ours_staff", "owner_blog_id": 2, "owner_name": "성민부계정"},
                {"ownership": "other", "owner_blog_id": None, "owner_name": None},
                # 자동 확정된 체험단처럼 owner_blog_id가 없는 경우는 계정별 집계에서 제외
                {"ownership": "ours_experience", "owner_blog_id": None, "owner_name": None},
            ],
        }
    ]
    stats = dashboard_service.aggregate_stats(summaries, open_alert_count=0)
    assert stats["account_breakdown"] == [
        {"blog_id": 1, "name": "성민본계정", "count": 2},
        {"blog_id": 2, "name": "성민부계정", "count": 1},
    ]


def test_build_trend_series_keeps_only_the_latest_check_per_day_per_keyword():
    """같은 날 같은 키워드를 여러 번 갱신해도, 그 날의 마지막 스냅샷만 대표로 써야
    그래프가 "하루에 여러 번 눌렀다"는 이유로 들쭉날쭉해지지 않는다."""
    from datetime import datetime

    checks = [
        {
            "checked_at": datetime(2026, 8, 20, 9, 0),
            "keyword_id": 1,
            "results": [{"position": 1, "ownership": "ours_staff"}],
        },
        {
            # 같은 날, 나중 시각 - 이게 대표값이 돼야 함 (앞의 1개가 아니라 이 3개)
            "checked_at": datetime(2026, 8, 20, 18, 0),
            "keyword_id": 1,
            "results": [
                {"position": 1, "ownership": "ours_staff"},
                {"position": 2, "ownership": "ours_experience"},
                {"position": 3, "ownership": "ours_company"},
            ],
        },
        {
            "checked_at": datetime(2026, 8, 21, 9, 0),
            "keyword_id": 1,
            "results": [{"position": 1, "ownership": "ours_staff"}],
        },
    ]
    series = dashboard_service.build_trend_series(checks, days=14)
    assert series == [
        {"date": "2026-08-20", "our_total": 3},
        {"date": "2026-08-21", "our_total": 1},
    ]


def test_build_trend_series_sums_across_multiple_keywords_on_same_day():
    from datetime import datetime

    checks = [
        {
            "checked_at": datetime(2026, 8, 20, 9, 0),
            "keyword_id": 1,
            "results": [{"position": 1, "ownership": "ours_staff"}],
        },
        {
            "checked_at": datetime(2026, 8, 20, 9, 5),
            "keyword_id": 2,
            "results": [
                {"position": 1, "ownership": "ours_staff"},
                {"position": 2, "ownership": "ours_staff"},
            ],
        },
    ]
    series = dashboard_service.build_trend_series(checks, days=14)
    assert series == [{"date": "2026-08-20", "our_total": 3}]


def test_build_trend_series_excludes_checks_older_than_window(monkeypatch):
    from datetime import datetime

    fixed_now = datetime(2026, 8, 31, 12, 0)

    class _FixedDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now

    monkeypatch.setattr(dashboard_service, "datetime", _FixedDateTime)

    checks = [
        {"checked_at": datetime(2026, 8, 1, 9, 0), "keyword_id": 1, "results": []},  # 너무 오래됨
        {
            "checked_at": datetime(2026, 8, 30, 9, 0),
            "keyword_id": 1,
            "results": [{"position": 1, "ownership": "ours_staff"}],
        },
    ]
    series = dashboard_service.build_trend_series(checks, days=14)
    assert series == [{"date": "2026-08-30", "our_total": 1}]


def test_build_trend_series_empty_input_returns_empty_list():
    assert dashboard_service.build_trend_series([], days=14) == []


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
