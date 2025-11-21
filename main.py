"""
AutoDrama - 제목만 입력하면 2시간 드라마 자동 생성
완전 자동화 파이프라인
"""

import yaml
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프롬프트 모듈
from prompts.outline_v2_final import generate_outline_prompt
from prompts.hook import generate_hook_prompt
from prompts.part_v3 import generate_part_v3_prompt
from prompts.hook_images import generate_hook_images_prompt
from prompts.main_images import generate_main_images_prompt

# 파이프라인 모듈 (신규 API)
from pipeline.llm import get_llm_engine
from pipeline.image import get_image_generator, generate_images
from pipeline.tts import generate_tts
from pipeline.subtitle import generate_subtitles
from pipeline.video import compile_video

# 유틸리티
from utils.file_utils import (
    save_json, load_json,
    save_text, load_text,
    create_output_dirs
)
from utils.logger import setup_logger, PhaseLogger
from utils.context_generator import create_part_context


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """설정 파일 로드"""
    if not Path(config_path).exists():
        # 기본 설정 생성 (72B 최적화)
        default_config = {
            "output": {"base_dir": "./output"},
            "logging": {"file": "./autodrama.log", "level": "INFO"},
            "llm": {
                "outline": {"temperature": 0.65, "max_tokens": 7000, "top_p": 0.92, "top_k": 40, "repetition_penalty": 1.13},
                "hook": {"temperature": 0.75, "max_tokens": 2048, "top_p": 0.92, "top_k": 40, "repetition_penalty": 1.13},
                "parts": {"temperature": 0.70, "max_tokens": 5000, "top_p": 0.92, "top_k": 40, "repetition_penalty": 1.13}
            },
            "image": {"batch_size": 4, "steps": 4},
            "tts": {"model": "tts_models/ko/cv/vits", "chunk_size": 500},
            "whisper": {"model": "large-v3"},
            "google_drive": {"enabled": False}
        }
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, allow_unicode=True)
        return default_config

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main(title: str) -> None:
    """
    메인 파이프라인 실행

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
    logger.info(f"AutoDrama Pipeline Started: {title}")
    logger.info("=" * 60)

    # 출력 디렉토리 생성
    dirs = create_output_dirs(title, config["output"]["base_dir"])
    logger.info(f"Output directory: {dirs['base']}")

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 1: Outline 생성 (1.0분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(1, "Outline Generation")

        llm = get_llm_engine(config_path="config.yaml")

        outline_prompt = generate_outline_prompt(title)
        outline_data = llm.call_llm(outline_prompt, phase="outline")

        # Outline 검증 및 보정
        from prompts.outline_v2_final import validate_outline
        outline_data = validate_outline(outline_data)

        save_json(outline_data, f"{dirs['base']}/outline.json")

        phase_logger.info(f"Outline generated: {len(outline_data.get('outline_full', ''))} chars")
        phase_logger.info(f"Characters: {len(outline_data.get('characters', []))}")
        phase_logger.info(f"Parts: {len(outline_data.get('part_breakdown', []))}")
        phase_logger.end_phase(1, "Outline Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 2: Hook 생성 (0.3분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(2, "Hook Generation")

        hook_prompt = generate_hook_prompt(title, outline_data["outline_full"])
        hook_text = llm.call_llm_text(hook_prompt, phase="hook")
        save_text(hook_text, f"{dirs['hook']}/hook.txt")

        phase_logger.info(f"Hook generated: {len(hook_text)} chars")
        phase_logger.end_phase(2, "Hook Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 3: Hook Images Prompts (0.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(3, "Hook Images Prompts")

        hook_images_prompt = generate_hook_images_prompt(hook_text)
        hook_images_data = llm.call_llm(hook_images_prompt, phase="outline")
        save_json(hook_images_data, f"{dirs['hook']}/image_prompts.json")

        phase_logger.info(f"Hook image prompts: {hook_images_data['total_scenes']} scenes")
        phase_logger.end_phase(3, "Hook Images Prompts")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 4: Hook Images 생성 (0.8분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(4, "Hook Images Generation")

        image_gen = get_image_generator()
        hook_image_paths = image_gen.generate_from_json(
            hook_images_data['scenes'],
            str(dirs['hook_images']),
            num_inference_steps=config["image"]["steps"]
        )

        phase_logger.info(f"Hook images generated: {len(hook_image_paths)} images")
        phase_logger.end_phase(4, "Hook Images Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 5: Parts 1-4 생성 (순차 + Context) (2.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(5, "Parts 1-4 Generation (Sequential with Context)")

        parts_text = []
        current_context = None

        # 순차 생성 (Part 1 → 2 → 3 → 4)
        from prompts.part_v3 import validate_part_text
        from utils.context_generator import sanitize_context

        for part_num in range(1, 5):
            phase_logger.info(f"Generating Part {part_num}...")

            # Part V3 프롬프트 생성
            part_prompt = generate_part_v3_prompt(
                part_number=part_num,
                outline_data=outline_data,
                context=current_context
            )

            # LLM 호출
            part_text = llm.call_llm_text(part_prompt, "parts")
            parts_text.append(part_text)

            # Part 검증
            is_valid, warnings, stats = validate_part_text(part_text, part_num)
            if warnings:
                for warning in warnings:
                    phase_logger.warning(f"Part {part_num}: {warning}")

            phase_logger.info(f"Part {part_num} stats: {stats.get('length', 0)} chars, dialogue {stats.get('dialogue_ratio', 0):.1f}%")

            # Part 저장
            save_text(part_text, f"{dirs['main']}/part{part_num}.txt")
            phase_logger.info(f"Part {part_num} completed: {len(part_text)} chars")

            # Part 1-3은 다음 Part를 위한 Context 생성
            if part_num < 4:
                phase_logger.info(f"Creating context for Part {part_num + 1}...")
                current_context = create_part_context(
                    part_text=part_text,
                    part_number=part_num,
                    outline_data=outline_data
                )
                # Context 안전화
                current_context = sanitize_context(current_context)

                # Context 저장 (디버깅용)
                save_json(current_context, f"{dirs['main']}/part{part_num}_context.json")
                phase_logger.info(f"Context created: {len(current_context.get('summary', ''))} chars summary")

        # Main 전체 병합
        main_full = "\n\n".join(parts_text)
        save_text(main_full, f"{dirs['main']}/main_full.txt")

        phase_logger.info(f"All parts generated: {len(main_full)} chars total")
        phase_logger.end_phase(5, "Parts 1-4 Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 6: Main Images Prompts (0.6분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(6, "Main Images Prompts")

        main_images_prompt = generate_main_images_prompt(
            parts_text[0] if len(parts_text) > 0 else "",
            parts_text[1] if len(parts_text) > 1 else "",
            parts_text[2] if len(parts_text) > 2 else "",
            parts_text[3] if len(parts_text) > 3 else ""
        )
        main_images_data = llm.call_llm(main_images_prompt, phase="outline")
        save_json(main_images_data, f"{dirs['main']}/image_prompts.json")

        phase_logger.info(f"Main image prompts: {main_images_data['total_scenes']} scenes")
        phase_logger.end_phase(6, "Main Images Prompts")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 7: Main Images 생성 (2.0분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(7, "Main Images Generation")

        main_image_paths = image_gen.generate_from_json(
            main_images_data['scenes'],
            str(dirs['main_images']),
            num_inference_steps=config["image"]["steps"]
        )

        phase_logger.info(f"Main images generated: {len(main_image_paths)} images")
        phase_logger.end_phase(7, "Main Images Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 8: TTS 생성 (병렬 처리) (1.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(8, "TTS Generation (Parallel)")

        hook_audio_path = f"{dirs['hook']}/hook_audio.wav"
        main_audio_path = f"{dirs['main']}/main_audio.wav"

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_hook_tts = executor.submit(
                generate_tts,
                hook_text,
                hook_audio_path,
                config["tts"]["model"]
            )

            future_main_tts = executor.submit(
                generate_tts,
                main_full,
                main_audio_path,
                config["tts"]["model"]
            )

            hook_audio = future_hook_tts.result()
            main_audio = future_main_tts.result()

        phase_logger.info("TTS generation completed")
        phase_logger.end_phase(8, "TTS Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 9: Subtitle 생성 (1.5분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(9, "Subtitle Generation")

        hook_subtitle_path = f"{dirs['hook']}/hook_subtitles.srt"
        main_subtitle_path = f"{dirs['main']}/main_subtitles.srt"

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_hook_sub = executor.submit(
                generate_subtitles,
                hook_audio,
                hook_subtitle_path,
                config["whisper"]["model"]
            )

            future_main_sub = executor.submit(
                generate_subtitles,
                main_audio,
                main_subtitle_path,
                config["whisper"]["model"]
            )

            hook_subtitle = future_hook_sub.result()
            main_subtitle = future_main_sub.result()

        phase_logger.info("Subtitles generated")
        phase_logger.end_phase(9, "Subtitle Generation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 10: Video 합성 (1.0분)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        phase_logger.start_phase(10, "Video Compilation")

        hook_video_path = f"{dirs['hook']}/hook_video.mp4"
        main_video_path = f"{dirs['main']}/main_video.mp4"

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_hook_video = executor.submit(
                compile_video,
                str(dirs['hook_images']),
                hook_audio,
                hook_subtitle,
                hook_video_path,
                hook_images_data
            )

            future_main_video = executor.submit(
                compile_video,
                str(dirs['main_images']),
                main_audio,
                main_subtitle,
                main_video_path,
                main_images_data
            )

            hook_video = future_hook_video.result()
            main_video = future_main_video.result()

        phase_logger.info("Videos compiled")
        phase_logger.end_phase(10, "Video Compilation")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 완료
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds() / 60

        metadata = {
            "title": title,
            "created_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_minutes": round(elapsed, 1),
            "hook_video": hook_video,
            "main_video": main_video,
            "status": "completed"
        }

        save_json(metadata, f"{dirs['base']}/metadata.json")

        logger.info("=" * 60)
        logger.info(f"✓ Pipeline Completed!")
        logger.info(f"  Total time: {elapsed:.1f} minutes")
        logger.info(f"  Output: {dirs['base']}")
        logger.info(f"  Hook video: {hook_video}")
        logger.info(f"  Main video: {main_video}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("AutoDrama - 2시간 드라마 자동 생성 시스템")
    print("=" * 60)
    print()

    title = input("제목을 입력하세요: ").strip()

    if not title:
        print("❌ 제목을 입력해주세요.")
        exit(1)

    print()
    print(f"✓ '{title}' 생성을 시작합니다...")
    print(f"  예상 소요 시간: 약 11-13분")
    print()

    try:
        main(title)
        print()
        print("✓ 완료! 영상이 생성되었습니다.")
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        exit(1)
