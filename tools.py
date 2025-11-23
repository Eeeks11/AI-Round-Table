"""Tools for AI models to access external information."""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp


class WebSearchTool:
    """Tool for searching the web and retrieving current information."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize web search tool.
        
        Args:
            api_key: Tavily API key (or from TAVILY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"
        
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_raw_content: bool = False
    ) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return (default: 5)
            search_depth: "basic" or "advanced" (default: "basic")
            include_raw_content: Whether to include raw HTML content (default: False)
            
        Returns:
            Dictionary with search results
        """
        if not self.api_key:
            return {
                "error": "No Tavily API key configured. Set TAVILY_API_KEY in .env file.",
                "results": []
            }
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_raw_content": include_raw_content,
            "include_answer": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "query": query,
                            "answer": data.get("answer", ""),
                            "results": data.get("results", []),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"Search API error (status {response.status}): {error_text}",
                            "results": []
                        }
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    def format_results_for_model(self, search_response: Dict[str, Any]) -> str:
        """
        Format search results for model consumption.
        
        Args:
            search_response: Response from search() method
            
        Returns:
            Formatted string with search results
        """
        if "error" in search_response:
            return f"Search Error: {search_response['error']}"
        
        output = []
        
        # Add quick answer if available
        if search_response.get("answer"):
            output.append(f"Quick Answer: {search_response['answer']}\n")
        
        # Add search results
        results = search_response.get("results", [])
        if results:
            output.append(f"Found {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                output.append(f"{i}. {result.get('title', 'No title')}")
                output.append(f"   URL: {result.get('url', 'N/A')}")
                output.append(f"   {result.get('content', 'No content available')}\n")
        else:
            output.append("No results found.")
        
        return "\n".join(output)


class DateTimeTool:
    """Tool for getting current date and time information."""
    
    @staticmethod
    def get_current_datetime(timezone: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current date and time.
        
        Args:
            timezone: Optional timezone (e.g., "Australia/Sydney")
            
        Returns:
            Dictionary with date/time information
        """
        try:
            from datetime import datetime
            import pytz
            
            if timezone:
                try:
                    tz = pytz.timezone(timezone)
                    now = datetime.now(tz)
                except Exception:
                    # Fallback to UTC if timezone is invalid
                    now = datetime.now(pytz.UTC)
                    timezone = "UTC (invalid timezone requested)"
            else:
                now = datetime.now(pytz.UTC)
                timezone = "UTC"
            
            return {
                "datetime": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "timezone": timezone,
                "day_of_week": now.strftime("%A"),
                "timestamp": now.timestamp()
            }
        except ImportError:
            # Fallback without pytz
            now = datetime.now()
            return {
                "datetime": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "timezone": "Local time (install pytz for timezone support)",
                "day_of_week": now.strftime("%A"),
                "timestamp": now.timestamp()
            }


class ToolRegistry:
    """Registry of all available tools for AI models."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.web_search = WebSearchTool()
        self.datetime = DateTimeTool()
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for function calling.
        
        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information, news, prices, product details, or any real-time data. Use this when you need up-to-date information that may not be in your training data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query. Be specific and detailed for better results."
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_datetime",
                    "description": "Get the current date and time, optionally for a specific timezone. Use this when you need to know what time or date it is right now.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "Optional timezone name (e.g., 'Australia/Sydney', 'America/New_York', 'Europe/London'). If not specified, returns UTC time."
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
    
    def get_anthropic_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions in Anthropic's format.
        
        Returns:
            List of tool definitions in Anthropic format
        """
        return [
            {
                "name": "web_search",
                "description": "Search the web for current information, news, prices, product details, or any real-time data. Use this when you need up-to-date information that may not be in your training data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query. Be specific and detailed for better results."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_current_datetime",
                "description": "Get the current date and time, optionally for a specific timezone. Use this when you need to know what time or date it is right now.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Optional timezone name (e.g., 'Australia/Sydney', 'America/New_York', 'Europe/London'). If not specified, returns UTC time."
                        }
                    },
                    "required": []
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        try:
            if tool_name == "web_search":
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 5)
                
                search_result = await self.web_search.search(query, max_results)
                return self.web_search.format_results_for_model(search_result)
            
            elif tool_name == "get_current_datetime":
                timezone = arguments.get("timezone")
                result = self.datetime.get_current_datetime(timezone)
                return json.dumps(result, indent=2)
            
            else:
                return f"Error: Unknown tool '{tool_name}'"
        
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
