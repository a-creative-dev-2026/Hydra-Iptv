import re
import time
import asyncio
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # تهيئة عميل تليجرام
        self.telegram_client = None
        self._init_telegram()
        
        # قائمة المصادر
        self.sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_world_iptv,
            self._search_iptv_hub,
            self._search_telegram_channels,
            self._search_web_engines,
            self._search_known_sites,
        ]
    
    def _init_telegram(self):
        """تهيئة عميل تليجرام"""
        try:
            if Config.TELEGRAM_API_ID and Config.TELEGRAM_API_HASH:
                self.telegram_client = TelegramClient(
                    'hydra_iptv_session',
                    Config.TELEGRAM_API_ID,
                    Config.TELEGRAM_API_HASH
                )
                logger.info("✅ تم تهيئة عميل تليجرام")
            else:
                logger.warning("⚠️ مفاتيح تليجرام غير متوفرة")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة تليجرام: {e}")
            self.telegram_client = None
    
    def search_channel(self, channel_name, country=None):
        """البحث الشامل عن قناة"""
        logger.info(f"🔍 جاري البحث الشامل عن: {channel_name}")
        all_links = []
        normalized = self._normalize_name(channel_name)
        
        # البحث في جميع المصادر بالتوازي
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(source_func, normalized): source_func.__name__
                for source_func in self.sources
            }
            for future in as_completed(futures):
                try:
                    links = future.result(timeout=20)
                    if links:
                        all_links.extend(links)
                        logger.info(f"✅ تم العثور على {len(links)} رابط من {futures[future]}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في المصدر {futures[future]}: {e}")
        
        # استخدام SerpAPI إذا توفر
        if Config.SERPAPI_KEY:
            serp_links = self._search_serpapi(normalized)
            if serp_links:
                all_links.extend(serp_links)
        
        # تنقية وفحص الروابط
        unique_links = list(set(all_links))
        valid_links = self._validate_links(unique_links)
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============== المصادر الأساسية ==============
    
    def _search_iptv_org(self, channel_name):
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
    
    def _search_free_tv(self, channel_name):
        try:
            url = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Free-TV: {e}")
        return []
    
    def _search_github(self, channel_name):
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
    
    def _search_world_iptv(self, channel_name):
        try:
            url = "https://romaxa55.github.io/world_ip_tv/output/index.m3u"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في World IPTV: {e}")
        return []
    
    def _search_iptv_hub(self, channel_name):
        try:
            url = "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في IPTV-Hub: {e}")
        return []
    
    # ============== البحث في تليجرام ==============
    
    def _search_telegram_channels(self, channel_name):
        if not self.telegram_client:
            return []
        
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            all_links = []
            
            for channel in Config.TELEGRAM_CHANNELS:
                try:
                    messages = loop.run_until_complete(
                        self._fetch_telegram_messages(channel, limit=50)
                    )
                    if messages:
                        links = self._extract_links_from_text(messages)
                        if links:
                            all_links.extend(links)
                            logger.info(f"✅ تم العثور على {len(links)} رابط من قناة {channel}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في قناة {channel}: {e}")
                    continue
            
            return all_links
        except Exception as e:
            logger.error(f"❌ خطأ في البحث في تليجرام: {e}")
            return []
    
    async def _fetch_telegram_messages(self, channel_name, limit=50):
        try:
            await self.telegram_client.start()
            entity = await self.telegram_client.get_entity(channel_name)
            history = await self.telegram_client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            return [msg.message for msg in history.messages if msg.message]
        except Exception as e:
            logger.warning(f"⚠️ خطأ في جلب رسائل {channel_name}: {e}")
            return []
    
    def _extract_links_from_text(self, messages):
        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
        all_links = []
        for text in messages:
            if text:
                links = re.findall(pattern, text, re.IGNORECASE)
                all_links.extend(links)
        return list(set(all_links))
    
    # ============== محركات البحث ==============
    
    def _search_web_engines(self, channel_name):
        try:
            links = []
            
            # DuckDuckGo
            ddg_url = f"https://html.duckduckgo.com/html/?q={channel_name.replace(' ', '+')}+m3u8"
            response = self.session.get(ddg_url, timeout=15)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                ddg_links = re.findall(pattern, response.text, re.IGNORECASE)
                links.extend(ddg_links)
            
            # Bing
            bing_url = f"https://www.bing.com/search?q={channel_name.replace(' ', '+')}+m3u8"
            response = self.session.get(bing_url, timeout=15)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                bing_links = re.findall(pattern, response.text, re.IGNORECASE)
                links.extend(bing_links)
            
            return list(set(links))
        except Exception as e:
            logger.warning(f"⚠️ خطأ في محركات البحث: {e}")
            return []
    
    # ============== مواقع معروفة ==============
    
    def _search_known_sites(self, channel_name):
        try:
            links = []
            for site in Config.KNOWN_SITES:
                try:
                    url = f"{site}/search?q={channel_name.replace(' ', '+')}"
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        found = re.findall(pattern, response.text, re.IGNORECASE)
                        if found:
                            links.extend(found)
                            logger.info(f"✅ تم العثور على {len(found)} رابط من {site}")
                except Exception as e:
                    continue
            return list(set(links))
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في المواقع: {e}")
            return []
    
    # ============== SerpAPI (اختياري) ==============
    
    def _search_serpapi(self, channel_name):
        if not Config.SERPAPI_KEY:
            return []
        try:
            params = {
                "q": f"{channel_name} m3u8 live stream",
                "api_key": Config.SERPAPI_KEY,
                "engine": "google"
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                links = []
                for result in data.get("organic_results", []):
                    link = result.get("link", "")
                    if "m3u8" in link or "m3u" in link:
                        links.append(link)
                return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في SerpAPI: {e}")
        return []
    
    # ============== دوال مساعدة ==============
    
    def _normalize_name(self, name):
        name = re.sub(r'[^\w\s]', '', name)
        name = name.lower()
        for word in ['hd', 'tv', 'channel', 'live', 'stream', 'sd', '4k', 'fhd', 'uhd']:
            name = name.replace(word, '')
        name = ' '.join(name.split())
        return name
    
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
