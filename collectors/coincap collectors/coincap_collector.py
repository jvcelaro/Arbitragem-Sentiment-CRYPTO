import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

from core.decorators import performance_monitor, cache_with_ttl, retry_on_failure
from core.context_managers import ProfiledExecution
from api.coincap_api import CoinCapAPI
from api.base_api_arbitragem import ExchangeData, PriceData

load_dotenv()

@dataclass
class CollectorMetrics:
    total_time_seconds: float
    exchanges_collected: int
    opportunities_found: int
    api_calls_made: int
    cache_hits: int
    errors_count: int
    timestamp: float

    
@dataclass
class ArbitrageData:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_percentage: float
    buy_volume_24h: float
    sell_volume_24h: float
    profit_potential: float
    timestamp: float
    data_source: str = "coincap"

class CoinCapCollector:
    
    def __init__(self, api_key: str, config: Optional[Dict] = None):
        self.api_key = api_key
        self.config = config or {}
        
        self.target_symbols = self.config.get('target_symbols', ['bitcoin', 'ethereum', 'cardano'])
        self.min_volume_threshold = self.config.get('min_volume_threshold', 100000)  
        self.min_spread_percentage = self.config.get('min_spread_percentage', 0.1) 
        
        self.metrics = CollectorMetrics(
            total_time_seconds=0,
            exchanges_collected=0,
            opportunities_found=0,
            api_calls_made=0,
            cache_hits=0,
            errors_count=0,
            timestamp=time.time()
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @performance_monitor  
    @cache_with_ttl(ttl=120)  
    @retry_on_failure(max_attempts=3)  
    async def collect_exchanges_data(self) -> List[ExchangeData]:

        with ProfiledExecution("coincap_exchanges_collection"): 
            
            async with CoinCapAPI(self.api_key) as api:
                self.metrics.api_calls_made += 1
                
                try:
                    exchanges_raw = await api.get_exchanges_data()
                    
                    if not isinstance(exchanges_raw, list):
                        self.logger.error(f"API retornou tipo incorreto: {type(exchanges_raw)}")
                        self.metrics.errors_count += 1
                        return []

                    exchanges_processed = exchanges_raw
                                        
                    self.metrics.exchanges_collected = len(exchanges_processed)
                    self.logger.info(f"Coletadas {len(exchanges_processed)} exchanges com sucesso")
                    
                    return exchanges_processed
                    
                except Exception as e:
                    self.logger.error(f"Erro na coleta de exchanges: {e}")
                    self.metrics.errors_count += 1
                    return []
    
    @performance_monitor
    @cache_with_ttl(ttl=60) 
    async def collect_arbitrage_opportunities(self, symbol: str = 'bitcoin') -> List[ArbitrageData]:
      
        with ProfiledExecution(f"arbitrage_detection_{symbol}"):
            
            async with CoinCapAPI(self.api_key) as api:
                self.metrics.api_calls_made += 1
                
                try:
                    markets = await api.get_arbitrage_opportunities(symbol)
                    
                    if len(markets) < 2:
                        self.logger.warning(f"Poucos markets encontrados para {symbol}: {len(markets)}")
                        return []
                    
                    liquid_markets = [
                        m for m in markets 
                        if float(m.get('volumeUsd24Hr', 0)) >= self.min_volume_threshold
                    ]
                    
                    if len(liquid_markets) < 2:
                        self.logger.info(f"Poucos markets líquidos para {symbol} (min volume ${self.min_volume_threshold:,.0f})")
                        return []
                    
                    opportunities = self._analyze_arbitrage_opportunities(liquid_markets, symbol)
                    
                    self.metrics.opportunities_found = len(opportunities)
                    self.logger.info(f"Encontradas {len(opportunities)} oportunidades para {symbol}")
                    
                    return opportunities
                    
                except Exception as e:
                    self.logger.error(f"Erro na coleta de arbitragem para {symbol}: {e}")
                    self.metrics.errors_count += 1
                    return []
    
    def _analyze_arbitrage_opportunities(self, markets: List[Dict], symbol: str) -> List[ArbitrageData]:
      
        opportunities = []
        
        markets_sorted = sorted(markets, key=lambda x: float(x.get('priceUsd', 0)))
        
        for i, buy_market in enumerate(markets_sorted[:-1]):
            for sell_market in markets_sorted[i+1:]:
                
                buy_price = float(buy_market.get('priceUsd', 0))
                sell_price = float(sell_market.get('priceUsd', 0))
                
                if buy_price <= 0 or sell_price <= 0:
                    continue
                
                spread_percentage = ((sell_price - buy_price) / buy_price) * 100
                
                if spread_percentage >= self.min_spread_percentage:
                    
                    buy_volume = float(buy_market.get('volumeUsd24Hr', 0))
                    sell_volume = float(sell_market.get('volumeUsd24Hr', 0))
                    
                    profit_potential = (sell_price - buy_price) * min(buy_volume, sell_volume) * 0.001
                    
                    opportunity = ArbitrageData(
                        symbol=symbol,
                        buy_exchange=buy_market.get('exchangeId', 'unknown'),
                        sell_exchange=sell_market.get('exchangeId', 'unknown'),
                        buy_price=buy_price,
                        sell_price=sell_price,
                        spread_percentage=spread_percentage,
                        buy_volume_24h=buy_volume,
                        sell_volume_24h=sell_volume,
                        profit_potential=profit_potential,
                        timestamp=time.time()
                    )
                    
                    opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x.spread_percentage, reverse=True)
    
    @performance_monitor
    async def collect_comprehensive_data(self) -> Dict[str, Any]:
        """
        Coleta completa de dados: exchanges + oportunidades de arbitragem.
        Método principal que orquestra toda a coleta.
        """
        collection_start = time.time()
        
        with ProfiledExecution("comprehensive_collection"):
            
            results = {
                'exchanges': [],
                'arbitrage_opportunities': {},
                'metadata': {
                    'collection_time': None,
                    'symbols_analyzed': self.target_symbols,
                    'metrics': None
                }
            }
            
            try:
                tasks = [
                    self.collect_exchanges_data(),
                    self.collect_arbitrage_opportunities(self.target_symbols[0])
                ]
                
                exchanges, first_opportunities = await asyncio.gather(*tasks, return_exceptions=True)
                
                if isinstance(exchanges, list):
                    results['exchanges'] = exchanges
                else:
                    self.logger.error(f"Erro na coleta de exchanges: {exchanges}")
                
                if isinstance(first_opportunities, list):
                    results['arbitrage_opportunities'][self.target_symbols[0]] = first_opportunities
                
                remaining_symbols = self.target_symbols[1:]
                if remaining_symbols:
                    arbitrage_tasks = [
                        self.collect_arbitrage_opportunities(symbol) 
                        for symbol in remaining_symbols
                    ]
                    
                    arbitrage_results = await asyncio.gather(*arbitrage_tasks, return_exceptions=True)
                    
                    for symbol, opportunities in zip(remaining_symbols, arbitrage_results):
                        if isinstance(opportunities, list):
                            results['arbitrage_opportunities'][symbol] = opportunities
                        else:
                            self.logger.error(f"Erro na arbitragem para {symbol}: {opportunities}")
                
                self.metrics.total_time_seconds = time.time() - collection_start
                self.metrics.timestamp = time.time()
                
                results['metadata']['collection_time'] = self.metrics.total_time_seconds
                results['metadata']['metrics'] = asdict(self.metrics)
                
                self.logger.info(f"Coleta completa finalizada em {self.metrics.total_time_seconds:.2f}s")
                
                return results
                
            except Exception as e:
                self.logger.error(f"Erro na coleta completa: {e}")
                self.metrics.errors_count += 1
                return results
    
    def get_metrics(self) -> CollectorMetrics:
        return self.metrics
    
    def reset_metrics(self):
        self.metrics = CollectorMetrics(
            total_time_seconds=0,
            exchanges_collected=0,
            opportunities_found=0,
            api_calls_made=0,
            cache_hits=0,
            errors_count=0,
            timestamp=time.time()
        )


