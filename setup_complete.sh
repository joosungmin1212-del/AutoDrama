#!/bin/bash
set -e

echo "=== AutoDrama 안정판 (A안: ONNX Edition) 설치 시작 ==="

apt-get update

echo "[1] 필수 패키지 설치..."
pip install pyyaml ffmpeg-python huggingface_hub hf_transfer --break-system-packages

echo "[2] vLLM 설치 (0.6.6 + Torch 2.5.1)..."
pip install "vllm==0.6.6.post1" --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages
pip install torch==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[3] torchaudio 설치..."
pip install torchaudio==2.5.1 --extra-index-url https://download.pytorch.org/whl/cu124 --break-system-packages

echo "[4] CosyVoice ONNX 설치..."
cd /workspace
rm -rf CosyVoice
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice

echo "[4-1] ONNX 모델 전용 패키지 설치"
pip install onnxruntime soundfile jieba numpy==1.26.4 --break-system-packages

echo "[4-2] CosyVoice 파이썬 패키지 설치 (torch 제외)"
grep -v -E 'torch|deepspeed|lightning|diffusers|conformer' requirements.txt > req_onnx.txt
pip install -r req_onnx.txt --break-system-packages || true

echo "[5] AutoDrama clone..."
cd /workspace
rm -rf AutoDrama
git clone https://github.com/joosungmin1212-del/AutoDrama.git

echo "[6] 모델 캐시 폴더 생성..."
mkdir -p /workspace/huggingface_cache

echo "[7] Qwen2.5-32B-AWQ 다운로드..."
hf download Qwen/Qwen2.5-32B-Instruct-AWQ --cache-dir /workspace/huggingface_cache

echo "=== 설치 완료! ==="
