"""
MCP Search server implementation.
"""
from mcp.server.fastmcp import FastMCP
import asyncio
import sys
from typing import Optional, List, Dict, Any

from utils.logging import logger
from utils.config import settings
from search.engine import search_information

class SearchMCPServer:
    """MCP Server for search functionality."""
    
    def __init__(self):
        """Initialize the MCP search server."""
        self.mcp = FastMCP("SearchEngine")
        self._register_tools()
        
    def _register_tools(self):
        """Register search tools with the MCP server."""
        
        @self.mcp.tool()
        async def search(query: str, num_results: int = 5) -> str:
            """
            Search for information online based on a query.
            
            Args:
                query: The search query string
                num_results: Number of search results to return (default: 5, max: 10)
                
            Returns:
                str: Formatted search results with content from the top search results
            """
            logger.info(f"Processing search request for query: {query}")
            
            # Validate and sanitize input
            if not query or not isinstance(query, str):
                return "Invalid query. Please provide a valid search query."
            
            # Limit the number of results to a reasonable range
            num_results = max(1, min(num_results, 10))
            
            try:
                # Perform the search
                results = await search_information(query, num_results)
                return results
            except Exception as e:
                logger.exception(f"Error during search: {str(e)}")
                return f"An error occurred during search: {str(e)}"
        
        @self.mcp.tool()
        async def advanced_search(
            query: str, 
            num_results: int = 5,
            include_domains: Optional[List[str]] = None,
            exclude_domains: Optional[List[str]] = None,
            time_range: Optional[str] = None
        ) -> str:
            """
            Perform an advanced search with domain filtering and time range options.
            
            Args:
                query: The search query string
                num_results: Number of search results to return (default: 5, max: 10)
                include_domains: List of domains to include in search results (e.g., ["example.com", "wikipedia.org"])
                exclude_domains: List of domains to exclude from search results
                time_range: Time range for search results (e.g., "past_hour", "past_day", "past_week", "past_month", "past_year")
                
            Returns:
                str: Formatted search results with content from the top search results
            """
            logger.info(f"Processing advanced search request for query: {query}")
            
            # Build a modified query with domain filters if specified
            modified_query = query
            
            if include_domains:
                domain_filter = " OR ".join([f"site:{domain}" for domain in include_domains])
                modified_query = f"({modified_query}) {domain_filter}"
            
            if exclude_domains:
                for domain in exclude_domains:
                    modified_query += f" -site:{domain}"
            
            # Limit the number of results to a reasonable range
            num_results = max(1, min(num_results, 10))
            
            try:
                # Perform the search with the modified query
                results = await search_information(modified_query, num_results)
                return results
            except Exception as e:
                logger.exception(f"Error during advanced search: {str(e)}")
                return f"An error occurred during advanced search: {str(e)}"
    
    def run(self, transport="stdio", port=None):
        """
        Run the MCP server.
        
        Args:
            transport: Transport method for MCP server
            port: Port for HTTP-based transports
        """
        if transport in ["sse", "ws"]:
            port = port or settings.MCP_SERVER_PORT
            self.mcp.run(transport=transport, port=port)
        else:
            self.mcp.run(transport=transport)


def main():
    """Run the search MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Search MCP Server")
    parser.add_argument(
        "--transport", 
        default="stdio", 
        choices=["stdio", "sse", "ws", "unix"], 
        help="Transport method for MCP server"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=settings.MCP_SERVER_PORT,
        help="Port for HTTP-based transports"
    )
    
    args = parser.parse_args()
    
    # Initialize and run the server
    server = SearchMCPServer()
    server.run(transport=args.transport, port=args.port)


if __name__ == "__main__":
    # Run the MCP server
    main()
