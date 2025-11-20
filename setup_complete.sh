#!/bin/bash
set -e

echo "=== AutoDrama 안정판 설치 시작 ==="

apt-get update

# -----------------------
# 1) LLM (vLLM + Qwen)
# -----------------------
echo "[1] LLM 환경 설치..."

pip install vllm==0.6.6.post1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages
pip install torch==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages
pip install huggingface_hub hf_transfer pyyaml --break-system-packages

# -----------------------
# 2) CosyVoice ONNX
# -----------------------
echo "[2] CosyVoice ONNX 설치..."

cd /workspace
rm -rf CosyVoice
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice

pip install onnxruntime soundfile jieba numpy==1.26.4 --break-system-packages
grep -v -E 'torch|deepspeed|lightning|diffusers|conformer' requirements.txt > req_onnx.txt
pip install -r req_onnx.txt --break-system-packages || true

# -----------------------
# 3) AutoDrama 프로젝트
# -----------------------
echo "[3] AutoDrama Clone..."

cd /workspace
rm -rf AutoDrama
git clone https://github.com/joosungmin1212-del/AutoDrama.git

# -----------------------
# 4) 캐시 폴더 + 모델 다운로드
# -----------------------
mkdir -p /workspace/huggingface_cache

echo "[4] Qwen 32B AWQ 다운로드..."
hf download Qwen/Qwen2.5-32B-Instruct-AWQ --cache-dir /workspace/huggingface_cache

echo "=== 설치 완료! ==="
