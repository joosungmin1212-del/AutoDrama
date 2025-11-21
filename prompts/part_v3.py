"""
Phase 3-6: Part 1-4 생성 프롬프트 V3
outline_v2_final.json 기반 완전 재설계 + 안정화 로직 강화
"""

from typing import Dict, Any, Optional
import re

# 금지 요소 (outline과 동일하게 유지)
from prompts.outline_v2_final import FORBIDDEN_ELEMENTS

PART_PROMPT_V3 = """
당신은 50~80대 한국 여성을 위한 유튜브 오디오 드라마 대본 작가입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【작성 대상】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Part {part_number}: {part_title}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【설계 문서】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【제목】
{title}

【장르와 톤】
- 장르: {genre}
- 전체 톤: {tone}
- 목표 감정: {target_emotion}

【일관성 기준점 (Consistency Anchors)】
{consistency_anchors}

⚠️ 위 4가지 기준은 절대 변경 금지입니다. 전 파트에서 동일하게 유지됩니다.

【전체 갈등 곡선 (Global Conflict Arc)】
{global_conflict_arc}

현재 위치: {current_arc_stage}

【감정 고정점 (Emotional Anchors)】
{emotional_anchors}

현재 Part의 지배 감정: {current_emotion}

⚠️ 이 Part는 **{current_emotion}**이 지배해야 합니다. 다른 감정으로 벗어나지 마세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【캐릭터 설계】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{characters}

⚠️ 각 캐릭터의 **핵심 목표(key_motivation)**는 전 파트 동일합니다. 변경 금지.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【이 Part의 스토리 목표】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{part_goal}

시간 범위: {time_range_minutes_start}분 ~ {time_range_minutes_end}분
분량 목표: {word_count_start:,}~{word_count_end:,}자
갈등 강도: {conflict_intensity}/10

【이 Part에서 반드시 포함할 요소 (Must Include)】
{must_include}

【이 Part에서 반드시 피해야 할 것 (Must Avoid)】
{must_avoid}

【이 Part에서 반드시 해결해야 할 것 (Must Resolve)】
{must_resolve}

【이 Part 끝에 남겨둘 미해결 요소 (Open Threads)】
{open_threads}

【이 Part에서 공개할 정보 (Key Revelations)】
{key_revelations}

【이 Part의 엔딩 훅】
{ending_hook}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【상징과 테마】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

메인 테마: {main_theme}

상징적 오브젝트:
{symbolic_objects}

⚠️ 상징의 의미는 일관되게 유지하세요. 함부로 변경하지 마세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{previous_context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【필수 문체 규칙】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭐⭐⭐ 핵심 규칙 ⭐⭐⭐
나레이션 90~95%
대사 5~10%
500-1000자마다 대사 1회 정도
대사 없는 긴 나레이션 장면이 많아야 함

1. 화자
- 전지적 3인칭 단일 내레이터
- "그는", "그녀는", "이름은" 사용
- 절대 "나는", "내가" 금지

2. 대사 최소화 ⭐⭐⭐
대사는 정말 중요한 순간에만:
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

4. 나레이션 전개 방식

【시공간 설정부터】
"비 오는 밤", "한편 그 시각", "며칠이 지난 어느 오후"

【행동 + 감각】
"~를 느끼며", "~를 바라보며", "~를 듣고"

【내면은 나레이션으로】
대사 아닌 혼잣말, 생각, 동기를 나레이션으로 전환

예시:
"제발 버텨줘. 민서는 속으로 빌었습니다."
"할머니 병원비를 내야 했어요."

【"한편"으로 인물 교차】
두 인물의 시점을 번갈아 보여주며 충돌 예고

【과거 자연스럽게 삽입】
"~년 전", "그때", "그날"

【템포 조절】
느린 장면: 디테일, 감각 묘사, 긴 문장 (감정, 회상)
빠른 장면: 핵심만, 짧은 문장 (전환, 충격)

5. 감정 표현
감정을 직접 말하지 말고 신체 반응으로만:

"슬펐다" (X) → "눈물이 흘렀다" (O)
"화났다" (X) → "주먹을 쥐었다" (O)
"놀랐다" (X) → "심장이 멎는 듯했다" (O)
"의심했다" (X) → "눈을 가늘게 떴다" (O)
"행복했다" (X) → "미소가 번졌다" (O)

6. 오디오 중심
시각 의존 최소화, 소리로 전달

의성어: "똑똑", "쿵", "끼익", "쏴아"
목소리: "떨리는 목소리로", "조용히", "크게", "숨을 몰아쉬며"
침묵: "아무 말도 하지 않았다", "침묵만 흘렀다", "고요했습니다"

7. 장면 전환
장면이 바뀔 때 명확한 신호:

시간: "그날 밤", "며칠 후", "다음날 아침"
공간: "한편", "~로 향했다", "~에 도착했습니다"
회상: "30년 전, ~였습니다", "그때를 떠올렸어요"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【절대 금지 사항 (Core Forbidden)】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{core_forbidden}

⚠️ 위 금지 사항 위반 시 전체 대본 재작성입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【루프 방지 규칙】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 동일 대사 2회 이상 반복 금지
2. 동일 상황 반복 금지 (예: 계속 고민만 하는 장면)
3. 스토리는 반드시 앞으로 진행해야 함
4. 500자마다 새로운 정보/사건/감정 변화 필수
5. 중국어 단어 사용 절대 금지
6. 영어 단어는 최소화 (50-80대가 모르는 단어 금지)

⚠️ 중국어가 섞이면 즉시 작성 중단하고 다시 시작하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【출력 형식】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 순수 텍스트만 출력하세요
- {word_count_start:,}~{word_count_end:,}자 분량
- JSON 출력 금지
- 코드블록 금지
- 설명 금지
- 중국어 금지
- 대본 텍스트만 출력

{ending_note}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【마지막 체크리스트】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작성 전 확인:
✓ 일관성 기준점(consistency_anchors) 숙지
✓ 현재 Part의 지배 감정({current_emotion}) 확인
✓ 캐릭터 핵심 목표 확인
✓ Must Include / Must Resolve 항목 확인
✓ 상징의 의미 확인

작성 중 확인:
✓ 대사 비율 5~10% 유지
✓ 500자마다 스토리 진행
✓ 중국어 혼입 없음
✓ 동일 대사/상황 반복 없음

작성 후 확인:
✓ 지배 감정({current_emotion})이 Part 전체를 관통했는가?
✓ Must Resolve 항목 모두 해결했는가?
✓ Open Threads는 남겨두었는가?
✓ Ending Hook으로 다음 Part에 대한 기대감을 심었는가?

지금 바로 Part {part_number} 대본을 작성하세요.
"""


