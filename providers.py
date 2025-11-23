"""API provider wrappers for multi-model deliberation."""

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, List, Any
import sys
import json

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


class ToolCall:
    """Represents a tool call from a model."""
    
    def __init__(self, id: str, name: str, arguments: Dict[str, Any]):
        self.id = id
        self.name = name
        self.arguments = arguments


class ModelResponseChunk:
    """Represents a chunk of model response that may include text or tool calls."""
    
    def __init__(self, text: Optional[str] = None, tool_calls: Optional[List[ToolCall]] = None):
        self.text = text
        self.tool_calls = tool_calls or []


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
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[ModelResponseChunk]:
        """
        Generate response from the model.
        
        Args:
            prompt: The prompt to send to the model
            system_message: Optional system message
            stream: Whether to stream the response
            tools: Optional list of tool definitions for function calling
            
        Yields:
            ModelResponseChunk objects containing text and/or tool calls
        """
        pass
    
    async def generate_full_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[str, List[ToolCall]]:
        """
        Generate complete response (convenience method).
        
        Args:
            prompt: The prompt to send to the model
            system_message: Optional system message
            tools: Optional list of tool definitions
            
        Returns:
            Tuple of (complete response string, list of tool calls)
        """
        text_chunks = []
        all_tool_calls = []
        async for chunk in self.generate_response(prompt, system_message, stream=False, tools=tools):
            if chunk.text:
                text_chunks.append(chunk.text)
            if chunk.tool_calls:
                all_tool_calls.extend(chunk.tool_calls)
        return "".join(text_chunks), all_tool_calls


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
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[ModelResponseChunk]:
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
                kwargs = {
                    "model": self.config.model_name,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_completion_tokens": self.config.max_tokens,
                    "stream": stream
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = await self.client.chat.completions.create(**kwargs)
                
                if stream:
                    tool_calls_buffer = {}
                    async for chunk in response:
                        delta = chunk.choices[0].delta
                        
                        # Handle text content
                        if delta.content:
                            yield ModelResponseChunk(text=delta.content)
                        
                        # Handle tool calls
                        if delta.tool_calls:
                            for tool_call_delta in delta.tool_calls:
                                idx = tool_call_delta.index
                                if idx not in tool_calls_buffer:
                                    tool_calls_buffer[idx] = {
                                        "id": "",
                                        "name": "",
                                        "arguments": ""
                                    }
                                
                                if tool_call_delta.id:
                                    tool_calls_buffer[idx]["id"] = tool_call_delta.id
                                if tool_call_delta.function.name:
                                    tool_calls_buffer[idx]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    tool_calls_buffer[idx]["arguments"] += tool_call_delta.function.arguments
                    
                    # Yield collected tool calls at the end
                    if tool_calls_buffer:
                        tool_calls = []
                        for tc in tool_calls_buffer.values():
                            try:
                                args = json.loads(tc["arguments"])
                                tool_calls.append(ToolCall(tc["id"], tc["name"], args))
                            except json.JSONDecodeError:
                                pass
                        if tool_calls:
                            yield ModelResponseChunk(tool_calls=tool_calls)
                else:
                    message = response.choices[0].message
                    
                    # Handle text content
                    if message.content:
                        yield ModelResponseChunk(text=message.content)
                    
                    # Handle tool calls
                    if message.tool_calls:
                        tool_calls = []
                        for tc in message.tool_calls:
                            try:
                                args = json.loads(tc.function.arguments)
                                tool_calls.append(ToolCall(tc.id, tc.function.name, args))
                            except json.JSONDecodeError:
                                pass
                        if tool_calls:
                            yield ModelResponseChunk(tool_calls=tool_calls)
                    
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
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[ModelResponseChunk]:
        """Generate response from Anthropic model."""
        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = (len(prompt) + len(system_message or "")) // 4 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        # Convert OpenAI-style tools to Anthropic format if provided
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    anthropic_tools.append({
                        "name": func["name"],
                        "description": func["description"],
                        "input_schema": func["parameters"]
                    })
        
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
                
                if anthropic_tools:
                    kwargs["tools"] = anthropic_tools
                
                if stream:
                    async with self.client.messages.stream(**kwargs) as response:
                        tool_calls_buffer = []
                        async for event in response:
                            # Handle text content
                            if hasattr(event, 'type'):
                                if event.type == "content_block_delta":
                                    if hasattr(event.delta, 'text'):
                                        yield ModelResponseChunk(text=event.delta.text)
                                elif event.type == "content_block_start":
                                    if hasattr(event.content_block, 'type') and event.content_block.type == "tool_use":
                                        tool_calls_buffer.append({
                                            "id": event.content_block.id,
                                            "name": event.content_block.name,
                                            "input": {}
                                        })
                                elif event.type == "content_block_delta":
                                    if hasattr(event.delta, 'partial_json'):
                                        # Accumulate tool input
                                        if tool_calls_buffer:
                                            tool_calls_buffer[-1]["input"] = event.delta.partial_json
                        
                        # Yield collected tool calls
                        if tool_calls_buffer:
                            tool_calls = []
                            for tc in tool_calls_buffer:
                                try:
                                    if isinstance(tc["input"], str):
                                        args = json.loads(tc["input"])
                                    else:
                                        args = tc["input"]
                                    tool_calls.append(ToolCall(tc["id"], tc["name"], args))
                                except (json.JSONDecodeError, KeyError):
                                    pass
                            if tool_calls:
                                yield ModelResponseChunk(tool_calls=tool_calls)
                else:
                    response = await self.client.messages.create(**kwargs)
                    
                    # Handle text and tool calls from content blocks
                    text_parts = []
                    tool_calls = []
                    
                    for block in response.content:
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_use":
                            tool_calls.append(ToolCall(block.id, block.name, block.input))
                    
                    if text_parts:
                        yield ModelResponseChunk(text="".join(text_parts))
                    if tool_calls:
                        yield ModelResponseChunk(tool_calls=tool_calls)
                    
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
    
    # Class-level cache for rate limiters to share limits between instances/models
    _shared_limiters: Dict[str, RateLimiter] = {}
    
    def __init__(self, config: ModelConfig):
        """Initialize Google provider."""
        super().__init__(config)
        
        # Determine which rate limiter configuration to use
        if "flash" in config.model_name.lower():
            limit_key = "gemini_flash"
            rate_limit_config = DEFAULT_RATE_LIMITS["gemini_flash"]
        elif "pro" in config.model_name.lower():
            limit_key = "gemini_pro"
            rate_limit_config = DEFAULT_RATE_LIMITS["gemini_pro"]
        else:
            limit_key = "google_default"
            rate_limit_config = DEFAULT_RATE_LIMITS["google"]
            
        # Use shared limiter if it exists, otherwise create and store it
        if limit_key not in self._shared_limiters:
            self._shared_limiters[limit_key] = RateLimiter(rate_limit_config)
            
        self.rate_limiter = self._shared_limiters[limit_key]
        
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
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[ModelResponseChunk]:
        """Generate response from Google model."""
        # Combine system message with prompt for Gemini
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        
        # Estimate tokens (conservative estimate: ~3 chars per token to be safe)
        estimated_tokens = len(full_prompt) // 3 + self.config.max_tokens
        
        # Wait if rate limit would be exceeded
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        # Convert OpenAI-style tools to Gemini format if provided
        gemini_tools = None
        if tools:
            import google.generativeai as genai
            gemini_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    # Gemini uses function declarations
                    gemini_tools.append(genai.protos.Tool(
                        function_declarations=[
                            genai.protos.FunctionDeclaration(
                                name=func["name"],
                                description=func["description"],
                                parameters=func["parameters"]
                            )
                        ]
                    ))
        
        async def _make_request():
            try:
                kwargs = {}
                if gemini_tools:
                    kwargs["tools"] = gemini_tools
                
                if stream:
                    response = await self.model.generate_content_async(
                        full_prompt,
                        stream=True,
                        **kwargs
                    )
                    async for chunk in response:
                        # Handle text
                        if chunk.text:
                            yield ModelResponseChunk(text=chunk.text)
                        
                        # Handle function calls
                        if hasattr(chunk, 'candidates') and chunk.candidates:
                            for candidate in chunk.candidates:
                                if hasattr(candidate.content, 'parts'):
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'function_call') and part.function_call:
                                            fc = part.function_call
                                            tool_calls = [ToolCall(
                                                id=fc.name,  # Gemini doesn't provide IDs, use name
                                                name=fc.name,
                                                arguments=dict(fc.args)
                                            )]
                                            yield ModelResponseChunk(tool_calls=tool_calls)
                else:
                    response = await self.model.generate_content_async(full_prompt, **kwargs)
                    
                    # Handle text
                    if response.text:
                        yield ModelResponseChunk(text=response.text)
                    
                    # Handle function calls
                    if hasattr(response, 'candidates') and response.candidates:
                        for candidate in response.candidates:
                            if hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'function_call') and part.function_call:
                                        fc = part.function_call
                                        tool_calls = [ToolCall(
                                            id=fc.name,  # Gemini doesn't provide IDs, use name
                                            name=fc.name,
                                            arguments=dict(fc.args)
                                        )]
                                        yield ModelResponseChunk(tool_calls=tool_calls)
                    
            except Exception as e:
                import google.api_core.exceptions as google_exceptions
                
                # Handle Google-specific exceptions
                if isinstance(e, google_exceptions.ResourceExhausted):
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name} (ResourceExhausted)")
                
                # Handle generic exceptions with error strings
                error_str = str(e).lower()
                if "quota" in error_str or "rate" in error_str or "429" in error_str:
                    raise RateLimitError(f"Rate limit exceeded for {self.config.display_name}")
                
                # Handle blocked content errors (common with Gemini)
                if "blocked" in error_str or "safety" in error_str:
                    # Treat safety blocks as a special provider error but not rate limit
                    raise ProviderError(f"Content blocked by safety filters: {str(e)}")
                    
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
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[ModelResponseChunk]:
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
                kwargs = {
                    "model": self.config.model_name,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_completion_tokens": self.config.max_tokens,
                    "stream": stream
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = await self.client.chat.completions.create(**kwargs)
                
                if stream:
                    tool_calls_buffer = {}
                    async for chunk in response:
                        delta = chunk.choices[0].delta
                        
                        # Handle text content
                        if delta.content:
                            yield ModelResponseChunk(text=delta.content)
                        
                        # Handle tool calls
                        if delta.tool_calls:
                            for tool_call_delta in delta.tool_calls:
                                idx = tool_call_delta.index
                                if idx not in tool_calls_buffer:
                                    tool_calls_buffer[idx] = {
                                        "id": "",
                                        "name": "",
                                        "arguments": ""
                                    }
                                
                                if tool_call_delta.id:
                                    tool_calls_buffer[idx]["id"] = tool_call_delta.id
                                if tool_call_delta.function.name:
                                    tool_calls_buffer[idx]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    tool_calls_buffer[idx]["arguments"] += tool_call_delta.function.arguments
                    
                    # Yield collected tool calls at the end
                    if tool_calls_buffer:
                        tool_calls = []
                        for tc in tool_calls_buffer.values():
                            try:
                                args = json.loads(tc["arguments"])
                                tool_calls.append(ToolCall(tc["id"], tc["name"], args))
                            except json.JSONDecodeError:
                                pass
                        if tool_calls:
                            yield ModelResponseChunk(tool_calls=tool_calls)
                else:
                    message = response.choices[0].message
                    
                    # Handle text content
                    if message.content:
                        yield ModelResponseChunk(text=message.content)
                    
                    # Handle tool calls
                    if message.tool_calls:
                        tool_calls = []
                        for tc in message.tool_calls:
                            try:
                                args = json.loads(tc.function.arguments)
                                tool_calls.append(ToolCall(tc.id, tc.function.name, args))
                            except json.JSONDecodeError:
                                pass
                        if tool_calls:
                            yield ModelResponseChunk(tool_calls=tool_calls)
                    
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
