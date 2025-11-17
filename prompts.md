# 🔥 최종 프롬프트 v2 (분석 기반)

---

## 1. outline.py

```python
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

지금 바로 JSON을 작성하세요.
"""
```

---

## 2. hook.py

```python
제목】
{title}

【전체 개요】
{outline_full}

【과제】
스토리의 가장 극적인 순간을 500자로 작성하세요.

━━━━━━━━━━━━━━━━
⭐ 훅 구조 ⭐
━━━━━━━━━━━━━━━━

1단계: 강렬한 대사 한 줄 (5-15자)

좋은 예:
"어머니, 이제 그만 죽어주세요."
"이 시계 우리 아빠 거예요."
"저 사람이 제 아들을 죽였어요."

나쁜 예:
"안녕하세요."
"어떻게 지내셨어요?"

2단계: 상황 설명 나레이션 (300자)
- 누가, 어디서, 무슨 일이 벌어졌는지
- 충격적인 사실 제시 (닮은 얼굴, 숨겨진 비밀, 예상치 못한 만남 등)
- 갈등의 핵심 암시

3단계: 의문 제기로 마무리 (30-50자)
"그렇다면 눈앞의 이 소년은 도대체 누구인 걸까요?"
"18년 전 그날 밤, 무슨 일이 있었던 걸까요?"

【필수 규칙】

1. 화자: 전지적 3인칭

2. 대사는 맨 처음 한 줄만
나머지는 전부 나레이션

3. 감정은 신체 반응
"놀랐다" (X) → "숨이 멎는 듯했습니다" (O)
"슬펐다" (X) → "눈물이 흘렀어요" (O)

4. 오디오 중심
소리, 목소리 톤, 의성어 활용

5. 마지막은 반드시 의문문

【출력】
순수 텍스트 500자

지금 바로 작성하세요.
"""
```

---

## 3. part.py

```python
PART_PROMPT = """
당신은 유튜브 오디오 드라마 작가입니다.

【제목】
{title}

【전체 개요】
{outline_full}

{previous_parts_text}

【당신의 과제】
{part_instruction}

━━━━━━━━━━━━━━━━━━━━
⭐⭐⭐ 핵심 규칙 ⭐⭐⭐
나레이션 90~95%
대사 5~10%
500-1000자마다 대사 1회 정도
대사 없는 긴 장면 많아야 함
━━━━━━━━━━━━━━━━━━━━

【필수 문체 규칙】

1. 화자
전지적 3인칭 단일 내레이터
"그는", "그녀는", "민서는" 사용
절대 "나는", "내가" 금지

2. 대사 최소화 ⭐⭐⭐
대사는 정말 중요한 순간에만 사용하세요:
- 첫 만남의 한마디
- 충격적 고백
- 결정적 질문
- 감정의 폭발{climax_dialogue_rule}

대사 형식:
"대사" → 누가 말했는지 명시 → 어떻게 말했는지/반응

좋은 예:
"괜찮아요." 민서가 떨리는 목소리로 대답했습니다. 눈가에 눈물이 맺혔어요.

나쁜 예:
"괜찮아요."
(화자 없음, 반응 없음)

3. 종결어미 혼용
자연스럽게 섞어 쓰세요:
- ~습니다/했습니다: 중요 사건, 전환점
- ~어요/아요/였어요: 일상 묘사, 감정 표현
- ~죠/거든요/니까요: 이유 설명, 배경 설명

예시:
"서영은 국밥집으로 향했습니다. 문을 열자 따뜻한 김이 올랐어요. 점심시간이라 손님이 많았거든요."

4. 나레이션 전개 방식

【시공간 설정부터】
"비 오는 밤", "한편 그 시각", "며칠이 지난 어느 오후"

예시:
"비가 억수같이 쏟아지는 밤이었습니다."
"한편, 강일성 회장은 검은 세단 안에 앉아 있었어요."

【행동 + 감각】
"~를 느끼며", "~를 바라보며", "~를 듣고"

예시:
"민서는 차가운 빗물을 느끼며 핸들을 꽉 쥐었어요."
"일성은 사진을 바라보며 긴 한숨을 내쉬었습니다."

【내면은 나레이션으로】
대사 아닌 혼잣말, 생각, 동기를 나레이션으로 전환

예시:
"제발 버텨줘. 민서는 속으로 빌었습니다."
"할머니 병원비를 내야 했어요."

【"한편"으로 인물 교차】
두 인물의 시점을 번갈아 보여주며 충돌 예고

예시:
"민서는 배달을 서두르고 있었습니다. 한편 같은 시각, 강회장은 병원으로 향하고 있었어요."

【과거 자연스럽게 삽입】
"~년 전", "그때", "그날"

예시:
"18년 전 그날도 비가 왔습니다."
"그때 일성은 모든 것을 잃었어요."

【템포 조절】
느린 장면: 디테일, 감각 묘사, 긴 문장 (감정, 회상)
빠른 장면: 핵심만, 짧은 문장 (전환, 충격)

느린 예시:
"민서는 헬멧 안쪽으로 스며드는 차가운 빗물을 느끼며 악셀을 더 세게 밟았습니다. 낡은 브레이크에서는 쇠 긁는 소리가 났고, 빗길에 미끄러질 뻔한 게 한두 번이 아니었어요."

빠른 예시:
"쿵. 부딪혔습니다. 민서가 땅에 쓰러졌어요. 회장이 차에서 내렸습니다."

5. 감정 표현
감정을 직접 말하지 말고 신체 반응으로만:

"슬펐다" (X) → "눈물이 흘렀다" (O)
"화났다" (X) → "주먹을 쥐었다" (O)
"놀랐다" (X) → "심장이 멎는 듯했다" (O)
"의심했다" (X) → "눈을 가늘게 떴다" (O)
"행복했다" (X) → "미소가 번졌다" (O)

6. 문장 길이 조절
상황에 맞게 자연스럽게 섞어 쓰세요:

짧은 문장 (10-20자): 충격적인 순간, 장면 전환
"숨이 멎었습니다."
"그는 돌아섰어요."

중간 문장 (30-60자): 기본 서술 (가장 많이 사용)
"민서는 배달 가방을 메고 스쿠터에 올라탔습니다."

긴 문장 (70-120자): 감정 묘사, 과거 회상
"18년 전 그날도 이렇게 비가 내렸고, 그날도 이 병원 앞에서 모든 것이 끝났으며, 그 이후로 일성의 삶은 텅 비어버렸습니다."

7. 오디오 중심
시각 의존 최소화, 소리로 전달

의성어: "똑똑", "쿵", "끼익", "쏴아"
목소리: "떨리는 목소리로", "조용히", "크게", "숨을 몰아쉬며"
침묵: "아무 말도 하지 않았다", "침묵만 흘렀다", "고요했습니다"

예시:
"똑똑. 문 두드리는 소리가 들렸습니다."
"끼익. 문이 천천히 열렸어요."

8. 장면 전환
장면이 바뀔 때 명확한 신호:

시간: "그날 밤", "며칠 후", "다음날 아침", "1년이 지나고"
공간: "한편", "~로 향했다", "~에 도착했습니다"
회상: "30년 전, ~였습니다", "그때를 떠올렸어요"

【중요】
나레이션이 스토리를 이끌어야 합니다.
대사는 정말 필요한 순간에만.
대사 없이 나레이션만으로 진행되는 긴 장면이 많아야 합니다.

【자유로운 영역】
위의 문체 규칙만 지키면:
- 스토리 전개 방향
- 갈등의 강도
- 캐릭터 성격
- 장르와 톤

모두 자유롭게 창작하세요.

단, 50~80대가 이해할 수 있는 범위에서:
- 복잡한 SF, 판타지 지양
- 현실적 갈등 중심
- 가족, 인간관계 소재

【출력】
순수 텍스트 {target_length}자

{ending_note}

지금 바로 작성하세요.
"""
```

