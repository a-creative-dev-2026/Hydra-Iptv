import requests
import re
from concurrent.futures import ThreadPoolExecutor
import time

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_channel(self, channel_name):
        """البحث عن قناة"""
        print(f"🔍 جاري البحث عن: {channel_name}")
        
        # 1. البحث في المصادر المفتوحة
        links = self._search_open_sources(channel_name)
        
        # 2. البحث في المصادر الإضافية
        if not links:
            links = self._search_extra_sources(channel_name)
        
        # 3. التحقق من الروابط
        valid_links = self._validate_links(links)
        
        return valid_links
    
    def _search_open_sources(self, channel_name):
        """بحث في المصادر المفتوحة"""
        sources = [
            "https://iptv-org.github.io/iptv/playlist.m3u",
            "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
        ]
        
        links = []
        for source in sources:
            try:
                response = self.session.get(source, timeout=10)
                if response.status_code == 200:
                    # البحث عن القناة في النص
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            except:
                continue
        
        return links
    
    def _search_extra_sources(self, channel_name):
        """بحث في مصادر إضافية"""
        try:
            # استخدام GitHub search
            url = f"https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                return matches
        except:
            pass
        
        return []
    
    def _validate_links(self, links):
        """اختبار صحة الروابط"""
        valid = []
        
        for link in links[:10]:  # حد أقصى 10 روابط
            try:
                response = self.session.head(link, timeout=3)
                if response.status_code in [200, 206, 302, 301]:
                    valid.append(link)
            except:
                continue
        
        return valid
