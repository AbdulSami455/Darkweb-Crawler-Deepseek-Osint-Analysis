#!/usr/bin/env python3
"""
Advanced model management for multiple LLM providers and models.
Supports model validation, fallback logic, and model-specific optimizations.
"""

import os
import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    id: str
    name: str
    provider: ModelProvider
    max_tokens: int
    cost_per_1k_tokens: float
    supports_structured_output: bool
    supports_streaming: bool
    recommended_for_osint: bool
    fallback_models: List[str]
    optimal_temperature: float
    optimal_max_tokens: int
    custom_prompt_template: Optional[str] = None


class ModelManager:
    """Advanced model management with validation and fallback logic."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self._model_cache = {}
        self._availability_cache = {}
        self._cache_expiry = 300  # 5 minutes
        
        # Initialize model configurations
        self._initialize_model_configs()
    
    def _initialize_model_configs(self):
        """Initialize comprehensive model configurations."""
        self.model_configs = {
            # DeepSeek models
            "deepseek/deepseek-r1:free": ModelConfig(
                id="deepseek/deepseek-r1:free",
                name="DeepSeek R1 (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["deepseek/deepseek-r1-0528:free", "anthropic/claude-3.5-sonnet:free"],
                optimal_temperature=0.3,
                optimal_max_tokens=2000,
                custom_prompt_template="deepseek_osint"
            ),
            "deepseek/deepseek-r1-0528:free": ModelConfig(
                id="deepseek/deepseek-r1-0528:free",
                name="DeepSeek R1 0528 (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["deepseek/deepseek-r1:free", "anthropic/claude-3.5-sonnet:free"],
                optimal_temperature=0.3,
                optimal_max_tokens=2000,
                custom_prompt_template="deepseek_osint"
            ),
            
            # Claude models
            "anthropic/claude-3.5-sonnet:free": ModelConfig(
                id="anthropic/claude-3.5-sonnet:free",
                name="Claude 3.5 Sonnet (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["anthropic/claude-3-haiku:free", "openai/gpt-3.5-turbo:free"],
                optimal_temperature=0.2,
                optimal_max_tokens=2500,
                custom_prompt_template="claude_osint"
            ),
            "anthropic/claude-3-haiku:free": ModelConfig(
                id="anthropic/claude-3-haiku:free",
                name="Claude 3 Haiku (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=False,
                fallback_models=["openai/gpt-3.5-turbo:free", "meta-llama/llama-3.1-8b-instruct:free"],
                optimal_temperature=0.3,
                optimal_max_tokens=2000,
                custom_prompt_template="claude_osint"
            ),
            
            # GPT models
            "openai/gpt-4:free": ModelConfig(
                id="openai/gpt-4:free",
                name="GPT-4 (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["openai/gpt-3.5-turbo:free", "anthropic/claude-3.5-sonnet:free"],
                optimal_temperature=0.2,
                optimal_max_tokens=3000,
                custom_prompt_template="gpt_osint"
            ),
            "openai/gpt-3.5-turbo:free": ModelConfig(
                id="openai/gpt-3.5-turbo:free",
                name="GPT-3.5 Turbo (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["meta-llama/llama-3.1-8b-instruct:free", "google/gemini-flash-1.5:free"],
                optimal_temperature=0.3,
                optimal_max_tokens=2000,
                custom_prompt_template="gpt_osint"
            ),
            
            # Llama models
            "meta-llama/llama-3.1-8b-instruct:free": ModelConfig(
                id="meta-llama/llama-3.1-8b-instruct:free",
                name="Llama 3.1 8B Instruct (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=False,
                fallback_models=["google/gemini-flash-1.5:free", "deepseek/deepseek-r1:free"],
                optimal_temperature=0.4,
                optimal_max_tokens=1500,
                custom_prompt_template="llama_osint"
            ),
            
            # Gemini models
            "google/gemini-flash-1.5:free": ModelConfig(
                id="google/gemini-flash-1.5:free",
                name="Gemini Flash 1.5 (Free)",
                provider=ModelProvider.OPENROUTER,
                max_tokens=4000,
                cost_per_1k_tokens=0.0,
                supports_structured_output=True,
                supports_streaming=False,
                recommended_for_osint=True,
                fallback_models=["openai/gpt-3.5-turbo:free", "anthropic/claude-3-haiku:free"],
                optimal_temperature=0.3,
                optimal_max_tokens=2000,
                custom_prompt_template="gemini_osint"
            ),
        }
    
    def get_recommended_models(self) -> List[str]:
        """Get list of models recommended for OSINT analysis."""
        return [
            model_id for model_id, config in self.model_configs.items()
            if config.recommended_for_osint
        ]
    
    def get_all_models(self) -> List[str]:
        """Get list of all available models."""
        return list(self.model_configs.keys())
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.model_configs.get(model_id)
    
    def validate_model(self, model_id: str) -> Tuple[bool, str]:
        """Validate if a model is available and properly configured."""
        if model_id not in self.model_configs:
            return False, f"Model '{model_id}' not found in configuration"
        
        config = self.model_configs[model_id]
        
        # Check if model is available via API
        if not self._is_model_available(model_id):
            return False, f"Model '{model_id}' is not available via API"
        
        return True, "Model is valid and available"
    
    def _is_model_available(self, model_id: str) -> bool:
        """Check if a model is available via API with caching."""
        current_time = time.time()
        
        # Check cache first
        if model_id in self._availability_cache:
            cached_time, is_available = self._availability_cache[model_id]
            if current_time - cached_time < self._cache_expiry:
                return is_available
        
        # Test model availability
        is_available = self._test_model_availability(model_id)
        
        # Cache the result
        self._availability_cache[model_id] = (current_time, is_available)
        
        return is_available
    
    def _test_model_availability(self, model_id: str) -> bool:
        """Test if a specific model is available via API."""
        if not self.api_key:
            return True  # Assume available if no API key (for testing)
        
        try:
            test_payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/GENAI-RAG",
                    "X-Title": "OnionScrap-API",
                },
                json=test_payload,
                timeout=10,
            )
            
            # 200 = available, 429 = rate limited but available
            return response.status_code in [200, 429]
            
        except Exception:
            return False
    
    def get_fallback_model(self, model_id: str) -> Optional[str]:
        """Get the best fallback model for a given model."""
        config = self.model_configs.get(model_id)
        if not config or not config.fallback_models:
            return None
        
        # Try fallback models in order
        for fallback_id in config.fallback_models:
            if self._is_model_available(fallback_id):
                return fallback_id
        
        return None
    
    def get_optimal_parameters(self, model_id: str) -> Dict[str, Any]:
        """Get optimal parameters for a specific model."""
        config = self.model_configs.get(model_id)
        if not config:
            return {
                "temperature": 0.3,
                "max_tokens": 2000,
                "supports_structured_output": True
            }
        
        return {
            "temperature": config.optimal_temperature,
            "max_tokens": config.optimal_max_tokens,
            "supports_structured_output": config.supports_structured_output,
            "supports_streaming": config.supports_streaming
        }
    
    def get_model_specific_prompt(self, model_id: str, base_prompt: str) -> str:
        """Get model-specific optimized prompt."""
        config = self.model_configs.get(model_id)
        if not config or not config.custom_prompt_template:
            return base_prompt
        
        # Model-specific prompt optimizations
        prompt_templates = {
            "deepseek_osint": self._get_deepseek_prompt(base_prompt),
            "claude_osint": self._get_claude_prompt(base_prompt),
            "gpt_osint": self._get_gpt_prompt(base_prompt),
            "llama_osint": self._get_llama_prompt(base_prompt),
            "gemini_osint": self._get_gemini_prompt(base_prompt),
        }
        
        return prompt_templates.get(config.custom_prompt_template, base_prompt)
    
    def _get_deepseek_prompt(self, base_prompt: str) -> str:
        """Optimized prompt for DeepSeek models."""
        return f"""You are an expert OSINT analyst specializing in dark web content analysis. 
