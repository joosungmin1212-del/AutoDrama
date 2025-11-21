"""
Part 간 연결을 위한 Context Generator
"""

from typing import Dict, Any, List
import re


def create_part_context(
    part_text: str,
    part_number: int,
    outline_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Part 대본에서 다음 Part로 전달할 context를 생성합니다.

    Args:
        part_text (str): 현재 Part의 대본 텍스트
        part_number (int): 현재 Part 번호 (1-3, Part 4는 context 생성 불필요)
        outline_data (dict): outline_v2_final.json 데이터

    Returns:
        dict: 다음 Part로 전달할 context

    Context 구조:
        {
            "summary": "300자 핵심 요약",
            "character_updates": {},
            "open_threads": [],
            "resolved_points": [],
            "next_must_address": [],
            "ending_sentence": "마지막 문장"
        }
    """
    # Part breakdown에서 현재 Part 정보 가져오기
    part_breakdown = outline_data.get("part_breakdown", [])
    current_part = None
    next_part = None

    for part in part_breakdown:
        if part.get("part") == part_number:
            current_part = part
        if part.get("part") == part_number + 1:
            next_part = part

    if not current_part:
        raise ValueError(f"Part {part_number} not found in part_breakdown")

    if not next_part:
        raise ValueError(f"Part {part_number + 1} not found in part_breakdown")

    # 1. Summary: 대본 앞부분 300자 추출
    summary = _extract_summary(part_text, max_length=300)

    # 2. Character updates: 캐릭터별 현재 상태 (간략)
    characters = outline_data.get("characters", [])
    character_updates = _extract_character_updates(part_text, characters, part_number)

    # 3. Open threads: 현재 Part의 open_threads 그대로 전달
    open_threads = current_part.get("open_threads", [])

    # 4. Resolved points: 현재 Part의 must_resolve 항목
    resolved_points = current_part.get("must_resolve", [])

    # 5. Next must address: 다음 Part의 must_include 항목
    next_must_address = next_part.get("must_include", [])

    # 6. Ending sentence: 대본의 마지막 문장 추출
    ending_sentence = _extract_ending_sentence(part_text)

    context = {
        "summary": summary,
        "character_updates": character_updates,
        "open_threads": open_threads,
        "resolved_points": resolved_points,
        "next_must_address": next_must_address,
        "ending_sentence": ending_sentence
    }

    return context


def _extract_summary(text: str, max_length: int = 300) -> str:
    """
    대본에서 핵심 요약을 추출합니다.

    Args:
        text (str): 대본 텍스트
        max_length (int): 최대 길이

    Returns:
        str: 요약 텍스트
    """
    # 앞부분 500자를 가져와서 300자로 자르기
    preview = text[:500]

    # 문장 단위로 자르기 (마침표, 물음표, 느낌표 기준)
    sentences = re.split(r'[\.?!]\s+', preview)

    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 1 > max_length:
            break
        summary += sentence + ". "

    return summary.strip()


def _extract_character_updates(
    text: str,
    characters: List[Dict[str, Any]],
    part_number: int
) -> Dict[str, str]:
    """
    캐릭터별 현재 상태를 추출합니다.

    Args:
        text (str): 대본 텍스트
        characters (list): 캐릭터 리스트
        part_number (int): 현재 Part 번호

    Returns:
        dict: {캐릭터명: 상태 설명}
    """
    updates = {}

    for char in characters:
        name = char.get("name", "")
        if not name:
            continue

        # 캐릭터 이름이 대본에 등장하는지 확인
        if name in text:
            # 감정 여정 기반 상태 추정
            emotional_arc = char.get("emotional_arc", {})
            journey = emotional_arc.get("journey", "")

            # Part별 감정 단계 추정
            if part_number == 1:
                status = f"{emotional_arc.get('start', '초기 상태')}"
            elif part_number == 2:
                # journey에서 중간 단계 추출
                stages = journey.split(" → ")
                if len(stages) > 1:
                    status = stages[1] if len(stages) > 1 else stages[0]
                else:
                    status = "갈등 중"
            elif part_number == 3:
                # journey 끝 단계
                stages = journey.split(" → ")
                status = stages[-1] if stages else "전환점"
            else:
                status = f"{emotional_arc.get('end', '최종 상태')}"

            updates[name] = status

    return updates


def _extract_ending_sentence(text: str) -> str:
    """
    대본의 마지막 문장을 추출합니다.

    Args:
        text (str): 대본 텍스트

    Returns:
        str: 마지막 문장
    """
    # 마지막 200자에서 마지막 문장 추출
    tail = text[-200:].strip()

    # 마지막 마침표/물음표/느낌표 찾기
    match = re.search(r'([^\.?!]+[\.?!])\s*$', tail)

    if match:
        return match.group(1).strip()
    else:
        # 매칭 실패 시 마지막 100자 반환
        return tail[-100:].strip()


def validate_context(context: Dict[str, Any]) -> bool:
    """
    Context의 필수 필드를 검증합니다.

    Args:
        context (dict): Context 데이터

    Returns:
        bool: 검증 통과 여부
    """
    required_fields = [
        "summary",
        "character_updates",
        "open_threads",
        "resolved_points",
        "next_must_address",
        "ending_sentence"
    ]

    for field in required_fields:
        if field not in context:
            return False

        # 빈 값 체크 (ending_sentence 제외)
        if field != "ending_sentence":
            value = context[field]
            if isinstance(value, str) and not value:
                return False
            elif isinstance(value, (list, dict)) and len(value) == 0:
                # open_threads, resolved_points는 비어있을 수 있음
                if field not in ["open_threads", "resolved_points"]:
                    return False

    return True
