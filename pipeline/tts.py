"""
TTS (Text-to-Speech) 모듈
OpenVoice를 사용한 한국어 음성 합성 (Python 3.12 호환)
"""

from pathlib import Path
import os
from typing import Optional
import torch
import numpy as np


class TTSEngine:
    """
    OpenVoice 기반 음성 합성 엔진
    - Python 3.12 완전 지원
    - 한국어 고품질 음성
    - 감정 제어 지원
    """

    def __init__(
        self,
        model_name: str = "openvoice",
        checkpoint_path: str = "checkpoints_v2/converter",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        TTS 엔진 초기화

        Args:
            model_name: TTS 모델 이름 (openvoice)
            checkpoint_path: OpenVoice 체크포인트 경로
            device: 디바이스 (cuda/cpu)
        """
        print(f"Loading OpenVoice TTS model: {model_name}")
        print(f"  Checkpoint: {checkpoint_path}")
        print(f"  Device: {device}")

        try:
            from openvoice import se_extractor
            from openvoice.api import ToneColorConverter

            self.device = device
            self.checkpoint_path = checkpoint_path

            # OpenVoice ToneColorConverter 초기화
            self.converter = ToneColorConverter(
                f'{checkpoint_path}/config.json',
                device=device
            )
            self.converter.load_ckpt(f'{checkpoint_path}/checkpoint.pth')

            # Base Speaker 초기화
            from openvoice.api import BaseSpeakerTTS
            self.base_speaker = BaseSpeakerTTS(
                model_path='checkpoints_v2/base_speakers/KO',
                device=device
            )

            print("✓ OpenVoice TTS model loaded successfully!")

        except Exception as e:
            raise RuntimeError(f"OpenVoice 모델 로드 실패: {model_name}\n오류: {e}")

    def synthesize(
        self,
        text: str,
        output_path: str,
        speaker: Optional[str] = None,
        language: Optional[str] = "ko"
    ) -> str:
        """
        텍스트를 음성으로 합성

        Args:
            text: 합성할 텍스트
            output_path: 출력 파일 경로 (.wav)
            speaker: 화자 (OpenVoice speaker)
            language: 언어 (기본: ko)

        Returns:
            생성된 오디오 파일 경로
        """
        if not text or not text.strip():
            raise ValueError("TTS 생성 실패: 텍스트가 비어있습니다")

        # 출력 디렉토리 생성
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        print(f"Synthesizing: {text[:50]}...")

        try:
            # OpenVoice TTS 생성
            # 1단계: Base speaker로 음성 생성
            temp_audio = str(Path(output_path).parent / "temp_base.wav")

            self.base_speaker.tts(
                text=text,
                output_path=temp_audio,
                speaker='default',
                language='Korean'
            )

            # 2단계: Tone color 변환 (선택적)
            if speaker and speaker != "default":
                # 커스텀 speaker가 있으면 tone color 변환 적용
                target_se = torch.load(f'checkpoints_v2/speakers/{speaker}.pth',
                                      map_location=self.device)

                self.converter.convert(
                    audio_src_path=temp_audio,
                    src_se=self.base_speaker.se,
                    tgt_se=target_se,
                    output_path=output_path,
                    message="@MyShell"
                )

                # 임시 파일 삭제
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
            else:
                # Default speaker는 base speaker 그대로 사용
                import shutil
                shutil.move(temp_audio, output_path)

            # 파일 생성 확인
            if not Path(output_path).exists():
                raise RuntimeError(f"TTS 파일이 생성되지 않았습니다: {output_path}")

            print(f"  ✓ Saved: {output_path}")
            return output_path

        except Exception as e:
            raise RuntimeError(f"TTS 합성 실패: {text[:50]}...\n오류: {e}")

    def synthesize_long_text(
        self,
        text: str,
        output_path: str,
        chunk_size: int = 500,
        speaker: Optional[str] = None
    ) -> str:
        """
        긴 텍스트를 청크로 나눠서 합성 후 병합

        Args:
            text: 긴 텍스트
            output_path: 출력 파일 경로
            chunk_size: 청크 크기 (문자 수)
            speaker: 화자

        Returns:
            생성된 오디오 파일 경로
        """
        # 문장 단위로 분리
        sentences = split_sentences(text)

        # 청크로 그룹화
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        print(f"Synthesizing {len(chunks)} chunks...")

        # 임시 파일들 생성
        temp_dir = Path(output_path).parent / "temp_audio"
        temp_dir.mkdir(exist_ok=True)

        temp_files = []
        try:
            for i, chunk in enumerate(chunks):
                temp_file = temp_dir / f"chunk_{i:03d}.wav"
                self.synthesize(chunk, str(temp_file), speaker=speaker)
                temp_files.append(str(temp_file))

            # FFmpeg로 병합
            print("Merging audio chunks...")
            merge_audio_files(temp_files, output_path)

            print(f"✓ Long text synthesis complete: {output_path}")
            return output_path

        except Exception as e:
            raise RuntimeError(f"긴 텍스트 TTS 생성 실패 (청크 {len(temp_files)}/{len(chunks)})\n오류: {e}")

        finally:
            # 임시 파일 삭제 (성공/실패 무관)
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            try:
                if temp_dir.exists():
                    temp_dir.rmdir()
            except:
                pass


def split_sentences(text: str) -> list:
    """
    텍스트를 문장 단위로 분리

    한국어 문장 부호 기준: ., !, ?, …

    Args:
        text: 분리할 텍스트

    Returns:
        문장 리스트
    """
    import re

    # 한국어 문장 부호로 분리
    sentences = re.split(r'([.!?…])', text)

    # 문장 부호를 문장에 다시 붙임
    result = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""
        if sentence:
            result.append(sentence + punct)

    # 마지막 문장 처리
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())

    return [s.strip() for s in result if s.strip()]


def merge_audio_files(input_files: list, output_file: str):
    """
    여러 오디오 파일을 하나로 병합 (FFmpeg 사용)

    Args:
        input_files: 입력 파일 경로 리스트
        output_file: 출력 파일 경로
    """
    import subprocess

    # 파일 리스트 생성
    list_file = Path(output_file).parent / "filelist.txt"
    with open(list_file, 'w') as f:
        for input_file in input_files:
            f.write(f"file '{input_file}'\n")

    # FFmpeg concat
    cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', str(list_file),
        '-c', 'copy',
        output_file,
        '-y'  # Overwrite
    ]

    subprocess.run(cmd, check=True, capture_output=True)

    # 리스트 파일 삭제
    list_file.unlink()


def generate_tts(
    text: str,
    output_path: str,
    model_name: str = "openvoice",
    chunk_size: int = 500
) -> str:
    """
    편의 함수: 텍스트 → TTS 오디오 생성

    Args:
        text: 입력 텍스트
        output_path: 출력 파일 경로
        model_name: TTS 모델 (openvoice)
        chunk_size: 긴 텍스트 청크 크기

    Returns:
        생성된 오디오 파일 경로
    """
    engine = get_tts_engine(model_name=model_name)

    if len(text) > chunk_size:
        return engine.synthesize_long_text(
            text=text,
            output_path=output_path,
            chunk_size=chunk_size
        )
    else:
        return engine.synthesize(
            text=text,
            output_path=output_path
        )


# ============================================
# 싱글톤 패턴
# ============================================
_tts_engine = None


def get_tts_engine(model_name: str = "openvoice") -> TTSEngine:
    """
    TTS 엔진 싱글톤 접근

    Args:
        model_name: TTS 모델 이름 (openvoice)

    Returns:
        TTSEngine 인스턴스
    """
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine(model_name=model_name)
    return _tts_engine


def reset_tts_engine():
    """TTS 엔진 리셋 (테스트용)"""
    global _tts_engine
    _tts_engine = None
