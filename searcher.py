import requests
import re
from concurrent.futures import ThreadPoolExecutor
import time
import random

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        
        # قائمة بروكسيات (اختياري - يمكنك إضافة المزيد)
        self.proxies = [
            None,  # بدون بروكسي
            # 'http://proxy1:8080',
            # 'http://proxy2:8080',
        ]
    
    def search_channel(self, channel_name, country=None):
        """البحث عن قناة مع تجاوز الحجب الجغرافي"""
        print(f"🔍 جاري البحث عن: {channel_name}")
        
        all_links = []
        
        # 1. البحث في المصادر الرئيسية (مع بروكسي)
        sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_open_load,
            self._search_web,
        ]
        
        # استخدام بروكسي مختلف لكل مصدر
        for idx, source_func in enumerate(sources):
            proxy = self.proxies[idx % len(self.proxies)]
            links = source_func(channel_name, proxy)
            if links:
                all_links.extend(links)
                print(f"✅ تم العثور على {len(links)} رابط من المصدر {idx+1}")
        
        # 2. البحث المباشر في المواقع (لتجاوز الحجب)
        if not all_links:
            print("🔄 جاري البحث المباشر في المواقع...")
            all_links = self._deep_search(channel_name)
        
        # 3. إزالة التكرار
        unique_links = list(set(all_links))
        
        # 4. التحقق من صحة الروابط (مع إعادة المحاولة)
        valid_links = self._validate_links(unique_links)
        
        return valid_links
    
    def _search_iptv_org(self, channel_name, proxy=None):
        """البحث في iptv-org مع تجاوز الحجب"""
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            
            for url in urls:
                response = self.session.get(url, timeout=15, proxies={'http': proxy, 'https': proxy} if proxy else None)
                if response.status_code == 200:
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            
            return links
        except Exception as e:
            print(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    def _search_free_tv(self, channel_name, proxy=None):
        """البحث في Free-TV"""
        try:
            url = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
            response = self.session.get(url, timeout=15, proxies={'http': proxy, 'https': proxy} if proxy else None)
            
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except Exception as e:
            print(f"⚠️ خطأ في Free-TV: {e}")
        
        return []
    
    def _search_github(self, channel_name, proxy=None):
        """البحث في مستودعات GitHub"""
        try:
            # محاولة جلب من مصادر متعددة
            urls = [
                "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
            ]
            links = []
            
            for url in urls:
                response = self.session.get(url, timeout=15, proxies={'http': proxy, 'https': proxy} if proxy else None)
                if response.status_code == 200:
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            
            return links
        except Exception as e:
            print(f"⚠️ خطأ في GitHub: {e}")
        
        return []
    
    def _search_open_load(self, channel_name, proxy=None):
        """البحث في OpenLoad"""
        try:
            url = f"https://openload.co/search/{channel_name.replace(' ', '+')}"
            response = self.session.get(url, timeout=15, proxies={'http': proxy, 'https': proxy} if proxy else None)
            
            if response.status_code == 200:
                # البحث عن روابط M3U8
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except Exception as e:
            print(f"⚠️ خطأ في OpenLoad: {e}")
        
        return []
    
    def _search_web(self, channel_name, proxy=None):
        """البحث في الويب باستخدام محركات بحث"""
        try:
            # محاولة استخدام محركات بحث مختلفة
            search_urls = [
                f"https://www.google.com/search?q={channel_name.replace(' ', '+')}+m3u8+live+stream",
                f"https://www.bing.com/search?q={channel_name.replace(' ', '+')}+iptv+link",
                f"https://duckduckgo.com/html/?q={channel_name.replace(' ', '+')}+m3u8",
            ]
            links = []
            
            for search_url in search_urls:
                response = self.session.get(search_url, timeout=15, proxies={'http': proxy, 'https': proxy} if proxy else None)
                if response.status_code == 200:
                    # البحث عن روابط M3U8 في النتائج
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            
            return links
        except Exception as e:
            print(f"⚠️ خطأ في البحث في الويب: {e}")
        
        return []
    
    def _deep_search(self, channel_name):
        """بحث عميق في مصادر متعددة"""
        try:
            # استخدام خدمات البحث المتخصصة
            search_queries = [
                f"{channel_name} live streaming m3u8",
                f"{channel_name} iptv link",
                f"{channel_name} channel stream",
            ]
            
            all_links = []
            
            for query in search_queries:
                # محاولة استخدام مصادر مختلفة
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 200:
                    # استخراج الروابط
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    all_links.extend(matches)
            
            return all_links
        except Exception as e:
            print(f"⚠️ خطأ في البحث العميق: {e}")
        
        return []
    
    def _validate_links(self, links):
        """اختبار صحة الروابط مع إعادة المحاولة"""
        valid = []
        
        for link in links[:10]:  # حد أقصى 10 روابط
            try:
                # محاولة الاتصال مرتين إذا فشلت الأولى
                for attempt in range(2):
                    try:
                        response = self.session.head(link, timeout=5, allow_redirects=True)
                        if response.status_code in [200, 206, 302, 301]:
                            valid.append(link)
                            print(f"✅ رابط صالح: {link[:50]}...")
                            break
                    except:
                        if attempt == 0:
                            time.sleep(1)  # انتظر قبل إعادة المحاولة
                        continue
            except Exception as e:
                print(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:50]}")
                continue
        
        return valid
