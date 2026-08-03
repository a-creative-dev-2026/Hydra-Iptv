import os

class Config:
    # إعدادات السيرفر الأساسية
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 10000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # إعدادات البث
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
    
    # ============================================================
    # إعدادات البحث المتقدم (جديدة)
    # ============================================================
    
    # مفاتيح تليجرام (سجل في my.telegram.org)
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID', '')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')
    
    # قنوات تليجرام للمتابعة
    TELEGRAM_CHANNELS = [
        'IPTV442WEB',
        'iptv_links',
        'm3u8_files',
        'beIN_Sports_links',
        'live_tv_channels',
        # أضف المزيد حسب الحاجة
    ]
    
    # إعدادات محركات البحث
    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search?q={query}+m3u8+live',
        'bing': 'https://www.bing.com/search?q={query}+m3u8+stream',
        'duckduckgo': 'https://html.duckduckgo.com/html/?q={query}+m3u8',
    }
    
    # SerpAPI (اختياري - سجل في serpapi.com)
    SERPAPI_KEY = os.getenv('SERPAPI_KEY', '')
    
    # مواقع معروفة للبحث
    KNOWN_SITES = [
        'https://iptv-org.github.io',
        'https://raw.githubusercontent.com',
        'https://pastebin.com',
        'https://telegra.ph',
        'https://t.me',
        'https://github.com',
    ]
