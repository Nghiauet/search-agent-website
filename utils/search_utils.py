import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
import os
import time
from typing import List, Dict, Any, Optional
import cachetools.func
import re
from loguru import logger

# Try to import Brotli for content decoding - make it optional
try:
    import brotli
    BROTLI_AVAILABLE = True
    logger.info("Brotli compression support is available")
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning("Brotli compression not available. Some websites may not be displayed properly. Install with: pip install brotli")

from utils.config import settings

# Constants for optimization
CONNECTION_TIMEOUT = 10  # seconds (increased from 5)
CONTENT_TIMEOUT = 15    # seconds (increased from 10)
MAX_CONTENT_LENGTH = 5000  # characters (increased from 3000)
CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)
MAX_CONCURRENT_REQUESTS = 5  # Limit concurrent requests (decreased from 10 for better stability)
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

# Shared aiohttp session for connection pooling
_session = None
# Semaphore for limiting concurrent searches
_search_semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent searches

async def get_session():
    """Get or create a shared aiohttp session for connection pooling."""
    global _session
    if _session is None or _session.closed:
        conn = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, ssl=False)
        _session = aiohttp.ClientSession(connector=conn)
    return _session

async def retry_with_backoff(func, *args, max_retries=3, base_delay=1, **kwargs):
    """Retry a function with exponential backoff."""
    for retry in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if retry == max_retries - 1:
                raise  # Re-raise on last attempt
            
            # Calculate delay with exponential backoff (1s, 2s, 4s...)
            delay = base_delay * (2 ** retry)
            logger.warning(f"Request failed: {str(e)}. Retrying in {delay}s... (Attempt {retry+1}/{max_retries})")
            await asyncio.sleep(delay)

@cachetools.func.ttl_cache(maxsize=100, ttl=CACHE_TTL)
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
            async with session.get(url, params=params, timeout=CONNECTION_TIMEOUT) as response:
                if response.status != 200:
                    logger.warning(f"Google search API returned status {response.status} for query: {query}")
                    return []
                return await response.json()
        
        # Make the request with retries
        results = await retry_with_backoff(make_search_request, max_retries=2)
        
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

async def extract_content_from_url(url: str) -> str:
    """
    Extract content from a given URL asynchronously with optimizations.
    
    Args:
        url (str): The URL to extract content from
        
    Returns:
        str: Extracted content from the webpage
    """
    # Skip URLs that are likely to be problematic
    if not url or not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL format: {url}")
        return "Invalid URL format"
    
    # Check for file types that are not HTML (images, PDFs, etc.)
    if re.search(r'\.(jpg|jpeg|png|gif|pdf|doc|docx|xls|xlsx|zip|tar)$', url, re.IGNORECASE):
        logger.warning(f"URL points to a non-HTML file: {url}")
        return "URL points to a non-HTML file"
    
    # Skip known problematic domains if Brotli is not available
    problematic_domains = ['facebook.com', 'instagram.com', 'twitter.com']
    if not BROTLI_AVAILABLE:
        # If Brotli is not available, add domains that use Brotli compression
        brotli_domains = ['nbcnews.com', 'cnn.com', 'edition.cnn.com', 'foxnews.com']
        problematic_domains.extend(brotli_domains)
    
    if any(domain in url.lower() for domain in problematic_domains):
        logger.warning(f"Skipping known problematic domain: {url}")
        return f"Content from {url} (URL requires Brotli support for proper access)"
    
    try:
        # Define a function to make the HTTP request with retry capability
        async def fetch_url_content():
            session = await get_session()
            
            # Prepare headers with compression support based on available libraries
            headers = dict(REQUEST_HEADERS)
            if BROTLI_AVAILABLE:
                # If Brotli is available, accept it as a content encoding
                headers['Accept-Encoding'] = 'gzip, deflate, br'
            else:
                # If Brotli is not available, only accept gzip and deflate
                headers['Accept-Encoding'] = 'gzip, deflate'
            
            async with session.get(
                url, 
                headers=headers,
                timeout=CONTENT_TIMEOUT,
                allow_redirects=True,
                ssl=False  # Skip SSL verification
            ) as response:
                if response.status != 200:
                    logger.warning(f"Got status {response.status} when extracting content from {url}")
                    return ""
                
                # Check content type to ensure it's HTML
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower():
                    logger.warning(f"Content type is not HTML: {content_type} for URL: {url}")
                    return ""
                
                # Get the HTML content
                return await response.text(errors='replace')
        
        # Make the request with retries
        html_content = await retry_with_backoff(fetch_url_content, max_retries=2, base_delay=0.5)
        
        # Skip processing if no content was retrieved
        if not html_content:
            return ""
        
        # Use a faster parser
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script, style, and other irrelevant elements
        for element in soup(['script', 'style', 'meta', 'noscript', 'header', 'footer', 'nav']):
            element.decompose()
        
        # Try to find the main content using common selectors
        text = ""
        # 1. First check for common article content containers
        article_containers = soup.select('article, .article, .post, .content, .entry, #article, #content, main, .main-content, [role="main"]')
        
        if article_containers:
            for container in article_containers:
                container_text = container.get_text(separator=' ', strip=True)
                if len(container_text) > len(text):
                    text = container_text
        
        # 2. If no article containers or text is too short, try common paragraph selectors
        if not text or len(text) < 200:
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li'])
            if paragraphs:
                text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
        # 3. As a last resort, get all text
        if not text or len(text) < 200:
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text effectively
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text[:MAX_CONTENT_LENGTH] + ("..." if len(text) > MAX_CONTENT_LENGTH else "")
            
        logger.debug(f"Successfully extracted {len(text)} characters from {url}")
        return text
        
    except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeDecodeError) as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return f"Error extracting content: {str(e)}"
    except Exception as e:
        logger.exception(f"Unexpected error extracting content from {url}: {str(e)}")
        return f"Unexpected error: {str(e)}"

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
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def extract_with_semaphore(result):
        try:
            async with sem:
                content = await extract_content_from_url(result['url'])
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

# LRU cache for search results with a process-safe wrapper
# We'll use a dictionary as an in-memory cache
_search_cache = {}
_cache_lock = asyncio.Lock()  # Lock for thread-safe cache operations

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
            if time.time() - cache_time < CACHE_TTL:
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
                    expired_keys = [k for k, (t, _) in _search_cache.items() if now - t > CACHE_TTL]
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
