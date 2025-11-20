"""
AutoDrama - Phase 1-7 테스트 스크립트
LLM부터 이미지 프롬프트 생성까지만 테스트 (TTS/이미지 생성/영상 제외)
"""

import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

# 프롬프트 모듈
from prompts.outline import generate_outline_prompt
from prompts.hook import generate_hook_prompt
from prompts.part import generate_part_prompt
from prompts.hook_images import generate_hook_images_prompt
from prompts.main_images import generate_main_images_prompt

# 파이프라인 모듈
from pipeline.llm import get_llm_engine

# 유틸리티
from utils.file_utils import (
    save_json, load_json,
    save_text, load_text,
    create_output_dirs
)
from utils.logger import setup_logger, PhaseLogger


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """설정 파일 로드"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_phase1_7(title: str) -> None:
    """
    Phase 1-7 테스트 실행

    Args:
        title: 드라마 제목
    """
    config = load_config()

    # 로거 설정
    logger = setup_logger(
        log_file=config["logging"]["file"],
        level=config["logging"]["level"]
    )
    phase_logger = PhaseLogger(logger)

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"AutoDrama Phase 1-7 Test Started: {title}")
    logger.info("=" * 60)

    # 출력 디렉토리 생성
    dirs = create_output_dirs(title, config["output"]["base_dir"])
    logger.info(f"Output directory: {dirs['base']}")

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 1: Outline 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(1, "Outline Generation")

        llm = get_llm_engine(config_path="config.yaml")

        outline_prompt = generate_outline_prompt(title)
        outline_data = llm.call_llm(outline_prompt, phase="outline")
        save_json(outline_data, f"{dirs['base']}/outline.json")

        phase_logger.info(f"✓ Outline generated: {len(outline_data.get('outline_full', ''))} chars")
        phase_logger.info(f"  File: {dirs['base']}/outline.json")
        phase_logger.end_phase(1, "Outline Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 2: Hook 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(2, "Hook Generation")

        hook_prompt = generate_hook_prompt(title, outline_data["outline_full"])
        hook_text = llm.call_llm_text(hook_prompt, phase="hook")
        save_text(hook_text, f"{dirs['hook']}/hook.txt")

        phase_logger.info(f"✓ Hook generated: {len(hook_text)} chars")
        phase_logger.info(f"  File: {dirs['hook']}/hook.txt")
        phase_logger.end_phase(2, "Hook Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 3: Hook Images Prompts
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(3, "Hook Images Prompts")

        hook_images_prompt = generate_hook_images_prompt(hook_text)
        hook_images_data = llm.call_llm(hook_images_prompt, phase="outline")
        save_json(hook_images_data, f"{dirs['hook']}/image_prompts.json")

        phase_logger.info(f"✓ Hook image prompts: {hook_images_data.get('total_scenes', 0)} scenes")
        phase_logger.info(f"  File: {dirs['hook']}/image_prompts.json")
        phase_logger.end_phase(3, "Hook Images Prompts")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 4-5: Parts 1-4 생성 (순차)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(4, "Parts 1-4 Generation")

        previous_parts = []
        parts_text = []

        # 순차 생성 (각 Part는 이전 Part 요약이 필요)
        for part_num in range(1, 5):
            logger.info(f"  Generating Part {part_num}...")

            part_prompt = generate_part_prompt(
                title,
                outline_data["outline_full"],
                previous_parts if previous_parts else None
            )

            part_text = llm.call_llm_text(part_prompt, "parts")
            parts_text.append(part_text)

            # Part 저장
            save_text(part_text, f"{dirs['main']}/part{part_num}.txt")
            phase_logger.info(f"  ✓ Part {part_num} completed: {len(part_text)} chars")
            phase_logger.info(f"    File: {dirs['main']}/part{part_num}.txt")

            # Part 1-3은 요약 생성 (다음 Part를 위해)
            if part_num < 4:
                summary = part_text[:500] + "..."
                previous_parts.append(summary)

        # Main 전체 병합
        main_full = "\n\n".join(parts_text)
        save_text(main_full, f"{dirs['main']}/main_full.txt")

        phase_logger.info(f"✓ All parts generated: {len(main_full)} chars total")
        phase_logger.info(f"  File: {dirs['main']}/main_full.txt")
        phase_logger.end_phase(4, "Parts 1-4 Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 6: Main Images Prompts
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(5, "Main Images Prompts")

        main_images_prompt = generate_main_images_prompt(
            previous_parts[0] if len(previous_parts) > 0 else "",
            previous_parts[1] if len(previous_parts) > 1 else "",
            previous_parts[2] if len(previous_parts) > 2 else "",
            parts_text[3] if len(parts_text) > 3 else ""
        )
        main_images_data = llm.call_llm(main_images_prompt, phase="outline")
        save_json(main_images_data, f"{dirs['main']}/image_prompts.json")

        phase_logger.info(f"✓ Main image prompts: {main_images_data.get('total_scenes', 0)} scenes")
        phase_logger.info(f"  File: {dirs['main']}/image_prompts.json")
        phase_logger.end_phase(5, "Main Images Prompts")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 완료 및 검증
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds() / 60

        logger.info("=" * 60)
        logger.info("✓ Phase 1-7 Test Completed!")
        logger.info(f"  Total time: {elapsed:.1f} minutes")
        logger.info("=" * 60)

        # 파일 검증
        logger.info("\n📁 Generated Files:")
        expected_files = [
            f"{dirs['base']}/outline.json",
            f"{dirs['hook']}/hook.txt",
            f"{dirs['hook']}/image_prompts.json",
            f"{dirs['main']}/part1.txt",
            f"{dirs['main']}/part2.txt",
            f"{dirs['main']}/part3.txt",
            f"{dirs['main']}/part4.txt",
            f"{dirs['main']}/main_full.txt",
            f"{dirs['main']}/image_prompts.json"
        ]

        all_exists = True
        for file_path in expected_files:
            exists = Path(file_path).exists()
            status = "✓" if exists else "✗"
            size = Path(file_path).stat().st_size if exists else 0
            logger.info(f"  {status} {file_path} ({size:,} bytes)")
            if not exists:
                all_exists = False

        if all_exists:
            logger.info("\n✅ All expected files generated successfully!")
        else:
            logger.warning("\n⚠️ Some files are missing!")

        # JSON 유효성 검증
        logger.info("\n🔍 JSON Validation:")
        json_files = [
            (f"{dirs['base']}/outline.json", "Outline"),
            (f"{dirs['hook']}/image_prompts.json", "Hook Images"),
            (f"{dirs['main']}/image_prompts.json", "Main Images")
        ]

        for json_path, label in json_files:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"  ✓ {label}: Valid JSON")
                if 'total_scenes' in data:
                    logger.info(f"    - Scenes: {data['total_scenes']}")
                if 'scenes' in data:
                    logger.info(f"    - Scene count: {len(data['scenes'])}")
            except Exception as e:
                logger.error(f"  ✗ {label}: Invalid JSON - {e}")

        logger.info("\n" + "=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("AutoDrama - Phase 1-7 Test (LLM + Image Prompts Only)")
    print("=" * 60)
    print()
    print("이 테스트는 다음을 검증합니다:")
    print("  • Phase 1-2: Outline + Hook 생성")
    print("  • Phase 3: Hook 이미지 프롬프트")
    print("  • Phase 4-5: Parts 1-4 생성 + 병합")
    print("  • Phase 6: Main 이미지 프롬프트")
    print()
    print("⚠️  TTS, 이미지 생성, 영상 합성은 실행하지 않습니다.")
    print()

    # 테스트 제목 사용
    title = "세탁기에서 발견된 오래된 반지"

    print(f"✓ 테스트 제목: '{title}'")
    print(f"  예상 소요 시간: 약 5-10분 (LLM 호출만)")
    print()

    try:
        test_phase1_7(title)
        print()
        print("✅ 테스트 완료! 출력 파일을 확인하세요.")
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        exit(1)
