"""
비디오 합성 모듈
FFmpeg을 사용한 이미지 + 오디오 + 자막 합성
"""

from pathlib import Path
from typing import List, Dict, Any
import subprocess
import json
import os


def get_audio_duration(audio_path: str) -> float:
    """
    오디오 파일의 길이를 초 단위로 반환 (ffprobe 사용)

    Args:
        audio_path: 오디오 파일 경로

    Returns:
        오디오 길이 (초)
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        audio_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    duration = float(data['format']['duration'])

    return duration


def compile_video(
    images_dir: str,
    audio_path: str,
    subtitles_path: str,
    output_path: str,
    image_prompts_json: Dict[str, Any],
    fps: int = 24
) -> str:
    """
    FFmpeg을 사용하여 이미지, 오디오, 자막을 합성하여 비디오 생성

    각 이미지를 타임스탬프에 맞게 배치

    Args:
        images_dir: 이미지 디렉토리
        audio_path: 오디오 파일 경로
        subtitles_path: 자막 파일 경로 (.srt)
        output_path: 출력 비디오 파일 경로 (.mp4)
        image_prompts_json: 이미지 프롬프트 JSON (타임스탬프 포함)
        fps: 비디오 프레임레이트

    Returns:
        생성된 비디오 파일 경로
    """
    print(f"Compiling video: {output_path}")

    # 출력 디렉토리 생성
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 오디오 길이 확인
    audio_duration = get_audio_duration(audio_path)
    print(f"  Audio duration: {audio_duration:.2f}s")

    # Scenes 정보 추출
    scenes = image_prompts_json["scenes"]
    print(f"  Total scenes: {len(scenes)}")

    # 이미지 파일 경로 매칭
    image_files = []
    for scene in scenes:
        # 이미지 파일 찾기 (scene_XXX.png 형식)
        pattern = f"scene_{scene['index']:03d}.png"
        image_path = Path(images_dir) / pattern

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        image_files.append({
            'path': str(image_path),
            'timestamp': scene['timestamp'],
            'duration': scene['duration']
        })

    # FFmpeg concat 파일 생성
    concat_file = Path(output_path).parent / "images_concat.txt"
    with open(concat_file, 'w') as f:
        for img in image_files:
            f.write(f"file '{img['path']}'\n")
            f.write(f"duration {img['duration']}\n")

        # 마지막 이미지 (FFmpeg concat 요구사항)
        f.write(f"file '{image_files[-1]['path']}'\n")

    print("  Creating video with FFmpeg...")

    # FFmpeg 명령어
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-i', audio_path,
        '-vf', f"subtitles={subtitles_path}",
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-r', str(fps),
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',  # 오디오 길이에 맞춤
        '-y',  # Overwrite
        output_path
    ]

    # 실행
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

    # concat 파일 삭제
    concat_file.unlink()

    print(f"✓ Video compilation complete: {output_path}")
    return output_path


def compile_video_simple(
    images_dir: str,
    audio_path: str,
    output_path: str,
    duration_per_image: float = 5.0,
    fps: int = 24
) -> str:
    """
    간단한 비디오 합성 (자막 없음)

    모든 이미지를 동일한 길이로 표시

    Args:
        images_dir: 이미지 디렉토리
        audio_path: 오디오 파일 경로
        output_path: 출력 비디오 파일 경로
        duration_per_image: 이미지당 표시 시간 (초)
        fps: 프레임레이트

    Returns:
        생성된 비디오 파일 경로
    """
    print(f"Compiling simple video: {output_path}")

    # 출력 디렉토리 생성
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 이미지 파일 수집
    image_files = sorted(Path(images_dir).glob("*.png"))
    if not image_files:
        raise ValueError(f"No images found in {images_dir}")

    print(f"  Found {len(image_files)} images")

    # Concat 파일 생성
    concat_file = Path(output_path).parent / "images_concat.txt"
    with open(concat_file, 'w') as f:
        for img_path in image_files:
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {duration_per_image}\n")
        f.write(f"file '{image_files[-1]}'\n")

    # FFmpeg 명령어
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-r', str(fps),
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-y',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

    concat_file.unlink()

    print(f"✓ Simple video compilation complete: {output_path}")
    return output_path


def add_subtitles_to_video(
    video_path: str,
    subtitles_path: str,
    output_path: str
) -> str:
    """
    기존 비디오에 자막 추가

    Args:
        video_path: 입력 비디오 파일
        subtitles_path: 자막 파일 (.srt)
        output_path: 출력 비디오 파일

    Returns:
        생성된 비디오 파일 경로
    """
    print(f"Adding subtitles to video...")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f"subtitles={subtitles_path}",
        '-c:a', 'copy',
        '-y',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg stderr: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

    print(f"✓ Subtitles added: {output_path}")
    return output_path
