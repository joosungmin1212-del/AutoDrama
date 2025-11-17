# runpod용 오디오 드라마 생성 시스템
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# 작업 디렉토리
WORKDIR /workspace

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# vLLM 설치
RUN pip install vllm

# 프로젝트 파일 복사
COPY src/ /workspace/src/
COPY output/ /workspace/output/
COPY config/ /workspace/config/
COPY prompts.md /workspace/
COPY workflow.md /workspace/
COPY README.md /workspace/

# 시작 스크립트 복사
COPY runpod_start.sh /workspace/
RUN chmod +x /workspace/runpod_start.sh

# 포트 노출
EXPOSE 8000 8888

# 시작 명령어
CMD ["/workspace/runpod_start.sh"]
