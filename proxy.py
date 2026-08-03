import requests
from flask import Response, stream_with_context, redirect
from cache import Cache
from searcher import ChannelSearcher
from channels import COUNTRY_CHANNELS  # ✅ استيراد الدول فقط
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
        logger.info("📥 جاري تحميل الروابط المسبقة...")
        
        # ✅ تحميل قنوات الدول فقط
        for country_code, data in COUNTRY_CHANNELS.items():
            channel_name = data['name']
            url = data['url']
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        logger.info(f"✅ تم تحميل {len(self.cache.cache)} قناة في الكاش")
    
    def get_stream(self, channel_name):
        logger.info(f"📺 طلب بث: {channel_name}")
        
        # ✅ البحث في الكاش فقط
        cached_links = self.cache.get(channel_name)
        if cached_links:
            logger.info(f"📦 تم العثور على {len(cached_links)} رابط في الكاش")
            for link in cached_links[:5]:
                if self._test_link(link):
                    logger.info(f"✅ رابط يعمل: {link[:50]}...")
                    return self._proxy_link(link)
                else:
                    logger.info(f"❌ رابط لا يعمل: {link[:50]}...")
        
        # ✅ البحث عن روابط جديدة
        logger.info(f"🔍 جاري البحث عن {channel_name}...")
        links = self.searcher.search_channel(channel_name)
        
        if links:
            for link in links[:5]:
                if self._test_link(link):
                    logger.info(f"✅ تم العثور على رابط صالح: {link[:50]}...")
                    self.cache.set(channel_name, [link])
                    return self._proxy_link(link)
        
        logger.error(f"❌ لم يتم العثور على روابط لـ {channel_name}")
        return None
    
    def _test_link(self, url):
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code in [200, 206, 302, 301]
        except:
            return False
    
    def _proxy_link(self, url):
        try:
            return redirect(url, code=302)
        except Exception as e:
            logger.warning(f"⚠️ فشل التوجيه المباشر: {e}")
        
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
