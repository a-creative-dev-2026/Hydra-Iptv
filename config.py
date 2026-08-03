import os

class Config:
    # إعدادات السيرفر
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # إعدادات البث
    TIMEOUT = 10
    CACHE_TTL = 3600  # ساعة
    MAX_RETRIES = 3
    
    # مصادر IPTV الأساسية
    SOURCES = {
        'iptv_org': 'https://iptv-org.github.io/iptv/index.m3u',
        'free_tv': 'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
        'iptv_hub': 'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u'
    }
    
    # إعدادات البروكسي
    PROXY_BUFFER_SIZE = 8192
    PROXY_TIMEOUT = 30
