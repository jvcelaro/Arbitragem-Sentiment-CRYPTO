from base_api_sentiment import BaseSentimentAPI, NewsArticle, SentimentData
from typing import Optional, Dict, List, Any
import asyncio
import time
import os
from dotenv import load_dotenv

import sys
sys.path.append(r'D:\Projetos\Arbitragem e Sentiment CRYPT\Project')
from config import Config

load_dotenv()

class NewsAPI(BaseSentimentAPI):
    
    def __init__(self):
        super().__init__(
            base_url=Config.NEWS_API_URL,
            api_key=os.getenv('NEWS_API_KEY'),
            rate_limit=Config.NEWS_RATE_LIMIT 
        )
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {'X-API-Key': self.api_key}
    
    async def get_news(self, query: str, from_date: str, to_date: str, limit: int = 100) -> List[NewsArticle]:
        endpoint = "/everything"
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'from' : from_date,
            'to': to_date,
        }
        
        response = await self._make_request(endpoint, params)


        
        if not response.success:
            print("Respose with empty data!")
            return []
        
        articles = []
        for article_data in response.data.get('articles', []):
            article = NewsArticle(
                title=article_data.get('title', ''),
                description=article_data.get('description', ''),
                url=article_data.get('url', ''),
                source=article_data.get('source', {}).get('name', ''),
                published_at=article_data.get('publishedAt', ''),
                content=article_data.get('content')
            )
            articles.append(article)
        
        return articles
    
    async def get_crypto_news(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        crypto_terms = {
            'bitcoin': 'bitcoin OR BTC OR cryptocurrency',
            'ethereum': 'ethereum OR ETH OR smart contracts',
            'cardano': 'cardano OR ADA'
        }
        
        query = crypto_terms.get(symbol.lower(), symbol)
        return await self.get_news(query, '2025-01-01', '2025-09-25', limit)
    

async def teste_news_api():
    
   async with NewsAPI() as api:
       
       news = await api.get_crypto_news("bitcoin")
       print(news)


if __name__ == "__main__":  

    asyncio.run(teste_news_api())