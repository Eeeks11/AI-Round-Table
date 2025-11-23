# Quick Start Guide

Get up and running with the Multi-Model AI Deliberation System in 5 minutes!

## 🚀 Fast Setup

### Step 1: Set Up Virtual Environment (1 minute)

**Recommended**: Use a virtual environment to isolate dependencies.

```bash
# Navigate to project directory
cd multi-model-deliberation

# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows (CMD):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt when activated.

### Step 2: Install Dependencies (30 seconds)

```bash
# With virtual environment activated
pip install -r requirements.txt
```

This installs:
- `openai` - For GPT models
- `anthropic` - For Claude models
- `google-generativeai` - For Gemini models
- `python-dotenv` - For environment variables
- `aiohttp` - For async HTTP requests
- `colorama` - For colored terminal output

### Step 3: Configure API Keys (2 minutes)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env   # or vim, code, etc.
```

Add at least one API key (you don't need all of them):

```env
OPENAI_API_KEY=sk-...              # Get from: https://platform.openai.com/api-keys
ANTHROPIC_API_KEY=sk-ant-...       # Get from: https://console.anthropic.com/
GOOGLE_API_KEY=AIza...             # Get from: https://makersuite.google.com/app/apikey
GROK_API_KEY=xai-...               # Get from: https://x.ai/
```

### Step 4: Verify Setup (10 seconds)

```bash
python deliberate.py --status
```

You should see:
```
📋 Model Status:
============================================================
GPT-4 Turbo          (gpt4   ): ✅ Available
Claude Sonnet 4.5    (claude ): ✅ Available
Gemini 2.0 Flash     (gemini ): ✅ Available
Grok Beta            (grok   ): ❌ Unavailable (missing API key)
============================================================
```

### Step 5: Run Your First Deliberation! (1 minute)

```bash
python deliberate.py "What are the key principles of good software architecture?"
```

Watch as multiple AI models discuss the question and reach consensus!

---

## 📖 Common Usage Patterns

### Simple Questions

```bash
python deliberate.py "What causes inflation?"
```

### Complex Analysis

```bash
python deliberate.py "What are the ethical implications of AGI?" --rounds 5
```

### Quick Answers

```bash
python deliberate.py "Best practices for code reviews?" --summary-only
```

### Using Specific Models

```bash
# Use only Claude and GPT-4
python deliberate.py "Explain quantum computing" --models gpt4 claude
```

### Interactive Mode

```bash
python deliberate.py --interactive
```

Then ask multiple questions:
```
❓ Your question: What is machine learning?
[deliberation happens...]

❓ Your question: How does it differ from traditional programming?
[deliberation happens...]

❓ Your question: quit
```

---

## 🎯 Quick Examples

### For Developers

```bash
# Software architecture
python deliberate.py "What makes a good API design?"

# Debugging strategy
python deliberate.py "How to debug a memory leak in Python?" --rounds 4

# Technology choice
python deliberate.py "When should I use SQL vs NoSQL databases?"
```

### For Researchers

```bash
# Research questions
python deliberate.py "What are the main challenges in quantum computing?" --rounds 5

# Literature review
python deliberate.py "What are the latest developments in transformer architectures?"
```

### For Decision Making

```bash
# Business decisions
python deliberate.py "What factors should I consider when choosing a cloud provider?"

# Personal decisions
python deliberate.py "What are the pros and cons of remote work?"
```

### For Learning

```bash
# Concept explanation
python deliberate.py "Explain blockchain in simple terms" --summary-only

# Deep dive
python deliberate.py "How do neural networks learn?" --rounds 5 --verbose
```

---

## 🔧 Troubleshooting

### ❌ Virtual Environment Issues

**Problem**: `python3: command not found` or `python: command not found`

**Solution**: 
- On Windows, use `python` instead of `python3`
- On Mac/Linux, try both `python` and `python3`
- Ensure Python 3.8+ is installed: `python --version`

**Problem**: PowerShell script execution error on Windows

**Solution**:
```powershell
# Run this in PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem**: Virtual environment not activating

**Solution**:
- Check you're in the correct directory
- Verify the `venv` folder exists
- Try creating it again: `python3 -m venv venv --clear`

**Problem**: How to deactivate virtual environment

**Solution**:
```bash
deactivate  # Works on all platforms
```

### ❌ "No models available"

**Problem**: No API keys configured

**Solution**: 
```bash
# Check which keys are missing
python deliberate.py --status

# Add at least one API key to .env file
nano .env
```

### ❌ "ModuleNotFoundError: No module named 'openai'"

**Problem**: Dependencies not installed or virtual environment not activated

**Solution**:
```bash
# Make sure virtual environment is activated (you should see (venv) in prompt)
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Then install dependencies
pip install -r requirements.txt

# Or install individually
pip install openai anthropic google-generativeai python-dotenv
```

### ❌ "Rate limit exceeded"

**Problem**: Too many requests to API

**Solution**:
- Wait a minute and try again
- Use fewer models: `--models gpt4 claude`
- Check your API usage quotas

### ❌ "Invalid API key"

**Problem**: API key is incorrect or expired

**Solution**:
1. Verify your API key in the provider's dashboard
2. Check for extra spaces in `.env` file
3. Regenerate the API key if needed

---

## 💡 Pro Tips

### 1. Start Small
Begin with 2-3 rounds to see if models converge quickly:
```bash
python deliberate.py "Your question" --rounds 2
```

### 2. Use Summary Mode for Quick Answers
Skip the round-by-round output:
```bash
python deliberate.py "Your question" --summary-only
```

### 3. Save Important Deliberations
Use verbose mode and export:
```bash
python deliberate.py "Important question" --verbose
# Then choose 'y' when prompted to save
```

### 4. Adjust Temperature for Different Tasks
```bash
# Factual questions (more deterministic)
python deliberate.py "What is the capital of France?" --temperature 0.3

# Creative questions (more diverse)
python deliberate.py "Write a short story about AI" --temperature 0.9
```

### 5. Use Specific Models for Specific Tasks
```bash
# Technical questions: GPT-4 + Claude
python deliberate.py "Explain async/await" --models gpt4 claude

# Current events: Include Grok
python deliberate.py "Latest developments in AI" --models grok gpt4
```

---

## 📚 Next Steps

1. **Read the full README**: `README.md` has complete documentation
2. **Check example output**: `EXAMPLE_OUTPUT.md` shows a real session
3. **Explore model configs**: `MODEL_REGISTRY.md` for model management
4. **Customize prompts**: Edit `prompts.py` to adjust how models are prompted
5. **Add custom models**: Follow the guide in `MODEL_REGISTRY.md`

---

## 🎉 You're Ready!

Start exploring complex questions with AI collaboration:

```bash
python deliberate.py "What question should I ask to test this system?"
```

Have fun deliberating! 🚀