async def teste_collector():

    print("CoinCap Collector - Teste Completo")
    print("=" * 50)
    
    config = {
        'target_symbols': ['bitcoin', 'ethereum', 'cardano'],
        'min_volume_threshold': 50000,  
        'min_spread_percentage': 0.05   
    }
    
    api_key = os.getenv("COINCAP_KEY")
    collector = CoinCapCollector(api_key, config)
    
    try:
        print("Iniciando coleta completa...")
        data = await collector.collect_comprehensive_data()
        
        print(f"RESULTADOS:")
        print(f"Exchanges coletadas: {len(data['exchanges'])}")
        
        for symbol, opportunities in data['arbitrage_opportunities'].items():
            print(f"{symbol}: {len(opportunities)} oportunidades")
            
            if opportunities:
                best = opportunities[0]
                print(f"Melhor: {best.spread_percentage:.2f}% "
                      f"({best.buy_exchange} → {best.sell_exchange})")
        
        metrics = collector.get_metrics()
        print(f"PERFORMANCE:")
        print(f"Tempo total: {metrics.total_time_seconds:.2f}s")
        print(f"API calls: {metrics.api_calls_made}")
        print(f"Erros: {metrics.errors_count}")
        
    except Exception as e:
        print(f"Erro no exemplo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(teste_collector())