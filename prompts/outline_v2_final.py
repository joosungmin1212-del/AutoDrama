"""
Phase 1: Outline 생성 프롬프트 (V2 Final)
72B 모델 최적화 + ChatGPT 검증 반영 버전 + 안정화 로직 강화
"""

# 시니어 드라마 금지 목록 (전역 상수)
FORBIDDEN_ELEMENTS = [
    "SF/판타지 모든 요소",
    "폭력적 장면",
    "자극적 요소",
    "복잡한 의학 전문용어",
    "복잡한 법률 전문용어",
    "동일 대사 2회 이상 반복",
    "동일 문장 구조 3회 이상 반복",
    "갑작스러운 성격 변화",
    "동기 없는 행동",
    "설명식 대사",
    "영어 단어 남발",
    "최신 인터넷 용어",
    "중국어 단어 사용"
]

OUTLINE_PROMPT_V2_FINAL = """
당신은 50~80대 한국 여성을 위한 유튜브 오디오 드라마 총괄 기획자입니다.

【제목】
{title}

【과제】
위 제목으로 2시간 분량 오디오 드라마의 **완전한 설계 문서**를 작성하세요.
이 문서는 단순한 개요가 아니라, 대본 작가가 일관성 있는 스토리를 쓸 수 있도록 하는 **구조 설계도**입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【핵심 원칙】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 장르와 톤 명확화
   - 제목을 보고 장르(가족드라마/복수극/치유/사이다)를 선택하세요
   - 전체 톤(따뜻함/긴장감/슬픔/통쾌함)을 결정하세요
   - 목표 감정(감동/카타르시스/위로)을 명시하세요

2. 캐릭터 중심 설계
   - 3-4명의 입체적 인물 (단순 역할 아님)
   - 각 인물의 감정 여정 (emotional arc) 명시
   - 인물 간 관계의 변화 추적

3. 5막 구조 (스토리 스파인)
   - 발단(Setup) → 갈등(Conflict) → 전환점(Midpoint) → 절정(Climax) → 해결(Resolution)
   - 각 막의 핵심 사건과 감정 변화 구체화
   - 정보 공개 순서(Revelation Schedule) 설계

4. 감정 곡선 설계
   - 전체 드라마의 감정 기준점(anchors) 명시
   - 파트별 감정 강도와 지배 감정 설계
   - 클라이맥스 배치 (보통 Part 3 후반)

5. 시각화 가능한 장면 설계
   - 8-12개의 핵심 장면 (key scenes)
   - 각 장면의 장소/시간/참여자/감정 피크 명시
   - 이미지 생성에 필요한 감각적 디테일 포함

6. 테마와 상징 설계
   - 메인 테마 + 서브 테마 2-3개
   - 상징적 오브젝트/장소 (반지, 편지, 오래된 집 등)
   - 테마의 자연스러운 전개 방식

7. 일관성 유지 장치
   - 캐릭터 목표/상징 의미/감정선의 기준점 명시
   - 72B 모델이 길게 써도 벗어나지 않도록 고정점 제공

8. 파트별 구체적 가이드
   - 각 Part의 목표/갈등 수준/엔딩 훅/분량 명시
   - Part 간 연결 장치(bridge) 설계
   - 해결해야 할 문제와 이어질 문제 명확히 구분

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【JSON 출력 형식】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

모든 필드는 필수입니다. 빠진 필드나 null 값이 있으면 오류입니다.

{{
  "meta": {{
    "title": "{title}",
    "genre": "가족드라마",
    "tone": "따뜻함",
    "target_emotion": "감동",
    "audience_age": "50-80",
    "duration_minutes": 120,
    "part_count": 4
  }},

  "consistency_anchors": [
    "캐릭터의 핵심 목표는 끝까지 동일해야 합니다",
    "상징적 오브젝트의 의미는 일관되어야 합니다",
    "감정선의 방향은 고정됩니다",
    "장르와 톤은 전 파트에서 동일합니다"
  ],

  "global_conflict_arc": {{
    "start": "미묘한 불안감",
    "rise": "가족과의 충돌",
    "peak": "진실 대면",
    "fall": "화해 과정",
    "end": "새로운 평온"
  }},

  "emotional_anchors": [
    "Part 1: 그리움",
    "Part 2: 혼란",
    "Part 3: 절정",
    "Part 4: 평온"
  ],

  "characters": [
    {{
      "id": "char_001",
      "name": "주인공이름",
      "age": 65,
      "role": "주인공",
      "archetype": "과거에 얽매인 여성",
      "core_trait": "고집스럽지만 따뜻한",
      "voice_type": "elderly_female",
      "emotional_arc": {{
        "start": "외로움",
        "journey": "집착에서 깨달음으로",
        "end": "평온"
      }},
      "relationships": {{
        "손녀": "현실을 깨우쳐주는 존재"
      }},
      "key_motivation": "과거와 화해하고 싶음"
    }}
  ],

  "story_spine": {{
    "act1_setup": {{
      "time_range_minutes": [0, 15],
      "key_events": [
        "사건 1",
        "사건 2",
        "사건 3"
      ],
      "emotional_shift": "평온에서 동요로",
      "information_revealed": "반지의 존재",
      "ending_hook": "Part 1 끝 질문"
    }},

    "act2_conflict": {{
      "time_range_minutes": [15, 60],
      "key_events": [
        "갈등 심화 사건들"
      ],
      "emotional_shift": "동요에서 갈등으로",
      "information_revealed": "과거 사랑 이야기",
      "escalation": "시간 압박"
    }},

    "act3_midpoint": {{
      "time_range_minutes": [60, 90],
      "turning_point": "결정적 전환 사건",
      "key_events": [
        "전환점 사건"
      ],
      "emotional_shift": "고통에서 깨달음으로",
      "information_revealed": "핵심 진실 50% 공개"
    }},

    "act4_climax": {{
      "time_range_minutes": [90, 105],
      "climax_event": "가장 극적인 순간",
      "key_events": [
        "진실 완전 폭로"
      ],
      "emotional_shift": "깨달음에서 절정으로",
      "peak_intensity": 9,
      "dramatic_question": "최종 질문"
    }},

    "act5_resolution": {{
      "time_range_minutes": [105, 120],
      "key_events": [
        "갈등 해소 과정"
      ],
      "emotional_shift": "절정에서 평온으로",
      "information_revealed": "마지막 여운",
      "final_message": "드라마 메시지",
      "closure_level": "완전 해결"
    }}
  }},

  "key_scenes": [
    {{
      "scene_id": "sc_001",
      "part": 1,
      "title": "장면 제목",
      "location": "거실",
      "time": "비 오는 밤",
      "participants": ["주인공", "손녀"],
      "core_action": "무엇이 일어나는가",
      "emotional_peak": "놀라움",
      "dialogue_highlight": "핵심 대사",
      "sensory_essentials": {{
        "sound": "빗소리",
        "touch": "차가운 금속",
        "sight": "낡았지만 빛나는 금빛"
      }},
      "thematic_significance": "과거의 재등장",
      "image_worthy": true
    }}
  ],

  "thematic_threads": {{
    "main_theme": "과거와 현재의 화해",
    "sub_themes": [
      "추억의 가치와 한계",
      "세대 간 이해"
    ],
    "symbolic_objects": {{
      "반지": "과거에 대한 집착",
      "세탁기": "정화"
    }},
    "motifs": [
      "반복되는 이미지: 비",
      "반복되는 행동: 반지 쓰다듬기"
    ],
    "thematic_progression": "집착에서 해방으로"
  }},

  "narrative_rules": {{
    "pov": "전지적 3인칭 단일 내레이터",
    "time_structure": "현재 중심",
    "pacing": {{
      "slow_moments": "감정 묘사",
      "fast_moments": "갈등 폭발"
    }},
    "dialogue_ratio": "5-10%",
    "tone_consistency": "따뜻하지만 진지함",

    "core_forbidden": {forbidden_elements_json},

    "required_elements": [
      "신체 반응으로 감정 표현",
      "감각적 디테일",
      "시간/장소 변화 시 명확한 신호",
      "50-80대 친숙한 어휘"
    ],

    "style_guide": {{
      "sentence_length": "평균 30-50자",
      "paragraph_length": "150-300자",
      "chapter_transitions": "며칠 후",
      "flashback_markers": "30년 전"
    }}
  }},

  "part_breakdown": [
    {{
      "part": 1,
      "title": "발견",
      "time_range_minutes": [0, 30],
      "word_count_range": [12000, 13000],

      "primary_goal": "상황 제시",
      "conflict_intensity": 3,

      "must_include": [
        "주요 인물 등장",
        "사건 발생"
      ],

      "must_avoid": [
        "너무 빠른 전개"
      ],

      "must_resolve": [
        "사건 확인"
      ],

      "open_threads": [
        "미해결 문제 1"
      ],

      "ending_hook": "다음 Part 기대감",

      "key_revelations": [
        "핵심 정보 1"
      ],

      "bridge_to_next": {{
        "connector_dialogue": "연결 대사",
        "carry_over_summary": "Part 2로 이어질 요소"
      }}
    }},

    {{
      "part": 2,
      "title": "갈등",
      "time_range_minutes": [30, 60],
      "word_count_range": [12000, 13000],
      "primary_goal": "갈등 심화",
      "conflict_intensity": 6,
      "must_include": ["가족과의 충돌"],
      "must_avoid": ["동일 대화 반복"],
      "must_resolve": ["첫 충돌 결과"],
      "open_threads": ["진짜 이야기"],
      "ending_hook": "진실의 단서",
      "key_revelations": ["과거 상세"],
      "bridge_to_next": {{
        "connector_dialogue": "연결 대사",
        "carry_over_summary": "Part 3으로 이어질 요소"
      }}
    }},

    {{
      "part": 3,
      "title": "절정",
      "time_range_minutes": [60, 105],
      "word_count_range": [12000, 13000],
      "primary_goal": "진실 폭로",
      "conflict_intensity": 9,
      "must_include": ["핵심 진실 공개"],
      "must_avoid": ["성급한 해결"],
      "must_resolve": ["진실 전부"],
      "open_threads": ["선택의 결과"],
      "ending_hook": "선택 후 여운",
      "key_revelations": ["진실 전부"],
      "bridge_to_next": {{
        "connector_dialogue": "연결 대사",
        "carry_over_summary": "Part 4로 이어질 요소"
      }}
    }},

    {{
      "part": 4,
      "title": "해소",
      "time_range_minutes": [105, 120],
      "word_count_range": [11500, 12500],
      "primary_goal": "갈등 해소",
      "conflict_intensity": 4,
      "must_include": ["화해 장면"],
      "must_avoid": ["설교조 마무리"],
      "must_resolve": ["모든 갈등"],
      "open_threads": [],
      "ending_note": "구독 유도 멘트는 자동 추가되므로 작성 금지",
      "final_message": "과거를 존중하되 현재를 살아가는 것의 의미",
      "key_revelations": ["상징의 최종 의미"],
      "bridge_to_next": {{
        "connector_dialogue": "없음",
        "carry_over_summary": "완결"
      }}
    }}
  ],

  "outline_full": "위 모든 요소를 통합한 전체 스토리 서술 (3000-3500자). 이 서술은 단순 요약이 아니라, 대본 작가가 읽고 전체 흐름을 완벽히 이해할 수 있도록: 사건의 인과관계를 명확히, 감정의 변화 과정을 상세히, 캐릭터 동기와 선택을 논리적으로, 테마의 전개를 자연스럽게 서술하세요. 시간 순서대로, 구체적으로, 감정선을 따라가며 작성하세요."
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【중요 지침】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 제목 해석
   - 제목을 깊이 해석하고, 적절한 장르와 톤을 자유롭게 결정하세요
   - 50~80대가 공감할 수 있는 소재로 변환하세요
   - 복잡한 SF/판타지는 피하되, 감동적이고 현실적인 이야기로

2. 일관성 유지
   - consistency_anchors의 기준을 전 파트에서 절대 지키세요
   - 캐릭터 목표, 상징 의미, 감정 방향은 고정입니다
   - 72B 모델이 길게 써도 이 기준점에서 벗어나지 않습니다

3. 정보 공개 전략
   - 모든 정보를 한 번에 주지 마세요
   - 궁금증을 유발하는 순서로 공개하세요
   - Part 3에서 핵심 진실이 드러나도록 설계하세요

4. 감정 곡선 설계
   - emotional_anchors를 절대 기준으로 삼으세요
   - Part 3에서 절정, Part 4에서 안정
   - 각 Part 끝에 다음을 기대하게 만드는 훅 필요

5. 시니어 감성 존중
   - 과거에 대한 향수는 좋지만, 집착은 경계
   - 가족의 중요성, 용서, 화해 같은 보편적 가치
   - 삶의 지혜, 늦지 않은 선택 같은 메시지

6. JSON 정확성
   - 모든 필드를 빠짐없이 채우세요
   - null이나 빈 문자열 금지
   - 한국어는 큰따옴표 안에, 숫자는 그대로
   - 배열 끝 콤마 주의
   - word_count_range, time_range_minutes는 숫자 배열로

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【절대 금지】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 무조건 **하나의 JSON**만 출력하세요
- JSON 이외의 어떤 텍스트도 출력하지 마세요
- 코드블록(```)도 금지입니다
- 중국어/영어 설명 금지입니다
- JSON만 단독으로 출력하세요

지금 바로 JSON을 작성하세요.
"""


