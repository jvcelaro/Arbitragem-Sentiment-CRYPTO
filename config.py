import os

class Config:
    # APIs
    COINCAP_BASE_URL = "https://rest.coincap.io/v3"
    NEWS_API_URL = "https://newsapi.org/v2"    
    # Rate limits
    COINCAP_RATE_LIMIT = 1000
    NEWS_RATE_LIMIT = 1000
    
    # Arbitragem
    MIN_SPREAD_PERCENTAGE = 0.1
    MIN_VOLUME_THRESHOLD = 100000
    TARGET_SYMBOLS = ['bitcoin', 'ethereum', 'cardano']
    
    # Cache
    CACHE_TTL_EXCHANGES = 120  # 2 minutos
    CACHE_TTL_PRICES = 60      # 1 minuto
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"