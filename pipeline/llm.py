"""
LLM 모듈
vLLM을 사용한 Qwen 2.5 72B AWQ 모델 추론
"""
import json
import yaml
from vllm import LLM, SamplingParams
from typing import Dict, Any


class LLMEngine:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        print(f"Loading model: {self.config['models']['llm']}...")
        
        self.llm = LLM(
            model=self.config['models']['llm'],
            download_dir=self.config['models']['cache_dir'],
            tensor_parallel_size=1,
            quantization="awq",
            enforce_eager=True,
            enable_chunked_prefill=False,
            gpu_memory_utilization=0.85
        )
        
        print("Model loaded successfully!")
    
    def call_llm(self, prompt: str, phase: str):
        if phase == "outline":
            params = self.config['llm']['outline']
        elif phase == "hook":
            params = self.config['llm']['hook']
        else:
            params = self.config['llm']['parts']
        
        sampling_params = SamplingParams(
            temperature=params['temperature'],
            max_tokens=params['max_tokens']
        )
        
        outputs = self.llm.generate([prompt], sampling_params)
        response_text = outputs[0].outputs[0].text
        
        print(f"\n[{phase}] Raw response:")
        print(response_text[:500])
        
        try:
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
            
            result = json.loads(json_text)
            print(f"[{phase}] JSON parsed successfully!")
            return result
            
        except json.JSONDecodeError as e:
            print(f"[{phase}] JSON parsing failed: {e}")
            print(f"Raw text: {response_text}")
            raise


_llm_engine = None

def get_llm_engine(config_path: str = "config.yaml"):
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine(config_path)
    return _llm_engine