#!/usr/bin/env python3
"""
runpod에서 직접 실행하는 드라마 생성 스크립트
vLLM이 localhost에서 실행 중이라고 가정
"""

import sys
import os

# 환경변수 설정 (localhost vLLM 사용)
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["MODEL_NAME"] = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-70B-Instruct")

# main.py 임포트 및 실행
sys.path.insert(0, '/workspace/src')
from main import main

if __name__ == "__main__":
    main()
