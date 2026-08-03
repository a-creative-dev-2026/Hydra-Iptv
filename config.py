import os

class Config:
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 10000))  # القيمة الافتراضية 10000
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    TIMEOUT = int(os.getenv('TIMEOUT', 10))
    CACHE_TTL = int(os.getenv('CACHE_TTL', 7200))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    PROXY_BUFFER_SIZE = 8192
    PROXY_TIMEOUT = int(os.getenv('PROXY_TIMEOUT', 30))
    
    SEARCH_TIMEOUT = int(os.getenv('SEARCH_TIMEOUT', 15))
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
    
    CACHE_FILE = os.getenv('CACHE_FILE', 'cache.json')
    
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 10))
    RATE_LIMIT_PER_DAY = int(os.getenv('RATE_LIMIT_PER_DAY', 200))
