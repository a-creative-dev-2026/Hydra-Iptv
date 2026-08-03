import time
import logging
from cache import Cache
import requests

logger = logging.getLogger(__name__)

# ✅ محاولة استيراد APScheduler، إذا لم يكن موجوداً نعطي رسالة
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    BackgroundScheduler = None
    IntervalTrigger = None

class LinkValidator:
    def __init__(self):
        self.cache = Cache(ttl=3600, cache_file='cache.json')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        })
    
    def validate_all_links(self):
        logger.info("🔄 بدء التحقق الدوري من الروابط...")
        cache_data = self.cache.get_all()
        removed_count = 0
        
        for channel_name, entry in cache_data.items():
            links = entry.get('data', [])
            if not links:
                continue
            
            valid_links = []
            for link in links:
                if self._test_link(link):
                    valid_links.append(link)
                else:
                    logger.info(f"❌ رابط تالف تمت إزالته: {link[:50]}...")
                    removed_count += 1
            
            if valid_links:
                self.cache.set(channel_name, valid_links)
            else:
                self.cache.remove(channel_name)
                logger.info(f"🗑️ تمت إزالة القناة {channel_name} (جميع روابطها تالفة)")
        
        logger.info(f"✅ تم الانتهاء من التحقق. تمت إزالة {removed_count} رابط تالف.")
    
    def _test_link(self, url):
        try:
            headers = {'Range': 'bytes=0-1024'}
            response = self.session.get(url, headers=headers, timeout=10, stream=True)
            if response.status_code not in [200, 206, 302, 301]:
                return False
            content = response.raw.read(1024)
            if b'<html' in content or b'<body' in content:
                return False
            return True
        except:
            return False

def start_scheduler():
    """بدء تشغيل المجدول (إذا كانت المكتبة متوفرة)"""
    if not APSCHEDULER_AVAILABLE:
        logger.warning("⚠️ APScheduler غير مثبت، لن يتم تشغيل المجدول الدوري")
        return None
    
    validator = LinkValidator()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        validator.validate_all_links,
        trigger=IntervalTrigger(hours=6),
        id='validate_links',
        replace_existing=True
    )
    scheduler.start()
    logger.info("⏰ تم بدء تشغيل المجدول (التحقق كل 6 ساعات)")
    
    # تنفيذ المهمة فوراً عند بدء التشغيل (في الخلفية)
    import threading
    threading.Thread(target=validator.validate_all_links, daemon=True).start()
    
    return scheduler