Your analysis should be thorough, accurate, and actionable.

{base_prompt}

Instructions:
- Provide detailed, structured analysis
- Focus on actionable intelligence
- Be precise with technical details
- Maintain analytical objectivity"""
    
    def _get_claude_prompt(self, base_prompt: str) -> str:
        """Optimized prompt for Claude models."""
        return f"""You are a cybersecurity analyst with expertise in dark web intelligence gathering.
Your role is to analyze and extract actionable intelligence from dark web content.

{base_prompt}

Analysis Guidelines:
- Provide comprehensive, well-structured analysis
- Emphasize security implications and threats
- Include detailed technical findings
- Maintain professional analytical standards"""
    
    def _get_gpt_prompt(self, base_prompt: str) -> str:
        """Optimized prompt for GPT models."""
        return f"""You are an OSINT specialist analyzing dark web content for intelligence purposes.
Your analysis should be comprehensive, accurate, and professionally formatted.

{base_prompt}

Key Requirements:
- Detailed technical analysis
- Clear categorization and assessment
- Actionable recommendations
- Professional documentation standards"""
    
    def _get_llama_prompt(self, base_prompt: str) -> str:
        """Optimized prompt for Llama models."""
        return f"""Analyze the following dark web content for OSINT purposes.
Provide a structured analysis with clear findings and recommendations.

{base_prompt}

Focus on:
- Key information extraction
- Security assessment
- Categorization
- Practical recommendations"""
    
    def _get_gemini_prompt(self, base_prompt: str) -> str:
        """Optimized prompt for Gemini models."""
        return f"""You are an expert in dark web intelligence analysis.
Analyze the provided content and extract actionable intelligence.

{base_prompt}

Analysis Framework:
- Comprehensive content analysis
- Security threat assessment
- Intelligence categorization
- Strategic recommendations"""
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive information about a model."""
        config = self.model_configs.get(model_id)
        if not config:
            return {"error": f"Model '{model_id}' not found"}
        
        is_available = self._is_model_available(model_id)
        fallback = self.get_fallback_model(model_id) if not is_available else None
        
        return {
            "id": config.id,
            "name": config.name,
            "provider": config.provider.value,
            "max_tokens": config.max_tokens,
            "cost_per_1k_tokens": config.cost_per_1k_tokens,
            "supports_structured_output": config.supports_structured_output,
            "supports_streaming": config.supports_streaming,
            "recommended_for_osint": config.recommended_for_osint,
            "is_available": is_available,
            "fallback_model": fallback,
            "optimal_parameters": self.get_optimal_parameters(model_id)
        }
    
    def get_models_by_provider(self, provider: ModelProvider) -> List[str]:
        """Get all models from a specific provider."""
        return [
            model_id for model_id, config in self.model_configs.items()
            if config.provider == provider
        ]
    
    def get_available_models(self) -> List[str]:
        """Get list of currently available models."""
        return [
            model_id for model_id in self.model_configs.keys()
            if self._is_model_available(model_id)
        ]
