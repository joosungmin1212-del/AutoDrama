"""
작당모의 프로젝트 - 메인 파이프라인

제목 입력 → 2시간 한국 드라마 영상 자동 생성
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 프롬프트 모듈
from prompts.outline import generate_outline_prompt
from prompts.hook import generate_hook_prompt
from prompts.part import generate_part_prompt
from prompts.hook_images import generate_hook_images_prompt
from prompts.main_images import generate_main_images_prompt

# 파이프라인 모듈
from pipeline.llm import call_llm
from pipeline.image_gen import generate_images
from pipeline.tts import generate_tts
from pipeline.subtitle import generate_subtitles
from pipeline.video import compile_video

# 유틸리티 모듈
from utils.file_utils import (
    save_json, load_json,
    save_text, load_text,
    create_output_dirs
)
from utils.logger import setup_logger, PhaseLogger


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    설정 파일을 로드합니다.

    Args:
        config_path (str): 설정 파일 경로

    Returns:
        Dict[str, Any]: 설정 딕셔너리
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main(title: str) -> None:
    """
    메인 파이프라인을 실행합니다.

    Args:
        title (str): 드라마 제목
    """
    # 설정 로드
    config = load_config()

    # 로거 설정
    logger = setup_logger(
        log_file=config["logging"]["file"],
        level=config["logging"]["level"]
    )
    phase_logger = PhaseLogger(logger)

    # 시작 시간
    start_time = datetime.now()
    logger.info("=" * 50)
    logger.info(f"작당모의 파이프라인 시작: {title}")
    logger.info("=" * 50)

    # 출력 디렉토리 생성
    dirs = create_output_dirs(title, config["output"]["base_dir"])
    logger.info(f"Output directory: {dirs['base']}")

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 1: Outline 생성 (1.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(1, "Outline Generation")
        phase_logger.info("Generating outline prompt...")

        # TODO: Outline 프롬프트 생성
        outline_prompt = generate_outline_prompt(title)

        phase_logger.info("Calling LLM for outline...")
        # TODO: LLM 호출
        # outline_json_str = call_llm(
        #     outline_prompt,
        #     temperature=config["llm"]["outline"]["temperature"],
        #     max_tokens=config["llm"]["outline"]["max_tokens"]
        # )
        # outline_data = json.loads(outline_json_str)

        phase_logger.info("Saving outline...")
        # TODO: outline.json 저장
        # save_json(outline_data, f"{dirs['base']}/outline.json")

        phase_logger.end_phase(1, "Outline Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 2: Hook 생성 (2분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(2, "Hook Generation")

        # TODO: Hook 프롬프트 생성
        # hook_prompt = generate_hook_prompt(title, outline_data["outline_full"])

        phase_logger.info("Calling LLM for hook...")
        # TODO: LLM 호출
        # hook_text = call_llm(
        #     hook_prompt,
        #     temperature=config["llm"]["hook"]["temperature"],
        #     max_tokens=config["llm"]["hook"]["max_tokens"]
        # )

        phase_logger.info("Saving hook...")
        # TODO: hook.txt 저장
        # save_text(hook_text, f"{dirs['hook']}/hook.txt")

        phase_logger.end_phase(2, "Hook Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 3-6: Parts 1-4 생성 (10분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        previous_parts = []
        parts_text = []

        for part_num in range(1, 5):
            phase_logger.start_phase(part_num + 2, f"Part {part_num} Generation")

            # TODO: Part 프롬프트 생성
            # part_prompt = generate_part_prompt(
            #     title,
            #     outline_data["outline_full"],
            #     previous_parts if previous_parts else None
            # )

            phase_logger.info(f"Calling LLM for Part {part_num}...")
            # TODO: LLM 호출
            # part_response = call_llm(
            #     part_prompt,
            #     temperature=config["llm"]["parts"]["temperature"],
            #     max_tokens=config["llm"]["parts"]["max_tokens"]
            # )

            # TODO: Part 본문과 요약 분리
            # if part_num < 4:  # Part 1-3은 요약 포함
            #     parts = part_response.split("===SUMMARY===")
            #     part_text = parts[0].strip()
            #     part_summary = parts[1].strip()
            #     save_text(part_text, f"{dirs['main']}/part{part_num}.txt")
            #     save_text(part_summary, f"{dirs['main']}/part{part_num}_summary.txt")
            #     previous_parts.append(part_summary)
            # else:  # Part 4는 요약 없음
            #     part_text = part_response.strip()
            #     save_text(part_text, f"{dirs['main']}/part4.txt")

            # parts_text.append(part_text)

            phase_logger.end_phase(part_num + 2, f"Part {part_num} Generation")

        # TODO: Main 전체 병합
        # main_full = "\n\n".join(parts_text)
        # save_text(main_full, f"{dirs['main']}/main_full.txt")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 7: 이미지 프롬프트 생성 (1.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(7, "Image Prompts Generation")

        # Phase 7-1: Hook 이미지 프롬프트
        phase_logger.info("Generating hook image prompts...")
        # TODO: Hook 이미지 프롬프트 생성
        # hook_images_prompt = generate_hook_images_prompt(hook_text)
        # hook_images_json = call_llm(hook_images_prompt)
        # save_json(json.loads(hook_images_json), f"{dirs['hook']}/image_prompts.json")

        # Phase 7-2: Main 이미지 프롬프트
        phase_logger.info("Generating main image prompts...")
        # TODO: Main 이미지 프롬프트 생성
        # main_images_prompt = generate_main_images_prompt(
        #     previous_parts[0],  # Part 1 요약
        #     previous_parts[1],  # Part 2 요약
        #     previous_parts[2],  # Part 3 요약
        #     parts_text[3]       # Part 4 전체
        # )
        # main_images_json = call_llm(main_images_prompt)
        # save_json(json.loads(main_images_json), f"{dirs['main']}/image_prompts.json")

        phase_logger.end_phase(7, "Image Prompts Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 8: 병렬 처리 - 이미지 생성 + Main TTS (5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(8, "Parallel: Images + Main TTS")

        # TODO: 병렬 처리 구현
        # from concurrent.futures import ThreadPoolExecutor
        #
        # with ThreadPoolExecutor(max_workers=2) as executor:
        #     # Thread 1: 이미지 생성
        #     future_images = executor.submit(generate_all_images, dirs, config)
        #
        #     # Thread 2: Main TTS 생성
        #     future_tts = executor.submit(
        #         generate_tts,
        #         main_full,
        #         f"{dirs['main']}/main_audio.mp3",
        #         config["tts"]["batch_size"]
        #     )
        #
        #     # 결과 대기
        #     images = future_images.result()
        #     audio = future_tts.result()

        phase_logger.info("Generating images...")
        # TODO: 이미지 생성 (Hook + Main)

        phase_logger.info("Generating Main TTS...")
        # TODO: Main TTS 생성

        phase_logger.end_phase(8, "Parallel: Images + Main TTS")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 9: 자막 생성 (1.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(9, "Subtitle Generation")

        phase_logger.info("Generating subtitles from Main audio...")
        # TODO: 자막 생성
        # generate_subtitles(
        #     f"{dirs['main']}/main_audio.mp3",
        #     f"{dirs['main']}/main_subtitles.srt"
        # )

        phase_logger.end_phase(9, "Subtitle Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 10: Main 영상 합성 (3분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(10, "Main Video Compilation")

        phase_logger.info("Compiling Main video...")
        # TODO: Main 영상 합성
        # compile_video(
        #     dirs['main_images'],
        #     f"{dirs['main']}/main_audio.mp3",
        #     f"{dirs['main']}/main_subtitles.srt",
        #     f"{dirs['main']}/main_video.mp4",
        #     load_json(f"{dirs['main']}/image_prompts.json")
        # )

        phase_logger.end_phase(10, "Main Video Compilation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 11: 백업 및 정리 (0.1분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(11, "Backup and Cleanup")

        # TODO: 메타데이터 생성
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds() / 60

        metadata = {
            "title": title,
            "created_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_minutes": round(elapsed, 1),
            "status": "completed"
        }

        save_json(metadata, f"{dirs['base']}/metadata.json")
        phase_logger.info("Metadata saved")

        # TODO: Google Drive 백업
        if config["google_drive"]["enabled"]:
            phase_logger.info("Backing up to Google Drive...")
            # rclone sync 또는 Google Drive API 사용

        phase_logger.end_phase(11, "Backup and Cleanup")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 완료
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        logger.info("=" * 50)
        logger.info(f"파이프라인 완료! 총 소요 시간: {elapsed:.1f}분")
        logger.info(f"출력 위치: {dirs['base']}")
        logger.info("=" * 50)

    except Exception as e:
        phase_logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 50)
    print("작당모의 - 2시간 드라마 자동 생성 시스템")
    print("=" * 50)
    print()

    title = input("제목을 입력하세요: ").strip()

    if not title:
        print("제목을 입력해주세요.")
        exit(1)

    print()
    print(f"'{title}' 생성을 시작합니다...")
    print()

    main(title)
