"""Configuration management for multi-model deliberation system."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""
    
    provider: str
    model_name: str
    display_name: str
    api_key_env: str
    temperature: float = 0.7
    max_tokens: int = 2000
    enabled: bool = True
    timeout: int = 60
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        return os.getenv(self.api_key_env)
    
    def is_available(self) -> bool:
        """Check if model is available (has API key and is enabled)."""
        return self.enabled and self.get_api_key() is not None


@dataclass
class DeliberationConfig:
    """Configuration for deliberation session."""
    
    rounds: int = 3
    temperature: float = 0.7
    max_tokens: int = 2000
    verbose: bool = False
    summary_only: bool = False
    stream: bool = True
    consensus_threshold: float = 0.75
    models: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.rounds < 1:
            raise ValueError("Number of rounds must be at least 1")
        if self.rounds > 10:
            raise ValueError("Number of rounds cannot exceed 10")
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if not 0.5 <= self.consensus_threshold <= 1.0:
            raise ValueError("Consensus threshold must be between 0.5 and 1.0")


# Default model configurations
DEFAULT_MODELS: Dict[str, ModelConfig] = {
    "gpt4": ModelConfig(
        provider="openai",
        model_name="gpt-5.1",
        display_name="GPT-5.1",
        api_key_env="OPENAI_API_KEY",
    ),
    "claude": ModelConfig(
        provider="anthropic",
        model_name="claude-sonnet-4.5",
        display_name="Claude Sonnet 4.5",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    "gemini": ModelConfig(
        provider="google",
        model_name="gemini-3-pro",
        display_name="Gemini 3 Pro",
        api_key_env="GOOGLE_API_KEY",
    ),
    "grok": ModelConfig(
        provider="grok",
        model_name="grok-4.1-thinking",
        display_name="Grok 4.1 Thinking",
        api_key_env="GROK_API_KEY",
    ),
}


def get_available_models(requested_models: Optional[List[str]] = None) -> Dict[str, ModelConfig]:
    """
    Get list of available models based on API key availability.
    
    Args:
        requested_models: Optional list of model names to filter by
        
    Returns:
        Dictionary of available model configurations
    """
    available = {}
    
    for model_id, config in DEFAULT_MODELS.items():
        # Skip if specific models requested and this isn't one
        if requested_models and model_id not in requested_models:
            continue
            
        # Check if model is available
        if config.is_available():
            available[model_id] = config
    
    return available


def update_model_config(model_id: str, **kwargs) -> None:
    """
    Update configuration for a specific model.
    
    Args:
        model_id: Model identifier
        **kwargs: Configuration parameters to update
    """
    if model_id not in DEFAULT_MODELS:
        raise ValueError(f"Unknown model: {model_id}")
    
    config = DEFAULT_MODELS[model_id]
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Invalid configuration parameter: {key}")


def add_custom_model(model_id: str, config: ModelConfig) -> None:
    """
    Add a custom model configuration.
    
    Args:
        model_id: Unique identifier for the model
        config: Model configuration
    """
    if model_id in DEFAULT_MODELS:
        raise ValueError(f"Model {model_id} already exists")
    
    DEFAULT_MODELS[model_id] = config


def get_model_list() -> List[str]:
    """Get list of all configured model IDs."""
    return list(DEFAULT_MODELS.keys())


def print_model_status() -> None:
    """Print status of all configured models."""
    print("\n📋 Model Status:")
    print("=" * 60)
    
    for model_id, config in DEFAULT_MODELS.items():
        status = "✅ Available" if config.is_available() else "❌ Unavailable (missing API key)"
        print(f"{config.display_name:20} ({model_id:8}): {status}")
    
    print("=" * 60)
