from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
import asyncio
import aiohttp
import time

@dataclass
class APIResponse:

    data: Any
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class PriceData:

    id: str
    rank: str
    symbol: str
    price_usd: float
    market_capusd: str
    volume_24h: float
    price: float
    changePercent: str
    vwap24Hr: Optional[float] = None

@dataclass
class ExchangeData:
    id: str
    name: str
    volume_24h_usd: float
    trading_pairs: int
    market_share_percentage: float
    last_updated: str
    timestamp: str
    data_source: str = "coincap"

    

class BaseArbitragemAPI(ABC):
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, rate_limit: int = 100):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit  
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_minute_start = time.time()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers=self._get_default_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_default_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': f'{self.__class__.__name__}/1.0',
            'Accept': 'application/json'
        }
    
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
    async def get_assets_prices(self) -> List[PriceData]:
        pass
    
    @abstractmethod
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_assets_per_exhange(self, asset_name: str) -> List[ExchangeData]:
        pass