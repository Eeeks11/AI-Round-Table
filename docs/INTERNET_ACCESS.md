# Internet Access & Web Search

This document explains how to enable and use internet access in the Multi-Model AI Deliberation System, allowing models to search the web and access current information during deliberations.

## 🌐 Overview

The system now supports **real-time internet access** through:
- **Web Search**: Search the internet for current information, prices, news, product reviews, etc.
- **Date/Time Tools**: Get current date and time for any timezone

Models can automatically use these tools during deliberation to:
- Verify claims with current data
- Look up product prices and availability
- Access recent news and developments
- Get information published after their training cutoff dates
- Check current dates and times globally

## 🚀 Quick Start

### 1. Get a Tavily API Key

Tavily is a search API optimized for AI applications. It provides clean, relevant results perfect for LLMs.

1. Go to https://tavily.com
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes **1,000 searches/month** - plenty for most use cases!

### 2. Add API Key to Environment

Edit your `.env` file and add:

```env
TAVILY_API_KEY=tvly-your_api_key_here
```

### 3. Install Dependencies

If you haven't already, make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### 4. That's It!

The models will now automatically use web search and date/time tools when needed during deliberations.

## 📖 How It Works

### Automatic Tool Use

When you ask a question, the AI models can now:

1. **Decide when to search**: Models intelligently determine when they need current information
2. **Search the web**: Execute searches for relevant, up-to-date data
3. **Use the results**: Incorporate search results into their analysis
4. **Verify information**: Cross-check claims made by other models

### Example Deliberation

```bash
python deliberate.py "What's the best sim racing wheel under $500 in 2025?"
```

**What happens:**
1. **Round 1**: Models recognize they need current pricing
2. **Tool Use**: 🔧 Using tool: web_search({"query": "best sim racing wheels 2025 under 500"})
3. **Results**: Models receive current product listings, prices, and reviews
4. **Analysis**: Models use this real data to provide accurate recommendations
5. **Consensus**: Final answer includes verified, current information

### Visual Feedback

When models use tools, you'll see:

```
[GPT-4 Turbo]
To answer this question accurately, let me search for current information...
🔧 Using tool: web_search({"query": "Logitech G923 price 2025"})
✓ Tool result received

Based on the current search results...
```

## 🛠️ Available Tools

### 1. Web Search (`web_search`)

Search the internet for current information.

**What models can search for:**
- Product prices and availability
- Current news and events
- Technical specifications
- User reviews and comparisons
- Recent developments and updates
- Any information that may be outdated in training data

**Parameters:**
- `query` (required): The search query
- `max_results` (optional): Number of results (default: 5)

**Example use by model:**
```json
{
  "query": "Tesla Model 3 price USA 2025",
  "max_results": 5
}
```

### 2. Current Date/Time (`get_current_datetime`)

Get the current date and time for any timezone.

**What models can get:**
- Current date in any timezone
- Current time with timezone info
- Day of the week
- ISO formatted timestamps

**Parameters:**
- `timezone` (optional): Timezone name (e.g., "Australia/Sydney", "America/New_York")

**Example use by model:**
```json
{
  "timezone": "Australia/Sydney"
}
```

## 💡 Use Cases

### Perfect for Internet-Access Questions

✅ **Great use cases:**
- "What's the current price of [product]?"
- "What are the latest developments in [technology]?"
- "Compare recent reviews of [product A] vs [product B]"
- "What happened at [recent event]?"
- "What's the weather forecast for [location]?"
- "What date is it in [timezone]?"

### Still Uses Training Data

ℹ️ **Models will use existing knowledge when appropriate:**
- General concepts and explanations
- Historical facts
- Established theories and principles
- Common knowledge

### Hybrid Approach

🎯 **Best results come from combining both:**
- Use training data for foundational knowledge
- Use web search for current specifics
- Cross-verify important claims
- Get the latest updates on evolving topics

## ⚙️ Configuration

### Disable Internet Access

To run deliberations without internet access (using only training data):

You would need to modify the orchestrator to not pass tools. Alternatively, just don't set `TAVILY_API_KEY` and models will work without web search.

### Custom Search Parameters

The default configuration provides 5 search results per query. To modify this, edit `tools.py`:

```python
# In tools.py, WebSearchTool.search() method
async def search(
    self,
    query: str,
    max_results: int = 10,  # Increase for more results
    search_depth: str = "advanced",  # "basic" or "advanced"
    ...
)
```

### Alternative Search APIs

While Tavily is recommended, you can integrate other search APIs:

**Supported alternatives:**
- **Brave Search API**: Privacy-focused search
- **Google Custom Search API**: Requires setup but very comprehensive
- **Bing Search API**: Microsoft's search API
- **SerpAPI**: Aggregates multiple search engines

