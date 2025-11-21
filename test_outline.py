"""
Outline 단독 테스트 스크립트
outline_v2_final.py 테스트용
"""

import json
from pathlib import Path
from prompts.outline_v2_final import generate_outline_prompt
from pipeline.llm import get_llm_engine
from utils.file_utils import save_json
from utils.logger import setup_logger


def test_outline(title: str, output_dir: str = "./test_output") -> dict:
    """
    Outline만 단독으로 생성하고 테스트합니다.

    Args:
        title (str): 드라마 제목
        output_dir (str): 출력 디렉토리

    Returns:
        dict: 생성된 outline JSON
    """
    # 로거 설정
    logger = setup_logger(name="test_outline", level="INFO")

    logger.info("=" * 60)
    logger.info(f"Outline Test Started: {title}")
    logger.info("=" * 60)

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # LLM 엔진 로드
        logger.info("Loading LLM engine...")
        llm = get_llm_engine(config_path="config.yaml")

        # Outline 프롬프트 생성
        logger.info("Generating outline prompt...")
        outline_prompt = generate_outline_prompt(title)

        logger.info(f"Prompt length: {len(outline_prompt)} chars")
        logger.info("Calling LLM...")

        # LLM 호출
        outline_data = llm.call_llm(outline_prompt, phase="outline")

        # 결과 저장
        output_file = output_path / f"outline_{title.replace(' ', '_')}.json"
        save_json(outline_data, str(output_file))

        logger.info("=" * 60)
        logger.info("✓ Outline generated successfully!")
        logger.info(f"  Output: {output_file}")
        logger.info(f"  Title: {outline_data.get('meta', {}).get('title', 'N/A')}")
        logger.info(f"  Genre: {outline_data.get('meta', {}).get('genre', 'N/A')}")
        logger.info(f"  Characters: {len(outline_data.get('characters', []))}")
        logger.info(f"  Key Scenes: {len(outline_data.get('key_scenes', []))}")
        logger.info(f"  Parts: {len(outline_data.get('part_breakdown', []))}")
        logger.info(f"  Outline length: {len(outline_data.get('outline_full', ''))} chars")
        logger.info("=" * 60)

        # 검증
        logger.info("\n[Validation]")
        validate_outline(outline_data, logger)

        return outline_data

    except Exception as e:
        logger.error(f"Outline test failed: {e}", exc_info=True)
        raise


def validate_outline(outline_data: dict, logger) -> None:
    """
    Outline JSON의 필수 필드를 검증합니다.

    Args:
        outline_data (dict): Outline JSON
        logger: 로거
    """
    required_fields = [
        "meta",
        "consistency_anchors",
        "global_conflict_arc",
        "emotional_anchors",
        "characters",
        "story_spine",
        "key_scenes",
        "thematic_threads",
        "narrative_rules",
        "part_breakdown",
        "outline_full"
    ]

    missing_fields = []
    for field in required_fields:
        if field not in outline_data:
            missing_fields.append(field)

    if missing_fields:
        logger.warning(f"  ⚠ Missing fields: {', '.join(missing_fields)}")
    else:
        logger.info("  ✓ All required fields present")

    # consistency_anchors 검증
    if "consistency_anchors" in outline_data:
        anchors = outline_data["consistency_anchors"]
        if len(anchors) == 4:
            logger.info(f"  ✓ Consistency anchors: {len(anchors)} items")
        else:
            logger.warning(f"  ⚠ Consistency anchors should be 4 items, got {len(anchors)}")

    # global_conflict_arc 검증
    if "global_conflict_arc" in outline_data:
        arc = outline_data["global_conflict_arc"]
        required_arc_keys = ["start", "rise", "peak", "fall", "end"]
        missing_arc = [k for k in required_arc_keys if k not in arc]
        if not missing_arc:
            logger.info(f"  ✓ Global conflict arc complete")
        else:
            logger.warning(f"  ⚠ Missing arc keys: {', '.join(missing_arc)}")

    # emotional_anchors 검증
    if "emotional_anchors" in outline_data:
        anchors = outline_data["emotional_anchors"]
        if len(anchors) == 4:
            logger.info(f"  ✓ Emotional anchors: {len(anchors)} items (Part 1-4)")
        else:
            logger.warning(f"  ⚠ Emotional anchors should be 4 items, got {len(anchors)}")

    # part_breakdown 검증
    if "part_breakdown" in outline_data:
        parts = outline_data["part_breakdown"]
        if len(parts) == 4:
            logger.info(f"  ✓ Part breakdown: {len(parts)} parts")

            for i, part in enumerate(parts, 1):
                required_part_fields = [
                    "part", "title", "time_range_minutes", "word_count_range",
                    "primary_goal", "conflict_intensity", "must_include",
                    "must_avoid", "must_resolve", "open_threads",
                    "ending_hook", "key_revelations", "bridge_to_next"
                ]

                missing_part_fields = [f for f in required_part_fields if f not in part]
                if missing_part_fields:
                    logger.warning(f"    ⚠ Part {i} missing: {', '.join(missing_part_fields)}")
                else:
                    # word_count_range 타입 검증
                    if isinstance(part.get("word_count_range"), list):
                        logger.info(f"    ✓ Part {i}: word_count_range is array")
                    else:
                        logger.warning(f"    ⚠ Part {i}: word_count_range is not array")

                    # time_range_minutes 타입 검증
                    if isinstance(part.get("time_range_minutes"), list):
                        logger.info(f"    ✓ Part {i}: time_range_minutes is array")
                    else:
                        logger.warning(f"    ⚠ Part {i}: time_range_minutes is not array")
        else:
            logger.warning(f"  ⚠ Part breakdown should be 4 parts, got {len(parts)}")


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Outline V2 Final Test Script")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        title = " ".join(sys.argv[1:])
    else:
        title = input("제목을 입력하세요: ").strip()

    if not title:
        print("❌ 제목을 입력해주세요.")
        sys.exit(1)

    print()
    print(f"✓ '{title}' Outline 생성을 시작합니다...")
    print()

    try:
        outline_data = test_outline(title)
        print()
        print("✓ 테스트 완료!")
        print(f"  결과: ./test_output/outline_{title.replace(' ', '_')}.json")
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        sys.exit(1)
