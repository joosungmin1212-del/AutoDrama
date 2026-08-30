"""OpenAI를 이용해 네이버 SEO에 맞춘 블로그 글 초안을 생성하는 서비스.

- 순수 텍스트 조립/파싱/체크 로직은 OpenAI 클라이언트 없이도 테스트 가능하게 분리했다
  (build_prompt, extract_json, compute_seo_check).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .. import config

SYSTEM_PROMPT = """당신은 대한민국 지역 피트니스(PT) 센터를 위한 네이버 블로그 SEO 전문 작가입니다.
네이버 블로그 노출 알고리즘(C-Rank, D.I.A.)을 고려해 글을 씁니다.

작성 규칙:
1. 제목에 들어간 핵심 키워드를 본문에 자연스럽게 5~10회 반복하되, 어색한 키워드 도배는 하지 않는다.
2. 소제목을 3~5개 사용한다. 각 소제목은 반드시 줄 맨 앞에 "## "를 붙인다.
3. 전체 글자 수는 1700~2500자(공백 포함) 사이로 작성한다.
4. 글 구조: 공감되는 도입부 -> 전문적인 정보/경험 설명(전후 변화, 실제 사례 언급) -> 상담/방문 유도 마무리.
5. 업체의 지역명, 강점을 자연스럽게 녹인다.
6. 과도한 의료적 효능 단정 표현은 피하고, 개인차가 있을 수 있다는 뉘앙스를 유지한다.
7. 결과는 반드시 아래 JSON 형식으로만 응답한다 (다른 설명 텍스트 금지):

{
  "content": "## 소제목1\\n본문...\\n\\n## 소제목2\\n본문...",
  "hashtags": ["#태그1", "#태그2", "..."]
}
"""


@dataclass
class BusinessProfile:
    business_name: str = ""
    address: str = ""
    phone: str = ""
    strengths: str = ""


@dataclass
class GeneratedPost:
    content: str
    hashtags: list[str]


class WriterError(RuntimeError):
    pass


def build_user_prompt(
    title: str, keyword: str | None, extra_request: str, profile: BusinessProfile
) -> str:
    keyword = keyword or title
    lines = [
        f"제목: {title}",
        f"핵심 키워드: {keyword}",
        f"업체명: {profile.business_name or '(미입력)'}",
        f"주소/지역: {profile.address or '(미입력)'}",
        f"전화번호: {profile.phone or '(미입력)'}",
        f"업체 강점/차별점: {profile.strengths or '(미입력)'}",
    ]
    if extra_request.strip():
        lines.append(f"추가 요청사항: {extra_request.strip()}")
    return "\n".join(lines)


def extract_json(text: str) -> dict:
    """모델 응답에서 첫 번째 완전한 JSON 객체만 추출한다 (여분의 설명 텍스트 방어)."""
    text = text.strip()
    # 코드블록으로 감싸서 온 경우 제거
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)

    start = text.find("{")
    if start == -1:
        raise WriterError("AI 응답에서 JSON을 찾을 수 없습니다.")

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                return json.loads(candidate)
    raise WriterError("AI 응답의 JSON이 완전하지 않습니다.")


def compute_seo_check(content: str, keyword: str) -> dict:
    length = len(content)
    keyword_count = content.lower().count(keyword.lower()) if keyword else 0
    subheading_count = len(re.findall(r"^##\s+", content, flags=re.MULTILINE))
    return {
        "length": length,
        "keyword_count": keyword_count,
        "length_ok": config.SEO_MIN_LENGTH <= length <= config.SEO_MAX_LENGTH,
        "keyword_count_ok": config.SEO_MIN_KEYWORD_COUNT
        <= keyword_count
        <= config.SEO_MAX_KEYWORD_COUNT,
        "subheading_count": subheading_count,
    }


def generate_post(
    api_key: str,
    model: str,
    title: str,
    keyword: str | None,
    extra_request: str,
    profile: BusinessProfile,
) -> GeneratedPost:
    if not api_key:
        raise WriterError("OpenAI API 키가 설정되어 있지 않습니다. 설정 화면에서 입력해주세요.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    user_prompt = build_user_prompt(title, keyword, extra_request, profile)

    response = client.chat.completions.create(
        model=model or config.DEFAULT_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
    )
    raw = response.choices[0].message.content or ""
    data = extract_json(raw)

    content = str(data.get("content", "")).strip()
    hashtags = data.get("hashtags", [])
    if not isinstance(hashtags, list):
        hashtags = []

    if not content:
        raise WriterError("AI가 본문을 생성하지 못했습니다. 다시 시도해주세요.")

    return GeneratedPost(content=content, hashtags=[str(h) for h in hashtags])
