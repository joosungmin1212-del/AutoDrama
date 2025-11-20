"""
LLM 모듈
vLLM을 사용한 Qwen 2.5 32B AWQ 모델 추론
"""
import json
import yaml
from vllm import LLM, SamplingParams
from typing import Dict, Any, Optional, List
import os


class LLMEngine:
    """
    vLLM 기반 LLM 엔진
    Qwen2.5-32B-AWQ 모델 최적화
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        model_path: Optional[str] = None,
        max_model_len: int = 16384,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.92
    ):
        """
        LLM 엔진 초기화

        Args:
            config_path: 설정 파일 경로
            model_path: 모델 경로 (None이면 config에서 읽음)
            max_model_len: 최대 모델 컨텍스트 길이 (8192, 16384, 32768)
            tensor_parallel_size: 텐서 병렬화 (GPU 개수)
            gpu_memory_utilization: GPU 메모리 사용률 (0.0~1.0)
        """
        # Config 로드
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 기본 설정
            self.config = {
                'models': {
                    'llm': '/workspace/huggingface_cache/Qwen2.5-32B-AWQ',
                    'cache_dir': '/workspace/huggingface_cache'
                },
                'llm': {
                    'outline': {'temperature': 0.7, 'max_tokens': 4096},
                    'hook': {'temperature': 0.8, 'max_tokens': 2048},
                    'parts': {'temperature': 0.75, 'max_tokens': 16384}
                }
            }

        # 모델 경로 결정
        if model_path is None:
            model_path = self.config['models']['llm']

        print(f"Loading vLLM model: {model_path}")
        print(f"  - max_model_len: {max_model_len}")
        print(f"  - tensor_parallel_size: {tensor_parallel_size}")
        print(f"  - gpu_memory_utilization: {gpu_memory_utilization}")

        # vLLM 엔진 초기화
        self.llm = LLM(
            model=model_path,
            download_dir=self.config['models'].get('cache_dir'),
            tensor_parallel_size=tensor_parallel_size,
            quantization="awq",
            max_model_len=max_model_len,
            enforce_eager=False,
            enable_chunked_prefill=True,
            gpu_memory_utilization=gpu_memory_utilization,
            trust_remote_code=True
        )

        print("✓ vLLM model loaded successfully!")

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0
    ) -> str:
        """
        텍스트 생성 (범용 함수)

        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 생성 토큰 수
            temperature: 온도 (0.0~2.0)
            top_p: Top-p 샘플링
            stop: 정지 토큰 리스트
            presence_penalty: Presence penalty
            frequency_penalty: Frequency penalty

        Returns:
            생성된 텍스트
        """
        if stop is None:
            stop = ["\n以上", "\nThis", "</s>"]

        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        )

        outputs = self.llm.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text

    def generate_text_chunked(
        self,
        prompt: str,
        total_target_length: int = 30000,
        chunk_size: int = 8192,
        temperature: float = 0.7,
        overlap: int = 200
    ) -> str:
        """
        대규모 출력 생성 (청킹 방식)

        긴 텍스트(2~3만자)를 여러 번 나눠서 생성

        Args:
            prompt: 입력 프롬프트
            total_target_length: 목표 텍스트 길이 (자)
            chunk_size: 청크당 토큰 수
            temperature: 온도
            overlap: 청크 간 겹침 (자)

        Returns:
            전체 생성된 텍스트
        """
        result_text = ""
        chunk_count = 0
        max_chunks = (total_target_length // (chunk_size * 2)) + 2  # 안전 마진

        print(f"Chunked generation: target={total_target_length} chars, chunk_size={chunk_size} tokens")

        while len(result_text) < total_target_length and chunk_count < max_chunks:
            # 청크 프롬프트 생성
            if chunk_count == 0:
                chunk_prompt = prompt
            else:
                # 이전 텍스트 일부를 컨텍스트로 포함
                context = result_text[-overlap:] if len(result_text) > overlap else result_text
                chunk_prompt = f"{prompt}\n\n지금까지 작성된 내용:\n{context}\n\n이어서 계속 작성:"

            # 생성
            chunk_text = self.generate_text(
                prompt=chunk_prompt,
                max_tokens=chunk_size,
                temperature=temperature
            )

            # 결과 추가
            result_text += chunk_text
            chunk_count += 1

            print(f"  Chunk {chunk_count}: +{len(chunk_text)} chars (total: {len(result_text)})")

        return result_text

    def extract_first_json(self, text: str) -> str:
        """
        LLM이 JSON을 두 번 출력하는 경우 첫 번째 JSON만 추출

        Args:
            text: JSON이 포함된 텍스트

        Returns:
            첫 번째 JSON 문자열

        Raises:
            ValueError: JSON을 찾을 수 없거나 형식이 잘못된 경우
        """
        start = text.find("{")
        if start == -1:
            raise ValueError("JSON start '{' not found")

        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    # JSON 닫힘
                    return text[start:i+1]

        raise ValueError("JSON not properly closed")

    def call_llm(self, prompt: str, phase: str) -> Dict[str, Any]:
        """
        LLM 호출 (기존 인터페이스 유지)

        Args:
            prompt: 프롬프트
            phase: 단계 ("outline", "hook", "parts")

        Returns:
            JSON 파싱된 결과
        """
        # Phase별 파라미터 로드
        if phase == "outline":
            params = self.config['llm']['outline']
        elif phase == "hook":
            params = self.config['llm']['hook']
        else:
            params = self.config['llm']['parts']

        # 생성
        response_text = self.generate_text(
            prompt=prompt,
            max_tokens=params['max_tokens'],
            temperature=params['temperature'],
            stop=["\n以上", "\nThis", "}\n이", "</s>"]
        )

        print(f"\n[{phase}] Raw response preview:")
        print(response_text[:500])
        print(f"[{phase}] Total length: {len(response_text)} chars")

        # JSON 파싱
        try:
            # Code block 제거
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            # 첫 번째 JSON만 추출 (LLM이 JSON을 두 번 출력하는 경우 대비)
            json_text = self.extract_first_json(json_text)

            result = json.loads(json_text)
            print(f"✓ [{phase}] JSON parsed successfully!")
            return result

        except json.JSONDecodeError as e:
            print(f"✗ [{phase}] JSON parsing failed: {e}")
            print(f"Raw text:\n{response_text}")
            raise
        except ValueError as e:
            print(f"✗ [{phase}] JSON extraction failed: {e}")
            print(f"Raw text:\n{response_text}")
            raise

    def call_llm_text(self, prompt: str, phase: str) -> str:
        """
        LLM 호출 (순수 텍스트 반환)

        JSON 파싱 없이 순수 텍스트 반환

        Args:
            prompt: 프롬프트
            phase: 단계

        Returns:
            생성된 텍스트
        """
        if phase in self.config['llm']:
            params = self.config['llm'][phase]
        else:
            params = {'temperature': 0.7, 'max_tokens': 4096}

        return self.generate_text(
            prompt=prompt,
            max_tokens=params['max_tokens'],
            temperature=params['temperature']
        )


# ============================================
# 싱글톤 패턴
# ============================================
_llm_engine = None


def get_llm_engine(config_path: str = "config.yaml") -> LLMEngine:
    """
    LLM 엔진 싱글톤 접근

    Args:
        config_path: 설정 파일 경로

    Returns:
        LLMEngine 인스턴스
    """
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine(config_path)
    return _llm_engine


def reset_llm_engine():
    """LLM 엔진 리셋 (테스트용)"""
    global _llm_engine
    _llm_engine = None
