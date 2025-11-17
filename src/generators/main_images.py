"""
main_images.py
메인 스토리 이미지 프롬프트 생성 모듈
"""

MAIN_IMAGES_PROMPT = """
당신은 이미지 프롬프트 생성 전문가입니다.

【Part 1-4 요약】
Part 1: {part1_summary}
Part 2: {part2_summary}
Part 3: {part3_summary}
Part 4: {part4_summary}

【과제】
위 메인 스토리에서 15개 핵심 장면을 선택하고 FLUX 프롬프트를 만드세요.

【장면 배분】
- Part 1: 4개 (시작 장면 필수)
- Part 2: 4개 (시작 장면 필수)
- Part 3: 4개 (시작 장면 필수, 클라이맥스 포함)
- Part 4: 3개 (시작 장면 필수, 결말 포함)

【장면 선정 기준】
- 감정적 전환점
- 중요한 대면
- 과거 회상 (흑백 느낌 가능)
- 클라이맥스 장면
- 결말 장면

【이미지 프롬프트 작성 규칙】
hook_images.py와 동일:
- 영어
- 나이+성별+국적
- "Korean drama style, high quality, realistic, cinematic"
- 조명, 분위기
- 캐릭터 일관성

【JSON 출력 형식】
모든 필드는 필수입니다. 빠진 필드나 null 값이 있으면 오류입니다.

{{
  "scenes": [
    {{
      "index": 0,
      "part": "part1",
      "position": "start",
      "text_reference": "해당 장면 (30자)",
      "timestamp": 180,
      "description": "한국어 묘사 (40자)",
      "mood": "contemplative/shocked/emotional",
      "prompt": "영어 FLUX 프롬프트 (100단어)"
    }},
    {{
      "index": 1,
      "part": "part1",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 660,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 2,
      "part": "part1",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 1140,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 3,
      "part": "part1",
      "position": "end",
      "text_reference": "...",
      "timestamp": 1620,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 4,
      "part": "part2",
      "position": "start",
      "text_reference": "...",
      "timestamp": 2130,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 5,
      "part": "part2",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 2610,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 6,
      "part": "part2",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 3090,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 7,
      "part": "part2",
      "position": "end",
      "text_reference": "...",
      "timestamp": 3570,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 8,
      "part": "part3",
      "position": "start",
      "text_reference": "...",
      "timestamp": 4080,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 9,
      "part": "part3",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 4560,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 10,
      "part": "part3",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 5040,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 11,
      "part": "part3",
      "position": "end",
      "text_reference": "...",
      "timestamp": 5520,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 12,
      "part": "part4",
      "position": "start",
      "text_reference": "...",
      "timestamp": 6030,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 13,
      "part": "part4",
      "position": "middle",
      "text_reference": "...",
      "timestamp": 6510,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }},
    {{
      "index": 14,
      "part": "part4",
      "position": "end",
      "text_reference": "...",
      "timestamp": 6990,
      "description": "...",
      "mood": "...",
      "prompt": "..."
    }}
  ],
  "total_scenes": 15
}}

【타임스탬프 가이드】
훅 끝: 180초

Part 1 (시작 180초, 길이 1,950초):
- 180초 (시작)
- 660초
- 1,140초
- 1,620초

Part 2 (시작 2,130초, 길이 1,950초):
- 2,130초 (시작)
- 2,610초
- 3,090초
- 3,570초

Part 3 (시작 4,080초, 길이 1,950초):
- 4,080초 (시작)
- 4,560초
- 5,040초
- 5,520초

Part 4 (시작 6,030초, 길이 1,870초):
- 6,030초 (시작)
- 6,510초
- 6,990초

지금 바로 JSON을 생성하세요.
"""


def generate_main_images_prompt(
    part1_summary: str,
    part2_summary: str,
    part3_summary: str,
    part4_summary: str
) -> str:
    """
    메인 이미지 프롬프트 생성

    Args:
        part1_summary: Part 1 요약
        part2_summary: Part 2 요약
        part3_summary: Part 3 요약
        part4_summary: Part 4 요약

    Returns:
        완성된 프롬프트
    """
    return MAIN_IMAGES_PROMPT.format(
        part1_summary=part1_summary,
        part2_summary=part2_summary,
        part3_summary=part3_summary,
        part4_summary=part4_summary
    )
