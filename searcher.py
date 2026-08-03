import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from config import Config
import logging

logger = logging.getLogger(__name__)
ua = UserAgent()

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })
    
    def search_channel(self, channel_name, country=None):
        """البحث عن قناة في مصادر متعددة"""
        logger.info(f"🔍 جاري البحث عن: {channel_name}")
        all_links = []
        keywords = self._extract_keywords(channel_name)
        
        # 1. البحث في مصادر iptv-org
        links = self._search_iptv_org(keywords)
        if links:
            all_links.extend(links)
            logger.info(f"✅ تم العثور على {len(links)} رابط من iptv-org")
        
        # 2. البحث في GitHub
        links = self._search_github(keywords)
        if links:
            all_links.extend(links)
            logger.info(f"✅ تم العثور على {len(links)} رابط من GitHub")
        
        # 3. البحث في World IPTV
        links = self._search_world_iptv(keywords)
        if links:
            all_links.extend(links)
            logger.info(f"✅ تم العثور على {len(links)} رابط من World IPTV")
        
        # 4. البحث الواسع في محركات البحث (إذا لم نجد نتائج)
        if not all_links:
            logger.info("🔄 جاري البحث الواسع...")
            links = self._deep_search(keywords)
            if links:
                all_links.extend(links)
                logger.info(f"✅ تم العثور على {len(links)} رابط من البحث الواسع")
        
        # 5. إزالة التكرار
        unique_links = list(set(all_links))
        return unique_links[:15]  # حد أقصى 15 رابطاً
    
    def _search_iptv_org(self, keywords):
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    for keyword in keywords[:3]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    def _search_github(self, keywords):
        try:
            urls = [
                "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
                "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    for keyword in keywords[:3]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في GitHub: {e}")
            return []
    
    def _search_world_iptv(self, keywords):
        try:
            url = "https://romaxa55.github.io/world_ip_tv/output/index.m3u"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                links = []
                for keyword in keywords[:3]:
                    pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
                return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في World IPTV: {e}")
            return []
    
    def _deep_search(self, keywords):
        """بحث واسع في محركات البحث"""
        try:
            links = []
            primary = keywords[0] if keywords else "tv"
            search_urls = [
                f"https://www.google.com/search?q={primary}+m3u8+stream",
                f"https://www.bing.com/search?q={primary}+m3u8",
                f"https://html.duckduckgo.com/html/?q={primary}+m3u8",
            ]
            for url in search_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        found = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(found)
                except:
                    continue
            return list(set(links))
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الواسع: {e}")
            return []
    
    def _extract_keywords(self, channel_name):
        keywords = []
        original = channel_name.lower().strip()
        keywords.append(original)
        base_name = re.sub(r'[^a-zA-Z\s]', '', original).strip()
        if base_name:
            keywords.append(base_name)
        for word in original.split():
            if len(word) > 2:
                keywords.append(word)
        return list(set(keywords))
