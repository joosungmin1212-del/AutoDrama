from app.services.naver_browser import parse_markdown_line


def test_parse_markdown_line_plain_text_no_bold():
    assert parse_markdown_line("그냥 평범한 문장입니다.") == [("그냥 평범한 문장입니다.", False)]


def test_parse_markdown_line_inline_bold_segments():
    segments = parse_markdown_line("이것은 **10년 차 운동 지도 경력**을 가진 트레이너입니다.")
    assert segments == [
        ("이것은 ", False),
        ("10년 차 운동 지도 경력", True),
        ("을 가진 트레이너입니다.", False),
    ]


def test_parse_markdown_line_multiple_bold_spans_in_one_line():
    segments = parse_markdown_line("**체형 개선**과 **자세 통제**가 핵심입니다.")
    assert segments == [
        ("체형 개선", True),
        ("과 ", False),
        ("자세 통제", True),
        ("가 핵심입니다.", False),
    ]


def test_parse_markdown_line_heading_strips_prefix_and_marks_whole_line_bold():
    """네이버 스마트에디터는 "## " 마크다운을 인식하지 못해 그대로 붙여넣으면 글자로
    노출된다 - 그래서 접두사는 없애고 대신 전체를 굵게 표시하는 힌트로 바꿔야 한다."""
    segments = parse_markdown_line("## 🔥 이렇게 달라졌어요")
    assert segments == [("🔥 이렇게 달라졌어요", True)]


def test_parse_markdown_line_heading_with_inner_bold_markers_gets_stripped():
    """소제목 줄 안에 실수로 "**"가 섞여 있어도(이미 줄 전체가 굵게 처리되니) 그냥
    제거만 하고 중복으로 토글하지 않는다."""
    segments = parse_markdown_line("## **소제목**입니다")
    assert segments == [("소제목입니다", True)]


def test_parse_markdown_line_empty_line_returns_empty_list():
    """빈 줄(문단 사이 여백)은 아무것도 타이핑하지 않고 그대로 빈 줄로 남아야 한다 -
    호출부가 이 결과를 가지고 Enter만 눌러서 줄바꿈 간격을 유지한다."""
    assert parse_markdown_line("") == []


def test_parse_markdown_line_empty_heading_returns_empty_list():
    assert parse_markdown_line("## ") == []
