"""로컬 서버 실행 엔트리포인트.

사용법:
    pip install -r requirements.txt
    playwright install chromium
    python run.py

실행하면 이 스크립트가 직접 브라우저를 열어준다 (인증 토큰이 포함된 주소로).
다른 방법으로 http://127.0.0.1:8000 에 그냥 접속하면 "인증이 필요합니다" 오류가 뜨는데,
이건 같은 PC의 다른 프로그램/계정이 이 서버를 함부로 쓰지 못하게 막는 보호장치다
(app/services/access_token.py 참고). 이 스크립트로 연 브라우저 창을 그대로 쓰면 된다.
"""
from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from app import config
from app.services import access_token


def _open_browser_when_ready(url: str) -> None:
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    token = access_token.get_or_create_token()
    url = f"http://127.0.0.1:{config.PORT}/?token={token}"

    threading.Thread(target=_open_browser_when_ready, args=(url,), daemon=True).start()
    print(f"브라우저가 자동으로 열리지 않으면 이 주소로 직접 접속하세요: {url}")

    uvicorn.run("app.main:app", host="127.0.0.1", port=config.PORT, reload=False)
