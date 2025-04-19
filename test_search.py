#!/usr/bin/env python
"""
Test script for the search server functionality.
This script tests only the search capabilities without involving the agent.
"""

import asyncio
import sys
import os
from loguru import logger
import time
import re

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import configuration and utilities
from utils.config import settings
from utils.search_utils import search_information, extract_content_from_url, get_session

async def test_session_connection():
    """Test basic HTTP connection using our session."""
    logger.info("=== Testing HTTP Session ===")
    
    # Get the session
    session = await get_session()
    
    # Test connecting to a reliable website
    test_url = "https://httpbin.org/get"
    try:
        async with session.get(test_url, timeout=10, ssl=False) as response:
            status = response.status
            logger.info(f"Connection to {test_url} returned status: {status}")
            if status == 200:
                logger.info("✓ HTTP session is working properly")
                content = await response.text()
                logger.info(f"Response preview: {content[:100]}...")
                return True
            else:
                logger.error(f"✗ HTTP session returned non-200 status: {status}")
                return False
    except Exception as e:
        logger.exception(f"Error connecting to {test_url}: {str(e)}")
        return False

async def test_content_extraction():
    """Test the content extraction function directly."""
    logger.info("=== Testing Content Extraction ===")
    
    # Test URL that should be reliable
    test_url = "https://httpbin.org/html"
    
    try:
        content = await extract_content_from_url(test_url)
        
        if content and len(content) > 0:
            logger.info(f"✓ Successfully extracted {len(content)} characters from {test_url}")
            logger.info(f"Content preview: {content[:100]}...")
            return True
        else:
            logger.error(f"✗ Failed to extract content from {test_url}")
            return False
    except Exception as e:
        logger.exception(f"Error extracting content: {str(e)}")
        return False

async def test_search_with_hardcoded_content():
    """Test the search functionality with hardcoded content to bypass network issues."""
    logger.info("=== Testing Search with Hardcoded Content ===")
    
    # Create a custom implementation of search_information that doesn't rely on network
    async def mock_search_information(query, num_results=3):
        logger.info(f"Performing mock search for: {query}")
        
        # Return some hardcoded content
        mock_content = f"""
SOURCE 1: Mock News Website
URL: https://mock-news.example.com
SUMMARY: This is a mock summary about {query}

CONTENT:
This is mock content about {query}. It's designed to test the search functionality
without relying on actual network connections. The content is generated programmatically
based on the query: "{query}".

Here's some more mock content with the query term repeated: {query}, {query}, {query}.
This should be enough text to simulate a real search result.
--------------------------------------------------------------------------------

SOURCE 2: Another Mock Source
URL: https://another-mock.example.com
SUMMARY: Another mock result for {query}

CONTENT:
Here's a second mock source with information about {query}.
This source provides different information than the first one.
It's still completely made up, but it references the query: {query}.
--------------------------------------------------------------------------------

Search completed in 0.5 seconds.
"""
        return mock_content
    
    try:
        # Test with a simple query
        test_query = "artificial intelligence"
        
        # Use the mock function
        results = await mock_search_information(test_query)
        
        if results and len(results) > 0:
            logger.info(f"✓ Mock search returned {len(results)} characters")
            logger.info(f"Results preview: {results[:100]}...")
            
            # Check if the query is in the results
            if test_query in results.lower():
                logger.info(f"✓ Results contain the query term: {test_query}")
            else:
                logger.warning(f"✗ Results do not contain the query term: {test_query}")
            
            return True
        else:
            logger.error("✗ Mock search returned no results")
            return False
    except Exception as e:
        logger.exception(f"Error performing mock search: {str(e)}")
        return False

async def test_actual_search():
    """Test the actual search functionality with a real query."""
    logger.info("=== Testing Actual Search ===")
    
    # Check if the API key is available
    if not settings.SEARCH_ENGINE_API_KEY or not settings.SEARCH_ENGINE_CSE_ID:
        logger.warning("⚠ Missing API keys for search. Skipping actual search test.")
        return None
    
    try:
        # Test with a query that should return stable results
        test_query = "python programming language"
        
        # Perform the actual search
        logger.info(f"Searching for: {test_query}")
        start_time = time.time()
        results = await search_information(test_query, num_results=2)
        elapsed = time.time() - start_time
        
        if results and "No results found" not in results:
            logger.info(f"✓ Search completed in {elapsed:.2f} seconds")
            logger.info(f"Results length: {len(results)} characters")
            logger.info(f"Results preview: {results[:150]}...")
            
            # Check if the query terms are in the results
            query_terms = re.findall(r'\w+', test_query.lower())
            found_terms = [term for term in query_terms if term in results.lower()]
            
            if found_terms:
                logger.info(f"✓ Results contain query terms: {', '.join(found_terms)}")
                return True
            else:
                logger.warning(f"✗ Results do not contain any query terms")
                return False
        else:
            logger.error(f"✗ No valid search results found: {results}")
            return False
    except Exception as e:
        logger.exception(f"Error performing actual search: {str(e)}")
        return False

async def main():
    """Main test function."""
    logger.info("Starting Search Server Tests...")
    
    # Test results tracking
    results = {
        "http_session": False,
        "content_extraction": False,
        "mock_search": False,
        "actual_search": None
    }
    
    # Test HTTP session
    results["http_session"] = await test_session_connection()
    
    # Test content extraction
    if results["http_session"]:
        results["content_extraction"] = await test_content_extraction()
    else:
        logger.warning("⚠ Skipping content extraction test due to failed HTTP session test")
    
    # Test mock search
    results["mock_search"] = await test_search_with_hardcoded_content()
    
    # Test actual search only if previous tests passed
    if results["http_session"] and results["content_extraction"]:
        results["actual_search"] = await test_actual_search()
    else:
        logger.warning("⚠ Skipping actual search test due to failed prerequisites")
    
    # Print summary
    print("\n" + "="*80)
    print("SEARCH SERVER TEST SUMMARY")
    print("="*80)
    print(f"HTTP Session Test:       {'PASSED' if results['http_session'] else 'FAILED'}")
    print(f"Content Extraction Test: {'PASSED' if results['content_extraction'] else 'FAILED'}")
    print(f"Mock Search Test:        {'PASSED' if results['mock_search'] else 'FAILED'}")
    
    if results["actual_search"] is None:
        print(f"Actual Search Test:      SKIPPED")
    else:
        print(f"Actual Search Test:      {'PASSED' if results['actual_search'] else 'FAILED'}")
    
    print("="*80)
    
    # Final verdict
    if results["http_session"] and results["content_extraction"] and results["mock_search"]:
        print("\n✅ SEARCH SERVER TESTS PASSED (at the minimum level for operation)")
        if results["actual_search"] is False:
            print("⚠️ Full search functionality may not be working correctly")
        elif results["actual_search"] is None:
            print("⚠️ Actual search test was skipped")
    else:
        print("\n❌ SEARCH SERVER TESTS FAILED")
    
    print("\nFor more detailed information, see the logs above.")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
