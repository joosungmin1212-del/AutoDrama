import pytest

from app.services import openai_writer


def test_extract_json_plain():
    data = openai_writer.extract_json('{"content": "hello", "hashtags": ["#a"]}')
    assert data["content"] == "hello"
    assert data["hashtags"] == ["#a"]


def test_extract_json_with_code_fence():
    text = '```json\n{"content": "hi"}\n```'
    assert openai_writer.extract_json(text) == {"content": "hi"}


def test_extract_json_ignores_trailing_text():
    text = '설명입니다.\n{"content": "본문", "hashtags": []}\n추가 설명'
    data = openai_writer.extract_json(text)
    assert data["content"] == "본문"


def test_extract_json_nested_braces():
    text = '{"content": "a { b } c", "hashtags": []}'
    data = openai_writer.extract_json(text)
    assert data["content"] == "a { b } c"


def test_extract_json_raises_when_missing():
    with pytest.raises(openai_writer.WriterError):
        openai_writer.extract_json("이건 JSON이 아닙니다.")


def test_compute_seo_check_within_range():
    content = "## 소제목1\n" + ("서상동PT " * 10) + "\n\n## 소제목2\n본문\n\n## 소제목3\n본문" + "가" * 1700
    check = openai_writer.compute_seo_check(content, "서상동PT")
    assert check["keyword_count"] == 10
    assert check["subheading_count"] == 3
    assert check["keyword_count_ok"] is True


def test_compute_seo_check_too_short_flagged():
    content = "짧은 글입니다."
    check = openai_writer.compute_seo_check(content, "서상동PT")
    assert check["length_ok"] is False
    assert check["keyword_count"] == 0
    assert check["keyword_count_ok"] is False
