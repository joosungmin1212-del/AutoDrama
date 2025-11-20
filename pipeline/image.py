"""
이미지 생성 모듈
SDXL Lightning을 사용한 고속 이미지 생성
"""

import torch
from diffusers import (
    StableDiffusionXLPipeline,
    EulerDiscreteScheduler,
    AutoencoderKL
)
from pathlib import Path
from typing import List, Optional
import os


class ImageGenerator:
    """
    SDXL Lightning 기반 이미지 생성기

    4-8 steps로 고품질 이미지 생성
    """

    def __init__(
        self,
        model_id: str = "ByteDance/SDXL-Lightning",
        device: str = "cuda",
        torch_dtype=torch.float16,
        enable_xformers: bool = True,
        enable_cpu_offload: bool = False
    ):
        """
        SDXL Lightning 파이프라인 초기화

        Args:
            model_id: HuggingFace 모델 ID
            device: 디바이스 (cuda/cpu)
            torch_dtype: 데이터 타입 (float16 권장)
            enable_xformers: xFormers 메모리 최적화
            enable_cpu_offload: CPU 오프로딩 (VRAM 부족 시)
        """
        print(f"Loading SDXL Lightning from {model_id}...")

        self.device = device
        self.torch_dtype = torch_dtype

        # VAE 로드 (fp16 안정성 개선)
        print("  Loading VAE...")
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix",
            torch_dtype=torch_dtype
        )

        # SDXL Lightning 파이프라인
        print("  Loading SDXL Lightning pipeline...")
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            vae=vae,
            torch_dtype=torch_dtype,
            variant="fp16",
            use_safetensors=True
        )

        # Euler 스케줄러 (Lightning 최적화)
        self.pipe.scheduler = EulerDiscreteScheduler.from_config(
            self.pipe.scheduler.config,
            timestep_spacing="trailing"
        )

        # 최적화
        self.pipe.to(device)

        if enable_xformers:
            try:
                self.pipe.enable_xformers_memory_efficient_attention()
                print("  ✓ xFormers enabled")
            except Exception as e:
                print(f"  ✗ xFormers failed: {e}")

        if enable_cpu_offload:
            self.pipe.enable_model_cpu_offload()
            print("  ✓ CPU offload enabled")
        else:
            self.pipe.enable_attention_slicing()
            print("  ✓ Attention slicing enabled")

        print("✓ SDXL Lightning loaded successfully!")

    def generate_single(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "blurry, low quality, ugly, distorted",
        num_inference_steps: int = 4,
        guidance_scale: float = 0.0,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> str:
        """
        단일 이미지 생성

        Args:
            prompt: 생성 프롬프트 (영어)
            output_path: 출력 파일 경로
            negative_prompt: 네거티브 프롬프트
            num_inference_steps: 추론 스텝 (Lightning: 4-8 권장)
            guidance_scale: CFG (Lightning: 0.0 권장)
            width, height: 이미지 크기
            seed: 시드 (None이면 랜덤)

        Returns:
            생성된 이미지 경로
        """
        # Generator
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        print(f"Generating image: {Path(output_path).name}")
        print(f"  Prompt: {prompt[:80]}...")
        print(f"  Steps: {num_inference_steps}, CFG: {guidance_scale}")

        # 생성
        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            generator=generator
        ).images[0]

        # 저장
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

        print(f"  ✓ Saved: {output_path}")
        return output_path

    def generate_batch(
        self,
        prompts: List[str],
        output_paths: List[str],
        negative_prompt: str = "blurry, low quality, ugly, distorted",
        num_inference_steps: int = 4,
        guidance_scale: float = 0.0,
        width: int = 1024,
        height: int = 1024,
        seed: int = 42,
        batch_size: int = 4
    ) -> List[str]:
        """
        배치 이미지 생성

        VRAM 부족 방지를 위해 batch_size로 나눠서 생성

        Args:
            prompts: 프롬프트 리스트
            output_paths: 출력 경로 리스트
            negative_prompt: 네거티브 프롬프트
            num_inference_steps: 추론 스텝 (4-8)
            guidance_scale: CFG (0.0 권장)
            width, height: 이미지 크기
            seed: 시드
            batch_size: 배치 크기 (VRAM에 따라 조절)

        Returns:
            생성된 이미지 경로 리스트
        """
        assert len(prompts) == len(output_paths), "프롬프트와 경로 수가 일치해야 합니다"

        total = len(prompts)
        generated_paths = []

        print(f"Batch generation: {total} images (batch_size={batch_size})")

        for i in range(0, total, batch_size):
            batch_prompts = prompts[i:i+batch_size]
            batch_paths = output_paths[i:i+batch_size]

            print(f"\n[Batch {i//batch_size + 1}/{(total-1)//batch_size + 1}] Generating {len(batch_prompts)} images...")

            # Generator
            generator = torch.Generator(device=self.device).manual_seed(seed + i)

            # 배치 생성
            images = self.pipe(
                prompt=batch_prompts,
                negative_prompt=[negative_prompt] * len(batch_prompts),
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator
            ).images

            # 저장
            for img, path in zip(images, batch_paths):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                img.save(path)
                generated_paths.append(path)
                print(f"  ✓ {Path(path).name}")

        print(f"\n✓ Total {len(generated_paths)} images generated!")
        return generated_paths

    def generate_from_json(
        self,
        scenes_data: List[dict],
        output_dir: str,
        num_inference_steps: int = 4,
        width: int = 1024,
        height: int = 1024
    ) -> List[str]:
        """
        JSON 씬 데이터에서 이미지 생성

        AutoDrama 이미지 프롬프트 JSON 형식 지원

        Args:
            scenes_data: 씬 데이터 리스트
                [{"index": 0, "prompt": "...", "description": "..."}, ...]
            output_dir: 출력 디렉토리
            num_inference_steps: 추론 스텝
            width, height: 이미지 크기

        Returns:
            생성된 이미지 경로 리스트
        """
        prompts = [scene['prompt'] for scene in scenes_data]
        output_paths = [
            os.path.join(output_dir, f"scene_{scene['index']:03d}.png")
            for scene in scenes_data
        ]

        return self.generate_batch(
            prompts=prompts,
            output_paths=output_paths,
            num_inference_steps=num_inference_steps,
            width=width,
            height=height
        )


