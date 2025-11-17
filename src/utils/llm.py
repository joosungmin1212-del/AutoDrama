"""
llm.py
LLM API 호출 유틸리티
다양한 LLM 백엔드 지원 (OpenAI 호환, Anthropic)
"""

import os
import json
from typing import Dict, Any, Optional


class LLMClient:
    """
    LLM API 클라이언트
    OpenAI 호환 API (runpod, vLLM, Ollama 등) 및 Anthropic API 지원
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: str = "openai"  # "openai" 또는 "anthropic"
    ):
        """
        LLM 클라이언트 초기화

        Args:
            api_key: API 키 (None인 경우 환경변수에서 가져옴)
            model: 사용할 모델명
            base_url: API 베이스 URL (OpenAI 호환 API용)
            provider: "openai" (runpod, vLLM 등) 또는 "anthropic"
        """
        self.provider = provider.lower()

        # 환경변수에서 설정 가져오기
        if self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "dummy")
            self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
            self.model = model or os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-70B-Instruct")

            # OpenAI 클라이언트 임포트 및 초기화
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError(
                    "OpenAI 패키지가 설치되지 않았습니다. "
                    "pip install openai를 실행하세요."
                )

        elif self.provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            self.model = model or os.getenv("MODEL_NAME", "claude-sonnet-4-5-20250929")

            # Anthropic 클라이언트 임포트 및 초기화
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic 패키지가 설치되지 않았습니다. "
                    "pip install anthropic을 실행하세요."
                )

        else:
            raise ValueError(f"지원하지 않는 provider: {provider}")

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 8000,
        temperature: float = 1.0
    ) -> str:
        """
        텍스트 생성

        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 생성 온도 (0.0 ~ 1.0)

        Returns:
            생성된 텍스트
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return message.content[0].text

        except Exception as e:
            raise Exception(f"LLM API 호출 실패: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 8000,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        JSON 형식 응답 생성

        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 생성 온도

        Returns:
            파싱된 JSON 딕셔너리
        """
        text = self.generate_text(prompt, max_tokens, temperature)

        try:
            # JSON 블록 추출 시도
            if "```json" in text:
                json_text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_text = text.split("```")[1].split("```")[0].strip()
            else:
                json_text = text.strip()

            return json.loads(json_text)

        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {str(e)}\n응답:\n{text}")
