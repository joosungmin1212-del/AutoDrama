"""
Phase 1: Outline 생성 프롬프트
"""

OUTLINE_PROMPT = """
당신은 50~80대 한국 여성을 위한 유튜브 오디오 드라마 작가입니다.

【제목】
{title}

【과제】
위 제목으로 2시간 분량 오디오 드라마의 전체 개요를 3,000자로 작성하세요.

【필수 형식】
- 전지적 3인칭 시점
- 오디오 중심 (화면 없이 소리만으로 이해 가능)
- 50~80대 한국 여성이 흥미롭게 즐길 수 있는 이야기

【포함 요소】
1. 등장인물 3-4명 (이름, 나이, 역할, 목소리 타입)
2. 핵심 갈등
3. 4개 전환점
4. 클라이맥스
5. 결말

【중요】
제목의 의미를 스스로 해석하고, 적절한 장르와 톤을 자유롭게 결정하세요.
단, 50~80대가 이해할 수 있는 범위에서:
- 복잡한 SF, 판타지 지양
- 현실적 가족/인간관계 갈등 중심
- 감동, 복수, 치유, 사이다 등 자유롭게 선택

【JSON 출력 형식】
모든 필드는 필수입니다. 빠진 필드나 null 값이 있으면 오류입니다.

{{
  "title": "제목",
  "characters": [
    {{
      "name": "이름",
      "age": 나이,
      "role": "역할",
      "voice_type": "mature_female/young_female/male/elderly",
      "personality": "성격 (50자)"
    }}
  ],
  "core_conflict": "핵심 갈등 (300자)",
  "turning_points": [
    {{"sequence": 1, "event": "전환점 1"}},
    {{"sequence": 2, "event": "전환점 2"}},
    {{"sequence": 3, "event": "전환점 3"}},
    {{"sequence": 4, "event": "전환점 4"}}
  ],
  "climax": "클라이맥스 (500자)",
  "resolution": "해결 과정 (300자)",
  "ending": "결말 (300자)",
  "theme": "주제",
  "outline_full": "전체 개요를 흐름있게 서술 (3,000자)"
}}

【중요】
- 무조건 **하나의 JSON**만 출력하세요.
- JSON 이외의 어떤 텍스트도 출력하지 마세요.
- 코드블록(```)도 금지입니다.
- JSON만 단독으로 출력하세요.

지금 바로 JSON을 작성하세요.
"""


def generate_outline_prompt(title: str) -> str:
    """
    Outline 생성 프롬프트를 생성합니다.

    Args:
        title (str): 드라마 제목

    Returns:
        str: 완성된 프롬프트
    """
    return OUTLINE_PROMPT.format(title=title)
