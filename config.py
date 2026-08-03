import os

class Config:
    # إعدادات السيرفر الأساسية
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # إعدادات البث والكاش
    TIMEOUT = int(os.getenv('TIMEOUT', 10))
    CACHE_TTL = int(os.getenv('CACHE_TTL', 7200))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # إعدادات البروكسي
    PROXY_BUFFER_SIZE = 8192
    PROXY_TIMEOUT = int(os.getenv('PROXY_TIMEOUT', 30))
    
    # إعدادات البحث
    SEARCH_TIMEOUT = int(os.getenv('SEARCH_TIMEOUT', 15))
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
    
    # ملف الكاش
    CACHE_FILE = os.getenv('CACHE_FILE', 'cache.json')
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 10))
    RATE_LIMIT_PER_DAY = int(os.getenv('RATE_LIMIT_PER_DAY', 200))
    
    # ❌ تم إزالة إعدادات تليجرام (غير مفعلة حالياً)
    # إذا أردت تفعيلها لاحقاً، أضفها مع تثبيت Telethon
