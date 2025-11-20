"""
자막 생성 모듈
whisper-ctranslate2를 사용한 고성능 STT
"""

from pathlib import Path
from whisper_ctranslate2 import Transcriber


# 전역 모델 캐싱
_whisper_model = None


def get_whisper_model(model_name: str = "large-v3", device: str = "cuda"):
    """
    Whisper-CTranslate2 모델을 싱글톤으로 로드합니다.

    Args:
        model_name: 모델 크기 (tiny, base, small, medium, large-v2, large-v3)
        device: 디바이스 (cuda, cpu)

    Returns:
        Transcriber 인스턴스
    """
    global _whisper_model
    if _whisper_model is None:
        print(f"Loading Whisper model: {model_name} on {device}...")
        _whisper_model = Transcriber(
            model_name_or_path=model_name,
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
        print("Whisper model loaded successfully!")
    return _whisper_model


def generate_subtitles(
    audio_path: str,
    output_path: str,
    model_name: str = "large-v3",
    language: str = "ko"
) -> str:
    """
    whisper-ctranslate2를 사용하여 오디오에서 자막을 생성합니다.

    Args:
        audio_path (str): 입력 오디오 파일 경로 (.mp3, .wav 등)
        output_path (str): 출력 자막 파일 경로 (.srt)
        model_name (str): Whisper 모델 (기본: large-v3)
        language (str): 언어 코드 (기본: ko)

    Returns:
        str: 생성된 자막 파일 경로

    Raises:
        RuntimeError: 자막 생성 실패 시
    """
    try:
        # 모델 로드
        whisper = get_whisper_model(model_name=model_name)

        print(f"Transcribing audio: {audio_path}")

        # 음성 인식 실행
        segments, info = whisper.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
            word_timestamps=False
        )

        print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

        # SRT 파일 생성
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}\n")
                f.write(f"{segment.text.strip()}\n")
                f.write("\n")

        print(f"Subtitles saved to: {output_path}")
        return output_path

    except Exception as e:
        raise RuntimeError(f"Subtitle generation failed: {e}")


def format_timestamp(seconds: float) -> str:
    """
    초를 SRT 타임스탬프 형식으로 변환합니다.

    Args:
        seconds (float): 시간 (초)

    Returns:
        str: SRT 타임스탬프 (00:00:00,000)

    Example:
        >>> format_timestamp(125.5)
        '00:02:05,500'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
