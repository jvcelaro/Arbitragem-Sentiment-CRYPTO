from base_api import BaseCryptoAPI, PriceData, APIResponse
from typing import Optional, Dict, List, Any
import asyncio
from config import Config

import os
from dotenv import load_dotenv

load_dotenv()

class CoinCapAPI(BaseCryptoAPI):
    def __init__(self, api_key: str):
        super().__init__(base_url="https://api.coincap.io/v3", api_key=api_key, rate_limit=30)

    def _get_default_headers(self) -> Dict[str, str]:

        headers = super()._get_default_headers()
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"  
        return headers
    
    async def get_assets_prices(self) -> List[PriceData]:
        endpoint = "/assets"

        params = {
            "limit": 30
        }

        try:

            response = await self._make_request(endpoint, params)

            results = []
            if response.success and response.data:
                for coins in  response.data["data"]:
                    results.append(PriceData(

                        id = coins.get("id", "Unknown"),
                        rank = coins.get("rank", "Unknown"),
                        symbol = coins.get("symbol", "Unknown"),
                        price_usd = float(coins.get("priceUsd", 0.0)),
                        volume_24h = float(coins.get("volumeUsd24Hr", 0.0)),
                        price_change_24h = coins.get("id", "Unknown"),
                        changePercent = coins.get("changePercent24Hr", "Unknown"),
                        market_cap = float(coins.get("marketCapUsd", 0.0)),

                    ))

                return results

            else:
                print(f"Error while fetching data from {self.__class__.__name__}")
                raise Exception
                
        except Exception as e:
            print(response.data)
            print(response.status_code)
            print(f"ERROR: {e}")
            raise Exception
            
    async def get_assets_per_exhange(self, asset_name: str) -> List[Dict[str, Any]]:
        
        endpoint = f"/assets/{asset_name}/mercados"

        params = {
            "limit": 50
        }

        try:

            response = await self._make_request(endpoint, params)

            results = []
            if response.success and response.data:
                for coins in  response.data["data"]:
                    results.append({

                        "exchangeId": coins.get("exchangeId", "Unknown"),
                        "baseId": coins.get("baseId", "Unknown"),
                        "baseSymbol": coins.get("baseSymbol", "Unknown"),
                        "quoteId": coins.get("quoteId", "Unknown"),
                        "quoteSymbol": coins.get("quoteSymbol", "Unknown"),
                        "priceUsd": coins.get("priceUsd", "Unknown"),
                        "volumeUsd24Hr": coins.get("volumeUsd24Hr", "Unknown"),
                        "volumePercent": coins.get("volumePercent", "Unknown"),
                        })

                return results

            else:
                print(f"Error while fetching data from {self.__class__.__name__}")
                raise Exception
                
        except Exception as e:
            print(response.data)
            print(response.status_code)
            print(f"ERROR: {e}")
            raise Exception
    
    async def get_exchanges_data(self) -> List[Dict[str, Any]]:

        endpoint = "/exchanges"

        params = {
            "limit" : 30,
            "offset": 0

        }

        results = []

        try:
            
            response = await self._make_request(endpoint, params)

            if response.success and response.data:
                for exchange in response.data["data"]:
                    results.append({
                        'id': exchange.get('exchangeId', exchange.get('id', 'unknown')),
                        'name': exchange.get('name', 'Unknown'),
                        'volumeUsd': float(exchange.get('volumeUsd', exchange.get('volume_24h_usd', 0)) or 0),
                        'tradingPairs': int(exchange.get('tradingPairs', exchange.get('trading_pairs', 0)) or 0),
                        'socket': exchange.get('socket', False),
                        'exchangeUrl': exchange.get('exchangeUrl', exchange.get('url', '')),
                        'percentTotalVolume': float(exchange.get('percentTotalVolume', 0) or 0),
                        'updated': exchange.get('updated', ''),  
                        'rank': exchange.get('rank', 999)
                    })

                
                return sorted(results, key=lambda x: x['volumeUsd'], reverse=True)


            else:
                print(f"Error while fetching data from {self.__class__.__name__}")
                raise Exception
                

        except Exception as e:
            print(response.data)
            print(response.status_code)
            print(f"ERROR: {e}")
            raise Exception
    


async def teste_apis():
    print("TESTANDO CoinCap API")
    ("=" * 40)
    
    api_key = os.getenv("COINCAP_KEY") 

    async with CoinCapAPI(api_key) as api:

        print("Testando top exchanges...")
        exchanges = await api.get_exchanges_data()
        print(f"Encontradas {len(exchanges)} exchanges")
        for exchange in exchanges: 
            volume = exchange['volumeUsd']
            print(f"{exchange['name']}: ${volume:,.0f} volume 24h")


        print("Testando top assets...")
        assets = await api.get_assets_prices()
        print(f"Encontradas {len(assets)} assets")
        asset_names = []
        for asset in assets: 
            valuation = asset['changePercent24Hr']
            print(f"{asset['id']}: ${valuation} valuation 24h")
            asset_names.append(asset["id"])



        print("Testando exchanges for each asset...")
        for name in asset_names:
            data = await api.get_assets_per_exhange(asset_name=name)
            print(f"Encontradas {len(data)} exchanges para {len(name)} cryptos")
            for exchange in exchanges: 
                volume = exchange['volumeUsd']
                print(f"{exchange['name']}: ${volume:,.0f} volume 24h")
       
    
    
if __name__ == "__main__":
    asyncio.run(teste_apis())
