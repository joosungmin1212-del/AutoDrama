# 🎭 작당모의 - 오디오 드라마 자동 생성 시스템

50~80대 한국 여성을 위한 유튜브 오디오 드라마를 AI로 자동 생성하는 시스템입니다.

## 📋 프로젝트 개요

이 시스템은 Claude AI를 활용하여 다음을 자동으로 생성합니다:

1. **전체 개요** (3,000자) - 등장인물, 갈등, 전환점, 결말
2. **훅** (500자) - 극적인 오프닝 장면
3. **본편** (Part 1-4, 각 12,000자) - 2시간 분량의 오디오 드라마 대본
4. **이미지 프롬프트** - 훅 5장면 + 메인 15장면의 FLUX 이미지 생성 프롬프트

## 🏗️ 프로젝트 구조

```
작당모의/
├── src/
│   ├── generators/          # 대본/프롬프트 생성 모듈
│   │   ├── outline.py       # 개요 생성
│   │   ├── hook.py          # 훅 생성
│   │   ├── part.py          # 파트 1-4 생성
│   │   ├── hook_images.py   # 훅 이미지 프롬프트
│   │   └── main_images.py   # 메인 이미지 프롬프트
│   ├── utils/               # 유틸리티
│   │   ├── llm.py           # LLM API 클라이언트
│   │   └── file_handler.py  # 파일 입출력
│   └── main.py              # 메인 실행 스크립트
├── output/                  # 생성된 파일 저장
│   ├── outlines/
│   ├── hooks/
│   ├── parts/
│   └── images/
├── config/
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 설치 및 설정

### 1. 필수 요구사항

- Python 3.8 이상
- **LLM 백엔드** (둘 중 하나 선택):
  - **runpod + Llama** (권장) - GPU 서버 대여
  - **Anthropic Claude API** - 유료 API
  - **로컬 Ollama** - 로컬 GPU 필요

### 2. 설치

```bash
# 저장소 클론 또는 다운로드
cd 작당모의

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. LLM 백엔드 설정

#### 옵션 A: runpod + Llama (권장)

runpod에서 vLLM Pod를 띄우고 설정하세요.
**상세 가이드**: [RUNPOD_SETUP.md](RUNPOD_SETUP.md) 참고

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 편집:
```bash
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://your-pod-id-8000.proxy.runpod.net/v1
MODEL_NAME=meta-llama/Llama-3.1-70B-Instruct
```

#### 옵션 B: Anthropic Claude API

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 편집:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
MODEL_NAME=claude-sonnet-4-5-20250929
```

#### 옵션 C: 로컬 Ollama

```bash
# Ollama 설치 후 모델 실행
ollama serve
ollama pull llama3.1:70b

# .env 설정
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama3.1:70b
```

## 💻 사용법

### 기본 사용법

전체 드라마 생성 (개요 + 훅 + Part 1-4 + 이미지):

```bash
cd src
python main.py "드라마 제목"
```

### 단계별 실행

특정 단계만 실행하려면 `--step` 옵션 사용:

```bash
# 개요만 생성
python main.py "드라마 제목" --step outline

# 훅까지 생성
python main.py "드라마 제목" --step hook

# Part 1만 생성
python main.py "드라마 제목" --step part1
```

### 옵션

```bash
python main.py "드라마 제목" [옵션]

옵션:
  --api-key API_KEY      Anthropic API 키 (환경변수 대신 사용)
  --output-dir PATH      출력 디렉토리 (기본값: output)
  --step STEP            실행 단계: outline, hook, part1-4, all (기본값: all)
```

### 사용 예시

```bash
# 예시 1: runpod로 전체 생성 (.env 설정 사용)
python main.py "며느리의 복수"

# 예시 2: runpod URL 직접 지정
python main.py "시어머니의 눈물" \
  --provider openai \
  --base-url https://xxxxx-8000.proxy.runpod.net/v1 \
  --model meta-llama/Llama-3.1-70B-Instruct

# 예시 3: Claude API 사용
python main.py "가족의 비밀" \
  --provider anthropic \
  --api-key sk-ant-xxxxx

# 예시 4: 다른 출력 디렉토리 사용
python main.py "복수의 시작" --output-dir ../my_output
```

## 📝 생성되는 파일

### 출력 구조

```
output/
├── outlines/
│   └── 드라마제목_outline_20250117_143022.json
├── hooks/
│   └── 드라마제목_hook_20250117_143045.txt
├── parts/
│   ├── 드라마제목_part1_20250117_143120.txt
│   ├── 드라마제목_part2_20250117_143250.txt
│   ├── 드라마제목_part3_20250117_143420.txt
│   └── 드라마제목_part4_20250117_143550.txt
└── images/
    ├── 드라마제목_hook_images_20250117_143610.json
    └── 드라마제목_main_images_20250117_143650.json
```

### 파일 형식

- **개요**: JSON 형식 (등장인물, 갈등, 전환점 등 구조화된 데이터)
- **훅/파트**: 순수 텍스트 형식 (오디오 드라마 대본)
- **이미지 프롬프트**: JSON 형식 (FLUX 이미지 생성용 영어 프롬프트)

## 🎨 특징

### 문체 특징

- **전지적 3인칭 시점**
- **나레이션 90-95%** - 대사는 극적인 순간에만 최소한으로 사용
- **오디오 중심** - 소리와 의성어로 상황 전달
- **자연스러운 종결어미** - ~습니다/~어요/~죠 혼용
- **감정은 신체 반응으로** - "슬펐다" → "눈물이 흘렀다"

### 대상 청중

- 50~80대 한국 여성
- 현실적 가족/인간관계 갈등
- 복잡한 SF, 판타지 지양
- 감동, 복수, 치유 등 다양한 주제

## 🔧 개발

### 모듈 설명

- **generators/outline.py**: 드라마 전체 개요 프롬프트 생성
- **generators/hook.py**: 극적인 오프닝 훅 프롬프트 생성
- **generators/part.py**: Part 1-4 본편 프롬프트 생성
- **generators/hook_images.py**: 훅 5장면 이미지 프롬프트 생성
- **generators/main_images.py**: 메인 15장면 이미지 프롬프트 생성
- **utils/llm.py**: Claude API 호출 래퍼
- **utils/file_handler.py**: 파일 저장/로드 유틸리티

### 커스터마이징

`src/generators/` 안의 각 모듈에서 프롬프트를 수정하여 문체나 스타일을 조정할 수 있습니다.

## 📄 라이선스

이 프로젝트는 개인 및 교육 목적으로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 개선 제안은 이슈로 등록해주세요.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 통해 연락주세요.

---

**🎬 즐거운 드라마 제작 되세요!**
