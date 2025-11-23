# 🌐 Internet Access Setup Guide

## What Was Added

Your Multi-Model AI Deliberation System now has **FULL INTERNET ACCESS**! 🎉

The AI models can now:
- ✅ Search the web for current information
- ✅ Look up real-time prices and product details
- ✅ Access recent news and developments  
- ✅ Get current date/time for any timezone
- ✅ Verify claims with live data during deliberations

## Quick Setup (3 Steps)

### Step 1: Get Tavily API Key (Free!)

1. Go to https://tavily.com
2. Sign up for a free account
3. Copy your API key from the dashboard
4. **Free tier includes 1,000 searches/month** - plenty for most use!

### Step 2: Add to .env File

Open your `.env` file and add:

```env
TAVILY_API_KEY=tvly-your_api_key_here
```

### Step 3: Install New Dependencies

```bash
pip install -r requirements.txt
```

That's it! Your system now has internet access.

## Test It Out

### Test Question 1: Current Date
```bash
python deliberate.py "What is the current date and time in Australia?"
```

**What will happen:**
- Models will use the `get_current_datetime` tool
- You'll see: 🔧 Using tool: get_current_datetime({"timezone": "Australia/Sydney"})
- Models will give you the ACTUAL current date/time!

### Test Question 2: Product Research
```bash
python deliberate.py "What's the best sim racing wheel under $500 in 2025?"
```

**What will happen:**
- Models will search the web for current products and prices
- You'll see: 🔧 Using tool: web_search({"query": "best sim racing wheels 2025 under 500"})
- Models will analyze REAL current market data!

### Test Question 3: Recent News
```bash
python deliberate.py "What are the latest developments in AI this week?"
```

**What will happen:**
- Models will search for recent news
- They'll discuss actual current events
- No more "I don't have real-time access" responses!

## What You'll See

When models use internet access, you'll see:

```
[GPT-4 Turbo]
Let me search for current information...

🔧 Using tool: web_search({"query": "Logitech G923 price 2025"})
✓ Tool result received

Based on the current search results, the Logitech G923 is priced at approximately $350...
```

## How It Works

### Before (Without Internet)
```
User: "What's the best sim racing wheel in 2025?"

Model: "I don't have real-time access, but based on my training data 
       from 2023, popular options included..."
```

### After (With Internet) ✨
```
User: "What's the best sim racing wheel in 2025?"

Model: 🔧 Using tool: web_search({"query": "best sim racing wheels 2025"})
       
       Based on current search results, the top options in 2025 are:
       1. Logitech G923 - $349.99
       2. Thrustmaster T300 RS GT - $399.99
       3. Fanatec CSL DD - $449.99
       [with actual current specs and reviews]
```

## Important Files Added/Modified

### New Files Created:
- `tools.py` - Web search and date/time tools
- `docs/INTERNET_ACCESS.md` - Comprehensive guide
- `INTERNET_ACCESS_SETUP.md` - This file!

### Files Modified:
- `providers.py` - Added function calling support to all providers
- `orchestrator.py` - Integrated tool execution
- `prompts.py` - Informed models about tool availability
- `requirements.txt` - Added pytz for timezone support
- `.env.example` - Added Tavily API key placeholder
- `README.md` - Updated with internet access features
- `docs/README.md` - Added internet access documentation link

## Features

### 1. Automatic Tool Selection
Models intelligently decide when to use tools:
- Need current price? → Web search
- Need current date? → Date/time tool  
- General knowledge? → Use training data
- Verify claim? → Web search to confirm

### 2. Multi-Tool Support
Models can use multiple tools in one deliberation:
```
Round 1: Search for "RTX 4090 price"
Round 1: Search for "RTX 4090 vs RTX 4080 benchmark"
Round 2: Search for "where to buy RTX 4090"
Final: Get current date to mention "as of [date]"
```

### 3. Tool Results in Deliberation
- Other models see tool results
- They can verify or challenge the data
- Leads to more accurate consensus

## Common Use Cases

### ✅ Perfect For:
- Product research and comparisons
- Current pricing and availability
- Recent news and developments
- Market trends and analysis
- Time-sensitive questions
- Fact verification during deliberation
- Getting current date/time

### 💡 Still Uses Training Data For:
- General concepts and explanations
- Historical facts
- Established theories
- Common knowledge
- Foundational understanding

### 🎯 Best Results:
Combining both approaches! Models use training data for knowledge and web search for current specifics.

## Cost & Limits

### Tavily Free Tier:
- **1,000 searches per month**
- Approximately 33 searches per day
- Most deliberations use 1-5 searches
- **Should be plenty for most users!**

### Typical Usage:
- Simple question: 0-2 searches
- Product comparison: 3-10 searches  
- Complex research: 10-20 searches

### If You Hit Limits:
- Upgrade to Tavily Pro: $100/month for 30,000 searches
- Or space out your deliberations
- Check usage on Tavily dashboard

## Troubleshooting

### Models Not Using Tools?

**Possible reasons:**
1. Question doesn't need current info
2. Models have sufficient training data
3. Tavily API key not set correctly

**Solutions:**
- Try a question that explicitly needs current data
- Check `.env` file has `TAVILY_API_KEY`
- Restart deliberation after adding key

### "No Tavily API key configured" Error?

**Solution:**
1. Get API key from https://tavily.com
2. Add to `.env`: `TAVILY_API_KEY=your_key_here`
3. Restart your deliberation

### Tool Calls Not Showing?

**Check:**
- Using `--summary-only` flag? (hides tool calls)
- Remove flag to see tool usage: `python deliberate.py "question"`

## Next Steps

1. ✅ Get Tavily API key
2. ✅ Add to `.env`
3. ✅ Install dependencies  
4. ✅ Test with a question needing current info
5. 🎉 Enjoy AI with internet access!

## Learn More

- **Full Documentation**: See `docs/INTERNET_ACCESS.md`
- **Main README**: See `README.md` (now updated with internet features)
- **Tavily API**: https://docs.tavily.com/

---

**You're all set!** Your AI models can now access the internet during deliberations. Try it out with any question that needs current information!
