from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import asyncio
import time

@dataclass
class APIResponse:
    """Estrutura padrão para respostas de API"""
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
    """Estrutura padrão para dados de preço (todas APIs retornam isso)"""
    symbol: str
    price_usd: float
    volume_24h: float
    price_change_24h: float
    market_cap: Optional[float] = None
    last_updated: Optional[float] = None

class BaseCryptoAPI(ABC):
    """
    Classe abstrata que define o 'contrato' que TODAS as APIs devem seguir.
    
    Vantagens:
    1. Padronização - todas APIs fazem as mesmas coisas
    2. Polimorfismo - pode trocar APIs sem quebrar código
    3. Testabilidade - fácil criar mocks
    4. Documentação - fica claro o que cada API deve fazer
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, rate_limit: int = 100):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit  # calls per minute
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.last_minute_start = time.time()
    
    async def __aenter__(self):
        """Context manager para controlar sessão HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers=self._get_default_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Headers padrão - cada API pode customizar"""
        return {
            'User-Agent': f'{self.__class__.__name__}/1.0',
            'Accept': 'application/json'
        }
    
    async def _handle_rate_limit(self):
        """Controla rate limit de forma inteligente"""
        current_time = time.time()
        
        # Se passou 1 minuto, reseta contador
        if current_time - self.last_minute_start >= 60:
            self.request_count = 0
            self.last_minute_start = current_time
        
        # Se atingiu limite, espera
        if self.request_count >= self.rate_limit:
            wait_time = 60 - (current_time - self.last_minute_start)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.last_minute_start = time.time()
        
        self.request_count += 1
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> APIResponse:
        """Método base para fazer requests - reutilizado por todas APIs"""
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
    
    # ==========================================
    # MÉTODOS ABSTRATOS - TODAS APIS DEVEM TER
    # ==========================================
    
    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """
        Cada API DEVE implementar este método.
        CoinGecko vai fazer de um jeito, CryptoCompare de outro,
        mas ambas DEVEM retornar PriceData
        """
        pass
    
    @abstractmethod
    async def get_multiple_prices(self, symbols: List[str]) -> List[PriceData]:
        """Todas APIs DEVEM conseguir pegar múltiplos preços"""
        pass
    
    @abstractmethod
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:
        """Todas APIs DEVEM fornecer dados de exchanges"""
        pass
    
    @abstractmethod
    async def get_exchange_tickers(self, exchange_id: str) -> List[Dict[str, Any]]:
        """Dados específicos de uma exchange"""
        pass
    
    # ==========================================
    # MÉTODOS OPCIONAIS - PODEM SER SOBRESCRITOS
    # ==========================================
    
    async def health_check(self) -> bool:
        """Verifica se API está funcionando"""
        try:
            # Faz um request simples para testar conectividade
            response = await self._make_request("/ping")
            return response.success
        except:
            return False
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Status do rate limit atual"""
        return {
            'requests_made': self.request_count,
            'rate_limit': self.rate_limit,
            'requests_remaining': self.rate_limit - self.request_count,
            'reset_time': self.last_minute_start + 60
        }

# ==========================================
# EXEMPLO DE COMO USAR (será implementado)
# ==========================================

class CoinGeckoAPI(BaseCryptoAPI):
    """Implementação específica para CoinGecko"""
    
    def __init__(self):
        super().__init__(
            base_url="https://api.coingecko.com/api/v3",
            rate_limit=30  # CoinGecko permite 30/min
        )
    
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """Implementa o método abstrato para CoinGecko"""
        # TODO: Implementação específica do CoinGecko
        pass
    
    async def get_multiple_prices(self, symbols: List[str]) -> List[PriceData]:
        """Implementa para CoinGecko"""
        # TODO: Implementação específica
        pass
    
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:
        """Implementa para CoinGecko"""
        # TODO: Implementação específica
        pass
    
    async def get_exchange_tickers(self, exchange_id: str) -> List[Dict[str, Any]]:
        """Implementa para CoinGecko"""
        # TODO: Implementação específica
        pass

class CryptoCompareAPI(BaseCryptoAPI):
    """Implementação específica para CryptoCompare"""
    
    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://min-api.cryptocompare.com/data",
            api_key=api_key,
            rate_limit=100  # CryptoCompare permite 100/min
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """CryptoCompare precisa de header específico"""
        headers = super()._get_default_headers()
        if self.api_key:
            headers['Authorization'] = f'Apikey {self.api_key}'
        return headers
    
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """Implementa para CryptoCompare (diferente do CoinGecko!)"""
        # TODO: Implementação específica
        pass
    
    async def get_multiple_prices(self, symbols: List[str]) -> List[PriceData]:
        """Implementa para CryptoCompare"""
        # TODO: Implementação específica  
        pass
    
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:
        """Implementa para CryptoCompare"""
        # TODO: Implementação específica
        pass
    
    async def get_exchange_tickers(self, exchange_id: str) -> List[Dict[str, Any]]:
        """Implementa para CryptoCompare"""
        # TODO: Implementação específica
        pass

# ==========================================
# EXEMPLO DE USO POLIMÓRFICO
# ==========================================

async def example_usage():
    """Exemplo mostrando a VANTAGEM do polimorfismo"""
    
    # Posso usar QUALQUER API da mesma forma!
    apis = [
        CoinGeckoAPI(),
        CryptoCompareAPI(api_key="your-key")
    ]
    
    symbols = ['bitcoin', 'ethereum']
    
    for api in apis:
        async with api:
            print(f"\n📊 Testando {api.__class__.__name__}:")
            
            # MESMA INTERFACE para todas APIs!
            prices = await api.get_multiple_prices(symbols)
            exchanges = await api.get_exchanges_data()
            
            print(f"Preços coletados: {len(prices)}")
            print(f"Exchanges: {len(exchanges)}")
            print(f"Rate limit status: {api.get_rate_limit_status()}")

if __name__ == "__main__":
    asyncio.run(example_usage())