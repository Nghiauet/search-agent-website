"""
Web content extraction functionality for the search engine.
"""
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

from utils.logging import logger
from utils.config import settings

# Try to import Brotli for content decoding - make it optional
try:
    import brotli
    BROTLI_AVAILABLE = True
    logger.info("Brotli compression support is available")
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning("Brotli compression not available. Some websites may not be displayed properly. Install with: pip install brotli")

# Standard request headers for web scraping
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

async def get_session():
    """Get or create a shared aiohttp session for connection pooling."""
    global _session
    if _session is None or _session.closed:
        conn = aiohttp.TCPConnector(limit=settings.MAX_CONCURRENT_REQUESTS, ssl=False)
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

async def extract_content(url: str) -> str:
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
                timeout=settings.CONTENT_TIMEOUT,
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
        text = text[:settings.MAX_CONTENT_LENGTH] + ("..." if len(text) > settings.MAX_CONTENT_LENGTH else "")
            
        logger.debug(f"Successfully extracted {len(text)} characters from {url}")
        return text
        
    except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeDecodeError) as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return f"Error extracting content: {str(e)}"
    except Exception as e:
        logger.exception(f"Unexpected error extracting content from {url}: {str(e)}")
        return f"Unexpected error: {str(e)}"