# ============================================
# 싱글톤 패턴
# ============================================
_image_generator = None


def get_image_generator(
    model_id: str = "ByteDance/SDXL-Lightning",
    enable_cpu_offload: bool = False
) -> ImageGenerator:
    """
    이미지 생성기 싱글톤 접근

    Args:
        model_id: 모델 ID
        enable_cpu_offload: CPU 오프로딩

    Returns:
        ImageGenerator 인스턴스
    """
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator(
            model_id=model_id,
            enable_cpu_offload=enable_cpu_offload
        )
    return _image_generator


def generate_images(
    prompts: List[str],
    output_dir: str,
    batch_size: int = 4,
    num_inference_steps: int = 4
) -> List[str]:
    """
    편의 함수: 프롬프트 리스트 → 이미지 생성

    Args:
        prompts: 프롬프트 리스트
        output_dir: 출력 디렉토리
        batch_size: 배치 크기
        num_inference_steps: 추론 스텝

    Returns:
        생성된 이미지 경로 리스트
    """
    generator = get_image_generator()

    output_paths = [
        os.path.join(output_dir, f"image_{i:03d}.png")
        for i in range(len(prompts))
    ]

    return generator.generate_batch(
        prompts=prompts,
        output_paths=output_paths,
        batch_size=batch_size,
        num_inference_steps=num_inference_steps
    )


def reset_image_generator():
    """이미지 생성기 리셋 (테스트용)"""
    global _image_generator
    _image_generator = None
