"""로컬에 저장하는 민감정보(네이버 로그인 세션, OpenAI API 키)를 평문으로 남기지 않기 위한 암호화 유틸.

- Windows(실제 배포 대상): DPAPI(CryptProtectData/CryptUnprotectData)로 암호화한다.
  DPAPI는 "현재 로그인한 Windows 계정"에 키가 묶여서, 같은 PC의 다른 계정이나 파일만
  복사해간 사람은 복호화할 수 없다. 우리가 따로 키를 관리할 필요도 없다.
- Windows가 아닌 환경(개발/테스트용 리눅스/맥): DPAPI를 쓸 수 없으므로, 로컬에 무작위로
  생성한 키 파일(`data/.secret.key`)로 Fernet 대칭키 암호화를 한다. 평문보다는 훨씬 낫지만
  키 파일이 유출되면 의미가 없어지므로, 진짜 배포 대상은 어디까지나 Windows(DPAPI)다.
- 이전 버전에서 평문으로 저장된 값도 그대로 읽을 수 있게 하위 호환을 유지한다
  (마이그레이션 없이도 다음 저장 시 자동으로 암호화된다).
"""
from __future__ import annotations

import base64
import os
import sys

from .. import config

_IS_WINDOWS = sys.platform == "win32"
_DPAPI_PREFIX = "dpapi:"
_FERNET_PREFIX = "fernet:"


def _dpapi_protect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    def _blob(buf: ctypes.Array) -> DATA_BLOB:
        return DATA_BLOB(len(buf), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _blob(in_buf)
    blob_out = DATA_BLOB()
    if not crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise OSError("DPAPI CryptProtectData 호출에 실패했습니다.")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    import ctypes
    import ctypes.wintypes as wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    def _blob(buf: ctypes.Array) -> DATA_BLOB:
        return DATA_BLOB(len(buf), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    in_buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _blob(in_buf)
    blob_out = DATA_BLOB()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise OSError("DPAPI CryptUnprotectData 호출에 실패했습니다.")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)


def _get_fallback_key() -> bytes:
    from cryptography.fernet import Fernet

    key_path = config.DATA_DIR / ".secret.key"
    if key_path.exists():
        return key_path.read_bytes()
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return key


def protect(plaintext: str) -> str:
    """평문 문자열을 암호화된 저장용 문자열로 바꾼다. 빈 문자열은 그대로 둔다."""
    if not plaintext:
        return ""

    if _IS_WINDOWS:
        try:
            encrypted = _dpapi_protect(plaintext.encode("utf-8"))
            return _DPAPI_PREFIX + base64.b64encode(encrypted).decode("ascii")
        except Exception:  # noqa: BLE001 - DPAPI 실패 시 폴백으로 진행
            pass

    from cryptography.fernet import Fernet

    token = Fernet(_get_fallback_key()).encrypt(plaintext.encode("utf-8"))
    return _FERNET_PREFIX + token.decode("ascii")


def unprotect(stored: str) -> str:
    """protect()로 저장한 값을 평문으로 복원한다. 옛 버전의 평문 값도 그대로 반환한다."""
    if not stored:
        return ""

    if stored.startswith(_DPAPI_PREFIX):
        raw = base64.b64decode(stored[len(_DPAPI_PREFIX):].encode("ascii"))
        return _dpapi_unprotect(raw).decode("utf-8")

    if stored.startswith(_FERNET_PREFIX):
        from cryptography.fernet import Fernet

        token = stored[len(_FERNET_PREFIX):].encode("ascii")
        return Fernet(_get_fallback_key()).decrypt(token).decode("utf-8")

    # 이전 버전에서 평문으로 저장된 값 (하위 호환) - 다음 저장 시 자동으로 암호화됨
    return stored
