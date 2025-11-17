"""
file_handler.py
파일 입출력 유틸리티
"""

import os
import json
from datetime import datetime
from typing import Dict, Any


class FileHandler:
    """
    파일 입출력 핸들러
    생성된 대본 및 이미지 프롬프트를 저장하고 불러옵니다.
    """

    def __init__(self, output_dir: str = "output"):
        """
        파일 핸들러 초기화

        Args:
            output_dir: 출력 디렉토리 경로
        """
        self.output_dir = output_dir
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리가 없으면 생성"""
        dirs = [
            self.output_dir,
            os.path.join(self.output_dir, "outlines"),
            os.path.join(self.output_dir, "hooks"),
            os.path.join(self.output_dir, "parts"),
            os.path.join(self.output_dir, "images"),
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

    def save_json(self, data: Dict[str, Any], filename: str, subdir: str = "") -> str:
        """
        JSON 데이터 저장

        Args:
            data: 저장할 데이터
            filename: 파일명
            subdir: 하위 디렉토리 (예: "outlines", "hooks")

        Returns:
            저장된 파일 경로
        """
        if subdir:
            filepath = os.path.join(self.output_dir, subdir, filename)
        else:
            filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def save_text(self, text: str, filename: str, subdir: str = "") -> str:
        """
        텍스트 데이터 저장

        Args:
            text: 저장할 텍스트
            filename: 파일명
            subdir: 하위 디렉토리

        Returns:
            저장된 파일 경로
        """
        if subdir:
            filepath = os.path.join(self.output_dir, subdir, filename)
        else:
            filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        return filepath

    def load_json(self, filename: str, subdir: str = "") -> Dict[str, Any]:
        """
        JSON 파일 불러오기

        Args:
            filename: 파일명
            subdir: 하위 디렉토리

        Returns:
            로드된 JSON 데이터
        """
        if subdir:
            filepath = os.path.join(self.output_dir, subdir, filename)
        else:
            filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_text(self, filename: str, subdir: str = "") -> str:
        """
        텍스트 파일 불러오기

        Args:
            filename: 파일명
            subdir: 하위 디렉토리

        Returns:
            로드된 텍스트
        """
        if subdir:
            filepath = os.path.join(self.output_dir, subdir, filename)
        else:
            filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_filename(self, title: str, file_type: str, extension: str = "txt") -> str:
        """
        타임스탬프가 포함된 파일명 생성

        Args:
            title: 드라마 제목
            file_type: 파일 타입 (예: "outline", "hook", "part1")
            extension: 파일 확장자

        Returns:
            생성된 파일명
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        return f"{safe_title}_{file_type}_{timestamp}.{extension}"