To integrate, modify the `WebSearchTool` class in `tools.py`.

## 📊 Usage Statistics

### Rate Limits

**Tavily Free Tier:**
- 1,000 searches per month
- ~33 searches per day
- Typically 1-5 searches per deliberation

**Typical Usage:**
- Simple question: 0-2 searches
- Product comparison: 3-10 searches
- Complex research: 10-20 searches

### Cost Considerations

**Free Tier is Usually Sufficient:**
- Most users stay well within 1,000/month
- Deliberations are selective about when to search
- Models don't search unnecessarily

**Paid Plans (if needed):**
- Tavily Pro: $100/month for 30,000 searches
- Enterprise: Custom pricing for high volume

## 🐛 Troubleshooting

### "No Tavily API key configured" Error

**Problem:** Models can't access web search

**Solution:**
1. Make sure `TAVILY_API_KEY` is in your `.env` file
2. Verify the API key is valid
3. Restart your deliberation session

### Search Returns No Results

**Problem:** Web search finds nothing relevant

**Possible causes:**
1. Very specific or rare query
2. Typos in search terms
3. Too narrow search parameters

**Solutions:**
- Models will typically rephrase and try again
- Check your internet connection
- Verify Tavily service status

### Models Not Using Tools

**Problem:** Models aren't searching even when they should

**Possible causes:**
1. Question doesn't require current information
2. Models have sufficient training data
3. Tool definitions not being passed

**Solutions:**
- Try questions that explicitly need current data
- Check that `tools.py` is properly imported in `orchestrator.py`
- Verify no errors in tool initialization

### Rate Limit Errors

**Problem:** "Rate limit exceeded" from Tavily

**Solution:**
1. Check your usage on Tavily dashboard
2. Upgrade to paid tier if needed
3. Space out deliberations if hitting limits

## 🔐 Security & Privacy

### API Key Security

- **Never commit** `.env` to version control
- Store API keys securely
- Rotate keys periodically
- Use environment variables in production

### Search Privacy

- Tavily doesn't track searches personally
- No search history stored by the system
- Queries are sent via HTTPS
- Consider privacy when searching sensitive topics

### Data Handling

- Search results are temporary
- Not stored after deliberation completes
- Models don't retain search data between sessions

## 📝 Examples

### Example 1: Product Research

```bash
python deliberate.py "What are the best noise-canceling headphones under $300 in 2025?"
```

**Models will:**
1. Search for current headphone models and prices
2. Look up recent reviews and comparisons
3. Verify availability and pricing
4. Provide recommendations based on real, current data

### Example 2: Current Events

```bash
python deliberate.py "What are the major AI breakthroughs announced this month?"
```

**Models will:**
1. Search for recent AI news
2. Identify significant announcements
3. Cross-reference information
4. Summarize key developments

### Example 3: Time-Sensitive Question

```bash
python deliberate.py "What date and time is it right now in Tokyo?"
```

**Models will:**
1. Use get_current_datetime tool
2. Specify "Asia/Tokyo" timezone
3. Return exact current date and time

### Example 4: Price Comparison

```bash
python deliberate.py "Compare current prices: iPhone 15 Pro vs Samsung S24 Ultra"
```

**Models will:**
1. Search for current prices of both phones
2. Check multiple retailers
3. Compare specifications
4. Provide data-driven comparison

## 🎓 Best Practices

### For Users

1. **Be specific** in questions requiring current data
2. **Ask for sources** if you want to verify information
3. **Use --verbose** to see exactly what tools models use
4. **Cross-reference** important decisions with manual research

### For Developers

1. **Test thoroughly** after adding new tools
2. **Handle errors gracefully** when search fails
3. **Cache results** if making multiple searches for same query
4. **Monitor API usage** to avoid unexpected costs
5. **Log tool calls** for debugging and optimization

## 🔮 Future Enhancements

Planned improvements:

- **Calculator tool** for precise numerical calculations
- **Code execution** for running and testing code snippets
- **File retrieval** for accessing local documents
- **API integration** for specialized data sources
- **Image search** for visual comparisons
- **News aggregation** from specific sources

## 📚 Additional Resources

- [Tavily API Documentation](https://docs.tavily.com/)
- [Function Calling Guide (OpenAI)](https://platform.openai.com/docs/guides/function-calling)
- [Tool Use (Anthropic)](https://docs.anthropic.com/claude/docs/tool-use)
- [Function Calling (Google AI)](https://ai.google.dev/docs/function_calling)

---

**Questions or issues?** Check the [main README](../README.md) or review the [troubleshooting](#troubleshooting) section above.
