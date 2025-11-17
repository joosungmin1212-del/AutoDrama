"""
main.py
오디오 드라마 자동 생성 메인 스크립트
"""

import os
import sys
from typing import Dict, Any, List

from utils import LLMClient, FileHandler
from generators import (
    generate_outline_prompt,
    generate_hook_prompt,
    generate_part_prompt,
    generate_hook_images_prompt,
    generate_main_images_prompt
)


class AudioDramaGenerator:
    """오디오 드라마 자동 생성기"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        provider: str = None,
        output_dir: str = "output"
    ):
        """
        초기화

        Args:
            api_key: API 키
            base_url: API 베이스 URL (OpenAI 호환용)
            model: 모델명
            provider: "openai" 또는 "anthropic"
            output_dir: 출력 디렉토리
        """
        # 환경변수에서 provider 가져오기
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "openai")

        self.llm = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider=provider
        )
        self.file_handler = FileHandler(output_dir=output_dir)
        self.title = None
        self.outline_data = None
        self.hook_text = None
        self.parts = []

    def generate_outline(self, title: str) -> Dict[str, Any]:
        """
        1단계: 전체 개요 생성

        Args:
            title: 드라마 제목

        Returns:
            개요 데이터 (JSON)
        """
        print(f"\n📝 '{title}' 개요 생성 중...")
        self.title = title

        prompt = generate_outline_prompt(title)
        outline_data = self.llm.generate_json(prompt, max_tokens=8000)

        # 저장
        filename = self.file_handler.generate_filename(title, "outline", "json")
        filepath = self.file_handler.save_json(outline_data, filename, "outlines")
        print(f"✅ 개요 저장: {filepath}")

        self.outline_data = outline_data
        return outline_data

    def generate_hook(self) -> str:
        """
        2단계: 훅 생성

        Returns:
            훅 텍스트
        """
        if not self.outline_data:
            raise ValueError("개요를 먼저 생성해야 합니다.")

        print("\n🎣 훅 생성 중...")

        prompt = generate_hook_prompt(
            self.title,
            self.outline_data["outline_full"]
        )
        hook_text = self.llm.generate_text(prompt, max_tokens=2000)

        # 저장
        filename = self.file_handler.generate_filename(self.title, "hook", "txt")
        filepath = self.file_handler.save_text(hook_text, filename, "hooks")
        print(f"✅ 훅 저장: {filepath}")

        self.hook_text = hook_text
        return hook_text

    def generate_part(self, part_number: int) -> str:
        """
        3단계: 파트 생성

        Args:
            part_number: 파트 번호 (1-4)

        Returns:
            파트 텍스트
        """
        if not self.outline_data:
            raise ValueError("개요를 먼저 생성해야 합니다.")

        if part_number < 1 or part_number > 4:
            raise ValueError("파트 번호는 1-4 사이여야 합니다.")

        print(f"\n📖 Part {part_number} 생성 중...")

        # 이전 파트 요약 준비
        previous_summaries = []
        for i in range(part_number - 1):
            if i < len(self.parts):
                # 실제로는 각 파트의 요약을 저장해야 하지만,
                # 여기서는 간단히 첫 500자를 사용
                summary = self.parts[i][:500] + "..."
                previous_summaries.append(summary)

        prompt = generate_part_prompt(
            self.title,
            self.outline_data["outline_full"],
            previous_summaries
        )

        part_text = self.llm.generate_text(prompt, max_tokens=16000)

        # 저장
        filename = self.file_handler.generate_filename(
            self.title, f"part{part_number}", "txt"
        )
        filepath = self.file_handler.save_text(part_text, filename, "parts")
        print(f"✅ Part {part_number} 저장: {filepath}")

        # 파트 저장
        if part_number > len(self.parts):
            self.parts.append(part_text)
        else:
            self.parts[part_number - 1] = part_text

        return part_text

    def generate_all_parts(self) -> List[str]:
        """
        3단계: 모든 파트 생성 (Part 1-4)

        Returns:
            모든 파트 텍스트 리스트
        """
        for i in range(1, 5):
            self.generate_part(i)

        return self.parts

    def generate_hook_images(self) -> Dict[str, Any]:
        """
        4단계: 훅 이미지 프롬프트 생성

        Returns:
            이미지 프롬프트 데이터
        """
        if not self.hook_text:
            raise ValueError("훅을 먼저 생성해야 합니다.")

        print("\n🖼️  훅 이미지 프롬프트 생성 중...")

        prompt = generate_hook_images_prompt(self.hook_text)
        images_data = self.llm.generate_json(prompt, max_tokens=8000)

        # 저장
        filename = self.file_handler.generate_filename(
            self.title, "hook_images", "json"
        )
        filepath = self.file_handler.save_json(images_data, filename, "images")
        print(f"✅ 훅 이미지 프롬프트 저장: {filepath}")

        return images_data

    def generate_main_images(self) -> Dict[str, Any]:
        """
        5단계: 메인 이미지 프롬프트 생성

        Returns:
            이미지 프롬프트 데이터
        """
        if len(self.parts) < 4:
            raise ValueError("모든 파트를 먼저 생성해야 합니다.")

        print("\n🖼️  메인 이미지 프롬프트 생성 중...")

        # 각 파트 요약 (첫 1000자)
        summaries = [part[:1000] + "..." for part in self.parts]

        prompt = generate_main_images_prompt(*summaries)
        images_data = self.llm.generate_json(prompt, max_tokens=10000)

        # 저장
        filename = self.file_handler.generate_filename(
            self.title, "main_images", "json"
        )
        filepath = self.file_handler.save_json(images_data, filename, "images")
        print(f"✅ 메인 이미지 프롬프트 저장: {filepath}")

        return images_data

    def generate_full_drama(self, title: str) -> Dict[str, Any]:
        """
        전체 프로세스 실행

        Args:
            title: 드라마 제목

        Returns:
            생성된 모든 데이터
        """
        print("\n" + "=" * 60)
        print(f"🎬 오디오 드라마 생성 시작: '{title}'")
        print("=" * 60)

        # 1. 개요
        outline = self.generate_outline(title)

        # 2. 훅
        hook = self.generate_hook()

        # 3. 파트 1-4
        parts = self.generate_all_parts()

        # 4. 훅 이미지
        hook_images = self.generate_hook_images()

        # 5. 메인 이미지
        main_images = self.generate_main_images()

        print("\n" + "=" * 60)
        print("✨ 생성 완료!")
        print("=" * 60)

        return {
            "title": title,
            "outline": outline,
            "hook": hook,
            "parts": parts,
            "hook_images": hook_images,
            "main_images": main_images
        }


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="오디오 드라마 자동 생성 시스템"
    )
    parser.add_argument(
        "title",
        type=str,
        help="드라마 제목"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default=None,
        help="LLM 백엔드: openai (runpod/vLLM) 또는 anthropic (환경변수 LLM_PROVIDER)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API 키 (환경변수 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API 베이스 URL (OpenAI 호환 API용, 환경변수 OPENAI_BASE_URL)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="모델명 (환경변수 MODEL_NAME)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="출력 디렉토리 (기본값: output)"
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["outline", "hook", "part1", "part2", "part3", "part4", "all"],
        default="all",
        help="실행할 단계 (기본값: all)"
    )

    args = parser.parse_args()

    try:
        generator = AudioDramaGenerator(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            provider=args.provider,
            output_dir=args.output_dir
        )

        if args.step == "all":
            generator.generate_full_drama(args.title)
        elif args.step == "outline":
            generator.generate_outline(args.title)
        elif args.step == "hook":
            generator.generate_outline(args.title)
            generator.generate_hook()
        elif args.step.startswith("part"):
            part_num = int(args.step[-1])
            generator.generate_outline(args.title)
            generator.generate_part(part_num)

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
