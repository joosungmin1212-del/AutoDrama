"""
로깅 유틸리티
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "작당모의",
    log_file: Optional[str] = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.

    Args:
        name (str): 로거 이름 (기본값: "작당모의")
        log_file (Optional[str]): 로그 파일 경로 (기본값: None, 콘솔만 출력)
        level (str): 로그 레벨 (기본값: "INFO")

    Returns:
        logging.Logger: 설정된 로거

    Example:
        >>> logger = setup_logger()
        >>> logger.info("Phase 1: Starting outline generation")
        [2024-11-16 14:23:05] [INFO] Phase 1: Starting outline generation

        >>> logger = setup_logger(log_file="pipeline.log")
        >>> logger.info("Process started")
    """
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()

    # 포맷터 생성 (타임스탬프 포함)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (옵션)
    if log_file:
        try:
            # 로그 파일 디렉토리 생성
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create file handler for {log_file}: {e}")

    return logger


class PhaseLogger:
    """
    Phase별 로깅을 위한 유틸리티 클래스
    """

    def __init__(self, logger: logging.Logger):
        """
        Args:
            logger (logging.Logger): 사용할 로거
        """
        self.logger = logger
        self.current_phase: Optional[int] = None
        self.phase_start_time: Optional[datetime] = None

    def start_phase(self, phase_number: int, phase_name: str) -> None:
        """
        Phase 시작을 로깅합니다.

        Args:
            phase_number (int): Phase 번호
            phase_name (str): Phase 이름

        Example:
            >>> phase_logger.start_phase(1, "Outline Generation")
            [2024-11-16 14:23:05] [INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━
            [2024-11-16 14:23:05] [INFO] Phase 1: Outline Generation
            [2024-11-16 14:23:05] [INFO] ━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        self.current_phase = phase_number
        self.phase_start_time = datetime.now()

        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.logger.info(f"Phase {phase_number}: {phase_name}")
        self.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def end_phase(self, phase_number: int, phase_name: str) -> None:
        """
        Phase 종료를 로깅하고 소요 시간을 출력합니다.

        Args:
            phase_number (int): Phase 번호
            phase_name (str): Phase 이름

        Example:
            >>> phase_logger.end_phase(1, "Outline Generation")
            [2024-11-16 14:24:35] [INFO] Phase 1 completed in 1.5 minutes
        """
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            minutes = elapsed / 60
            self.logger.info(f"Phase {phase_number} completed in {minutes:.1f} minutes")
        else:
            self.logger.info(f"Phase {phase_number} completed")

        self.current_phase = None
        self.phase_start_time = None

    def info(self, message: str) -> None:
        """
        INFO 레벨 로그를 출력합니다.

        Args:
            message (str): 로그 메시지
        """
        if self.current_phase:
            self.logger.info(f"  [{self.current_phase}] {message}")
        else:
            self.logger.info(message)

    def error(self, message: str) -> None:
        """
        ERROR 레벨 로그를 출력합니다.

        Args:
            message (str): 로그 메시지
        """
        if self.current_phase:
            self.logger.error(f"  [{self.current_phase}] {message}")
        else:
            self.logger.error(message)

    def warning(self, message: str) -> None:
        """
        WARNING 레벨 로그를 출력합니다.

        Args:
            message (str): 로그 메시지
        """
        if self.current_phase:
            self.logger.warning(f"  [{self.current_phase}] {message}")
        else:
            self.logger.warning(message)
