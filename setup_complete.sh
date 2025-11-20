#!/bin/bash
set -e

echo "=== AutoDrama Full Install (Qwen2.5-32B-AWQ + 충돌 제로 Edition) ==="

apt-get update

# ============================================
# 1) Core Python Packages (충돌 방지 버전 고정)
# ============================================
echo "[1] Core 패키지 설치 (버전 고정)..."
pip install --break-system-packages \
  "numpy>=1.26.0,<2.0.0" \
  "pyyaml>=6.0" \
  "ffmpeg-python>=0.2.0"

# ============================================
# 2) HuggingFace 생태계 (버전 제한)
# ============================================
echo "[2] HuggingFace 생태계 설치..."
pip install --break-system-packages \
  "huggingface-hub>=0.23.0,<0.30.0" \
  "hf-transfer>=0.1.0" \
  "transformers==4.45.2" \
  "tokenizers==0.20.3"

# ============================================
# 3) PyTorch 2.5.1 + cu124 (vLLM 호환)
# ============================================
echo "[3] PyTorch 2.5.1 + cu124 설치..."
pip install --break-system-packages \
  torch==2.5.1 \
  torchaudio==2.5.1 \
  --extra-index-url https://download.pytorch.org/whl/cu124

# ============================================
# 4) vLLM 0.6.6.post1 (Qwen2.5-32B-AWQ용)
# ============================================
echo "[4] vLLM 0.6.6.post1 설치..."
pip install --break-system-packages "vllm==0.6.6.post1"

# ============================================
# 5) Whisper-CTranslate2 (자막 생성)
# ============================================
echo "[5] whisper-ctranslate2 설치 (faster-whisper 대체)..."
pip install --break-system-packages "whisper-ctranslate2>=0.4.3"

# ============================================
# 6) XTTS (TTS)
# ============================================
echo "[6] XTTS 설치..."
pip install --break-system-packages "TTS>=0.22.0"

# ============================================
# 7) 불필요한 패키지 제거
# ============================================
echo "[7] 충돌 패키지 제거..."
pip uninstall -y faster-whisper 2>/dev/null || true
rm -rf /workspace/CosyVoice || true

# ============================================
# 8) 모델 캐시 폴더 생성
# ============================================
echo "[8] 모델 캐시 폴더 생성..."
mkdir -p /workspace/huggingface_cache

# ============================================
# 9) Qwen2.5-32B-AWQ 사전 다운로드
# ============================================
echo "[9] Qwen2.5-32B-AWQ 다운로드..."
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ \
  --local-dir /workspace/huggingface_cache/Qwen2.5-32B-AWQ \
  --local-dir-use-symlinks False

# ============================================
# 10) 버전 확인
# ============================================
echo ""
echo "=== 설치된 패키지 버전 확인 ==="
pip show vllm torch transformers tokenizers numpy huggingface-hub whisper-ctranslate2 TTS | grep -E "Name|Version"

echo ""
echo "=== 설치 완료! ==="
echo "충돌 없는 환경이 구성되었습니다."
