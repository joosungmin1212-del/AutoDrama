"""
LLM 모듈 (72B 최적화 + 안정화 로직 강화)
vLLM을 사용한 Qwen 2.5 72B AWQ 모델 추론
"""
import json
import yaml
import re
import time
from vllm import LLM, SamplingParams
from typing import Dict, Any, Optional, List
import os


class LLMEngine:
    """
    vLLM 기반 LLM 엔진
    Qwen2.5-72B-AWQ 모델 최적화
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        model_path: Optional[str] = None,
        max_model_len: int = 16384,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.92
    ):
        """LLM 엔진 초기화"""
        # Config 로드
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 기본 설정 (72B 최적화)
            self.config = {
                'models': {
                    'llm': '/workspace/huggingface_cache/Qwen2.5-72B-AWQ',
                    'cache_dir': '/workspace/huggingface_cache'
                },
                'llm': {
                    'outline': {'temperature': 0.65, 'max_tokens': 7000, 'top_p': 0.92, 'top_k': 40, 'repetition_penalty': 1.13},
                    'hook': {'temperature': 0.75, 'max_tokens': 2048, 'top_p': 0.92, 'top_k': 40, 'repetition_penalty': 1.13},
                    'parts': {'temperature': 0.70, 'max_tokens': 5000, 'top_p': 0.92, 'top_k': 40, 'repetition_penalty': 1.13}
                }
            }

        if model_path is None:
            model_path = self.config['models']['llm']

        print(f"Loading vLLM model: {model_path}")
        print(f"  - max_model_len: {max_model_len}")
        print(f"  - tensor_parallel_size: {tensor_parallel_size}")

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
        top_p: float = 0.92,
        top_k: int = 40,
        repetition_penalty: float = 1.13,
        stop: Optional[List[str]] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0
    ) -> str:
        """텍스트 생성 (72B 최적화 파라미터)"""
        if stop is None:
            stop = ["\n以上", "\nThis", "</s>", "}\n이"]

        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        )

        outputs = self.llm.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text

    def extract_first_json(self, text: str) -> str:
        """첫 번째 JSON만 추출 (중복 출력 방지)"""
        # UTF-8 BOM 제거
        text = text.replace('\ufeff', '')

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
                    return text[start:i+1]

        raise ValueError("JSON not properly closed")

    def clean_json_string(self, json_str: str) -> str:
        """JSON 문자열 정리 (invalid escape 제거)"""
        # 코드블록 제거
        json_str = json_str.replace("```json", "").replace("```", "")

        # UTF-8 BOM 제거
        json_str = json_str.replace('\ufeff', '')

        # null, None, N/A 처리
        json_str = re.sub(r':\s*null\s*,', ': "",', json_str)
        json_str = re.sub(r':\s*None\s*,', ': "",', json_str)
        json_str = re.sub(r':\s*"N/A"\s*,', ': "",', json_str)

        return json_str.strip()

    def detect_chinese(self, text: str) -> bool:
        """중국어 감지"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_chars > 5

    def call_llm(self, prompt: str, phase: str, max_retry: int = 3) -> Dict[str, Any]:
        """
        LLM 호출 (JSON 모드) - 재시도 로직 포함

        Args:
            prompt: 프롬프트
            phase: 단계 ("outline", "hook", "parts")
            max_retry: 최대 재시도 횟수

        Returns:
            JSON 파싱된 결과
        """
        # Phase별 파라미터 로드 (72B 최적화)
        if phase == "outline":
            params = self.config['llm'].get('outline', {
                'temperature': 0.65,
                'max_tokens': 7000,
                'top_p': 0.92,
                'top_k': 40,
                'repetition_penalty': 1.13
            })
        elif phase == "hook":
            params = self.config['llm'].get('hook', {
                'temperature': 0.75,
                'max_tokens': 2048,
                'top_p': 0.92,
                'top_k': 40,
                'repetition_penalty': 1.13
            })
        else:
            params = self.config['llm'].get('parts', {
                'temperature': 0.70,
                'max_tokens': 5000,
                'top_p': 0.92,
                'top_k': 40,
                'repetition_penalty': 1.13
            })

        for attempt in range(max_retry):
            try:
                print(f"\n[{phase}] Attempt {attempt + 1}/{max_retry}")

                # 1. LLM 생성
                response_text = self.generate_text(
                    prompt=prompt,
                    max_tokens=params.get('max_tokens', 4096),
                    temperature=params.get('temperature', 0.7),
                    top_p=params.get('top_p', 0.92),
                    top_k=params.get('top_k', 40),
                    repetition_penalty=params.get('repetition_penalty', 1.13),
                    stop=["\n以上", "\nThis", "}\n이", "</s>", "}\n\n"]
                )

                print(f"[{phase}] Raw response: {len(response_text)} chars")
                print(f"[{phase}] Preview: {response_text[:300]}")

                # 2. 중국어 감지
                if self.detect_chinese(response_text):
                    print(f"✗ [{phase}] Chinese detected, retrying...")
                    time.sleep(1)
                    continue

                # 3. JSON 추출
                json_candidate = self.extract_first_json(response_text)
                json_candidate = self.clean_json_string(json_candidate)

                # 4. JSON 파싱
                result = json.loads(json_candidate)
                print(f"✓ [{phase}] JSON parsed successfully!")
                return result

            except json.JSONDecodeError as e:
                print(f"✗ [{phase}] JSON decode error: {e}")
                if attempt < max_retry - 1:
                    print(f"   Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("----- RAW TEXT -----")
                    print(response_text)
                    print("--------------------")
                    raise

            except Exception as e:
                print(f"✗ [{phase}] Error: {e}")
                if attempt < max_retry - 1:
                    print(f"   Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    raise

        raise RuntimeError(f"Failed to generate valid JSON after {max_retry} attempts")

    def call_llm_text(self, prompt: str, phase: str, max_retry: int = 2) -> str:
        """
        LLM 호출 (텍스트 모드) - 재시도 로직 포함

        Args:
            prompt: 프롬프트
            phase: 단계
            max_retry: 최대 재시도 횟수

        Returns:
            생성된 텍스트
        """
        if phase in self.config['llm']:
            params = self.config['llm'][phase]
        else:
            params = {'temperature': 0.7, 'max_tokens': 4096, 'top_p': 0.92, 'top_k': 40, 'repetition_penalty': 1.13}

        for attempt in range(max_retry):
            try:
                print(f"\n[{phase}] Text generation attempt {attempt + 1}/{max_retry}")

                response_text = self.generate_text(
                    prompt=prompt,
                    max_tokens=params.get('max_tokens', 4096),
                    temperature=params.get('temperature', 0.7),
                    top_p=params.get('top_p', 0.92),
                    top_k=params.get('top_k', 40),
                    repetition_penalty=params.get('repetition_penalty', 1.13)
                )

                # 중국어 감지
                if self.detect_chinese(response_text):
                    print(f"✗ [{phase}] Chinese detected, retrying...")
                    if attempt < max_retry - 1:
                        time.sleep(1)
                        continue
                    else:
                        print(f"⚠ [{phase}] Warning: Chinese detected but no retries left")

                print(f"✓ [{phase}] Text generated: {len(response_text)} chars")
                return response_text

            except Exception as e:
                print(f"✗ [{phase}] Error: {e}")
                if attempt < max_retry - 1:
                    time.sleep(2)
                else:
                    raise

        raise RuntimeError(f"Failed to generate text after {max_retry} attempts")


# 싱글톤 패턴
_llm_engine = None


def get_llm_engine(config_path: str = "config.yaml") -> LLMEngine:
    """LLM 엔진 싱글톤 반환"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine(config_path)
    return _llm_engine


def reset_llm_engine():
    """LLM 엔진 리셋 (테스트용)"""
    global _llm_engine
    _llm_engine = None
