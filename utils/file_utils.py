"""
파일 입출력 유틸리티
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    딕셔너리를 JSON 파일로 저장합니다.

    Args:
        data (Dict[str, Any]): 저장할 데이터
        filepath (str): 저장할 파일 경로

    Raises:
        IOError: 파일 저장 실패 시
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise IOError(f"Failed to save JSON to {filepath}: {e}")


def load_json(filepath: str) -> Dict[str, Any]:
    """
    JSON 파일을 로드하여 딕셔너리로 반환합니다.

    Args:
        filepath (str): 로드할 파일 경로

    Returns:
        Dict[str, Any]: 로드된 데이터

    Raises:
        IOError: 파일 로드 실패 시
        json.JSONDecodeError: JSON 파싱 실패 시
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise IOError(f"Failed to load JSON from {filepath}: {e}")


def save_text(text: str, filepath: str) -> None:
    """
    텍스트를 파일로 저장합니다.

    Args:
        text (str): 저장할 텍스트
        filepath (str): 저장할 파일 경로

    Raises:
        IOError: 파일 저장 실패 시
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        raise IOError(f"Failed to save text to {filepath}: {e}")


def load_text(filepath: str) -> str:
    """
    텍스트 파일을 로드하여 반환합니다.

    Args:
        filepath (str): 로드할 파일 경로

    Returns:
        str: 로드된 텍스트

    Raises:
        IOError: 파일 로드 실패 시
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to load text from {filepath}: {e}")


def create_output_dirs(title: str, base_dir: str = "/workspace/outputs") -> Dict[str, str]:
    """
    출력 디렉토리 구조를 생성합니다.

    Args:
        title (str): 프로젝트 제목
        base_dir (str): 기본 출력 디렉토리 (기본값: /workspace/outputs)

    Returns:
        Dict[str, str]: 생성된 디렉토리 경로들
            - base: 기본 출력 경로 (/workspace/outputs/제목/)
            - hook: Hook 출력 경로
            - hook_images: Hook 이미지 경로
            - main: Main 출력 경로
            - main_images: Main 이미지 경로

    Example:
        >>> dirs = create_output_dirs("테스트 드라마")
        >>> print(dirs["base"])
        /workspace/outputs/테스트 드라마/
        >>> print(dirs["hook"])
        /workspace/outputs/테스트 드라마/hook/
    """
    try:
        # 기본 경로 생성
        base_path = Path(base_dir) / title

        # 하위 디렉토리 경로
        hook_path = base_path / "hook"
        hook_images_path = hook_path / "images"
        main_path = base_path / "main"
        main_images_path = main_path / "images"

        # 디렉토리 생성
        base_path.mkdir(parents=True, exist_ok=True)
        hook_path.mkdir(exist_ok=True)
        hook_images_path.mkdir(exist_ok=True)
        main_path.mkdir(exist_ok=True)
        main_images_path.mkdir(exist_ok=True)

        return {
            "base": str(base_path),
            "hook": str(hook_path),
            "hook_images": str(hook_images_path),
            "main": str(main_path),
            "main_images": str(main_images_path)
        }
    except Exception as e:
        raise IOError(f"Failed to create output directories for '{title}': {e}")
