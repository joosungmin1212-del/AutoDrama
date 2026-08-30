"""이 서버는 127.0.0.1에만 열려 있지만, 같은 PC의 다른 Windows 계정/프로그램도
로컬호스트 포트에는 동일하게 접근할 수 있다. 이를 막기 위해 최초 실행 시 무작위 토큰을
하나 만들어두고, 그 토큰을 아는 브라우저(= run.py가 직접 열어준 그 창)만 /api/* 를 쓸 수
있게 한다.
"""
from __future__ import annotations

import os
import secrets

from .. import config

_TOKEN_PATH = config.DATA_DIR / ".access_token"


def get_or_create_token() -> str:
    if _TOKEN_PATH.exists():
        token = _TOKEN_PATH.read_text(encoding="utf-8").strip()
        if token:
            return token

    token = secrets.token_hex(16)
    _TOKEN_PATH.write_text(token, encoding="utf-8")
    try:
        os.chmod(_TOKEN_PATH, 0o600)
    except OSError:
        pass
    return token
