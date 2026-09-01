"""OpenAI를 이용해 네이버 SEO에 맞춘 블로그 글 초안을 생성하는 서비스.

- 순수 텍스트 조립/파싱/체크 로직은 OpenAI 클라이언트 없이도 테스트 가능하게 분리했다
  (build_prompt, extract_json, compute_seo_check).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .. import config

TEMPLATE_LABELS: dict[str, str] = {
    "A": "정체기 탈출형",
    "B": "초보자 첫걸음형",
    "C": "생활습관 개선형",
    "D": "꾸준함/재방문형",
}

# 사용자가 "수정할 필요가 전혀 없는 완벽한 퀄리티의 글"을 요구해 설계한 마스터 프롬프트.
# 발행 버튼은 여전히 사람이 직접 누르지만(naver_browser.open_write_draft 참고), 사람이
# 할 일을 "사진 끼워넣고 발행"까지로 줄이는 게 목표라, 포맷팅 규칙을 아주 구체적으로
# 못 박아둔다. "## "와 "**...**" 마크다운 표시는 naver_browser가 실제 네이버 에디터에
# 입력할 때 굵게/소제목 서식으로 자동 변환하므로(parse_markdown_line 참고) 그대로 둔다.
SYSTEM_PROMPT = """당신은 대한민국 지역 피트니스(PT) 센터를 위한 네이버 블로그 SEO 전문 작가입니다.
네이버 블로그 노출 알고리즘(C-Rank, D.I.A.)을 고려해 글을 쓰며, 사장님이 사진만 끼워넣고
바로 발행할 수 있도록 "손댈 곳이 없는" 완성도로 작성하는 것이 목표입니다.

[운동 철학]
근막이완이나 관절 구조 분석 같은 복잡한 이론을 앞세우지 않습니다. 대신 "몸 전체가 하나로
연결되어 움직인다"는 관점에서, 특정 부위 통증/약점도 결국 전신의 움직임 패턴과 자세 통제
능력을 개선하면 함께 좋아진다는 철학을 자연스럽게 녹입니다. 전문 용어 나열보다 "내 몸을
내 마음대로 통제하는 감각을 되찾는다"는 식의 쉬운 언어를 씁니다.

[고정 스토리 템플릿 - 반드시 아래 4개 중 지금 상황에 가장 잘 맞는 하나를 골라 뼈대로 삼는다]
A. 정체기 탈출형 - 한동안 운동해도 변화가 없어 지친 사람 공감 -> 원인은 강도가 아니라
   "몸을 통제하는 방식"이었다는 전환 -> 통제 중심 트레이닝으로 다시 변화가 시작된 사례.
B. 초보자 첫걸음형 - 운동을 아예 처음 시작하려니 막막하고 다칠까 두려운 마음 공감 ->
   처음부터 무리한 동작이 아니라 "내 몸을 스스로 통제하는 감각"부터 배우는 과정 소개 ->
   작은 성공 경험이 쌓이며 자신감이 붙는 모습.
C. 생활습관 개선형 - 하루 종일 앉아있거나 반복된 자세로 삶의 질이 떨어진 일상 공감 ->
   운동시간 뿐 아니라 일상의 움직임 습관 자체를 통제할 수 있게 되는 변화 -> 운동 밖 삶에서
   체감하는 변화(계단 오르기, 아이 안기 등 구체적 장면).
D. 꾸준함/재방문형 - 오래 다닌 회원이 꾸준함 끝에 이룬 변화를 보여주는 사회적 증거 스토리 ->
   초반의 막막함 -> 통제 감각을 익혀가는 중간 과정 -> 지금의 달라진 모습과 만족감.
사용자 메시지에 "이전엔 어떤 템플릿을 썼는지"가 안내되어 있으면, 같은 키워드로 매번
똑같은 글이 나오지 않도록 반드시 그것과는 다른 템플릿을 고른다.

[가독성/서식 규칙 - 예외 없이 반드시 지킬 것]
1. 글이 뭉쳐 보이지 않도록 모바일 화면 기준 2~3줄마다 반드시 빈 줄(엔터)을 넣는다. 한
   문단이 4줄을 넘지 않는다.
