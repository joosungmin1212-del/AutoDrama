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


def test_build_user_prompt_includes_avoid_template_instruction_when_given():
    profile = openai_writer.BusinessProfile(business_name="OO PT샵")
    prompt_without = openai_writer.build_user_prompt("제목", "키워드", "", profile)
    assert "템플릿" not in prompt_without

    prompt_with = openai_writer.build_user_prompt("제목", "키워드", "", profile, avoid_template="A")
    assert "템플릿 A" in prompt_with
    assert openai_writer.TEMPLATE_LABELS["A"] in prompt_with


def test_extract_json_and_generate_post_parse_template_used(monkeypatch):
    """generate_post가 모델 응답의 template_used를 대문자로 정규화해서 담아온다."""

    class _FakeMessage:
        content = (
            '{"content": "## 소제목\\n본문", "hashtags": ["#a"], "template_used": "b"}'
        )

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self, api_key):
            pass

        chat = _FakeChat()

    monkeypatch.setattr("openai.OpenAI", _FakeClient)

    result = openai_writer.generate_post(
        api_key="sk-test",
        model="gpt-4o-mini",
        title="제목",
        keyword="키워드",
        extra_request="",
        profile=openai_writer.BusinessProfile(),
    )
    assert result.template_used == "B"


def test_generate_post_ignores_invalid_template_used(monkeypatch):
    """모델이 커스텀 프롬프트 등으로 template_used를 아예 안 주거나 이상한 값을 주면
    빈 문자열로 무시해야 한다 (다음 생성에 잘못된 회피 힌트를 넘기지 않도록)."""

    class _FakeMessage:
        content = '{"content": "본문", "hashtags": []}'  # template_used 없음

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeResponse:
        choices = [_FakeChoice()]

    class _FakeCompletions:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeChat:
        completions = _FakeCompletions()

    class _FakeClient:
        def __init__(self, api_key):
            pass

        chat = _FakeChat()

    monkeypatch.setattr("openai.OpenAI", _FakeClient)

    result = openai_writer.generate_post(
        api_key="sk-test",
        model="gpt-4o-mini",
        title="제목",
        keyword="키워드",
        extra_request="",
        profile=openai_writer.BusinessProfile(),
    )
    assert result.template_used == ""
