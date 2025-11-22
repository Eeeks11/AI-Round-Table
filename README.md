# Multi-Model AI Deliberation System

A sophisticated Python application that orchestrates round-table discussions between multiple AI models (OpenAI GPT, Google Gemini, Anthropic Claude, and Grok) to collaboratively answer questions through iterative deliberation until consensus is reached.

## 🌟 Features

- **Multi-Provider Support**: Seamlessly integrates OpenAI, Anthropic, Google Gemini, and Grok APIs
- **Iterative Deliberation**: Models discuss questions over multiple rounds, building on each other's insights
- **Consensus Detection**: Automatically detects when models converge on similar conclusions
- **Real-time Streaming**: Watch responses stream in real-time as models think
- **Flexible Configuration**: Customize rounds, models, temperature, and more
- **Interactive Mode**: Ask multiple questions in a single session
- **Export Capability**: Save complete deliberation transcripts

## 📋 Requirements

- Python 3.8+
- API keys for the models you want to use:
  - OpenAI API key (for GPT models)
  - Anthropic API key (for Claude models)
  - Google API key (for Gemini models)
  - Grok API key (for Grok models)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd multi-model-deliberation

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GROK_API_KEY=your_grok_api_key_here
```

**Note**: You only need API keys for the models you want to use. The system will automatically use all available models.

### 3. Model Configuration (Optional)

All model configurations are now centralized in `models.json`. To add, remove, or modify models, simply edit this file. See [`MODEL_CONFIG.md`](MODEL_CONFIG.md) for details.

To validate your configuration:
```bash
python validate_models.py
```

### 4. Basic Usage

```bash
# Simple deliberation
python deliberate.py "What are the biggest risks in AI development?"

# Specify number of rounds
python deliberate.py "How can we address climate change?" --rounds 5

# Use specific models only
python deliberate.py "What is consciousness?" --models gpt4 claude

# Interactive mode
python deliberate.py --interactive
```

## 📖 Detailed Usage

### Command-Line Options

```bash
usage: deliberate.py [-h] [-r ROUNDS] [-m MODELS [MODELS ...]] 
                     [-t TEMPERATURE] [--max-tokens MAX_TOKENS] 
                     [-v] [-s] [--no-stream] 
                     [--consensus-threshold CONSENSUS_THRESHOLD]
                     [-i] [--status]
                     [question]

Arguments:
  question              Question to deliberate on

Options:
  -h, --help            Show help message and exit
  -r, --rounds ROUNDS   Number of deliberation rounds (default: 3)
  -m, --models MODELS   Specific models to use (gpt4, claude, gemini, grok)
  -t, --temperature T   Temperature for responses (default: 0.7)
  --max-tokens N        Maximum tokens per response (default: 2000)
  -v, --verbose         Show detailed output with all rounds
  -s, --summary-only    Show only final consensus
  --no-stream           Disable streaming output
  --consensus-threshold T  Threshold for consensus (default: 0.75)
  -i, --interactive     Start interactive mode
  --status              Show available models and exit
```

### Examples

#### Basic Deliberation

```bash
python deliberate.py "What are the ethical implications of artificial general intelligence?"
```

This will:
1. Send the question to all available models
2. Run 3 rounds of deliberation (default)
3. Display each model's response in real-time
4. Show consensus analysis after each round
5. Generate a final synthesized consensus

#### Custom Number of Rounds

```bash
python deliberate.py "How should governments regulate social media?" --rounds 5
```

More rounds allow for deeper exploration and refinement of ideas.

#### Using Specific Models

```bash
# Use only GPT-4 and Claude
python deliberate.py "Explain quantum computing" --models gpt4 claude

# Use all models except one (by specifying the ones you want)
python deliberate.py "Best practices for code review" --models gpt4 gemini grok
```

#### Summary-Only Mode

```bash
python deliberate.py "What causes inflation?" --summary-only
```

This skips the round-by-round output and shows only the final consensus.

#### Interactive Mode

```bash
python deliberate.py --interactive
```

Interactive mode allows you to ask multiple questions in sequence:

```
❓ Your question: What is machine learning?
[Models deliberate...]

