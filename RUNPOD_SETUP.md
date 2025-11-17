# 🚀 runpod에서 Llama 모델로 실행하기

이 가이드는 runpod에서 vLLM으로 Llama 모델을 실행하고 오디오 드라마를 생성하는 방법을 설명합니다.

## 📋 준비사항

1. runpod 계정
2. GPU 크레딧
3. 로컬 머신 (드라마 생성 스크립트 실행용)

---

## 🖥️ 1단계: runpod Pod 설정

### 1.1 Pod 생성

1. [runpod.io](https://runpod.io) 로그인
2. **Pods** → **+ Deploy** 클릭
3. GPU 선택 (권장: A100 40GB 이상)
4. **Template** → `vLLM` 템플릿 선택

### 1.2 모델 설정

**Environment Variables**에 다음 추가:

```bash
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
# 또는
# MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct  # 작은 GPU용
# MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

# HuggingFace 토큰 (gated 모델용)
HUGGING_FACE_HUB_TOKEN=your_hf_token_here
```

### 1.3 포트 설정

- **HTTP Ports** → `8000` 포트 노출
- **Deploy** 클릭

### 1.4 Pod 시작 확인

Pod가 시작되면:
1. **Connect** → **HTTP Service** URL 확인
2. 예시: `https://xxxxx-8000.proxy.runpod.net`
3. `/docs`를 붙여서 API 문서 확인: `https://xxxxx-8000.proxy.runpod.net/docs`

---

## 💻 2단계: 로컬 환경 설정

### 2.1 프로젝트 설정

```bash
cd 작당모의
pip install -r requirements.txt
```

### 2.2 환경변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 편집:

```bash
# LLM 백엔드
LLM_PROVIDER=openai

# runpod vLLM API 설정
OPENAI_API_KEY=dummy  # vLLM은 API 키가 필요 없음
OPENAI_BASE_URL=https://xxxxx-8000.proxy.runpod.net/v1  # 실제 Pod URL로 변경

# 모델명 (Pod에서 설정한 것과 동일)
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
```

---

## 🎬 3단계: 드라마 생성

### 3.1 기본 사용법

```bash
cd src
python main.py "드라마 제목"
```

### 3.2 환경변수 없이 직접 지정

```bash
python main.py "며느리의 복수" \
  --provider openai \
  --base-url https://xxxxx-8000.proxy.runpod.net/v1 \
  --model meta-llama/Llama-3.1-70B-Instruct
```

### 3.3 단계별 실행

```bash
# 1. 개요만 생성
python main.py "제목" --step outline

# 2. 훅까지 생성
python main.py "제목" --step hook

# 3. Part 1 생성
python main.py "제목" --step part1
```

---

## 🔧 고급 설정

### vLLM 파라미터 조정 (선택사항)

runpod Pod Environment Variables에서:

```bash
# GPU 메모리 최적화
GPU_MEMORY_UTILIZATION=0.9

# 최대 시퀀스 길이
MAX_MODEL_LEN=16384

# 배치 크기
MAX_NUM_BATCHED_TOKENS=8192
```

### 커스텀 vLLM 시작 명령어

Pod 생성 시 **Docker Command** 오버라이드:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --served-model-name meta-llama/Llama-3.1-70B-Instruct \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.9 \
  --port 8000
```

---

## 💰 비용 최적화

### 1. 작은 모델 사용

**Llama 3.1 8B** (RTX 4090에서 실행 가능):

```bash
# Pod 설정
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# .env 설정
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
```

### 2. Spot 인스턴스 사용

- runpod에서 **Spot** 인스턴스 선택 (비용 ~70% 절감)
- 단, 중단될 수 있으므로 중요한 작업은 저장 필수

### 3. 필요할 때만 Pod 실행

- 사용 후 **Stop** 클릭
- 다시 사용할 때 **Start** 클릭

---

## 🐛 트러블슈팅

### 문제 1: Connection Error

**증상**: `Connection refused` 또는 `Timeout`

**해결**:
1. Pod가 **Running** 상태인지 확인
2. Pod 로그에서 vLLM 서버 시작 확인
3. URL이 정확한지 확인 (끝에 `/v1` 필수)

### 문제 2: Model Loading 실패

**증상**: Pod가 시작되지 않음

**해결**:
1. GPU 메모리 부족 → 더 큰 GPU 선택
2. HuggingFace 토큰 누락 → `HUGGING_FACE_HUB_TOKEN` 추가
3. 모델명 오타 확인

### 문제 3: 생성이 너무 느림

**증상**: 응답이 1분 이상 걸림

**해결**:
1. 더 큰 GPU 사용 (A100 > A6000 > RTX 4090)
2. 작은 모델 사용 (8B < 70B)
3. `max_tokens` 줄이기 (코드에서 조정)

### 문제 4: 한글 생성 품질이 낮음

**증상**: 한글이 어색하거나 영어 섞임

**해결**:
1. **Qwen 2.5** 모델 사용 (한글 성능 우수):
   ```bash
   MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
   ```
2. 프롬프트에 "한국어로만 작성" 강조 추가

---

## 📊 모델 선택 가이드

| 모델 | GPU 요구사항 | 한글 품질 | 속도 | 비용 |
|------|-------------|----------|------|------|
| Llama 3.1 8B | RTX 4090 | ⭐⭐⭐ | 빠름 | $ |
| Llama 3.1 70B | A100 40GB | ⭐⭐⭐⭐ | 보통 | $$$ |
| Qwen 2.5 72B | A100 80GB | ⭐⭐⭐⭐⭐ | 느림 | $$$$ |

---

## 🎯 성능 벤치마크

전체 드라마 생성 (개요 + 훅 + Part 1-4 + 이미지):

- **Llama 3.1 70B (A100)**: 15-25분, ~$3-5
- **Llama 3.1 8B (RTX 4090)**: 30-45분, ~$1-2
- **Qwen 2.5 72B (A100)**: 25-40분, ~$5-8

---

## 🆚 로컬 vs runpod

| 항목 | 로컬 (Ollama) | runpod |
|------|--------------|---------|
| 초기 비용 | 높음 (GPU 구매) | 없음 |
| 사용 비용 | 전기료만 | 시간당 과금 |
| 속도 | GPU 성능에 따라 | A100으로 최고 속도 |
| 확장성 | 제한적 | 무제한 |
| 관리 | 직접 관리 필요 | 자동 관리 |

---

## 🔗 유용한 링크

- [runpod 가격표](https://www.runpod.io/pricing)
- [vLLM 문서](https://docs.vllm.ai/)
- [Llama 3.1 모델 카드](https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct)
- [Qwen 2.5 모델 카드](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)

---

**💡 팁**: 처음 시도할 때는 `--step outline`으로 개요만 먼저 생성해서 테스트하세요!
