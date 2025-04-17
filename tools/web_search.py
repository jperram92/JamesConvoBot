"""
Web search tool for AI Meeting Assistant.
"""
import json
import os
from typing import Dict, List, Optional, Type

from pydantic import Field

import requests
from langchain.tools import BaseTool

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class WebSearchTool(BaseTool):
    """Tool for performing web searches."""

    name: str = Field(default="web_search")
    description: str = Field(default="Useful for searching the web for current information or answering questions about current events, facts, etc.")

    def __init__(self):
        """Initialize the web search tool."""
        super().__init__()
        self.search_engine = config.get('agent.tools.web_search_engine', 'google')

        # Set up Google Custom Search
        if self.search_engine == 'google':
            self.google_api_key = config.get_nested_value(['api_keys', 'google', 'api_key'])
            self.google_cse_id = config.get_nested_value(['api_keys', 'google', 'cse_id'])

            if not self.google_api_key or not self.google_cse_id:
                logger.warning("Google API key or CSE ID not found. Web search will not work.")

    def _run(self, query: str, num_results: int = 5) -> str:
        """
        Run the web search tool.

        Args:
            query: Search query.
            num_results: Number of results to return.

        Returns:
            Search results as a formatted string.
        """
        if self.search_engine == 'google':
            return self._google_search(query, num_results)
        else:
            return f"Search engine {self.search_engine} not supported."

    def _google_search(self, query: str, num_results: int = 5) -> str:
        """
        Perform a Google search using the Custom Search API.

        Args:
            query: Search query.
            num_results: Number of results to return.

        Returns:
            Search results as a formatted string.
        """
        if not self.google_api_key or not self.google_cse_id:
            return "Google API key or CSE ID not configured."

        try:
            # Build the API URL
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": query,
                "num": min(num_results, 10)  # API limit is 10
            }

            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()

            # Parse the response
            results = response.json()

            if "items" not in results:
                return f"No results found for query: {query}"

            # Format the results
            formatted_results = f"Search results for '{query}':\n\n"

            for i, item in enumerate(results["items"][:num_results], 1):
                title = item.get("title", "No title")
                link = item.get("link", "No link")
                snippet = item.get("snippet", "No description")

                formatted_results += f"{i}. {title}\n"
                formatted_results += f"   URL: {link}\n"
                formatted_results += f"   Description: {snippet}\n\n"

            return formatted_results

        except Exception as e:
            logger.error(f"Error performing Google search: {e}")
            return f"Error performing search: {str(e)}"

    async def _arun(self, query: str, num_results: int = 5) -> str:
        """
        Run the web search tool asynchronously.

        Args:
            query: Search query.
            num_results: Number of results to return.

        Returns:
            Search results as a formatted string.
        """
        # For simplicity, we'll just call the synchronous version
        return self._run(query, num_results)
