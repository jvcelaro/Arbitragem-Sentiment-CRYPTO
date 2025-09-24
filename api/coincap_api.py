from base_api import BaseCryptoAPI, PriceData, APIResponse, ExchangeData
from typing import Optional, Dict, List, Any
import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

class CoinCapAPI(BaseCryptoAPI):
    def __init__(self, api_key: str):
        super().__init__(base_url=os.getenv("COINCAP_BASE_URL"), api_key=api_key, rate_limit=int(os.getenv("COINCAP_RATE_LIMIT")))

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
                        market_capusd = coins.get("marketCapUsd", "Unknown"),
                        volume_24h = float(coins.get("volumeUsd24Hr", 0.0)),
                        price = coins.get("priceUsd", "Unknown"),
                        changePercent = coins.get("changePercent24Hr", "Unknown"),
                        vwap24Hr = float(coins.get("vwap24Hr", 0.0)),

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
        
        endpoint = f"/assets/{asset_name}/markets"

        params = {
            "limit": 10
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
    
    async def get_exchanges_data(self) -> List[ExchangeData]:

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
                    results.append(ExchangeData(
                            id = exchange.get("exchangeId"),
                            name = exchange.get("name"),
                            volume_24h_usd = exchange.get("volumeUsd"),
                            trading_pairs = exchange.get("tradingPairs"),
                            market_share_percentage = exchange.get("percentTotalVolume"),
                            last_updated = exchange.get("updated"),
                            timestamp = str(time.time()),
                            data_source =  "coincap"

                    ))

                
                return sorted(results, key=lambda x: x.volume_24h_usd, reverse=True)


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

        # print("Testando top exchanges...")
        # exchanges = await api.get_exchanges_data()
        # print(f"Encontradas {len(exchanges)} exchanges")
        # for exchange in exchanges: 
        #     volume = exchange.volume_24h_usd
        #     print(f"{exchange.name}: ${volume} volume 24h")


        print("Testando top assets...")
        assets = await api.get_assets_prices()
        print(f"Encontradas {len(assets)} assets")
        asset_names = []
        for asset in assets: 
            valuation = asset.changePercent
            print(f"{asset.id}: ${valuation} valuation 24h")
            asset_names.append(asset.id)
        


        print("Testando exchanges for each asset...")
        for name in asset_names:
            data = await api.get_assets_per_exhange(asset_name=name)
            print(f"Encontradas {len(data)} exchanges para {len(name)} cryptos")
            for exchange in data: 
                volume = exchange['priceUsd']
                print(f"Exchange: {exchange['exchangeId']}: ${volume} for {exchange['baseSymbol']}")
       
    
    
if __name__ == "__main__":
    asyncio.run(teste_apis())
