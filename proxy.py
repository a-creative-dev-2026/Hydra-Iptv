import requests
from flask import Response, stream_with_context, redirect
from cache import Cache
from searcher import ChannelSearcher
from channels import COUNTRY_CHANNELS, STATIC_CHANNELS
import logging
import re
import time

logger = logging.getLogger(__name__)

class SmartProxy:
    def __init__(self):
        self.cache = Cache(ttl=3600, cache_file='cache.json')
        self.searcher = ChannelSearcher()
        self.session = requests.Session()
        self.session.stream = True
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })
        self._load_predefined_links()
    
    def _load_predefined_links(self):
        """تحميل القنوات الثابتة والمحلية"""
        logger.info("📥 جاري تحميل الروابط المسبقة...")
        
        # 1. تحميل القنوات الثابتة
        for channel_name, data in STATIC_CHANNELS.items():
            url = data['url']
            if self._test_link_deep(url):  # اختبار عميق
                links = self.cache.get(channel_name) or []
                if url not in links:
                    links.insert(0, url)
                    self.cache.set(channel_name, links)
                    logger.info(f"✅ قناة ثابتة تعمل: {channel_name}")
        
        # 2. تحميل قنوات الدول
        for country_code, data in COUNTRY_CHANNELS.items():
            channel_name = data['name']
            url = data['url']
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        logger.info(f"✅ تم تحميل {len(self.cache.cache)} قناة في الكاش")
    
    def get_stream(self, channel_name):
        """الحصول على تيار البث مع اختبار عميق"""
        logger.info(f"📺 طلب بث: {channel_name}")
        
        # 1. التحقق من القناة الثابتة أولاً
        if channel_name in STATIC_CHANNELS:
            url = STATIC_CHANNELS[channel_name]['url']
            if self._test_link_deep(url):
                logger.info(f"✅ بث قناة ثابتة: {channel_name}")
                return self._proxy_link(url)
        
        # 2. البحث في الكاش
        cached_links = self.cache.get(channel_name)
        if cached_links:
            logger.info(f"📦 تم العثور على {len(cached_links)} رابط في الكاش")
            for link in cached_links[:10]:
                if self._test_link_deep(link):
                    logger.info(f"✅ رابط يعمل: {link[:50]}...")
                    return self._proxy_link(link)
                else:
                    logger.info(f"❌ رابط لا يعمل: {link[:50]}...")
                    # إزالة الرابط التالف من الكاش
                    self.cache.remove(channel_name)
        
        # 3. البحث عن روابط جديدة
        logger.info(f"🔍 جاري البحث العميق عن {channel_name}...")
        links = self.searcher.search_channel(channel_name)
        
        if links:
            for link in links[:10]:
                if self._test_link_deep(link):
                    logger.info(f"✅ تم العثور على رابط صالح: {link[:50]}...")
                    self.cache.set(channel_name, [link])
                    return self._proxy_link(link)
        
        logger.error(f"❌ لم يتم العثور على روابط صالحة لـ {channel_name}")
        return None
    
    def _test_link_deep(self, url):
        """اختبار عميق للرابط (يتجاوز مجرد HEAD)"""
        try:
            # 1. اختبار HEAD أولاً
            try:
                head_response = self.session.head(url, timeout=5, allow_redirects=True)
                if head_response.status_code not in [200, 206, 302, 301]:
                    return False
            except:
                return False
            
            # 2. اختبار GET مع نطاق صغير (Range) لتحميل جزء من البث
            headers = {'Range': 'bytes=0-1024'}
            try:
                response = self.session.get(url, headers=headers, timeout=10, stream=True)
                if response.status_code not in [200, 206, 302, 301]:
                    return False
                
                # 3. تحميل أول 1024 بايت للتحقق من أن المحتوى صالح
                content = response.raw.read(1024)
                if not content:
                    return False
                
                # 4. التحقق من أن المحتوى ليس صفحة HTML (خطأ شائع)
                content_str = content.decode('utf-8', errors='ignore')
                if '<html' in content_str.lower() or '<body' in content_str.lower():
                    logger.warning(f"⚠️ الرابط {url[:50]}... أعاد HTML بدلاً من بث")
                    return False
                
                # 5. التحقق من وجود #EXTM3U أو #EXTINF (للملفات M3U)
                if '#EXTM3U' in content_str or '#EXTINF' in content_str:
                    return True
                
                # 6. التحقق من أن المحتوى يبدو كبث (غير فارغ)
                if len(content) > 100:  # لا يقل عن 100 بايت
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ فشل اختبار GET للرابط {url[:50]}: {e}")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ خطأ في اختبار الرابط {url[:50]}: {e}")
            return False
    
    def _proxy_link(self, url):
        """إعادة توجيه البث مع تحسين التخزين المؤقت"""
        try:
            return redirect(url, code=302)
        except Exception as e:
            logger.warning(f"⚠️ فشل التوجيه المباشر، استخدام البروكسي: {e}")
        
        try:
            response = self.session.get(url, stream=True, timeout=30)
            return Response(
                stream_with_context(response.iter_content(chunk_size=8192)),
                status=response.status_code,
                content_type=response.headers.get('content-type', 'application/vnd.apple.mpegurl'),
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=300',
                    'Content-Disposition': 'inline'
                }
            )
        except Exception as e:
            logger.error(f"❌ خطأ في البروكسي: {e}")
            return None
