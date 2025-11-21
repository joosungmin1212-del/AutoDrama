"""
Phase 1: Outline 생성 프롬프트 (V2 Final)
72B 모델 최적화 + ChatGPT 검증 반영 버전
"""

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
    "genre": "가족드라마|복수극|치유드라마|사이다극 중 택1",
    "tone": "따뜻함|긴장감|슬픔|통쾌함|혼합(따뜻함+긴장감)",
    "target_emotion": "감동|카타르시스|위로|희망",
    "audience_age": "50-80",
    "duration_minutes": 120,
    "part_count": 4
  }},

  "consistency_anchors": [
    "캐릭터의 핵심 목표는 끝까지 동일해야 합니다 (예: 유진은 과거와 화해하고 싶음)",
    "상징적 오브젝트의 의미는 일관되어야 합니다 (예: 반지는 과거의 집착)",
    "감정선의 방향은 고정됩니다 (예: 집착 → 깨달음 → 화해)",
    "장르와 톤은 전 파트에서 동일합니다"
  ],

  "global_conflict_arc": {{
    "start": "미묘한 불안감 (평온한 일상의 균열)",
    "rise": "가족과의 충돌 (과거 vs 현재)",
    "peak": "진실 대면 (핵심 깨달음의 순간)",
    "fall": "화해 과정 (관계 회복)",
    "end": "새로운 평온 (성장한 상태)"
  }},

  "emotional_anchors": [
    "Part 1: 그리움 (과거에 대한 향수)",
    "Part 2: 혼란 (갈등과 선택의 압박)",
    "Part 3: 절정 (깨달음과 결단)",
    "Part 4: 평온 (화해와 새로운 시작)"
  ],

  "characters": [
    {{
      "id": "char_001",
      "name": "이름 (50~80대가 친숙한 이름)",
      "age": 65,
      "role": "주인공|조력자|갈등자|관찰자",
      "archetype": "과거에 얽매인 여성|억울함을 품은 노인|화해를 원하는 어머니 등",
      "core_trait": "고집스럽지만 따뜻한|조용하지만 강인한 등 (2-3가지 특성)",
      "voice_type": "elderly_female|mature_female|young_female|male",
      "emotional_arc": {{
        "start": "초기 감정 상태 (외로움/분노/그리움)",
        "journey": "감정 여정 (집착 → 깨달음 → 화해)",
        "end": "최종 감정 상태 (평온/용서/희망)"
      }},
      "relationships": {{
        "캐릭터B 이름": "관계 설명 (손녀, 현실을 깨우쳐주는 존재)",
        "캐릭터C 이름": "관계 설명 (첫사랑, 과거의 상징)"
      }},
      "key_motivation": "이 인물이 원하는 것 (구체적으로, 전 파트 동일)"
    }}
  ],

  "story_spine": {{
    "act1_setup": {{
      "time_range_minutes": [0, 15],
      "key_events": [
        "사건 1: 반지 발견 (구체적 상황 묘사)",
        "사건 2: 가족 반응",
        "사건 3: 첫 갈등 시작"
      ],
      "emotional_shift": "평온 → 동요",
      "information_revealed": "반지의 존재, 과거 암시",
      "ending_hook": "Part 1 끝에서 제기될 질문"
    }},

    "act2_conflict": {{
      "time_range_minutes": [15, 60],
      "key_events": [
        "갈등 심화 사건들",
        "과거 회상 장면",
        "가족 간 의견 충돌"
      ],
      "emotional_shift": "동요 → 갈등 → 고통",
      "information_revealed": "과거 사랑 이야기, 숨겨진 사실 일부",
      "escalation": "갈등 강화 요소 (시간 압박/선택 강요 등)"
    }},

    "act3_midpoint": {{
      "time_range_minutes": [60, 90],
      "turning_point": "결정적 전환 사건 (진실 발견/충격적 만남 등)",
      "key_events": [
        "전환점 사건",
        "캐릭터 선택의 순간",
        "새로운 정보 공개"
      ],
      "emotional_shift": "고통 → 깨달음 시작",
      "information_revealed": "핵심 진실 50% 공개"
    }},

    "act4_climax": {{
      "time_range_minutes": [90, 105],
      "climax_event": "가장 극적인 순간 (구체적 장면 묘사)",
      "key_events": [
        "진실 완전 폭로",
        "캐릭터 최종 선택",
        "감정 폭발 장면"
      ],
      "emotional_shift": "깨달음 → 결단 → 절정",
      "peak_intensity": 9,
      "dramatic_question": "최종적으로 던지는 질문"
    }},

    "act5_resolution": {{
      "time_range_minutes": [105, 120],
      "key_events": [
        "갈등 해소 과정",
        "캐릭터 변화 확인",
        "새로운 균형 도달"
      ],
      "emotional_shift": "절정 → 해소 → 평온",
      "information_revealed": "마지막 여운, 상징적 의미",
      "final_message": "드라마가 전달하는 메시지",
      "closure_level": "완전 해결|열린 결말|희망적 암시"
    }}
  }},

  "key_scenes": [
    {{
      "scene_id": "sc_001",
      "part": 1,
      "title": "장면 제목 (예: 반지의 발견)",
      "location": "세탁실|거실|병원 등",
      "time": "비 오는 밤|이른 아침|황혼 무렵",
      "participants": ["유진", "하영"],
      "core_action": "무엇이 일어나는가 (100자)",
      "emotional_peak": "놀라움 → 그리움",
      "dialogue_highlight": "이 장면의 핵심 대사 1개 (15자 이내)",
      "sensory_essentials": {{
        "sound": "빗소리, 세탁기 돌아가는 소리",
        "touch": "차가운 금속 촉감",
        "sight": "낡았지만 빛나는 금빛"
      }},
      "thematic_significance": "과거의 재등장, 선택의 시작",
      "image_worthy": true
    }}
  ],

  "thematic_threads": {{
    "main_theme": "과거와 현재의 화해|가족의 의미|용서와 치유 중 택1",
    "sub_themes": [
      "추억의 가치와 한계",
      "세대 간 이해",
      "선택의 무게"
    ],
    "symbolic_objects": {{
      "반지": "과거에 대한 집착",
      "세탁기": "정화, 새로운 시작",
      "빗소리": "슬픔과 정화"
    }},
    "motifs": [
      "반복되는 이미지: 비",
      "반복되는 행동: 반지 쓰다듬기",
      "반복되는 대사: '그때도 비가 왔어요'"
    ],
    "thematic_progression": "집착(Part 1) → 갈등(Part 2) → 깨달음(Part 3) → 해방(Part 4)"
  }},

  "narrative_rules": {{
    "pov": "전지적 3인칭 단일 내레이터",
    "time_structure": "현재 중심, 과거 회상 삽입 (회상 비율 20% 이내)",
    "pacing": {{
      "slow_moments": "감정 묘사, 회상 장면",
      "fast_moments": "갈등 폭발, 진실 발견"
    }},
    "dialogue_ratio": "전체의 5-10% (나레이션 90-95%)",
    "tone_consistency": "따뜻하지만 진지함, 과도한 유머 금지",

    "core_forbidden": [
      "SF/판타지 요소",
      "폭력적 장면",
      "복잡한 전문용어",
      "동일 대사 2회 이상 반복",
      "갑작스러운 성격 변화",
      "동기 없는 행동",
      "설명식 대사",
      "영어 단어 남발",
      "최신 인터넷 용어"
    ],

    "required_elements": [
      "신체 반응으로 감정 표현 (눈물/주먹/숨)",
      "감각적 디테일 (소리/촉감/시각)",
      "시간/장소 변화 시 명확한 신호",
      "50-80대 친숙한 어휘",
      "~습니다/~어요 자연스러운 혼용"
    ],

    "style_guide": {{
      "sentence_length": "평균 30-50자, 최대 80자",
      "paragraph_length": "150-300자 단위로 호흡",
      "chapter_transitions": "며칠 후|그날 밤|한편 그 시각",
      "flashback_markers": "30년 전|그때도|그날의 기억"
    }}
  }},

  "part_breakdown": [
    {{
      "part": 1,
      "title": "발견 (Discovery)",
      "time_range_minutes": [0, 30],
      "word_count_range": [12000, 13000],

      "primary_goal": "상황 제시, 인물 소개, 갈등 씨앗",
      "conflict_intensity": 3,

      "must_include": [
        "반지 발견 장면 (구체적 묘사)",
        "주요 인물 3-4명 등장",
        "과거 암시 (회상 장면 1-2개)",
        "가족들의 첫 반응"
      ],

      "must_avoid": [
        "너무 빠른 전개",
        "과도한 설명",
        "캐릭터 과다 등장 (4명 이내)"
      ],

      "must_resolve": [
        "반지 발견 사실 확인",
        "가족들에게 알림"
      ],

      "open_threads": [
        "반지의 처리 방법 미정",
        "영호에 대한 미완성 회상",
        "가족 갈등 시작"
      ],

      "ending_hook": "가족들의 우려 시작, '이 반지 어떻게 할 거예요?'",

      "key_revelations": [
        "반지의 존재",
        "영호라는 이름",
        "유진의 과거 사랑 암시"
      ],

      "bridge_to_next": {{
        "connector_dialogue": "하영의 질문: '할머니, 그 반지 어떻게 할 거예요?'",
        "carry_over_summary": "반지의 의미, 가족의 우려, 유진의 동요가 Part 2로 이어집니다."
      }}
    }},

    {{
      "part": 2,
      "title": "갈등 (Conflict)",
      "time_range_minutes": [30, 60],
      "word_count_range": [12000, 13000],

      "primary_goal": "갈등 심화, 과거 공개, 선택 압박",
      "conflict_intensity": 6,

      "must_include": [
        "가족과의 본격 충돌",
        "과거 회상 확대 (영호와의 추억)",
        "유진의 내적 갈등 심화",
        "시간 압박 요소 도입"
      ],

      "must_avoid": [
        "동일 대화 반복",
        "정체된 스토리",
        "캐릭터 동기 불명확"
      ],

      "must_resolve": [
        "가족과의 첫 충돌 결과",
        "과거 회상 일부 완결"
      ],

      "open_threads": [
        "영호의 진짜 이야기",
        "유진의 선택",
        "가족 관계 악화"
      ],

      "ending_hook": "진실의 단서 발견, '이럴 수가...'",

      "key_revelations": [
        "영호와의 과거 상세",
        "반지의 의미",
        "숨겨진 사실 암시"
      ],

      "bridge_to_next": {{
        "connector_dialogue": "유진의 독백: '이제 진실을 알아야 해...'",
        "carry_over_summary": "진실 단서, 유진의 혼란, 가족 긴장이 Part 3의 폭발로 이어집니다."
      }}
    }},

    {{
      "part": 3,
      "title": "절정 (Climax)",
      "time_range_minutes": [60, 105],
      "word_count_range": [12000, 13000],

      "primary_goal": "진실 폭로, 클라이맥스, 결단",
      "conflict_intensity": 9,

      "must_include": [
        "핵심 진실 완전 공개",
        "감정 폭발 장면",
        "유진의 최종 선택 순간",
        "상징적 장면 (반지 처리 등)"
      ],

      "must_avoid": [
        "성급한 해결",
        "설명식 진실 폭로",
        "감정 과잉"
      ],

      "must_resolve": [
        "영호의 진실 전부",
        "유진의 최종 선택"
      ],

      "open_threads": [
        "선택의 결과",
        "가족 화해 가능성",
        "새로운 시작"
      ],

      "ending_hook": "선택 후 여운, '이제 괜찮을까요?'",

      "key_revelations": [
        "영호의 진실 전부",
        "유진의 진짜 바람",
        "가족의 진심"
      ],

      "bridge_to_next": {{
        "connector_dialogue": "유진의 결단: '이제 내려놓을게요.'",
        "carry_over_summary": "선택의 여파, 관계 변화, 새로운 균형이 Part 4에서 완결됩니다."
      }}
    }},

    {{
      "part": 4,
      "title": "해소 (Resolution)",
      "time_range_minutes": [105, 120],
      "word_count_range": [11500, 12500],

      "primary_goal": "갈등 해소, 화해, 새로운 시작",
      "conflict_intensity": 4,

      "must_include": [
        "가족과의 화해 장면",
        "유진의 변화 확인",
        "상징적 마무리 (반지 보관/처리)",
        "따뜻한 여운"
      ],

      "must_avoid": [
        "설교조 마무리",
        "과도한 해피엔딩",
        "미완성 감정선"
      ],

      "must_resolve": [
        "모든 갈등",
        "모든 캐릭터의 감정 정리",
        "테마의 완결"
      ],

      "open_threads": [],

      "ending_note": "구독 유도 멘트는 자동 추가되므로 작성 금지",

      "final_message": "과거를 존중하되 현재를 살아가는 것의 의미",

      "key_revelations": [
        "상징의 최종 의미",
        "캐릭터의 성장 확인"
      ],

      "bridge_to_next": {{
        "connector_dialogue": "없음 (마지막 파트)",
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
    return OUTLINE_PROMPT_V2_FINAL.format(title=title)
