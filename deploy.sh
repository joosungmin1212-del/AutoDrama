#!/bin/bash
# runpod에 수동으로 배포하는 스크립트

set -e

echo "=========================================="
echo "runpod 배포 스크립트"
echo "=========================================="
echo ""

# runpod SSH 정보 입력
read -p "runpod SSH 주소 (예: root@xxx.runpod.io): " SSH_HOST
read -p "runpod SSH 포트 (예: 12345): " SSH_PORT

SSH_TARGET="$SSH_HOST"
SSH_CMD="ssh -p $SSH_PORT $SSH_TARGET"
SCP_CMD="scp -P $SSH_PORT"

echo ""
echo "연결 테스트 중..."
if ! $SSH_CMD "echo 'SSH 연결 성공'" > /dev/null 2>&1; then
    echo "❌ SSH 연결 실패. 주소와 포트를 확인하세요."
    exit 1
fi

echo "✅ SSH 연결 성공"
echo ""

# 작업 디렉토리 생성
echo "작업 디렉토리 생성 중..."
$SSH_CMD "mkdir -p /workspace/audio-drama"

# 파일 복사
echo "파일 업로드 중..."
echo "  - 소스 코드..."
$SCP_CMD -r src/ $SSH_TARGET:/workspace/audio-drama/

echo "  - 설정 파일..."
$SCP_CMD requirements.txt .env.example $SSH_TARGET:/workspace/audio-drama/

echo "  - 스크립트..."
$SCP_CMD runpod_start.sh runpod_generate.py $SSH_TARGET:/workspace/audio-drama/
$SSH_CMD "chmod +x /workspace/audio-drama/runpod_start.sh"
$SSH_CMD "chmod +x /workspace/audio-drama/runpod_generate.py"

echo "  - 문서..."
$SCP_CMD README.md workflow.md prompts.md RUNPOD_DEPLOY.md $SSH_TARGET:/workspace/audio-drama/

echo "  - 디렉토리 생성..."
$SSH_CMD "mkdir -p /workspace/audio-drama/output/{outlines,hooks,parts,images}"
$SSH_CMD "mkdir -p /workspace/audio-drama/config"

# 패키지 설치
echo ""
echo "Python 패키지 설치 중..."
$SSH_CMD "cd /workspace/audio-drama && pip install -q -r requirements.txt"

# vLLM 설치 확인
echo "vLLM 설치 확인 중..."
if ! $SSH_CMD "python -c 'import vllm' 2>/dev/null"; then
    echo "vLLM 설치 중... (5-10분 소요)"
    $SSH_CMD "pip install -q vllm"
fi

# .env 파일 생성
echo ""
echo ".env 파일 생성 중..."
$SSH_CMD "cat > /workspace/audio-drama/.env << 'EOF'
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=dummy
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
EOF"

echo ""
echo "=========================================="
echo "✅ 배포 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo ""
echo "1. SSH 접속:"
echo "   ssh -p $SSH_PORT $SSH_TARGET"
echo ""
echo "2. vLLM 서버 시작:"
echo "   cd /workspace/audio-drama"
echo "   bash runpod_start.sh"
echo ""
echo "3. 새 터미널에서 SSH 재접속 후 드라마 생성:"
echo "   cd /workspace/audio-drama"
echo "   python runpod_generate.py \"며느리의 복수\""
echo ""
echo "=========================================="
