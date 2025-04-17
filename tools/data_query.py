"""
Data query tool for AI Meeting Assistant.
"""
import json
import os
from typing import Any, Dict, List, Optional, Type

from pydantic import Field

import requests
from langchain.tools import BaseTool

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class DataQueryTool(BaseTool):
    """Tool for querying data from APIs or databases."""

    name: str = Field(default="data_query")
    description: str = Field(default="Useful for retrieving data from company databases, dashboards, or APIs to answer questions about metrics, KPIs, etc.")

    def __init__(self):
        """Initialize the data query tool."""
        super().__init__()
        self.api_base_url = config.get('agent.tools.data_query_api_url', '')
        self.api_key = config.get_nested_value(['api_keys', 'data_api', 'api_key'], '')

        # For demo purposes, we'll use a mock data store
        self.use_mock = config.get('agent.tools.use_mock_data', True)
        self.mock_data_path = 'mock_data'

        if self.use_mock and not os.path.exists(self.mock_data_path):
            os.makedirs(self.mock_data_path)
            self._create_mock_data()

    def _create_mock_data(self) -> None:
        """Create mock data for demonstration purposes."""
        # Sales data
        sales_data = {
            "quarterly_revenue": {
                "2023-Q1": 1250000,
                "2023-Q2": 1450000,
                "2023-Q3": 1650000,
                "2023-Q4": 1850000,
                "2024-Q1": 1950000
            },
            "product_sales": {
                "Product A": {
                    "2023": 750000,
                    "2024-YTD": 250000
                },
                "Product B": {
                    "2023": 950000,
                    "2024-YTD": 350000
                },
                "Product C": {
                    "2023": 1150000,
                    "2024-YTD": 450000
                }
            }
        }

        # User metrics
        user_metrics = {
            "monthly_active_users": {
                "2023-12": 25000,
                "2024-01": 27500,
                "2024-02": 30000,
                "2024-03": 32500,
                "2024-04": 35000
            },
            "user_retention": {
                "2023-Q4": 0.85,
                "2024-Q1": 0.87
            },
            "user_acquisition_cost": {
                "2023-Q4": 25.50,
                "2024-Q1": 23.75
            }
        }

        # Team metrics
        team_metrics = {
            "engineering": {
                "headcount": 45,
                "open_positions": 5,
                "projects": {
                    "Project X": {
                        "status": "In Progress",
                        "completion": 0.75,
                        "deadline": "2024-06-30"
                    },
                    "Project Y": {
                        "status": "Planning",
                        "completion": 0.15,
                        "deadline": "2024-09-30"
                    }
                }
            },
            "sales": {
                "headcount": 30,
                "open_positions": 3,
                "regions": {
                    "North America": {
                        "target": 2000000,
                        "actual": 1250000,
                        "pipeline": 1500000
                    },
                    "Europe": {
                        "target": 1500000,
                        "actual": 950000,
                        "pipeline": 1200000
                    },
                    "Asia": {
                        "target": 1000000,
                        "actual": 650000,
                        "pipeline": 850000
                    }
                }
            }
        }

        # Save mock data to files
        with open(f"{self.mock_data_path}/sales_data.json", "w") as f:
            json.dump(sales_data, f, indent=2)

        with open(f"{self.mock_data_path}/user_metrics.json", "w") as f:
            json.dump(user_metrics, f, indent=2)

        with open(f"{self.mock_data_path}/team_metrics.json", "w") as f:
            json.dump(team_metrics, f, indent=2)

        logger.info("Created mock data for data query tool")

    def _query_mock_data(self, query_type: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query mock data.

        Args:
            query_type: Type of data to query (sales, users, team).
            query_params: Query parameters.

        Returns:
            Query results.
        """
        try:
            # Determine which file to load based on query type
            if query_type == "sales":
                file_path = f"{self.mock_data_path}/sales_data.json"
            elif query_type == "users":
                file_path = f"{self.mock_data_path}/user_metrics.json"
            elif query_type == "team":
                file_path = f"{self.mock_data_path}/team_metrics.json"
            else:
                return {"error": f"Unknown query type: {query_type}"}

            # Load data from file
            with open(file_path, "r") as f:
                data = json.load(f)

            # Process query parameters
            if "metric" in query_params:
                metric = query_params["metric"]
                if metric in data:
                    return {metric: data[metric]}
                else:
                    # Try to find the metric in nested dictionaries
                    for key, value in data.items():
                        if isinstance(value, dict) and metric in value:
                            return {metric: value[metric]}

            # If no specific metric is requested or found, return all data
            return data

        except Exception as e:
            logger.error(f"Error querying mock data: {e}")
            return {"error": str(e)}

    def _query_api(self, query_type: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query data from API.

        Args:
            query_type: Type of data to query.
            query_params: Query parameters.

        Returns:
            Query results.
        """
        try:
            # Build API URL
            url = f"{self.api_base_url}/{query_type}"

            # Add API key to headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Make request
            response = requests.get(url, params=query_params, headers=headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error querying API: {e}")
            return {"error": str(e)}

    def _run(self, query_type: str, query_params: Dict[str, Any]) -> str:
        """
        Run the data query tool.

        Args:
            query_type: Type of data to query (sales, users, team).
            query_params: Query parameters.

        Returns:
            Query results as a formatted string.
        """
        try:
            # Query data
            if self.use_mock:
                results = self._query_mock_data(query_type, query_params)
            else:
                results = self._query_api(query_type, query_params)

            # Check for errors
            if "error" in results:
                return f"Error querying data: {results['error']}"

            # Format results
            formatted_results = f"Data query results for {query_type}:\n\n"
            formatted_results += json.dumps(results, indent=2)

            return formatted_results

        except Exception as e:
            logger.error(f"Error running data query tool: {e}")
            return f"Error running data query tool: {str(e)}"

    async def _arun(self, query_type: str, query_params: Dict[str, Any]) -> str:
        """
        Run the data query tool asynchronously.

        Args:
            query_type: Type of data to query (sales, users, team).
            query_params: Query parameters.

        Returns:
            Query results as a formatted string.
        """
        # For simplicity, we'll just call the synchronous version
        return self._run(query_type, query_params)
