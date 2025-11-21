"""
Part V3 단독 테스트 스크립트
outline_v2_final + part_v3 + context_generator 통합 테스트
"""

import json
from pathlib import Path
from prompts.outline_v2_final import generate_outline_prompt
from prompts.part_v3 import generate_part_v3_prompt
from pipeline.llm import get_llm_engine
from utils.file_utils import save_json, save_text
from utils.logger import setup_logger
from utils.context_generator import create_part_context


def test_part_v3(title: str, output_dir: str = "./test_output") -> None:
    """
    Outline → Part 1~4 → Context 전체 흐름 테스트

    Args:
        title (str): 드라마 제목
        output_dir (str): 출력 디렉토리
    """
    logger = setup_logger(name="test_part_v3", level="INFO")

    logger.info("=" * 60)
    logger.info(f"Part V3 Test Started: {title}")
    logger.info("=" * 60)

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 1: Outline 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("[Step 1] Generating outline...")
        llm = get_llm_engine(config_path="config.yaml")

        outline_prompt = generate_outline_prompt(title)
        outline_data = llm.call_llm(outline_prompt, phase="outline")

        outline_file = output_path / f"outline_{title.replace(' ', '_')}.json"
        save_json(outline_data, str(outline_file))

        logger.info(f"✓ Outline generated: {outline_file}")
        logger.info(f"  Characters: {len(outline_data.get('characters', []))}")
        logger.info(f"  Parts: {len(outline_data.get('part_breakdown', []))}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 2: Parts 1-4 순차 생성 + Context
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n[Step 2] Generating Parts 1-4 sequentially...")

        parts_text = []
        current_context = None

        for part_num in range(1, 5):
            logger.info(f"\n--- Part {part_num} ---")

            # Part V3 프롬프트 생성
            part_prompt = generate_part_v3_prompt(
                part_number=part_num,
                outline_data=outline_data,
                context=current_context
            )

            # 프롬프트 저장 (디버깅용)
            prompt_file = output_path / f"part{part_num}_prompt.txt"
            save_text(part_prompt, str(prompt_file))
            logger.info(f"  Prompt saved: {prompt_file}")
            logger.info(f"  Prompt length: {len(part_prompt)} chars")

            # LLM 호출
            logger.info(f"  Calling LLM for Part {part_num}...")
            part_text = llm.call_llm_text(part_prompt, "parts")
            parts_text.append(part_text)

            # Part 저장
            part_file = output_path / f"part{part_num}.txt"
            save_text(part_text, str(part_file))
            logger.info(f"✓ Part {part_num} completed: {len(part_text)} chars")
            logger.info(f"  Saved: {part_file}")

            # Part 1-3은 Context 생성
            if part_num < 4:
                logger.info(f"  Creating context for Part {part_num + 1}...")
                current_context = create_part_context(
                    part_text=part_text,
                    part_number=part_num,
                    outline_data=outline_data
                )

                # Context 저장
                context_file = output_path / f"part{part_num}_context.json"
                save_json(current_context, str(context_file))
                logger.info(f"  Context saved: {context_file}")
                logger.info(f"  Summary length: {len(current_context.get('summary', ''))} chars")
                logger.info(f"  Open threads: {len(current_context.get('open_threads', []))}")
                logger.info(f"  Ending sentence: {current_context.get('ending_sentence', '')[:50]}...")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 3: 전체 병합
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n[Step 3] Merging all parts...")
        main_full = "\n\n".join(parts_text)
        main_file = output_path / f"main_full_{title.replace(' ', '_')}.txt"
        save_text(main_full, str(main_file))

        logger.info("=" * 60)
        logger.info("✓ Test completed successfully!")
        logger.info(f"  Total length: {len(main_full)} chars")
        logger.info(f"  Output dir: {output_path}")
        logger.info("=" * 60)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 4: 검증
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("\n[Validation]")
        validate_parts(parts_text, logger)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


def validate_parts(parts_text: list, logger) -> None:
    """
    생성된 Part들의 품질을 검증합니다.

    Args:
        parts_text (list): Part 텍스트 리스트
        logger: 로거
    """
    for i, part in enumerate(parts_text, 1):
        logger.info(f"\nPart {i}:")
        logger.info(f"  Length: {len(part):,} chars")

        # 대사 비율 체크 (간단한 추정)
        dialogue_count = part.count('"')
        total_chars = len(part)
        dialogue_ratio = (dialogue_count / total_chars * 100) if total_chars > 0 else 0

        logger.info(f"  Dialogue ratio (est): {dialogue_ratio:.1f}%")

        if dialogue_ratio > 15:
            logger.warning(f"  ⚠ High dialogue ratio in Part {i}")
        else:
            logger.info(f"  ✓ Dialogue ratio OK")

        # 중국어 체크
        chinese_chars = sum(1 for c in part if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > 0:
            logger.warning(f"  ⚠ Chinese characters detected: {chinese_chars} chars")
        else:
            logger.info(f"  ✓ No Chinese characters")

        # 반복 체크 (간단한 추정: 동일 문장 2회 이상)
        sentences = part.split('.')
        unique_sentences = len(set(sentences))
        total_sentences = len(sentences)
        repetition_ratio = (1 - unique_sentences / total_sentences) * 100 if total_sentences > 0 else 0

        logger.info(f"  Repetition ratio: {repetition_ratio:.1f}%")
        if repetition_ratio > 10:
            logger.warning(f"  ⚠ High repetition in Part {i}")
        else:
            logger.info(f"  ✓ Repetition OK")


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Part V3 Integration Test Script")
    print("outline_v2_final + part_v3 + context_generator")
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
    print(f"✓ '{title}' 전체 흐름 테스트를 시작합니다...")
    print(f"  Outline → Part 1 → Part 2 → Part 3 → Part 4")
    print(f"  예상 소요 시간: 약 5-10분 (72B 모델 기준)")
    print()

    try:
        test_part_v3(title)
        print()
        print("✓ 테스트 완료!")
        print(f"  결과: ./test_output/")
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        sys.exit(1)
