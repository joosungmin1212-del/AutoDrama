"""
Part 간 연결을 위한 Context Generator (안정화 로직 강화)
"""

from typing import Dict, Any, List
import re


def create_part_context(
    part_text: str,
    part_number: int,
    outline_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Part 대본에서 다음 Part로 전달할 context를 생성합니다. (안정화 버전)

    Args:
        part_text (str): 현재 Part의 대본 텍스트
        part_number (int): 현재 Part 번호 (1-3, Part 4는 context 생성 불필요)
        outline_data (dict): outline_v2_final.json 데이터

    Returns:
        dict: 다음 Part로 전달할 context
    """
    # Part breakdown에서 현재 Part와 다음 Part 정보 가져오기
    part_breakdown = outline_data.get("part_breakdown", [])
    current_part = None
    next_part = None

    for part in part_breakdown:
        if part.get("part") == part_number:
            current_part = part
        if part.get("part") == part_number + 1:
            next_part = part

    # 기본값 설정 (안전장치)
    if not current_part:
        current_part = {
            "must_resolve": [],
            "open_threads": []
        }

    if not next_part:
        next_part = {
            "must_include": []
        }

    # 1. Summary: 대본 요약 (300-350자)
    summary = _extract_summary(part_text, max_length=350)

    # 2. Character updates: 캐릭터별 현재 상태
    characters = outline_data.get("characters", [])
    character_updates = _extract_character_updates(part_text, characters, part_number)

    # 3. Open threads: 현재 Part의 open_threads + 자동 감지
    open_threads = current_part.get("open_threads", [])
    auto_detected_threads = _detect_open_threads(part_text)
    open_threads = list(set(open_threads + auto_detected_threads))[:5]  # 최대 5개

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


def _extract_summary(text: str, max_length: int = 350) -> str:
    """
    대본에서 핵심 요약을 추출합니다.

    Args:
        text (str): 대본 텍스트
        max_length (int): 최대 길이

    Returns:
        str: 요약 텍스트
    """
    if not text or len(text) < 100:
        return "요약 없음"

    # 앞부분 500자를 가져와서 요약 생성
    preview = text[:600]

    # 문장 단위로 자르기
    sentences = re.split(r'[\.?!]\s+', preview)

    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 2 > max_length:
            break
        if sentence.strip():
            summary += sentence.strip() + ". "

    # 최소 길이 보장
    if len(summary) < 50:
        summary = text[:max_length].strip() + "..."

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
        if not name or name == "주인공":
            continue

        # 캐릭터 이름이 대본에 등장하는지 확인
        if name in text:
            # 감정 여정 기반 상태 추정
            emotional_arc = char.get("emotional_arc", {})
            journey = emotional_arc.get("journey", "")

            # Part별 감정 단계 추정
            if part_number == 1:
                status = emotional_arc.get('start', '초기 상태')
            elif part_number == 2:
                stages = journey.split(" → ") if journey else []
                status = stages[1] if len(stages) > 1 else "갈등 중"
            elif part_number == 3:
                stages = journey.split(" → ") if journey else []
                status = stages[-1] if stages else "전환점"
            else:
                status = emotional_arc.get('end', '최종 상태')

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
    if not text or len(text) < 10:
        return ""

    # 마지막 300자에서 마지막 문장 추출
    tail = text[-300:].strip()

    # 마지막 마침표/물음표/느낌표 찾기
    match = re.search(r'([^\.?!]{10,}[\.?!])\s*$', tail)

    if match:
        return match.group(1).strip()
    else:
        # 매칭 실패 시 마지막 100자 반환
        return tail[-100:].strip()


def _detect_open_threads(text: str) -> List[str]:
    """
    대본에서 미해결 요소를 자동으로 감지합니다.

    Args:
        text (str): 대본 텍스트

    Returns:
        list: 감지된 미해결 요소 리스트
    """
    threads = []

    # 질문 패턴 감지
    questions = re.findall(r'[가-힣\s]{5,30}\?', text)
    if questions:
        # 마지막 2개 질문 추가
        for q in questions[-2:]:
            threads.append(q.strip())

    # "왜", "어떻게" 등의 패턴 감지
    uncertainty_patterns = [
        r'(왜\s+[가-힣]{2,10})',
        r'(어떻게\s+[가-힣]{2,10})',
        r'([가-힣]{2,10}\s+수\s+있을까)',
    ]

    for pattern in uncertainty_patterns:
        matches = re.findall(pattern, text)
        threads.extend([m.strip() for m in matches[:1]])  # 각 패턴당 1개만

    return threads[:3]  # 최대 3개


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

    # summary는 반드시 값이 있어야 함
    if not context.get("summary"):
        return False

    return True


def sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context의 필드를 정리하고 안전하게 만듭니다.

    Args:
        context (dict): Context 데이터

    Returns:
        dict: 정리된 Context
    """
    sanitized = {
        "summary": context.get("summary", "요약 없음"),
        "character_updates": context.get("character_updates", {}),
        "open_threads": context.get("open_threads", [])[:5],  # 최대 5개
        "resolved_points": context.get("resolved_points", [])[:5],
        "next_must_address": context.get("next_must_address", [])[:5],
        "ending_sentence": context.get("ending_sentence", "")
    }

    # 빈 리스트나 딕셔너리를 기본값으로 보장
    if not isinstance(sanitized["character_updates"], dict):
        sanitized["character_updates"] = {}

    for key in ["open_threads", "resolved_points", "next_must_address"]:
        if not isinstance(sanitized[key], list):
            sanitized[key] = []

    return sanitized
