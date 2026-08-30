from app.services import naver_browser


def test_session_state_is_not_stored_as_plaintext_json(tmp_path, monkeypatch):
    state_path = tmp_path / "naver_state.json"
    monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", state_path)

    fake_state = {"cookies": [{"name": "NID_AUT", "value": "secret-session-value"}]}
    naver_browser._save_state(fake_state)

    raw = state_path.read_text(encoding="utf-8")
    assert "secret-session-value" not in raw  # 평문으로 남으면 안 된다

    loaded = naver_browser._load_state()
    assert loaded == fake_state


def test_has_and_clear_saved_session(tmp_path, monkeypatch):
    state_path = tmp_path / "naver_state.json"
    monkeypatch.setattr(naver_browser.config, "NAVER_STATE_PATH", state_path)

    assert naver_browser.has_saved_session() is False
    naver_browser._save_state({"cookies": []})
    assert naver_browser.has_saved_session() is True

    naver_browser.clear_saved_session()
    assert naver_browser.has_saved_session() is False
