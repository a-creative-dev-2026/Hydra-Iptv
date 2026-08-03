import requests
from flask import Response, stream_with_context, redirect
from cache import Cache
from searcher import ChannelSearcher
from channels import COUNTRY_CHANNELS, SPORTS_CHANNELS
import logging

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
        
        try:
            from channels import POPULAR_CHANNELS
            for channel_name, url in POPULAR_CHANNELS.items():
                links = self.cache.get(channel_name) or []
                if url not in links:
                    links.append(url)
                    self.cache.set(channel_name, links)
            logger.info(f"✅ تم تحميل {len(POPULAR_CHANNELS)} قناة مشهورة")
        except ImportError:
            logger.warning("⚠️ لا توجد قنوات مشهورة محددة")
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تحميل القنوات المشهورة: {e}")
        
        for country_code, data in COUNTRY_CHANNELS.items():
            channel_name = data['name']
            url = data['url']
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        for channel_name, url in SPORTS_CHANNELS.items():
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        logger.info(f"✅ تم تحميل {len(self.cache.cache)} قناة مسبقة في الكاش")
    
    def get_stream(self, channel_name):
        cached_links = self.cache.get(channel_name)
        if cached_links:
            logger.info(f"📦 تم العثور على {len(cached_links)} رابط في الكاش لـ {channel_name}")
            for link in cached_links:
                if self._test_link(link):
                    logger.info(f"✅ رابط يعمل: {link[:50]}...")
                    return self._proxy_link(link)
                else:
                    logger.info(f"❌ رابط لا يعمل: {link[:50]}...")
        
        logger.info(f"🔍 لم يتم العثور على {channel_name} في الكاش، جاري البحث العميق...")
        links = self.searcher.search_channel(channel_name)
        
        if links:
            logger.info(f"✅ تم العثور على {len(links)} رابط جديد!")
            self.cache.set(channel_name, links)
            return self._proxy_link(links[0])
        
        logger.error(f"❌ لم يتم العثور على روابط لـ {channel_name}")
        return None
    
    def _test_link(self, url):
        try:
            for attempt in range(2):
                try:
                    response = self.session.head(url, timeout=5, allow_redirects=True)
                    if response.status_code in [200, 206, 302, 301]:
                        return True
                except:
                    if attempt == 0:
                        import time
                        time.sleep(1)
                    continue
            return False
        except:
            return False
    
    def _proxy_link(self, url):
        try:
            return redirect(url, code=302)
        except Exception as e:
            logger.error(f"❌ خطأ في التوجيه المباشر: {e}")
        
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
    
    def add_channel(self, channel_name, url):
        links = self.cache.get(channel_name) or []
        if url not in links:
            links.append(url)
            self.cache.set(channel_name, links)
            return True
        return False
    
    def get_channels_by_country(self, country_code):
        return COUNTRY_CHANNELS.get(country_code, {}).get('name')
