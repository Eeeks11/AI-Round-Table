"""API provider wrappers for multi-model deliberation."""

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
import sys

from config import ModelConfig
from rate_limiter import RateLimiter, retry_with_exponential_backoff, DEFAULT_RATE_LIMITS


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded."""
    pass


class APIKeyError(ProviderError):
    """Invalid or missing API key."""
    pass


class BaseProvider(ABC):
    """Base class for AI model providers."""
    
    def __init__(self, config: ModelConfig):
        """
        Initialize provider with configuration.
        
        Args:
            config: Model configuration
        """
        self.config = config
        self.api_key = config.get_api_key()
        
        if not self.api_key:
            raise APIKeyError(
                f"API key not found for {config.display_name}. "
                f"Please set {config.api_key_env} in your .env file."
            )
        
        # Initialize rate limiter
        rate_limit_config = DEFAULT_RATE_LIMITS.get(
            config.provider,
            DEFAULT_RATE_LIMITS["anthropic"]  # Default fallback
        )
        self.rate_limiter = RateLimiter(rate_limit_config)
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Generate response from the model.
        
        Args:
            prompt: The prompt to send to the model
            system_message: Optional system message
            stream: Whether to stream the response
            
        Yields:
            Response chunks if streaming, or full response
        """
        pass
    
    async def generate_full_response(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate complete response (convenience method).
        
        Args:
            prompt: The prompt to send to the model
            system_message: Optional system message
            
        Returns:
            Complete response string
        """
        chunks = []
        async for chunk in self.generate_response(prompt, system_message, stream=False):
            chunks.append(chunk)
        return "".join(chunks)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models (GPT)."""
    
    def __init__(self, config: ModelConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ProviderError("openai package not installed. Run: pip install openai")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Generate response from OpenAI model."""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = (len(prompt) + len(system_message or "")) // 4 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        async def _make_request():
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_completion_tokens=self.config.max_tokens,
                    stream=stream
                )
                
                if stream:
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                else:
                    yield response.choices[0].message.content
                    
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name}")
                raise ProviderError(f"Error from {self.config.display_name}: {str(e)}")
        
        # Use retry logic
        try:
            async for chunk in retry_with_exponential_backoff(
                _make_request,
                self.rate_limiter.config
            ):
                yield chunk
            
            # Record successful request
            self.rate_limiter.record_request(estimated_tokens)
        except Exception as e:
            raise


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic models (Claude)."""
    
    def __init__(self, config: ModelConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ProviderError("anthropic package not installed. Run: pip install anthropic")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Generate response from Anthropic model."""
        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = (len(prompt) + len(system_message or "")) // 4 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        async def _make_request():
            try:
                kwargs = {
                    "model": self.config.model_name,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                if system_message:
                    kwargs["system"] = system_message
                
                if stream:
                    async with self.client.messages.stream(**kwargs) as response:
                        async for chunk in response.text_stream:
                            yield chunk
                else:
                    response = await self.client.messages.create(**kwargs)
                    yield response.content[0].text
                    
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name}")
                raise ProviderError(f"Error from {self.config.display_name}: {str(e)}")
        
        # Use retry logic
        try:
            async for chunk in retry_with_exponential_backoff(
                _make_request,
                self.rate_limiter.config
            ):
                yield chunk
            
            # Record successful request
            self.rate_limiter.record_request(estimated_tokens)
        except Exception as e:
            raise


class GoogleProvider(BaseProvider):
    """Provider for Google models (Gemini)."""
    
    def __init__(self, config: ModelConfig):
        """Initialize Google provider."""
        super().__init__(config)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            generation_config = {
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            }
            
            self.model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config
            )
        except ImportError:
            raise ProviderError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Generate response from Google model."""
        # Combine system message with prompt for Gemini
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        
        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = len(full_prompt) // 4 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        async def _make_request():
            try:
                if stream:
                    response = await self.model.generate_content_async(
                        full_prompt,
                        stream=True
                    )
                    async for chunk in response:
                        if chunk.text:
                            yield chunk.text
                else:
                    response = await self.model.generate_content_async(full_prompt)
                    yield response.text
                    
            except Exception as e:
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "429" in str(e):
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name}")
                raise ProviderError(f"Error from {self.config.display_name}: {str(e)}")
        
        # Use retry logic
        try:
            async for chunk in retry_with_exponential_backoff(
                _make_request,
                self.rate_limiter.config
            ):
                yield chunk
            
            # Record successful request
            self.rate_limiter.record_request(estimated_tokens)
        except Exception as e:
            raise


class GrokProvider(BaseProvider):
    """Provider for Grok models (using OpenAI-compatible API)."""
    
    def __init__(self, config: ModelConfig):
        """Initialize Grok provider."""
        super().__init__(config)
        
        try:
            from openai import AsyncOpenAI
            # Grok uses OpenAI-compatible API with custom base URL
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
        except ImportError:
            raise ProviderError("openai package not installed. Run: pip install openai")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Generate response from Grok model."""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = (len(prompt) + len(system_message or "")) // 4 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        async def _make_request():
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_completion_tokens=self.config.max_tokens,
                    stream=stream
                )
                
                if stream:
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                else:
                    yield response.choices[0].message.content
                    
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name}")
                raise ProviderError(f"Error from {self.config.display_name}: {str(e)}")
        
        # Use retry logic
        try:
            async for chunk in retry_with_exponential_backoff(
                _make_request,
                self.rate_limiter.config
            ):
                yield chunk
            
            # Record successful request
            self.rate_limiter.record_request(estimated_tokens)
        except Exception as e:
            raise


class ProviderFactory:
    """Factory for creating provider instances."""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "grok": GrokProvider,
    }
    
    @classmethod
    def create_provider(cls, config: ModelConfig) -> BaseProvider:
        """
        Create provider instance based on configuration.
        
        Args:
            config: Model configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        provider_class = cls.PROVIDERS.get(config.provider)
        
        if not provider_class:
            raise ValueError(f"Unknown provider: {config.provider}")
        
        return provider_class(config)
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class: type):
        """
        Register a custom provider.
        
        Args:
            provider_name: Name to register provider under
            provider_class: Provider class to register
        """
        cls.PROVIDERS[provider_name] = provider_class