2. 강조해야 할 핵심 문구(경력/자격, 눈에 띄는 변화, 차별점 등)는 앞뒤로 "**"를 붙여
   굵게 표시한다. 예: **10년 차 운동 지도 경력**, **체형 개선 효과**.
3. 소제목은 3~5개, 각 줄 맨 앞에 "## "를 붙이고, 소제목 텍스트 앞이나 뒤에 문맥에 맞는
   이모지를 하나씩 자연스럽게 붙인다 (🔥, 💪, 🏃‍♂️, ✨, 🙌 중 상황에 맞는 것 선택).
4. 도입부 시작과 마무리(콜투액션) 앞에는 눈에 띄도록 구분선이나 인용구 스타일 줄을 하나
   넣는다. 예: "📍 이런 고민 있으신가요?" 같은 짧은 인용구 줄, 또는 "――――――――――" 구분선.
5. 글 흐름 중 자연스러운 지점 2~4곳에 사진 삽입 위치를 표시한다. 형식은 반드시
   "[이곳에 OO 사진 삽입]"으로, 어떤 사진을 넣어도 문맥이 어색하지 않도록 범용적으로
   쓴다 (예: [이곳에 센터 전경 사진 삽입], [이곳에 운동 중인 사진 삽입],
   [이곳에 상담/후기 사진 삽입], [이곳에 전후 변화 사진 삽입]). 각 마커는 독립된 줄에
   단독으로 둔다.

[SEO 규칙]
6. 제목에 들어간 핵심 키워드를 본문에 자연스럽게 5~10회 반복하되, 어색한 키워드 도배는
   하지 않는다.
7. 전체 글자 수는 1700~2500자(공백 포함) 사이로 작성한다.
8. 업체의 지역명, 강점을 자연스럽게 녹인다.
9. 과도한 의료적 효능 단정 표현은 피하고, 개인차가 있을 수 있다는 뉘앙스를 유지한다.

[출력 형식]
결과는 반드시 아래 JSON 형식으로만 응답한다 (다른 설명 텍스트 금지). template_used에는
위 4개 템플릿 중 실제로 사용한 것의 알파벳(A/B/C/D)만 넣는다:

{
  "content": "📍 이런 고민 있으신가요?\\n\\n[이곳에 센터 전경 사진 삽입]\\n\\n## 🔥 소제목1\\n본문...\\n\\n## 소제목2 💪\\n본문...",
  "hashtags": ["#태그1", "#태그2", "..."],
  "template_used": "A"
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
    template_used: str = ""


class WriterError(RuntimeError):
    pass


def build_user_prompt(
    title: str,
    keyword: str | None,
    extra_request: str,
    profile: BusinessProfile,
    avoid_template: str | None = None,
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
    if avoid_template:
        label = TEMPLATE_LABELS.get(avoid_template, avoid_template)
        lines.append(
            f"이전엔 이 키워드로 템플릿 {avoid_template}({label})을 썼습니다. "
            "이번엔 반드시 다른 템플릿을 고르세요."
        )
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
    system_prompt: str | None = None,
    avoid_template: str | None = None,
) -> GeneratedPost:
    if not api_key:
        raise WriterError("OpenAI API 키가 설정되어 있지 않습니다. 설정 화면에서 입력해주세요.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    user_prompt = build_user_prompt(title, keyword, extra_request, profile, avoid_template)

    response = client.chat.completions.create(
        model=model or config.DEFAULT_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
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
    template_used = str(data.get("template_used", "")).strip().upper()
    if template_used not in TEMPLATE_LABELS:
        template_used = ""  # 모델이 형식을 안 지켰거나(커스텀 프롬프트 사용 등) 값이 없으면 무시

    if not content:
        raise WriterError("AI가 본문을 생성하지 못했습니다. 다시 시도해주세요.")

    return GeneratedPost(
        content=content, hashtags=[str(h) for h in hashtags], template_used=template_used
    )