def generate_part_v3_prompt(
    part_number: int,
    outline_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Part V3 프롬프트를 생성합니다. (안정화 로직 강화)

    Args:
        part_number (int): Part 번호 (1-4)
        outline_data (dict): outline_v2_final.json 데이터 (validate_outline 통과한 것)
        context (dict, optional): 이전 Part의 context (Part 2-4에서 사용)

    Returns:
        str: 완성된 프롬프트
    """
    # 1. Outline 데이터 안전하게 가져오기 (기본값 설정)
    meta = outline_data.get("meta", {})
    title = meta.get("title", "제목 없음")
    genre = meta.get("genre", "가족드라마")
    tone = meta.get("tone", "따뜻함")
    target_emotion = meta.get("target_emotion", "감동")

    # 2. Consistency anchors
    consistency_anchors = outline_data.get("consistency_anchors", [
        "캐릭터의 핵심 목표는 끝까지 동일해야 합니다",
        "상징적 오브젝트의 의미는 일관되어야 합니다",
        "감정선의 방향은 고정됩니다",
        "장르와 톤은 전 파트에서 동일합니다"
    ])
    anchors_text = "\n".join([f"{i+1}. {anchor}" for i, anchor in enumerate(consistency_anchors)])

    # 3. Global conflict arc
    global_conflict_arc = outline_data.get("global_conflict_arc", {})
    arc_stages = ["start", "rise", "peak", "fall", "end"]
    arc_text = "\n".join([
        f"{stage.upper()}: {global_conflict_arc.get(stage, '')}"
        for stage in arc_stages
    ])

    # Part별 갈등 단계 매핑
    arc_stage_map = {
        1: f"START → RISE (발단~갈등 시작)\n현재: {global_conflict_arc.get('start', '')}",
        2: f"RISE (갈등 심화)\n현재: {global_conflict_arc.get('rise', '')}",
        3: f"PEAK → FALL (절정~해소 시작)\n현재: {global_conflict_arc.get('peak', '')}",
        4: f"FALL → END (해소~완결)\n현재: {global_conflict_arc.get('end', '')}"
    }
    current_arc_stage = arc_stage_map.get(part_number, "")

    # 4. Emotional anchors
    emotional_anchors = outline_data.get("emotional_anchors", [
        "Part 1: 그리움",
        "Part 2: 혼란",
        "Part 3: 절정",
        "Part 4: 평온"
    ])
    anchors_emotion_text = "\n".join([f"- {anchor}" for anchor in emotional_anchors])
    current_emotion = emotional_anchors[part_number - 1] if part_number <= len(emotional_anchors) else "감정"

    # 5. Characters
    characters = outline_data.get("characters", [])
    characters_text = ""
    for char in characters:
        char_text = f"""
[{char.get('name', '인물')}]
- 나이: {char.get('age', 65)}세
- 역할: {char.get('role', '역할')}
- 핵심 목표: {char.get('key_motivation', '목표')} ⚠️ (전 파트 동일)
- 감정 여정: {char.get('emotional_arc', {}).get('start', '시작')} → {char.get('emotional_arc', {}).get('journey', '변화')} → {char.get('emotional_arc', {}).get('end', '종료')}
- 목소리: {char.get('voice_type', 'elderly_female')}
"""
        characters_text += char_text

    # 6. Part breakdown (안전하게 가져오기)
    part_breakdown = outline_data.get("part_breakdown", [])
    current_part = None
    for part in part_breakdown:
        if part.get("part") == part_number:
            current_part = part
            break

    # Part를 찾지 못하면 기본값 생성
    if not current_part:
        current_part = {
            "part": part_number,
            "title": f"Part {part_number}",
            "time_range_minutes": [(part_number-1)*30, part_number*30],
            "word_count_range": [12000, 13000],
            "primary_goal": "목표",
            "conflict_intensity": 5,
            "must_include": [],
            "must_avoid": [],
            "must_resolve": [],
            "open_threads": [],
            "ending_hook": "",
            "key_revelations": []
        }

    part_title = current_part.get("title", f"Part {part_number}")
    part_goal = current_part.get("primary_goal", "목표")

    # time_range_minutes와 word_count_range 안전하게 추출
    time_range = current_part.get("time_range_minutes", [(part_number-1)*30, part_number*30])
    if isinstance(time_range, list) and len(time_range) >= 2:
        time_range_start = time_range[0]
        time_range_end = time_range[1]
    else:
        time_range_start = (part_number-1)*30
        time_range_end = part_number*30

    word_count_range = current_part.get("word_count_range", [12000, 13000])
    if isinstance(word_count_range, list) and len(word_count_range) >= 2:
        word_count_start = word_count_range[0]
        word_count_end = word_count_range[1]
    else:
        word_count_start = 12000
        word_count_end = 13000

    conflict_intensity = current_part.get("conflict_intensity", 5)

    # Must include/avoid/resolve 안전하게 추출
    must_include = "\n".join([f"✓ {item}" for item in current_part.get("must_include", [])])
    must_avoid = "\n".join([f"✗ {item}" for item in current_part.get("must_avoid", [])])
    must_resolve = "\n".join([f"→ {item}" for item in current_part.get("must_resolve", [])])
    open_threads = "\n".join([f"⇢ {item}" for item in current_part.get("open_threads", [])])
    key_revelations = "\n".join([f"⚡ {item}" for item in current_part.get("key_revelations", [])])
    ending_hook = current_part.get("ending_hook", "")

    # 7. Thematic threads
    thematic_threads = outline_data.get("thematic_threads", {})
    main_theme = thematic_threads.get("main_theme", "가족의 의미")
    symbolic_objects = thematic_threads.get("symbolic_objects", {})
    symbolic_text = "\n".join([f"- {obj}: {meaning}" for obj, meaning in symbolic_objects.items()])

    # 8. Narrative rules
    narrative_rules = outline_data.get("narrative_rules", {})
    core_forbidden = narrative_rules.get("core_forbidden", FORBIDDEN_ELEMENTS)
    forbidden_text = "\n".join([f"✗ {item}" for item in core_forbidden])

    # 9. Climax dialogue rule
    climax_dialogue_rule = ""
    if part_number == 3:
        climax_dialogue_rule = "\n\n클라이맥스에서만 예외적으로 대사 25-30자 허용합니다."

    # 10. Ending note (Part 4만)
    ending_note = ""
    if part_number == 4:
        ending_note = """
※ 마지막 구독 유도 멘트는 자동으로 추가되므로 작성하지 마세요:
"오늘의 이야기가 당신의 마음에 작은 울림을 드렸다면 구독과 좋아요를 눌러주세요. 당신의 오늘을 늘 응원합니다."
"""

    # 11. Previous context (Part 2-4)
    previous_context = ""
    if context and part_number > 1:
        # Context 필드 안전하게 추출
        summary = context.get('summary', '')
        resolved_points = context.get('resolved_points', [])
        open_threads_ctx = context.get('open_threads', [])
        next_must_address = context.get('next_must_address', [])
        ending_sentence = context.get('ending_sentence', '')

        previous_context = f"""
【이전 Part 요약】

{summary if summary else '(요약 없음)'}

【해결된 문제】
{chr(10).join(['✓ ' + item for item in resolved_points]) if resolved_points else '(없음)'}

【이어받은 미해결 요소】
{chr(10).join(['⇢ ' + item for item in open_threads_ctx]) if open_threads_ctx else '(없음)'}

【이 Part에서 다뤄야 할 것】
{chr(10).join(['→ ' + item for item in next_must_address]) if next_must_address else '(없음)'}

【이전 Part 마지막 문장】
"{ending_sentence if ending_sentence else '(없음)'}"

⚠️ 위 문장에서 자연스럽게 이어지도록 시작하세요.
"""
    else:
        previous_context = """
【시작 지점】

이 Part는 전체 드라마의 시작입니다.
Hook(180초 예고편) 직후 본편이 시작되는 것으로 자연스럽게 이어지세요.
"""

    # 12. 프롬프트 조립
    prompt = PART_PROMPT_V3.format(
        part_number=part_number,
        part_title=part_title,
        title=title,
        genre=genre,
        tone=tone,
        target_emotion=target_emotion,
        consistency_anchors=anchors_text,
        global_conflict_arc=arc_text,
        current_arc_stage=current_arc_stage,
        emotional_anchors=anchors_emotion_text,
        current_emotion=current_emotion,
        characters=characters_text,
        part_goal=part_goal,
        time_range_minutes_start=time_range_start,
        time_range_minutes_end=time_range_end,
        word_count_start=word_count_start,
        word_count_end=word_count_end,
        conflict_intensity=conflict_intensity,
        must_include=must_include if must_include else "(없음)",
        must_avoid=must_avoid if must_avoid else "(없음)",
        must_resolve=must_resolve if must_resolve else "(없음)",
        open_threads=open_threads if open_threads else "(없음)",
        key_revelations=key_revelations if key_revelations else "(없음)",
        ending_hook=ending_hook if ending_hook else "(없음)",
        main_theme=main_theme,
        symbolic_objects=symbolic_text if symbolic_text else "(없음)",
        previous_context=previous_context,
        climax_dialogue_rule=climax_dialogue_rule,
        core_forbidden=forbidden_text,
        ending_note=ending_note
    )

    return prompt


def validate_part_text(part_text: str, part_number: int) -> tuple:
    """
    생성된 Part 텍스트의 품질을 검증합니다.

    Args:
        part_text (str): 생성된 Part 텍스트
        part_number (int): Part 번호

    Returns:
        tuple: (is_valid: bool, warnings: list, stats: dict)
    """
    warnings = []
    stats = {}

    # 1. 대사 비율 체크
    dialogue_count = part_text.count('"')
    total_chars = len(part_text)
    dialogue_ratio = (dialogue_count / total_chars * 100) if total_chars > 0 else 0
    stats['dialogue_ratio'] = dialogue_ratio

    if dialogue_ratio > 15:
        warnings.append(f"대사 비율이 {dialogue_ratio:.1f}%로 너무 높습니다 (권장: 5-10%)")

    # 2. 중국어 체크
    chinese_chars = sum(1 for c in part_text if '\u4e00' <= c <= '\u9fff')
    stats['chinese_chars'] = chinese_chars

    if chinese_chars > 0:
        warnings.append(f"중국어 문자 {chinese_chars}개 발견")

    # 3. 반복 체크 (동일 문장 2회 이상)
    sentences = re.split(r'[\.?!]\s+', part_text)
    unique_sentences = len(set(sentences))
    total_sentences = len(sentences)
    repetition_ratio = (1 - unique_sentences / total_sentences) * 100 if total_sentences > 0 else 0
    stats['repetition_ratio'] = repetition_ratio

    if repetition_ratio > 10:
        warnings.append(f"반복률이 {repetition_ratio:.1f}%로 높습니다 (권장: 10% 이하)")

    # 4. 길이 체크
    stats['length'] = total_chars
    target_min = 12000 if part_number < 4 else 11500
    target_max = 13000 if part_number < 4 else 12500

    if total_chars < target_min:
        warnings.append(f"분량이 {total_chars}자로 부족합니다 (최소: {target_min}자)")
    elif total_chars > target_max * 1.2:
        warnings.append(f"분량이 {total_chars}자로 너무 깁니다 (최대: {target_max}자)")

    # 5. 영어 단어 과다 사용 체크
    english_words = re.findall(r'[A-Za-z]{3,}', part_text)
    stats['english_words'] = len(english_words)

    if len(english_words) > 10:
        warnings.append(f"영어 단어가 {len(english_words)}개 사용되었습니다")

    # 검증 통과 여부
    is_valid = chinese_chars == 0 and dialogue_ratio <= 15 and repetition_ratio <= 15

    return is_valid, warnings, stats
