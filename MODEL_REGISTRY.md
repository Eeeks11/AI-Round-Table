# Model Registry

This document tracks all supported AI models and their configurations. Update this file when adding new models or changing model versions.

## Currently Supported Models

### OpenAI GPT Models

**Model ID**: `gpt4`
- **Provider**: OpenAI
- **Model Name**: `gpt-5.1`
- **Display Name**: GPT-5.1
- **API Key Environment Variable**: `OPENAI_API_KEY`
- **Status**: Active
- **Last Updated**: 2025-11
- **Notes**: Latest GPT-5.1 model with advanced capabilities

**Alternative GPT Models** (to use, modify `config.py`):
- `gpt-4-turbo-preview`: Previous GPT-4 Turbo model
- `gpt-4`: Standard GPT-4 model
- `gpt-3.5-turbo`: Faster, more economical option

### Anthropic Claude Models

**Model ID**: `claude`
- **Provider**: Anthropic
- **Model Name**: `claude-sonnet-4-5-20250929`
- **Display Name**: Claude Sonnet 4.5
- **API Key Environment Variable**: `ANTHROPIC_API_KEY`
- **Status**: Active
- **Last Updated**: 2025-11-21
- **Notes**: Latest Sonnet 4.5 model with excellent reasoning

**Alternative Claude Models**:
- `claude-opus-4-20250514`: Most capable model, higher cost
- `claude-3-5-sonnet-20241022`: Previous Sonnet version
- `claude-3-opus-20240229`: Claude 3 Opus

### Google Gemini Models

**Model ID**: `gemini`
- **Provider**: Google
- **Model Name**: `gemini-2.5-pro`
- **Display Name**: Gemini 2.5 Pro
- **API Key Environment Variable**: `GOOGLE_API_KEY`
- **Status**: Active
- **Last Updated**: 2025-11-21
- **Notes**: Latest Gemini 2.5 Pro model with enhanced capabilities

**Alternative Gemini Models**:
- `gemini-2.5-flash`: Faster Gemini 2.5 model
- `gemini-2.0-flash-exp`: Experimental Gemini 2.0 model
- `gemini-1.5-pro`: Stable production model
- `gemini-1.5-flash`: Faster, cost-effective option

### Grok Models

**Model ID**: `grok`
- **Provider**: X.AI (OpenAI-compatible)
- **Model Name**: `grok-4.1-thinking`
- **Display Name**: Grok 4.1 Thinking
- **API Key Environment Variable**: `GROK_API_KEY`
- **Base URL**: `https://api.x.ai/v1`
- **Status**: Active
- **Last Updated**: 2025-11
- **Notes**: Uses OpenAI-compatible API with advanced thinking capabilities

**Alternative Grok Models**:
- Check X.AI documentation for latest available models

---

## How to Update Model Versions

### Method 1: Quick Update in config.py

Edit the `DEFAULT_MODELS` dictionary in `config.py`:

```python
"gpt4": ModelConfig(
    provider="openai",
    model_name="gpt-4-turbo-preview",  # Change this to new model name
    display_name="GPT-4 Turbo",
    api_key_env="OPENAI_API_KEY",
),
```

### Method 2: Programmatic Update

```python
from config import update_model_config

# Update model name for existing model
update_model_config("gpt4", model_name="gpt-4-32k")

# Update multiple parameters
update_model_config("claude", 
    model_name="claude-opus-4-20250514",
    temperature=0.8,
    max_tokens=4000
)
```

---

## How to Add New Models

### Adding a Model from Supported Provider

If the provider is already supported (OpenAI, Anthropic, Google, Grok), add to `config.py`:

```python
from config import add_custom_model, ModelConfig

add_custom_model("gpt3", ModelConfig(
    provider="openai",  # Use existing provider
    model_name="gpt-3.5-turbo",
    display_name="GPT-3.5 Turbo",
    api_key_env="OPENAI_API_KEY",
    temperature=0.7,
    max_tokens=2000
))
```

### Adding a New Provider

1. **Create Provider Class** in `providers.py`:

```python
class NewProvider(BaseProvider):
    """Provider for New AI Service."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # Initialize your API client
        
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        # Implement response generation
        pass
```

2. **Register Provider** in `providers.py`:

```python
class ProviderFactory:
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "grok": GrokProvider,
        "new_provider": NewProvider,  # Add here
    }
```

3. **Add Model Configuration** in `config.py`:

```python
DEFAULT_MODELS = {
    # ... existing models ...
    "new_model": ModelConfig(
        provider="new_provider",
        model_name="model-v1",
        display_name="New Model",
        api_key_env="NEW_API_KEY",
    ),
}
```

4. **Update `.env.example`**:

```env
# New Provider API Key
NEW_API_KEY=your_api_key_here
```

---

## Model Comparison

| Model | Strengths | Best For | Cost | Speed |
|-------|-----------|----------|------|-------|
| GPT-4 Turbo | Versatile, strong reasoning | General purpose, complex tasks | $$$ | Medium |
| Claude Sonnet 4.5 | Thoughtful, nuanced analysis | Ethical reasoning, long-form | $$$ | Medium |
| Gemini 2.0 Flash | Fast, efficient | Quick responses, high volume | $$ | Fast |
| Grok Beta | Up-to-date knowledge | Current events, trending topics | $$$ | Medium |

---

## Testing New Models

After adding or updating a model, test it:

```bash
# Check model status
python deliberate.py --status

# Test with a simple question
python deliberate.py "What is 2+2?" --models your_new_model --rounds 1

# Test with other models
python deliberate.py "Test question" --models gpt4 your_new_model
```

---

## Model Best Practices

### Temperature Settings

- **0.0-0.3**: Deterministic, factual responses
- **0.4-0.7**: Balanced creativity and consistency (default: 0.7)
- **0.8-1.0**: More creative, diverse responses
- **1.0+**: Highly creative, less predictable

### Token Limits

- **1000-2000**: Concise responses (default: 2000)
- **2000-4000**: Detailed analysis
- **4000+**: Comprehensive, long-form content

### Timeout Settings

- **30-60s**: Standard timeout (default: 60)
- **60-120s**: For complex queries or slow models
- **120s+**: For very large contexts

---

## Upcoming Models (Watch List)

Track new models to add:

- [ ] GPT-5 (when released)
- [ ] Claude Opus 4
- [ ] Gemini 2.0 Pro (stable release)
- [ ] Llama 3.1
- [ ] Mistral Large 2

---

## Deprecation Notice

When models are deprecated by providers:

1. Update status in this document
2. Add deprecation notice to `config.py`
3. Update README.md
4. Consider migration path to newer models

---

## Provider API Documentation

- **OpenAI**: https://platform.openai.com/docs/models
- **Anthropic**: https://docs.anthropic.com/claude/docs/models
- **Google**: https://ai.google.dev/gemini-api/docs/models
- **X.AI (Grok)**: https://docs.x.ai/

---

Last Updated: 2025-11-21
