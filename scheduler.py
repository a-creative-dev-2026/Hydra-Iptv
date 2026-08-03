from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time
import logging
from cache import Cache
from proxy import SmartProxy
import requests

logger = logging.getLogger(__name__)

class LinkValidator:
    def __init__(self):
        self.cache = Cache(ttl=3600, cache_file='cache.json')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        })
    
    def validate_all_links(self):
        """التحقق من جميع الروابط في الكاش وإزالة التالفة"""
        logger.info("🔄 بدء التحقق الدوري من الروابط...")
        
        # الحصول على نسخة من الكاش
        cache_data = self.cache.get_all()
        removed_count = 0
        
        for channel_name, entry in cache_data.items():
            links = entry.get('data', [])
            if not links:
                continue
            
            # اختبار الروابط
            valid_links = []
            for link in links:
                if self._test_link(link):
                    valid_links.append(link)
                else:
                    logger.info(f"❌ رابط تالف تمت إزالته: {link[:50]}...")
                    removed_count += 1
            
            # تحديث الكاش بالروابط الصالحة فقط
            if valid_links:
                self.cache.set(channel_name, valid_links)
            else:
                self.cache.remove(channel_name)
                logger.info(f"🗑️ تمت إزالة القناة {channel_name} (جميع روابطها تالفة)")
        
        logger.info(f"✅ تم الانتهاء من التحقق. تمت إزالة {removed_count} رابط تالف.")
    
    def _test_link(self, url):
        """اختبار الرابط (تحميل أول 1024 بايت)"""
        try:
            headers = {'Range': 'bytes=0-1024'}
            response = self.session.get(url, headers=headers, timeout=10, stream=True)
            
            if response.status_code not in [200, 206, 302, 301]:
                return False
            
            # التحقق من المحتوى (ليس HTML)
            content = response.raw.read(1024)
            if b'<html' in content or b'<body' in content:
                return False
            
            return True
        except:
            return False

def start_scheduler():
    """بدء تشغيل المجدول"""
    validator = LinkValidator()
    
    # إنشاء المجدول
    scheduler = BackgroundScheduler()
    
    # إضافة مهمة دورية (كل 6 ساعات)
    scheduler.add_job(
        validator.validate_all_links,
        trigger=IntervalTrigger(hours=6),
        id='validate_links',
        replace_existing=True
    )
    
    # تشغيل المجدول في الخلفية
    scheduler.start()
    logger.info("⏰ تم بدء تشغيل المجدول (التحقق كل 6 ساعات)")
    
    # تنفيذ المهمة فوراً عند بدء التشغيل
    validator.validate_all_links()
    
    return scheduler
