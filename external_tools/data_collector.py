"""
Data Collector Module
Wrapper for web search and data collection from external sources
Implements targeted querying, data cleaning, and source prioritization
Includes retry logic and rate limit handling
"""
from typing import List, Dict, Set
from datetime import datetime
import logging
import re
import time
import random
from gnews import GNews
from duckduckgo_search import DDGS
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataCollector:
    """Collects market data from web sources using GNews API with DuckDuckGo fallback"""
    
    def __init__(self):
        self.use_gnews = bool(settings.gnews_api_key)
        
        # Initialize GNews client
        if self.use_gnews:
            self.gnews = GNews(language='en', country='IN', max_results=3, period='7d')
            logger.info("[DATA COLLECTOR] Using GNews API")
        else:
            logger.warning("[DATA COLLECTOR] Using DuckDuckGo fallback (may be rate limited)")
    
    def _search_gnews(self, query: str, max_results: int = 3) -> List:
        """
        Search using GNews API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results in standardized format
        """
        try:
            logger.debug(f"[DATA COLLECTOR] Searching with GNews API: {query}")
            articles = self.gnews.get_news(query)
            
            # Convert GNews format to our standard format
            results = []
            for article in articles[:max_results]:
                results.append({
                    'title': article.get('title', 'No Title'),
                    'body': article.get('description', ''),
                    'source': article.get('publisher', {}).get('title', 'Unknown'),
                    'href': article.get('url', ''),
                    'published': article.get('published date', '')
                })
            
            logger.debug(f"[DATA COLLECTOR] ✓ GNews returned {len(results)} articles")
            return results
            
        except Exception as e:
            logger.warning(f"[DATA COLLECTOR] GNews search failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=4, max=15),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _search_duckduckgo(self, query: str, max_results: int = 3) -> List:
        """
        Fallback search using DuckDuckGo (with retry)
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
            
        Raises:
            Exception: If all retry attempts fail
        """
        try:
            logger.debug(f"[DATA COLLECTOR] Attempting DuckDuckGo search (fallback)...")
            ddgs = DDGS(timeout=20)
            results = list(ddgs.text(query, max_results=max_results))
            logger.debug(f"[DATA COLLECTOR] ✓ DuckDuckGo returned {len(results)} results")
            return results
        except Exception as e:
            logger.debug(f"[DATA COLLECTOR] DuckDuckGo search failed: {e}")
            raise
    
    def _search_with_retry(self, query: str, max_results: int = 3) -> List:
        """
        Execute search with automatic provider selection and fallback
        Uses GNews API if available, falls back to DuckDuckGo
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if self.use_gnews:
            try:
                return self._search_gnews(query, max_results)
            except Exception as e:
                logger.warning(f"[DATA COLLECTOR] GNews failed, trying DuckDuckGo fallback: {e}")
                # Fall through to DuckDuckGo
        
        # Use DuckDuckGo (either as primary or fallback)
        return self._search_duckduckgo(query, max_results)
    
    def collect_sector_data(self, sector: str, country: str = "India") -> Dict:
        """
        Collect comprehensive data about a sector
        
        Args:
            sector: Sector to research
            country: Target country
            
        Returns:
            Dictionary with search results and raw data
        """
        logger.info(f"[DATA COLLECTOR] Collecting data for: {sector} in {country}")
        
        # Prepare targeted search queries (reduced to 3 to avoid rate limiting)
        year = datetime.now().year
        queries = [
            f"{country} {sector} trade opportunities market growth {year}",
            f"{country} {sector} export import policy investment {year}",
            f"{country} {sector} market size companies trends {year}"
        ]
        
        all_results = []
        raw_texts = []
        seen_content: Set[str] = set()  # For deduplication
        
        # Execute searches with prioritization and rate limit handling
        for idx, query in enumerate(queries, 1):
            try:
                logger.debug(f"[DATA COLLECTOR] Query {idx}/{len(queries)}: {query}")
                
                # Add small delay between queries (GNews is more generous than DuckDuckGo)
                if idx > 1:
                    delay = random.uniform(1.0, 2.0) if self.use_gnews else random.uniform(5.0, 8.0)
                    logger.debug(f"[DATA COLLECTOR] Waiting {delay:.1f}s before next query...")
                    time.sleep(delay)
                
                # Execute search with retry logic (backoff handled by tenacity)
                results = self._search_with_retry(query, max_results=3)
                
                for result in results:
                    title = result.get('title', 'No Title')
                    body = result.get('body', '')
                    source = result.get('source', 'Unknown')
                    url = result.get('href', '')
                    
                    # Clean and normalize text
                    cleaned_body = self._clean_text(body)
                    
                    # Deduplicate based on content similarity
                    content_hash = self._generate_content_hash(cleaned_body)
                    if content_hash in seen_content:
                        logger.debug(f"[DATA COLLECTOR] Skipping duplicate: {title[:50]}...")
                        continue
                    seen_content.add(content_hash)
                    
                    # Prioritize based on source quality
                    priority = self._assess_source_priority(source, title, body)
                    
                    all_results.append({
                        'title': title,
                        'snippet': cleaned_body[:300],  # Keep snippet clean
                        'url': url,
                        'source': source,
                        'priority': priority,
                        'query_type': self._classify_query(idx)
                    })
                    
                    # Format with clear delimiters for LLM
                    article_text = self._format_article(
                        article_num=len(raw_texts) + 1,
                        title=title,
                        source=source,
                        content=cleaned_body,
                        url=url
                    )
                    raw_texts.append(article_text)
                    
            except Exception as e:
                logger.warning(f"[DATA COLLECTOR] Query {idx} failed after retries: {e}")
                # Continue with other queries even if one fails
                continue
        
        # Sort by priority and limit to top sources
        all_results.sort(key=lambda x: x['priority'], reverse=True)
        top_results = all_results[:8]  # Limit to top 8 most relevant sources
        
        # Determine data quality
        data_quality = 'high' if len(top_results) >= 5 else 'moderate' if len(top_results) >= 3 else 'low'
        
        # Prepare final cleaned corpus using ONLY top-quality sources (aligns AI context with UI)
        if top_results:
            # Build raw_data from top_results only (not all collected articles)
            top_raw_texts = []
            for idx, result in enumerate(top_results, 1):
                article_text = self._format_article(
                    article_num=idx,
                    title=result['title'],
                    source=result['source'],
                    content=result['snippet'],  # Use cleaned snippet
                    url=result['url']
                )
                top_raw_texts.append(article_text)
            raw_data = "\n\n".join(top_raw_texts)
        else:
            raw_data = self._generate_fallback_context(sector, country)
            logger.warning("[DATA COLLECTOR] No search results, using fallback")
        
        data = {
            'sector': sector,
            'country': country,
            'timestamp': datetime.utcnow().isoformat(),
            'search_results': top_results,
            'raw_data': raw_data,
            'total_results': len(top_results),
            'data_quality': data_quality,
            'fallback_used': len(top_results) == 0
        }
        
        logger.info(f"[DATA COLLECTOR] Collected {len(top_results)} high-quality results (quality: {data_quality})")
        return data
    
    def _generate_fallback_context(self, sector: str, country: str) -> str:
        """
        Generate minimal context when search fails
        
        Args:
            sector: Sector name
            country: Country name
            
        Returns:
            Fallback context string
        """
        return f"""---Fallback Context---
SOURCE: System Context
TITLE: {sector.title()} Sector Analysis Framework - {country}

**IMPORTANT INSTRUCTION TO AI:**
No external search data is currently available due to API rate limiting. 

You MUST generate a report based on:
1. Your general knowledge of the {country} {sector} sector
2. Standard industry analysis frameworks
3. General economic trends in {country}

**MANDATORY DISCLAIMERS:**
- All data points MUST be labeled as "Estimated" or "Approximate"
- Source all claims as "Industry estimates" or "General market observations"
- Focus on QUALITATIVE analysis over specific numbers
- Emphasize that this is a preliminary analysis pending data availability
- Recommend data sources for future validation

**REPORT STRUCTURE:**
- Use conditional language (e.g., "typically", "generally", "estimated")
- Provide framework for analysis rather than specific claims
- List data sources that SHOULD be consulted for verification
- Make it clear this is based on general industry knowledge, not real-time data

---End Fallback Context---"""
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and tabs
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web noise patterns
        noise = r'(cookie policy|terms of service|privacy policy|sign up for.*newsletter|subscribe now|related articles?:?|read more:?|share this article|advertisement|\[.*?\])'
        text = re.sub(noise, '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _generate_content_hash(self, text: str) -> str:
        """Generate a simple hash for deduplication"""
        return re.sub(r'\W+', '', text.lower())[:100]
    
    def _assess_source_priority(self, source: str, title: str, body: str) -> int:
        """
        Assess source quality and relevance
        
        Returns:
            Priority score (higher is better)
        """
        score = 50  # Base score
        
        # Prioritize financial/business news sources
        high_quality_sources = [
            'economic times', 'business standard', 'financial express',
            'livemint', 'moneycontrol', 'reuters', 'bloomberg',
            'ministry', 'government', 'rbi', 'sebi', 'nse', 'bse'
        ]
        
        source_lower = source.lower()
        for quality_source in high_quality_sources:
            if quality_source in source_lower:
                score += 30
                break
        
        # Bonus for key terms in title
        if any(term in title.lower() for term in ['trade', 'export', 'import', 'investment', 'growth', 'policy', 'opportunity', 'market']):
            score += 5
        
        # Bonus for recent/current data indicators
        if any(ind in (title + ' ' + body).lower() for ind in ['2025', '2024', 'latest', 'current', 'recent']):
            score += 3
        
        return score
    
    def _classify_query(self, query_index: int) -> str:
        """Classify query type for metadata"""
        return {1: 'Trade & Growth', 2: 'Policy & Investment', 3: 'Market Data'}.get(query_index, 'General')
    
    def _format_article(self, article_num: int, title: str, source: str, 
                       content: str, url: str) -> str:
        """
        Format article with clear delimiters for LLM parsing
        
        Args:
            article_num: Article number
            title: Article title
            source: Source name
            content: Article content
            url: Source URL
            
        Returns:
            Formatted article string
        """
        return f"""---Article {article_num}---
SOURCE: {source}
TITLE: {title}
URL: {url}

{content}

---End Article {article_num}---"""


# Global collector instance
data_collector = DataCollector()