❓ Your question: How does it differ from traditional programming?
[Models deliberate...]

❓ Your question: quit
👋 Goodbye!
```

#### Check Model Status

```bash
python deliberate.py --status
```

Shows which models are available based on your API keys.

## 🏗️ Architecture

### Project Structure

```
multi-model-deliberation/
├── deliberate.py           # Main CLI entry point
├── orchestrator.py         # Discussion orchestration logic
├── providers.py            # API client wrappers
├── consensus.py            # Consensus detection algorithms
├── prompts.py             # Prompt templates
├── config.py              # Configuration management
├── models.json            # Model configurations (edit this!)
├── validate_models.py     # Validation script for models.json
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
├── .env                   # Your API keys (create this)
├── README.md              # This file
├── MODEL_CONFIG.md        # Model configuration guide
└── MODELS_QUICK_START.md  # Quick reference for model config
```

### How It Works

1. **Initialization**: The system initializes providers for all available models based on API keys

2. **Round 1 - Initial Responses**: Each model receives the question independently and provides its initial analysis

3. **Round 2+ - Deliberation**: Each model receives:
   - The original question
   - All responses from other models in the previous round
   - Instructions to consider others' perspectives and refine their answer

4. **Consensus Detection**: After each round (starting from round 2), the system analyzes:
   - Cross-referencing between models
   - Stability of positions
   - Keyword overlap
   - Agreement language usage

5. **Final Synthesis**: A synthesized consensus answer is generated combining insights from all models

### Consensus Detection

The system uses multiple heuristics to detect consensus:

- **Cross-Reference Score**: How often models reference each other's points
- **Stability Score**: Whether models' positions are stabilizing between rounds
- **Keyword Overlap**: Common themes and terminology across responses
- **Agreement Language**: Usage of phrases like "agree", "similarly", "consensus"

A convergence score is calculated (0.0 to 1.0), and consensus is reached when it exceeds the threshold (default: 0.75).

## 🎨 Customization

### Adding or Modifying Models

**Easy Way**: All model configurations are in `models.json` - just edit this one file! See [`MODEL_CONFIG.md`](MODEL_CONFIG.md) for complete details.

Example - Add a new model to `models.json`:

```json
{
  "id": "gpt35",
  "provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "display_name": "GPT-3.5 Turbo",
  "api_key_env": "OPENAI_API_KEY",
  "temperature": 0.7,
  "max_tokens": 1500,
  "enabled": true
}
```

### Adding Custom Providers

To support a completely new AI provider (beyond OpenAI, Anthropic, Google, Grok):

```python
# In your code or a custom module
from providers import BaseProvider, ProviderFactory

# Create a custom provider class
class CustomProvider(BaseProvider):
    async def generate_response(self, prompt, system_message=None, stream=True):
        # Your implementation
        pass

# Register it
ProviderFactory.register_provider("custom", CustomProvider)
```

Then add your model to `models.json`:

```json
{
  "id": "my-model",
  "provider": "custom",
  "model_name": "model-name",
  "display_name": "My Custom Model",
  "api_key_env": "CUSTOM_API_KEY",
  "enabled": true
}
```

### Customizing Prompts

Modify `prompts.py` to adjust how models are prompted:

```python
@staticmethod
def initial_prompt(question: str) -> str:
    return f"""Your custom initial prompt here: {question}"""

@staticmethod
def deliberation_prompt(question: str, round_number: int, other_responses: Dict[str, str]) -> str:
    return f"""Your custom deliberation prompt here"""
```

## 🔧 Advanced Usage

### Programmatic Usage

You can use the system programmatically in your own Python code:

```python
import asyncio
from config import DeliberationConfig
from orchestrator import DeliberationOrchestrator

async def run_deliberation():
    config = DeliberationConfig(
        rounds=3,
        temperature=0.7,
        models=["gpt4", "claude"],
        verbose=True
    )
    
    orchestrator = DeliberationOrchestrator(config)
    session = await orchestrator.run_deliberation(
        "What is the future of renewable energy?"
    )
    
    print(f"Final consensus: {session.final_consensus}")
    return session

