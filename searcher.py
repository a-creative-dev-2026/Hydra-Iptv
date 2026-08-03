import requests
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })
        self.proxies = [None]
    
    def search_channel(self, channel_name, country=None):
        logger.info(f"🔍 جاري البحث عن: {channel_name}")
        all_links = []
        normalized = self._normalize_name(channel_name)
        
        sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_open_load,
        ]
        
        for idx, source_func in enumerate(sources):
            proxy = self.proxies[idx % len(self.proxies)]
            links = source_func(normalized, proxy)
            if links:
                all_links.extend(links)
                logger.info(f"✅ تم العثور على {len(links)} رابط من المصدر {idx+1}")
        
        if not all_links:
            logger.info("🔄 جاري البحث المباشر في المواقع...")
            all_links = self._search_web_alternative(normalized)
        
        if not all_links:
            logger.info("🔍 جاري البحث العميق...")
            all_links = self._deep_search(normalized)
        
        unique_links = list(set(all_links))
        valid_links = self._validate_links(unique_links)
        return valid_links
    
    def _normalize_name(self, name):
        name = re.sub(r'[^\w\s]', '', name)
        name = name.lower()
        for word in ['hd', 'tv', 'channel', 'live', 'stream', 'sd', '4k', 'fhd', 'uhd']:
            name = name.replace(word, '')
        name = ' '.join(name.split())
        return name
    
    def _search_iptv_org(self, channel_name, proxy=None):
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    def _search_free_tv(self, channel_name, proxy=None):
        try:
            url = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Free-TV: {e}")
        return []
    
    def _search_github(self, channel_name, proxy=None):
        try:
            urls = [
                "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
                "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في GitHub: {e}")
        return []
    
    def _search_open_load(self, channel_name, proxy=None):
        try:
            url = "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في OpenLoad: {e}")
        return []
    
    def _search_web_alternative(self, channel_name):
        try:
            url = f"https://html.duckduckgo.com/html/?q={channel_name.replace(' ', '+')}+m3u8+live"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في DuckDuckGo: {e}")
        
        try:
            url = f"https://www.bing.com/search?q={channel_name.replace(' ', '+')}+m3u8"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Bing: {e}")
        return []
    
    def _deep_search(self, channel_name):
        try:
            urls = [
                "https://iptv-org.github.io/iptv/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
            ]
            all_links = []
            for url in urls:
                try:
                    response = self.session.get(url, timeout=20)
                    if response.status_code == 200:
                        pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        all_links.extend(matches)
                except:
                    continue
            return all_links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث العميق: {e}")
        return []
    
    def _validate_links(self, links):
        valid = []
        for link in links[:10]:
            try:
                for attempt in range(2):
                    try:
                        response = self.session.head(link, timeout=5, allow_redirects=True)
                        if response.status_code in [200, 206, 302, 301]:
                            valid.append(link)
                            logger.info(f"✅ رابط صالح: {link[:50]}...")
                            break
                    except:
                        if attempt == 0:
                            time.sleep(1)
                        continue
            except Exception as e:
                logger.warning(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:50]}")
                continue
        return valid
