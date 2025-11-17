# 🚀 runpod 배포 가이드

runpod Pod에 오디오 드라마 생성 시스템을 배포하는 방법입니다.

## 📦 방법 1: Docker 이미지로 배포 (권장)

### 1단계: Docker 이미지 빌드 및 푸시

로컬에서 실행:

```bash
# Docker 이미지 빌드
docker build -t your-dockerhub-username/audio-drama:latest .

# Docker Hub에 푸시
docker login
docker push your-dockerhub-username/audio-drama:latest
```

### 2단계: runpod Pod 생성

1. [runpod.io](https://runpod.io) 로그인
2. **Pods** → **+ Deploy**
3. GPU 선택 (A100 40GB 이상 권장)
4. **Custom Docker Image** 탭 선택
5. 이미지 입력: `your-dockerhub-username/audio-drama:latest`

**Environment Variables**:
```bash
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
GPU_MEMORY_UTILIZATION=0.9
MAX_MODEL_LEN=16384
HUGGING_FACE_HUB_TOKEN=your_hf_token_here
```

6. **Deploy** 클릭

### 3단계: 드라마 생성

Pod SSH 접속:

```bash
# SSH 접속 (runpod 웹에서 SSH 명령어 복사)
ssh root@xxx.runpod.io -p xxxxx

# 작업 디렉토리로 이동
cd /workspace

# 드라마 생성
python runpod_generate.py "며느리의 복수"

# 또는 직접 실행
python src/main.py "며느리의 복수"
```

생성된 파일은 `/workspace/output/`에 저장됩니다.

---

## 📁 방법 2: 수동 배포 (Docker 없이)

### 1단계: runpod Pod 생성

1. **Template**: `RunPod PyTorch 2.1` 또는 `vLLM` 선택
2. GPU 선택 (A100 40GB 이상)
3. **Deploy**

### 2단계: SSH 접속 및 설치

```bash
# SSH 접속
ssh root@xxx.runpod.io -p xxxxx

# 작업 디렉토리 생성
cd /workspace
mkdir audio-drama
cd audio-drama

# Git으로 코드 받기 (또는 직접 업로드)
git clone https://github.com/your-repo/작당모의.git .

# 또는 로컬에서 scp로 업로드
# scp -P xxxxx -r ./* root@xxx.runpod.io:/workspace/audio-drama/

# 패키지 설치
pip install -r requirements.txt
pip install vllm
```

### 3단계: vLLM 서버 시작

터미널 1 (vLLM 서버):

```bash
# vLLM 서버 실행
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --served-model-name meta-llama/Llama-3.1-70B-Instruct \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.9 \
  --port 8000 \
  --host 0.0.0.0
```

서버가 시작될 때까지 기다리세요 (5-10분 소요).

### 4단계: 드라마 생성

터미널 2 (새 SSH 세션):

```bash
cd /workspace/audio-drama

# .env 파일 생성
cat > .env << EOF
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=dummy
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
EOF

# 드라마 생성
python src/main.py "며느리의 복수"
```

---

## 📥 생성된 파일 다운로드

### 방법 1: scp로 다운로드

로컬 터미널에서:

```bash
# 전체 output 폴더 다운로드
scp -P xxxxx -r root@xxx.runpod.io:/workspace/audio-drama/output ./

# 특정 파일만 다운로드
scp -P xxxxx root@xxx.runpod.io:/workspace/audio-drama/output/parts/*.txt ./
```

### 방법 2: runpod 웹 파일 브라우저

1. runpod 웹에서 **File Browser** 클릭
2. `/workspace/audio-drama/output/` 이동
3. 파일 다운로드

### 방법 3: Google Drive/S3 업로드

Pod에서:

```bash
# rclone 설치 및 설정
pip install rclone-python

# Google Drive 마운트
rclone config  # 설정 진행

# 업로드
rclone copy /workspace/audio-drama/output gdrive:audio-drama-output
```

---

## 🔧 자동화 스크립트

한 번에 실행하는 스크립트:

```bash
#!/bin/bash
# auto_generate.sh

# vLLM 서버가 실행 중인지 확인
if ! curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "❌ vLLM 서버가 실행 중이 아닙니다."
    echo "먼저 vLLM 서버를 시작하세요:"
    echo "  bash runpod_start.sh"
    exit 1
fi

# 드라마 제목 입력
if [ -z "$1" ]; then
    echo "사용법: bash auto_generate.sh \"드라마 제목\""
    exit 1
fi

TITLE="$1"

echo "=========================================="
echo "드라마 생성 시작: $TITLE"
echo "=========================================="

cd /workspace/audio-drama
python src/main.py "$TITLE"

echo ""
echo "=========================================="
echo "✅ 생성 완료!"
echo "=========================================="
echo "출력 디렉토리: /workspace/audio-drama/output/"
echo ""
ls -lh /workspace/audio-drama/output/*/*.txt
ls -lh /workspace/audio-drama/output/*/*.json
```

사용법:

```bash
chmod +x auto_generate.sh
bash auto_generate.sh "며느리의 복수"
```

---

## 💰 비용 최적화

### 1. Pod 일시 중지

생성 후:

```bash
# 로컬에서 파일 다운로드
scp -P xxxxx -r root@xxx.runpod.io:/workspace/audio-drama/output ./

# runpod 웹에서 Pod Stop
```

### 2. 배치 처리

여러 드라마를 한 번에:

```bash
#!/bin/bash
# batch_generate.sh

TITLES=(
    "며느리의 복수"
    "시어머니의 눈물"
    "가족의 비밀"
)

for TITLE in "${TITLES[@]}"; do
    echo "생성 중: $TITLE"
    python src/main.py "$TITLE"
    sleep 10  # 서버 부하 방지
done
```

### 3. Spot 인스턴스

runpod에서 Spot 인스턴스 선택 (비용 ~70% 절감)

---

## 🐛 트러블슈팅

### vLLM 서버가 시작되지 않음

```bash
# GPU 확인
nvidia-smi

# CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"

# vLLM 재설치
pip uninstall vllm
pip install vllm --no-cache-dir
```

### 메모리 부족

```bash
# GPU 메모리 사용률 낮추기
GPU_MEMORY_UTILIZATION=0.8 bash runpod_start.sh

# 또는 작은 모델 사용
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct bash runpod_start.sh
```

### 생성 속도가 느림

```bash
# 더 큰 GPU로 변경 (A100 > A6000)
# 또는 max_tokens 줄이기 (src/main.py 수정)
```

---

## 📊 예상 시간 및 비용

| 모델 | GPU | 전체 생성 시간 | 예상 비용 |
|------|-----|--------------|----------|
| Llama 3.1 70B | A100 40GB | 15-25분 | $0.50-1.00 |
| Llama 3.1 70B | A100 80GB | 10-20분 | $0.80-1.50 |
| Llama 3.1 8B | RTX 4090 | 30-45분 | $0.20-0.40 |

---

**🎬 이제 runpod에서 오디오 드라마를 생성하세요!**
