# Model Configuration - Quick Reference

## What Changed?

Previously, to add or modify models, you needed to edit:
1. ✗ `config.py` - Add/modify model in `DEFAULT_MODELS` dictionary
2. ✗ `providers.py` - Sometimes add provider class to `PROVIDERS` mapping

Now, you only need to edit:
1. ✓ `models.json` - Single configuration file for all models

## Quick Examples

### Add a new model
Open `models.json` and add to the `models` array:

```json
{
  "id": "my-model-id",
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "display_name": "My Model Name",
  "api_key_env": "OPENAI_API_KEY",
  "enabled": true
}
```

### Disable a model temporarily
Change `enabled` to `false`:

```json
{
  "id": "grok",
  "enabled": false,
  ...
}
```

### Change model parameters
Edit the values:

```json
{
  "id": "claude",
  "temperature": 0.9,
  "max_tokens": 4000,
  ...
}
```

### Remove a model
Delete its entire entry from the `models` array in `models.json`.

## Supported Providers

- `openai` - OpenAI models (GPT series)
- `anthropic` - Anthropic models (Claude series)
- `google` - Google models (Gemini series)
- `grok` - xAI models (Grok series)

## Full Documentation

See [`MODEL_CONFIG.md`](MODEL_CONFIG.md) for complete documentation with all available options and advanced usage.

## Your API Keys

API keys are still configured in `.env` file - that hasn't changed:

```env
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
GROK_API_KEY=your-key-here
```
