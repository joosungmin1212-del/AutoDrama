"""
Phase 7-1: Hook 이미지 프롬프트 생성
"""

HOOK_IMAGES_PROMPT = """
당신은 이미지 프롬프트 생성 전문가입니다.

【훅 대본】
{hook_text}

【과제】
위 훅 대본에서 5개 장면을 추출하고, 각 장면마다 FLUX 이미지 생성 프롬프트를 만드세요.

【이미지 프롬프트 작성 규칙】

1. 영어로 작성

2. 인물 묘사 구체적으로
나이 + 성별 + 국적 명시
예: "50-year-old Korean woman", "8-year-old Korean boy"

3. 필수 키워드
"Korean drama style, high quality, realistic, cinematic"

4. 조명과 분위기
"dramatic lighting", "soft morning light", "tense atmosphere" 등

5. 캐릭터 일관성
같은 인물은 매번 동일한 특징 반복
예: "50-year-old Korean woman, short permed hair, elegant business suit"

【JSON 출력 형식】
모든 필드는 필수입니다. 빠진 필드나 null 값이 있으면 오류입니다.

{{
  "scenes": [
    {{
      "index": 0,
      "part": "hook",
      "text_reference": "대본의 해당 부분 (20자)",
      "timestamp": 0,
      "duration": 36,
      "description": "한국어로 장면 묘사 (30자)",
      "mood": "tense/sad/hopeful/shocking",
      "prompt": "영어 FLUX 프롬프트 (80-120단어)"
    }},
    {{
      "index": 1,
      "part": "hook",
      "text_reference": "...",
      "timestamp": 36,
      "duration": 36,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 2,
      "part": "hook",
      "text_reference": "...",
      "timestamp": 72,
      "duration": 36,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 3,
      "part": "hook",
      "text_reference": "...",
      "timestamp": 108,
      "duration": 36,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 4,
      "part": "hook",
      "text_reference": "...",
      "timestamp": 144,
      "duration": 36,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }}
  ],
  "total_scenes": 5
}}

【타임스탬프】
각 장면 36초씩:
- Scene 0: 0초
- Scene 1: 36초
- Scene 2: 72초
- Scene 3: 108초
- Scene 4: 144초

【예시 프롬프트】
"50-year-old Korean woman in living room at night, holding envelope with trembling hands, anxious worried expression, dramatic indoor lighting casting shadows, Korean apartment interior with traditional furniture, tense atmosphere before revelation, close-up emotional shot, high quality, realistic, cinematic, Korean drama aesthetic, detailed facial expression"

【중요】
- 무조건 **하나의 JSON**만 출력하세요.
- JSON 이외의 어떤 텍스트도 출력하지 마세요.
- 코드블록(```)도 금지입니다.
- JSON만 단독으로 출력하세요.

지금 바로 JSON을 생성하세요.
"""


def generate_hook_images_prompt(hook_text: str) -> str:
    """
    Hook 이미지 프롬프트 생성 프롬프트를 생성합니다.

    Args:
        hook_text (str): Hook 대본 (500자)

    Returns:
        str: 완성된 프롬프트
    """
    return HOOK_IMAGES_PROMPT.format(hook_text=hook_text)
