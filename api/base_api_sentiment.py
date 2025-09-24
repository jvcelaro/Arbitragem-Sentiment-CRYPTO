from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
import asyncio
import aiohttp
import time

from base_api_arbitragem import APIResponse

@dataclass
class NewsArticle:
    """Estrutura padronizada para artigos de notícias"""
    title: str
    description: str
    url: str
    source: str
    published_at: str
    content: Optional[str] = None
    sentiment_score: Optional[float] = None
    language: str = "en"

@dataclass
class SentimentData:
    symbol: str
    overall_sentiment: float  
    positive_ratio: float    
    negative_ratio: float   
    neutral_ratio: float   
    news_count: int
    confidence_score: float 
    timestamp: float
    data_source: str

class BaseSentimentAPI(ABC):
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, rate_limit: int = 1000):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_minute_start = time.time()
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30), 
            headers=self._get_default_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_default_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': f'{self.__class__.__name__}/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers.update(self._get_auth_headers())
        
        return headers
    
    def _get_auth_headers(self) -> Dict[str, str]:
        
        return {'X-API-Key': self.api_key}
    
    async def _handle_rate_limit(self):
        current_time = time.time()
        
        if current_time - self.last_minute_start >= 60:
            self.request_count = 0
            self.last_minute_start = current_time
        
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.last_minute_start)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_minute_start = time.time()
        
        self.request_count += 1
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> APIResponse:
        await self._handle_rate_limit()
        
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response_time = (time.time() - start_time) * 1000
                print(response)
                
                if response.status == 200:
                    data = await response.json()
                    return APIResponse(
                        data=data,
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    return APIResponse(
                        data=None,
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=False,
                        error_message=error_text
                    )
                    
        except Exception as e:
            return APIResponse(
                data=None,
                status_code=500,
                response_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )
    
    @abstractmethod
    async def get_news(self, query: str, limit: int = 100) -> List[NewsArticle]:
        """Busca notícias para uma query específica"""
        pass
    
    @abstractmethod
    async def get_crypto_news(self, symbol: str, limit: int = 50) -> List[NewsArticle]:
        """Busca notícias específicas sobre uma criptomoeda"""
        pass