# Run it
session = asyncio.run(run_deliberation())
```

### Custom Output Callbacks

Implement custom output handling:

```python
def my_callback(message: str, msg_type: str):
    # Log to file, send to UI, etc.
    if msg_type == "error":
        logging.error(message)
    else:
        logging.info(message)

orchestrator = DeliberationOrchestrator(config, output_callback=my_callback)
```

## 📊 Example Output

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          MULTI-MODEL AI DELIBERATION SYSTEM                   ║
║                                                               ║
║  Orchestrating collaborative AI discussions for              ║
║  deeper insights and consensus building                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

================================================================================
MULTI-MODEL DELIBERATION SESSION
================================================================================

Question: What are the biggest risks in AI development?

Models: GPT-4 Turbo, Claude Sonnet 4.5, Gemini 2.0 Flash
Rounds: 3

✓ Initialized GPT-4 Turbo
✓ Initialized Claude Sonnet 4.5
✓ Initialized Gemini 2.0 Flash

────────────────────────────────────────────────────────────────────────────────
ROUND 1
────────────────────────────────────────────────────────────────────────────────

[GPT-4 Turbo]
The development of AI presents several significant risks... [response continues]

[Claude Sonnet 4.5]
I'll analyze the key risks in AI development... [response continues]

[Gemini 2.0 Flash]
AI development carries multiple risk dimensions... [response continues]

────────────────────────────────────────────────────────────────────────────────
ROUND 2
────────────────────────────────────────────────────────────────────────────────

[GPT-4 Turbo]
Building on the perspectives shared, I agree that alignment is crucial...

[Claude Sonnet 4.5]
I concur with the points raised about safety concerns...

[Gemini 2.0 Flash]
The other models have highlighted important aspects...

────────────────────────────────
Consensus Analysis:
Convergence: 78%
Agreement Level: high
Consensus Reached: Yes
────────────────────────────────

✓ Consensus reached after 2 rounds!

================================================================================
GENERATING FINAL CONSENSUS...
================================================================================

Final Consensus:
─────────────────────────────────────────────────────────────────────────────
Based on the multi-model deliberation, the biggest risks in AI development include:

1. Alignment and Control: Ensuring AI systems act in accordance with human values...
2. Safety and Robustness: Preventing unintended behaviors and failure modes...
3. Societal Impact: Addressing job displacement, inequality, and access...
[continues...]

================================================================================
Session completed in 45.2 seconds
================================================================================
```

## 🐛 Troubleshooting

### No Models Available

**Error**: "No models available. Please check your API keys."

**Solution**: Ensure you have created a `.env` file with at least one valid API key. Check the API key format and validity.

### Rate Limit Errors

**Error**: "Rate limit exceeded"

**Solution**: The system automatically retries once after a 5-second delay. If this persists:
- Reduce the number of models used with `--models`
- Wait a few minutes between runs
- Check your API usage quotas

### Module Import Errors

**Error**: "ModuleNotFoundError: No module named 'openai'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Streaming Issues

If streaming output appears garbled, disable it:
```bash
python deliberate.py "Your question" --no-stream
```

## 🔐 Security Notes

- **Never commit your `.env` file** to version control
- Store API keys securely
- Use environment variables in production
- Regularly rotate your API keys
- Monitor API usage for unexpected activity

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

To add support for new AI models:

1. Create a new provider class in `providers.py` inheriting from `BaseProvider`
2. Add model configuration to `config.py`
3. Register the provider in `ProviderFactory`
4. Update documentation

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review the examples
- Ensure all dependencies are installed
- Verify API keys are correctly configured

## 🎯 Use Cases

- **Research**: Explore different AI perspectives on complex topics
- **Decision Making**: Get multi-angle analysis for important decisions
- **Education**: Understand how different models approach problems
- **Content Creation**: Generate comprehensive, well-rounded content
- **Problem Solving**: Benefit from diverse AI reasoning approaches

## 🚦 Best Practices

1. **Start with fewer rounds** (2-3) and increase if needed
2. **Use specific models** when you want particular expertise
3. **Enable verbose mode** when you want to understand the deliberation process
4. **Use summary mode** when you just need the final answer
5. **Save transcripts** of important deliberations for future reference

---

**Happy Deliberating! 🎉**
