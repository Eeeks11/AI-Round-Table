# Model Configuration Guide

## Overview

All model configurations are now centralized in a **single file**: `models.json`

To add, remove, or modify models, you only need to edit `models.json` - no Python code changes required!

## Quick Start

### Adding a New Model

Edit `models.json` and add a new entry to the `models` array:

```json
{
  "id": "my-new-model",
  "provider": "openai",
  "model_name": "gpt-4-turbo",
  "display_name": "GPT-4 Turbo",
  "api_key_env": "OPENAI_API_KEY",
  "temperature": 0.7,
  "max_tokens": 2000,
  "timeout": 60,
  "enabled": true
}
```

### Disabling a Model

Set `"enabled": false` in the model's configuration:

```json
{
  "id": "grok",
  "enabled": false,
  ...
}
```

### Changing Model Parameters

Modify the values in `models.json`:

```json
{
  "id": "claude",
  "temperature": 0.9,
  "max_tokens": 4000,
  ...
}
```

## Configuration Fields

### Model Fields (Required)

- **`id`**: Unique identifier for the model (e.g., "gpt4", "claude")
- **`provider`**: Provider type - must be one of: `openai`, `anthropic`, `google`, `grok`
- **`model_name`**: Actual model name used by the API (e.g., "gpt-4", "claude-3-opus-20240229")
- **`display_name`**: Human-readable name shown in output (e.g., "GPT-4", "Claude 3 Opus")
- **`api_key_env`**: Environment variable name for the API key (e.g., "OPENAI_API_KEY")

### Model Fields (Optional)

- **`temperature`**: Sampling temperature, 0-2 (default: 0.7)
- **`max_tokens`**: Maximum tokens in response (default: 2000)
- **`timeout`**: Request timeout in seconds (default: 60)
- **`enabled`**: Whether model is active (default: true)

## Supported Providers

The system currently supports these provider types:

1. **`openai`** - OpenAI models (GPT-4, GPT-3.5, etc.)
   - Requires: `pip install openai`
   - API Key: Set `OPENAI_API_KEY` in `.env`

2. **`anthropic`** - Anthropic models (Claude)
   - Requires: `pip install anthropic`
   - API Key: Set `ANTHROPIC_API_KEY` in `.env`

3. **`google`** - Google models (Gemini)
   - Requires: `pip install google-generativeai`
   - API Key: Set `GOOGLE_API_KEY` in `.env`

4. **`grok`** - xAI models (Grok)
   - Requires: `pip install openai` (uses OpenAI-compatible API)
   - API Key: Set `GROK_API_KEY` in `.env`

## Examples

### Example 1: Adding a New OpenAI Model

```json
{
  "id": "gpt35",
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "display_name": "GPT-3.5 Turbo",
  "api_key_env": "OPENAI_API_KEY",
  "temperature": 0.7,
  "max_tokens": 1500,
  "timeout": 30,
  "enabled": true
}
```

### Example 2: Adding Multiple Claude Models

```json
{
  "id": "claude-opus",
  "provider": "anthropic",
  "model_name": "claude-3-opus-20240229",
  "display_name": "Claude 3 Opus",
  "api_key_env": "ANTHROPIC_API_KEY",
  "enabled": true
},
{
  "id": "claude-sonnet",
  "provider": "anthropic",
  "model_name": "claude-3-sonnet-20240229",
  "display_name": "Claude 3 Sonnet",
  "api_key_env": "ANTHROPIC_API_KEY",
  "enabled": true
}
```

### Example 3: Using Different API Keys

You can configure different API keys for different models:

```json
{
  "id": "work-gpt4",
  "provider": "openai",
  "model_name": "gpt-4",
  "display_name": "Work GPT-4",
  "api_key_env": "WORK_OPENAI_KEY",
  "enabled": true
},
{
  "id": "personal-gpt4",
  "provider": "openai",
  "model_name": "gpt-4",
  "display_name": "Personal GPT-4",
  "api_key_env": "PERSONAL_OPENAI_KEY",
  "enabled": true
}
```

Then in your `.env` file:
```
WORK_OPENAI_KEY=sk-work-key-here
PERSONAL_OPENAI_KEY=sk-personal-key-here
```

## Usage

After modifying `models.json`, run:

```bash
# Check which models are available
python deliberate.py --status

# Use specific models
python deliberate.py "Your question" --models gpt4 claude

# Use all enabled models
python deliberate.py "Your question"
```

## Troubleshooting

### "Model configuration file not found"
- Make sure `models.json` exists in the same directory as `config.py`

### "Invalid JSON in models.json"
- Check your JSON syntax (use a JSON validator)
- Ensure all quotes are double quotes (`"`)
- Ensure no trailing commas

### "Invalid model configuration"
- Verify all required fields are present: `id`, `provider`, `model_name`, `display_name`, `api_key_env`
- Check that field names are spelled correctly

### Model not appearing
- Check that `"enabled": true` (or field is omitted, as true is default)
- Verify the API key environment variable is set in `.env`
- Run `python deliberate.py --status` to see availability

## Migration from Old System

If you were previously modifying `config.py` directly, those changes are no longer needed. The old hardcoded `DEFAULT_MODELS` has been replaced with the JSON configuration system.

Your existing `.env` file with API keys remains unchanged.
