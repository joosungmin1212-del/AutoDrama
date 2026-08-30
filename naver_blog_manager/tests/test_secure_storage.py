from app.services import secure_storage


def test_protect_unprotect_roundtrip():
    plaintext = "sk-test-1234567890"
    stored = secure_storage.protect(plaintext)
    assert stored != plaintext  # 평문 그대로 저장되면 안 된다
    assert secure_storage.unprotect(stored) == plaintext


def test_protect_empty_string_stays_empty():
    assert secure_storage.protect("") == ""
    assert secure_storage.unprotect("") == ""


def test_unprotect_is_backward_compatible_with_old_plaintext_values():
    # 이 기능이 추가되기 전 버전에서 평문으로 저장된 값도 깨지지 않고 그대로 읽혀야 한다
    old_plaintext_value = "sk-old-plain-key"
    assert secure_storage.unprotect(old_plaintext_value) == old_plaintext_value


def test_protect_uses_fallback_on_non_windows(monkeypatch):
    monkeypatch.setattr(secure_storage, "_IS_WINDOWS", False)
    stored = secure_storage.protect("hello world")
    assert stored.startswith(secure_storage._FERNET_PREFIX)
    assert secure_storage.unprotect(stored) == "hello world"
