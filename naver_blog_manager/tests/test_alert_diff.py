from app.services.naver_rank import RankItem, detect_dropouts


def item(position, ownership, blog_id, content_type="blog"):
    return RankItem(
        position=position,
        content_type=content_type,
        url=f"https://blog.naver.com/{blog_id}/{position}",
        blog_id=blog_id,
        title=f"title {position}",
        ownership=ownership,
    )


def test_detect_dropouts_finds_missing_ours_entry():
    previous = [
        item(1, "ours_staff", "wonjang_pt"),
        item(2, "other", "someone"),
        item(3, "ours_experience", "mini_review"),
    ]
    current = [
        item(1, "other", "someone"),
        item(2, "ours_experience", "mini_review"),
    ]
    dropped = detect_dropouts(previous, current)
    assert len(dropped) == 1
    assert dropped[0].blog_id == "wonjang_pt"


def test_detect_dropouts_ignores_other_ownership():
    previous = [item(1, "other", "someone")]
    current = []
    assert detect_dropouts(previous, current) == []


def test_detect_dropouts_no_change_means_no_alert():
    previous = [item(1, "ours_staff", "wonjang_pt")]
    current = [item(3, "ours_staff", "wonjang_pt")]  # 순위는 바뀌었지만 여전히 존재
    assert detect_dropouts(previous, current) == []


def test_detect_dropouts_empty_previous():
    assert detect_dropouts([], [item(1, "ours_staff", "wonjang_pt")]) == []
