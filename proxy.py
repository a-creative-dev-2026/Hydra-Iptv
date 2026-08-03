import requests
import os
import re
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
        
        # قاموس كامل للقنوات المحلية (اسم -> قائمة روابط)
        self.local_channels = {}
        # محتوى قائمة التشغيل المحلية الخام
        self.local_playlist_content = None
        
        # تحميل الروابط المسبقة
        self._load_predefined_links()
    
    def _load_predefined_links(self):
        """تحميل الروابط المسبقة من channels.py + playlist.m3u8 المحلي"""
        print("📥 جاري تحميل الروابط المسبقة...")
        
        # 0. تحميل قائمة التشغيل المحلية (الأولوية العالية)
        self._load_local_playlist()
        
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
    
    def _load_local_playlist(self):
        """تحميل وتحليل ملف playlist.m3u8 المحلي"""
        playlist_path = os.path.join(os.path.dirname(__file__), 'playlist.m3u8')
        if not os.path.exists(playlist_path):
            print("⚠️ ملف playlist.m3u8 غير موجود")
            return
        
        try:
            with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.local_playlist_content = content
            lines = content.splitlines()
            
            current_name = None
            count = 0
            
            for line in lines:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    # استخراج اسم القناة من نهاية السطر بعد الفاصلة
                    if ',' in line:
                        current_name = line.split(',', 1)[1].strip()
                    else:
                        current_name = None
                elif line and not line.startswith('#') and current_name:
                    url = line
                    # تخزين في القاموس المحلي
                    if current_name not in self.local_channels:
                        self.local_channels[current_name] = []
                    if url not in self.local_channels[current_name]:
                        self.local_channels[current_name].append(url)
                    
                    # تخزين في الكاش أيضاً
                    links = self.cache.get(current_name) or []
                    if url not in links:
                        links.append(url)
                        self.cache.set(current_name, links)
                    
                    count += 1
                    current_name = None
            
            print(f"✅ تم تحميل {count} قناة من playlist.m3u8 المحلي ({len(self.local_channels)} اسم فريد)")
        except Exception as e:
            print(f"❌ خطأ في تحميل playlist.m3u8: {e}")
    
    def get_stream(self, channel_name):
        """الحصول على تيار البث"""
        # 1. بحث دقيق في الكاش
        cached_links = self.cache.get(channel_name)
        if cached_links:
            print(f"📦 تم العثور على {len(cached_links)} رابط في الكاش لـ {channel_name}")
            for link in cached_links:
                if self._test_link(link):
                    print(f"✅ رابط يعمل: {link[:50]}...")
                    return self._proxy_link(link)
                else:
                    print(f"❌ رابط لا يعمل: {link[:50]}...")
        
        # 2. بحث جزئي في القنوات المحلية (تجاهل حالة الأحرف)
        channel_lower = channel_name.lower().strip()
        for name, links in self.local_channels.items():
            if channel_lower in name.lower() or name.lower() in channel_lower:
                print(f"📦 تطابق جزئي: {name}")
                for link in links:
                    if self._test_link(link):
                        print(f"✅ رابط يعمل: {link[:50]}...")
                        # حفظ الاسم الدقيق في الكاش للمرات القادمة
                        self.cache.set(channel_name, links)
                        return self._proxy_link(link)
        
        # 3. البحث عن روابط جديدة باستخدام المحرك المطور
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
                        time.sleep(0.5)
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
    
    def get_local_playlist(self):
        """إرجاع محتوى قائمة التشغيل المحلية"""
        return self.local_playlist_content
    
    def search_local(self, query):
        """بحث في القنوات المحلية"""
        query_lower = query.lower().strip()
        results = {}
        for name, links in self.local_channels.items():
            if query_lower in name.lower():
                results[name] = links
        return results
