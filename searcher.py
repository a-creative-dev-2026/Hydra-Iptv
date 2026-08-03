import requests
import re
from concurrent.futures import ThreadPoolExecutor

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_channel(self, channel_name):
        """البحث عن قناة في مصادر متعددة"""
        print(f"🔍 جاري البحث عن: {channel_name}")
        
        # 1. البحث في iptv-org (أكبر مصدر مفتوح)
        links = self._search_iptv_org(channel_name)
        
        # 2. البحث في Free-TV
        if not links:
            links = self._search_free_tv(channel_name)
        
        # 3. البحث المباشر في GitHub
        if not links:
            links = self._search_github(channel_name)
        
        # التحقق من الروابط
        valid_links = self._validate_links(links)
        
        return valid_links
    
    def _search_iptv_org(self, channel_name):
        """البحث في iptv-org"""
        try:
            # جلب القائمة الكاملة
            url = "https://iptv-org.github.io/iptv/index.m3u"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                # البحث عن القناة في النص
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except Exception as e:
            print(f"⚠️ خطأ في iptv-org: {e}")
        
        return []
    
    def _search_free_tv(self, channel_name):
        """البحث في Free-TV"""
        try:
            url = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except Exception as e:
            print(f"⚠️ خطأ في Free-TV: {e}")
        
        return []
    
    def _search_github(self, channel_name):
        """البحث في مستودعات GitHub"""
        try:
            # البحث في iptv-org channels
            url = f"https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except Exception as e:
            print(f"⚠️ خطأ في GitHub: {e}")
        
        return []
    
    def _validate_links(self, links):
        """اختبار صحة الروابط"""
        valid = []
        
        for link in links[:5]:  # حد أقصى 5 روابط
            try:
                response = self.session.head(link, timeout=5, allow_redirects=True)
                if response.status_code in [200, 206, 302, 301]:
                    valid.append(link)
                    print(f"✅ رابط صالح: {link[:50]}...")
            except Exception as e:
                print(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:50]}")
                continue
        
        return valid
