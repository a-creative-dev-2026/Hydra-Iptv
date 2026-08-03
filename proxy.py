import requests
from flask import Response, stream_with_context
from cache import Cache
from searcher import ChannelSearcher
from channels import COUNTRY_CHANNELS, SPORTS_CHANNELS

class SmartProxy:
    def __init__(self):
        self.cache = Cache(ttl=3600)
        self.searcher = ChannelSearcher()
        self.session = requests.Session()
        self.session.stream = True
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })
        
        # تحميل الروابط المسبقة
        self._load_predefined_links()
    
    def _load_predefined_links(self):
        """تحميل الروابط المسبقة من channels.py"""
        print("📥 جاري تحميل الروابط المسبقة...")
        
        # 1. تحميل القنوات المشهورة (إذا كانت موجودة في channels.py)
        try:
            from channels import POPULAR_CHANNELS
            for channel_name, url in POPULAR_CHANNELS.items():
                links = self.cache.get(channel_name) or []
                if url not in links:
                    links.append(url)
                    self.cache.set(channel_name, links)
            print(f"✅ تم تحميل {len(POPULAR_CHANNELS)} قناة مشهورة")
        except ImportError:
            print("⚠️ لا توجد قنوات مشهورة محددة في channels.py")
        except Exception as e:
            print(f"⚠️ خطأ في تحميل القنوات المشهورة: {e}")
        
        # 2. تحميل قنوات الدول
        for country_code, data in COUNTRY_CHANNELS.items():
            channel_name = data['name']
            url = data['url']
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        # 3. تحميل القنوات الرياضية
        for channel_name, url in SPORTS_CHANNELS.items():
            links = self.cache.get(channel_name) or []
            if url not in links:
                links.append(url)
                self.cache.set(channel_name, links)
        
        print(f"✅ تم تحميل {len(self.cache.cache)} قناة مسبقة في الكاش")
    
    def get_stream(self, channel_name):
        """الحصول على تيار البث"""
        # 1. البحث في الكاش
        cached_links = self.cache.get(channel_name)
        if cached_links:
            print(f"📦 تم العثور على {len(cached_links)} رابط في الكاش لـ {channel_name}")
            for link in cached_links:
                if self._test_link(link):
                    print(f"✅ رابط يعمل: {link[:50]}...")
                    return self._proxy_link(link)
                else:
                    print(f"❌ رابط لا يعمل: {link[:50]}...")
        
        # 2. البحث عن روابط جديدة باستخدام المحرك المطور
        print(f"🔍 لم يتم العثور على {channel_name} في الكاش، جاري البحث العميق...")
        links = self.searcher.search_channel(channel_name)
        
        if links:
            print(f"✅ تم العثور على {len(links)} رابط جديد!")
            self.cache.set(channel_name, links)
            return self._proxy_link(links[0])
        
        print(f"❌ لم يتم العثور على روابط لـ {channel_name}")
        return None
    
    def _test_link(self, url):
        """اختبار الرابط مع إعادة المحاولة"""
        try:
            # محاولة مرتين
            for attempt in range(2):
                try:
                    response = self.session.head(url, timeout=5, allow_redirects=True)
                    if response.status_code in [200, 206, 302, 301]:
                        return True
                except:
                    if attempt == 0:
                        import time
                        time.sleep(1)  # انتظر ثانية قبل إعادة المحاولة
                    continue
            return False
        except:
            return False
    
    def _proxy_link(self, url):
        """إعادة توجيه البث"""
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
            print(f"❌ خطأ في البروكسي: {e}")
            return None
    
    def add_channel(self, channel_name, url):
        """إضافة قناة يدوياً"""
        links = self.cache.get(channel_name) or []
        if url not in links:
            links.append(url)
            self.cache.set(channel_name, links)
            return True
        return False
    
    def get_channels_by_country(self, country_code):
        """الحصول على قنوات دولة معينة"""
        return COUNTRY_CHANNELS.get(country_code, {}).get('name')
