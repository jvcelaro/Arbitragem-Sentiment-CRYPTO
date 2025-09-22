from base_api import BaseCryptoAPI, PriceData, APIResponse
from typing import Optional, Dict, List, Any

class CryptoCompareAPI(BaseCryptoAPI):
    def __init__(self, api_key: str):
        super().__init__(base_url="https://min-api.cryptocompare.com/data", api_key=api_key, rate_limit=100)

    def _get_default_headers(self) -> Dict[str, str]:
        """Headers específicos do CoinMarketCap"""
        headers = super()._get_default_headers()
        if self.api_key:
            headers['X-CMC_PRO_API_KEY'] = self.api_key  
        return headers
    
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        return await super().get_price(symbol)
    
    async def get_multiple_prices(self, symbols: List[str]) -> List[PriceData]:
        return await super().get_multiple_prices(symbols)
    
    async def get_exchange_tickers(self, exchange_id: str) -> List[Dict[str, Any]]:
        return await super().get_exchange_tickers(exchange_id)
    
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:
        return await super().get_exchanges_data()
    
    async def authentication(self, token):
        return await super().authentication(token)