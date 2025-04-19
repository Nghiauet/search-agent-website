"""
Search engine implementation for the MCP Agent.
"""
import time
import asyncio
import aiohttp
import json
import re
import cachetools.func
from typing import List, Dict, Any, Optional

from utils.logging import logger
from utils.config import settings
from search.content import extract_content, get_session

# Semaphore for limiting concurrent searches
_search_semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent searches

# Search cache
_search_cache = {}
_cache_lock = asyncio.Lock()  # Lock for thread-safe cache operations

@cachetools.func.ttl_cache(maxsize=100, ttl=settings.CACHE_TTL)
async def search_google(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search Google for a given query and return a list of URLs.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return (max 10 for free tier)
        
    Returns:
        list: List of dictionaries containing URL, title, and snippet
    """
    # Google Custom Search API endpoint
    url = "https://www.googleapis.com/customsearch/v1"
    
    # Parameters for the API request
    params = {
        'q': query,
        'key': settings.SEARCH_ENGINE_API_KEY,
        'cx': settings.SEARCH_ENGINE_CSE_ID,
        'num': min(num_results, 10)  # Ensure we don't exceed API limits
    }
    
    try:
        # Use the shared session
        session = await get_session()
        
        # Use retry with backoff to make request more resilient
        async def make_search_request():
            async with session.get(url, params=params, timeout=settings.CONNECTION_TIMEOUT) as response:
                if response.status != 200:
                    logger.warning(f"Google search API returned status {response.status} for query: {query}")
                    return []
                return await response.json()
        
        # Make the request with retries
        results = await make_search_request()
        
        # Check if there are search results
        if 'items' not in results:
            logger.info(f"No search results found for query: {query}")
            return []
            
        # Extract relevant information from search results
        search_results = []
        for item in results['items']:
            search_results.append({
                'title': item.get('title', 'No title'),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', 'No snippet')
            })
        
        logger.info(f"Found {len(search_results)} search results for query: {query}")
        return search_results
        
    except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
        logger.error(f"Error in Google search for query '{query}': {str(e)}")
        return []

async def search_and_extract(query: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search for websites based on a query and extract information from them asynchronously.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to process
        
    Returns:
        list: List of dictionaries containing website information and extracted content
    """
    # Search for websites
    search_results = await search_google(query, num_results)
    
    if not search_results:
        logger.warning(f"No search results found for query: {query}")
        return []
    
    # Extract content from each website concurrently with a semaphore to limit concurrency
    sem = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
    
    async def extract_with_semaphore(result):
        try:
            async with sem:
                content = await extract_content(result['url'])
                return {
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result['snippet'],
                    'content': content
                }
        except Exception as e:
            logger.error(f"Error extracting content from {result['url']}: {str(e)}")
            # Return result with empty content instead of failing
            return {
                'title': result['title'],
                'url': result['url'],
                'snippet': result['snippet'],
                'content': f"Failed to extract content: {str(e)}"
            }
    
    # Create extraction tasks
    tasks = [extract_with_semaphore(result) for result in search_results]
    
    # Wait for all extraction tasks to complete with timeout
    results_with_content = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and empty results
    valid_results = []
    for i, result in enumerate(results_with_content):
        if isinstance(result, Exception):
            logger.error(f"Error extracting content from {search_results[i]['url']}: {str(result)}")
            continue
        if result and result.get('content'):
            valid_results.append(result)
    
    logger.info(f"Extracted content from {len(valid_results)} out of {len(search_results)} search results for query: {query}")
    
    return valid_results

async def search_information(search_query: str, num_results: int = 5) -> str:
    """
    Fully asynchronous function to search for information based on a query.
    
    Args:
        search_query: The search query
        num_results: Number of search results to use (default 5)
        
    Returns:
        str: Organized text content from the top search results
    """
    logger.info(f"Searching for information: {search_query}")
    
    # Check cache first
    cache_key = f"{search_query}_{num_results}"
    async with _cache_lock:
        cached_result = _search_cache.get(cache_key)
        if cached_result:
            cache_time, result = cached_result
            # Return cached result if it's less than an hour old
            if time.time() - cache_time < settings.CACHE_TTL:
                logger.info(f"Returning cached result for query: {search_query}")
                return result
    
    # Use a semaphore to limit concurrent searches to prevent overloading
    async with _search_semaphore:
        try:
            start_time = time.time()
            
            # Search and extract content
            results = await search_and_extract(search_query, num_results)
            
            # If no results found, try with a modified query or different approach
            if not results:
                logger.warning(f"No results found for '{search_query}', trying with modified query")
                # Try with a simplified query (remove special characters and extra words)
                simplified_query = re.sub(r'[^\w\s]', '', search_query)
                simplified_query = re.sub(r'\b(what|how|when|where|who|is|are|the|a|an)\b', '', simplified_query, flags=re.IGNORECASE)
                simplified_query = re.sub(r'\s+', ' ', simplified_query).strip()
                
                if simplified_query and simplified_query != search_query:
                    logger.info(f"Trying simplified query: '{simplified_query}'")
                    results = await search_and_extract(simplified_query, num_results)
            
            if not results:
                no_results_msg = "No results found for the given query. Try rephrasing your question or using different keywords."
                logger.warning(f"{no_results_msg} Query: {search_query}")
                return no_results_msg
            
            # Organize the extracted content
            organized_content = []
            
            for i, result in enumerate(results, 1):
                if not result['content']:
                    continue
                    
                # Format each result
                result_text = f"SOURCE {i}: {result['title']}\n"
                result_text += f"URL: {result['url']}\n"
                result_text += f"SUMMARY: {result['snippet']}\n"
                result_text += f"\nCONTENT:\n{result['content']}\n"
                result_text += "-" * 80 + "\n"  # Separator
                
                organized_content.append(result_text)
            
            # Combine all content
            content = "\n".join(organized_content)
            
            # Add timing information
            elapsed = time.time() - start_time
            content += f"\nSearch completed in {elapsed:.2f} seconds."
            
            # Cache the result
            async with _cache_lock:
                _search_cache[cache_key] = (time.time(), content)
                
                # Clean up old cache entries if there are too many
                if len(_search_cache) > 100:
                    now = time.time()
                    # Remove oldest and expired entries
                    expired_keys = [k for k, (t, _) in _search_cache.items() if now - t > settings.CACHE_TTL]
                    for k in expired_keys:
                        _search_cache.pop(k, None)
            
            logger.info(f"Search completed for '{search_query}' in {elapsed:.2f} seconds with {len(organized_content)} results")
            return content
            
        except asyncio.TimeoutError:
            error_msg = "Search timed out. Please try a more specific query."
            logger.error(f"{error_msg} Query: {search_query}")
            return error_msg
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            logger.exception(f"{error_msg} Query: {search_query}")
            return error_msg