---

## 8. hook_images.py

```python
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

지금 바로 JSON을 생성하세요.
"""
```

---

## 9. main_images.py

```python
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
```

---

## 파이썬 코드

def generate_part_prompt(title, outline, previous_parts=None):
"""
입력 개수로 Part 번호 자동 판단
"""
if previous_parts is None:
previous_parts = []

```
part_number = len(previous_parts) + 1

# Part별 설정
configs = {
    1: {
        "instruction": "Part 1을 작성하세요.\\n\\n전체의 시작~1/4 구간입니다.\\n- 훅 직후 자연스럽게 시작\\n- 주요 인물 소개\\n- 사건 발생\\n- 갈등의 시작",
        "target_length": "12,000~13,000",
        "climax_dialogue_rule": "",
        "ending_note": ""
    },
    2: {
        "instruction": "Part 2를 작성하세요.\\n\\n전체의 2/4 구간입니다.\\n- 갈등 심화\\n- 진실에 접근\\n- 긴장감 고조",
        "target_length": "12,000~13,000",
        "climax_dialogue_rule": "",
        "ending_note": ""
    },
    3: {
        "instruction": "Part 3를 작성하세요.\\n\\n전체의 3/4 구간입니다.\\n- 클라이맥스\\n- 진실 폭로\\n- 가장 극적인 순간",
        "target_length": "12,000~13,000",
        "climax_dialogue_rule": "\\n\\n클라이맥스에서만 예외적으로 대사 25-30자 허용합니다.",
        "ending_note": ""
    },
    4: {
        "instruction": "Part 4를 작성하세요.\\n\\n전체의 마지막 1/4 구간입니다.\\n- 갈등 해소\\n- 결말\\n- 여운",
        "target_length": "11,500~12,500",
        "climax_dialogue_rule": "",
        "ending_note": "※ 마지막 구독 유도 멘트는 자동으로 추가되므로 작성하지 마세요:\\n\\"오늘의 이야기가 당신의 마음에 작은 울림을 드렸다면 구독과 좋아요를 눌러주세요. 당신의 오늘을 늘 응원합니다.\\""
    }
}

config = configs[part_number]

# 이전 파트 텍스트 생성
if previous_parts:
    prev_text = "\\n".join([
        f"【Part {i} 요약】\\n{summary}"
        for i, summary in enumerate(previous_parts, 1)
    ])
else:
    prev_text = ""

# 프롬프트 조립
prompt = PART_PROMPT.format(
    title=title,
    outline_full=outline,
    previous_parts_text=prev_text,
    part_instruction=config["instruction"],
    climax_dialogue_rule=config["climax_dialogue_rule"],
    target_length=config["target_length"],
    ending_note=config["ending_note"]
)

return prompt

```

# 사용 예시

part1 = generate_part_prompt(
title="제목",
outline="개요"
)

part2 = generate_part_prompt(
title="제목",
outline="개요",
previous_parts=["Part 1 요약"]
)

part3 = generate_part_prompt(
title="제목",
outline="개요",
previous_parts=["Part 1 요약", "Part 2 요약"]
)

part4 = generate_part_prompt(
title="제목",
outline="개요",
previous_parts=["Part 1 요약", "Part 2 요약", "Part 3 요약"]
)