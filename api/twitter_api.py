from api.base_api_sentiment import BaseSentimentAPI, NewsArticle, SentimentData
from typing import Optional, Dict, List, Any
import asyncio
import time
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()


class TwitterAPI(BaseSentimentAPI):
    """Implementação para Twitter API v2"""
    
    def __init__(self, bearer_token: str):
        super().__init__(
            base_url="https://api.twitter.com/2",
            api_key=bearer_token, 
            rate_limit=300 
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Twitter usa Bearer token"""
        return {'Authorization': f'Bearer {self.api_key}'}
    
    async def get_news(self, query: str, limit: int = 100) -> List[NewsArticle]:
        """Implementa busca de tweets como 'notícias'"""
        endpoint = "/tweets/search/recent"
        params = {
            'query': query,
            'max_results': min(limit, 100),
            'tweet.fields': 'created_at,author_id,public_metrics'
        }
        
        response = await self._make_request(endpoint, params)
        
        if not response.success:
            return []
        
        articles = []
        for tweet in response.data.get('data', []):
            article = NewsArticle(
                title=tweet.get('text', '')[:100] + "...",  
                description=tweet.get('text', ''),
                url=f"https://twitter.com/user/status/{tweet.get('id')}",
                source="Twitter",
                published_at=tweet.get('created_at', ''),
                content=tweet.get('text')
            )
            articles.append(article)
        
        return articles
    
    async def get_crypto_news(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Busca tweets sobre crypto"""
        query = f"#{symbol} OR ${symbol.upper()} OR {symbol} -is:retweet lang:en"
        return await self.get_news(query, limit)