def generate_outline_prompt(title: str) -> str:
    """
    Outline 생성 프롬프트를 생성합니다. (V2 Final 버전)

    Args:
        title (str): 드라마 제목

    Returns:
        str: 완성된 프롬프트
    """
    import json

    # 금지 요소를 JSON 배열로 변환
    forbidden_json = json.dumps(FORBIDDEN_ELEMENTS, ensure_ascii=False)

    return OUTLINE_PROMPT_V2_FINAL.format(
        title=title,
        forbidden_elements_json=forbidden_json
    )


def validate_outline(outline_data: dict) -> dict:
    """
    Outline JSON을 검증하고 누락된 필드를 자동으로 보충합니다.

    Args:
        outline_data (dict): Outline JSON 데이터

    Returns:
        dict: 검증 및 보정된 Outline JSON

    Raises:
        ValueError: 필수 필드가 심각하게 누락된 경우
    """
    import copy

    # 깊은 복사로 원본 보존
    validated = copy.deepcopy(outline_data)

    # 1. meta 검증
    if "meta" not in validated or not validated["meta"]:
        validated["meta"] = {}

    meta_defaults = {
        "title": "제목 없음",
        "genre": "가족드라마",
        "tone": "따뜻함",
        "target_emotion": "감동",
        "audience_age": "50-80",
        "duration_minutes": 120,
        "part_count": 4
    }

    for key, default_value in meta_defaults.items():
        if key not in validated["meta"] or not validated["meta"][key]:
            validated["meta"][key] = default_value

    # 2. consistency_anchors 검증 (4개 필수)
    if "consistency_anchors" not in validated or not validated["consistency_anchors"]:
        validated["consistency_anchors"] = [
            "캐릭터의 핵심 목표는 끝까지 동일해야 합니다",
            "상징적 오브젝트의 의미는 일관되어야 합니다",
            "감정선의 방향은 고정됩니다",
            "장르와 톤은 전 파트에서 동일합니다"
        ]
    elif len(validated["consistency_anchors"]) < 4:
        while len(validated["consistency_anchors"]) < 4:
            validated["consistency_anchors"].append("일관성 유지")

    # 3. global_conflict_arc 검증
    if "global_conflict_arc" not in validated or not validated["global_conflict_arc"]:
        validated["global_conflict_arc"] = {}

    arc_defaults = {
        "start": "평온한 일상",
        "rise": "갈등 시작",
        "peak": "진실 대면",
        "fall": "화해 과정",
        "end": "새로운 평온"
    }

    for key, default_value in arc_defaults.items():
        if key not in validated["global_conflict_arc"] or not validated["global_conflict_arc"][key]:
            validated["global_conflict_arc"][key] = default_value

    # 4. emotional_anchors 검증 (4개 필수)
    if "emotional_anchors" not in validated or not validated["emotional_anchors"]:
        validated["emotional_anchors"] = [
            "Part 1: 그리움",
            "Part 2: 혼란",
            "Part 3: 절정",
            "Part 4: 평온"
        ]
    elif len(validated["emotional_anchors"]) < 4:
        defaults = ["Part 1: 그리움", "Part 2: 혼란", "Part 3: 절정", "Part 4: 평온"]
        while len(validated["emotional_anchors"]) < 4:
            idx = len(validated["emotional_anchors"])
            validated["emotional_anchors"].append(defaults[idx] if idx < len(defaults) else f"Part {idx+1}: 감정")

    # 5. characters 검증
    if "characters" not in validated or not validated["characters"]:
        validated["characters"] = [{
            "id": "char_001",
            "name": "주인공",
            "age": 65,
            "role": "주인공",
            "archetype": "일반인",
            "core_trait": "따뜻한 성격",
            "voice_type": "elderly_female",
            "emotional_arc": {
                "start": "평온",
                "journey": "변화",
                "end": "성장"
            },
            "relationships": {},
            "key_motivation": "목표"
        }]

    # 6. part_breakdown 검증 (4개 필수)
    if "part_breakdown" not in validated or not validated["part_breakdown"]:
        validated["part_breakdown"] = []

    while len(validated["part_breakdown"]) < 4:
        part_num = len(validated["part_breakdown"]) + 1
        validated["part_breakdown"].append({
            "part": part_num,
            "title": f"Part {part_num}",
            "time_range_minutes": [(part_num-1)*30, part_num*30],
            "word_count_range": [12000, 13000],
            "primary_goal": "목표",
            "conflict_intensity": 5,
            "must_include": [],
            "must_avoid": [],
            "must_resolve": [],
            "open_threads": [],
            "ending_hook": "",
            "key_revelations": [],
            "bridge_to_next": {
                "connector_dialogue": "",
                "carry_over_summary": ""
            }
        })

    # 각 part_breakdown 필드 검증
    for i, part in enumerate(validated["part_breakdown"]):
        # time_range_minutes, word_count_range를 배열로 강제 변환
        if "time_range_minutes" not in part or not isinstance(part["time_range_minutes"], list):
            part["time_range_minutes"] = [i*30, (i+1)*30]

        if "word_count_range" not in part or not isinstance(part["word_count_range"], list):
            part["word_count_range"] = [12000, 13000]

        # 문자열이 배열에 들어간 경우 숫자로 변환
        if isinstance(part["time_range_minutes"], list):
            part["time_range_minutes"] = [
                int(x) if isinstance(x, str) and x.isdigit() else x
                for x in part["time_range_minutes"]
            ]

        if isinstance(part["word_count_range"], list):
            part["word_count_range"] = [
                int(x) if isinstance(x, str) and x.isdigit() else x
                for x in part["word_count_range"]
            ]

        # 필수 필드 기본값 설정
        if "must_include" not in part or not part["must_include"]:
            part["must_include"] = []
        if "must_avoid" not in part or not part["must_avoid"]:
            part["must_avoid"] = []
        if "must_resolve" not in part or not part["must_resolve"]:
            part["must_resolve"] = []
        if "open_threads" not in part or not part["open_threads"]:
            part["open_threads"] = []
        if "key_revelations" not in part or not part["key_revelations"]:
            part["key_revelations"] = []
        if "bridge_to_next" not in part or not part["bridge_to_next"]:
            part["bridge_to_next"] = {
                "connector_dialogue": "",
                "carry_over_summary": ""
            }

    # 7. outline_full 검증
    if "outline_full" not in validated or not validated["outline_full"]:
        validated["outline_full"] = "전체 개요가 생성되지 않았습니다."

    # 8. 기타 필수 필드 검증
    if "story_spine" not in validated or not validated["story_spine"]:
        validated["story_spine"] = {}

    if "key_scenes" not in validated or not validated["key_scenes"]:
        validated["key_scenes"] = []

    if "thematic_threads" not in validated or not validated["thematic_threads"]:
        validated["thematic_threads"] = {
            "main_theme": "가족의 의미",
            "sub_themes": [],
            "symbolic_objects": {},
            "motifs": [],
            "thematic_progression": "변화"
        }

    if "narrative_rules" not in validated or not validated["narrative_rules"]:
        validated["narrative_rules"] = {
            "pov": "전지적 3인칭",
            "dialogue_ratio": "5-10%",
            "core_forbidden": FORBIDDEN_ELEMENTS
        }

    return validated
