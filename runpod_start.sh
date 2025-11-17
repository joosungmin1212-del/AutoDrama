#!/bin/bash
set -e

echo "=========================================="
echo "오디오 드라마 생성 시스템 시작"
echo "=========================================="

# 환경변수 기본값 설정
MODEL_NAME=${MODEL_NAME:-"meta-llama/Llama-3.1-70B-Instruct"}
GPU_MEMORY_UTILIZATION=${GPU_MEMORY_UTILIZATION:-"0.9"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-"16384"}
PORT=${PORT:-"8000"}

echo "모델: $MODEL_NAME"
echo "GPU 메모리 사용률: $GPU_MEMORY_UTILIZATION"
echo "최대 시퀀스 길이: $MAX_MODEL_LEN"
echo ""

# vLLM 서버 백그라운드 실행
echo "vLLM 서버 시작 중..."
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_NAME \
    --served-model-name $MODEL_NAME \
    --max-model-len $MAX_MODEL_LEN \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --port $PORT \
    --host 0.0.0.0 &

VLLM_PID=$!
echo "vLLM 서버 PID: $VLLM_PID"

# vLLM 서버 준비 대기
echo "vLLM 서버 준비 대기 중..."
until curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; do
    echo "대기 중..."
    sleep 5
done

echo ""
echo "=========================================="
echo "✅ vLLM 서버 준비 완료!"
echo "=========================================="
echo ""
echo "사용 방법:"
echo "1. SSH로 접속"
echo "2. cd /workspace"
echo "3. python src/main.py \"드라마 제목\""
echo ""
echo "예시:"
echo "  python src/main.py \"며느리의 복수\""
echo ""
echo "=========================================="

# vLLM 프로세스 유지
wait $VLLM_PID
