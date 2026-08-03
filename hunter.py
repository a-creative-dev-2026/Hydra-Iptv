import asyncio
import aiohttp
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class LinkHunter:
    """صياد الروابط - محرك بحث متقدم يجلب روابط البث من كل مكان"""
    
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        }
        
        # قنوات تليجرام للبحث (مصادر إضافية)
        self.telegram_sources = [
            'iptv_links',
            'm3u8_files',
            'beIN_Sports_links',
            'live_tv_channels',
            'IPTV442WEB',
            'iptv_m3u'
        ]
        
        # مواقع معروفة للبحث عن روابط IPTV
        self.known_sites = [
            'https://iptv-org.github.io',
            'https://raw.githubusercontent.com',
            'https://pastebin.com',
            'https://telegra.ph',
            'https://t.me',
            'https://github.com',
            'https://www.reddit.com/r/IPTV',
            'https://www.reddit.com/r/m3u8',
        ]
    
    async def hunt(self, channel_name, max_results=15):
        """الصيد الرئيسي - بحث عن روابط القناة"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        all_links = []
        
        # 1. البحث في المصادر الرئيسية
        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            self.session = session
            
            # تنفيذ المهام بالتوازي
            tasks = [
                self._search_iptv_org(channel_name),
                self._search_github(channel_name),
                self._search_world_iptv(channel_name),
                self._search_web(channel_name),
                self._search_telegram(channel_name),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ خطأ في أحد المصادر: {result}")
        
        # 2. تنقية النتائج
        unique_links = self._deduplicate_links(all_links)
        
        # 3. ترتيب حسب الجودة
        ranked_links = self._rank_links(unique_links, channel_name)
        
        # 4. اختبار سريع للروابط (أول 10 فقط)
        valid_links = await self._quick_validate(ranked_links[:10])
        
        # 5. إذا لم نجد نتائج، استخدم Fuzzy Search
        if not valid_links:
            logger.info("🔄 لم يتم العثور على روابط، جاري البحث الضبابي...")
            fuzzy_links = await self._fuzzy_search(channel_name)
            if fuzzy_links:
                valid_links = await self._quick_validate(fuzzy_links[:10])
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============================================================
    # 1. المصادر الأساسية
    # ============================================================
    
    async def _search_iptv_org(self, channel_name):
        """البحث في iptv-org"""
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    async def _search_github(self, channel_name):
        """البحث في مستودعات GitHub"""
        try:
            urls = [
                "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
                "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            ]
            links = []
            for url in urls:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في GitHub: {e}")
            return []
    
    async def _search_world_iptv(self, channel_name):
        """البحث في World IPTV"""
        try:
            url = "https://romaxa55.github.io/world_ip_tv/output/index.m3u"
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    return re.findall(pattern, content, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في World IPTV: {e}")
            return []
    
    # ============================================================
    # 2. البحث في الويب (Google, DuckDuckGo, Bing)
    # ============================================================
    
    async def _search_web(self, channel_name):
        """البحث في محركات البحث"""
        try:
            # استخدام googlesearch-python (متزامن، لكننا نستخدم ThreadPool)
            with ThreadPoolExecutor(max_workers=3) as executor:
                loop = asyncio.get_event_loop()
                search_tasks = [
                    loop.run_in_executor(executor, self._search_google, channel_name),
                    loop.run_in_executor(executor, self._search_duckduckgo, channel_name),
                    loop.run_in_executor(executor, self._search_bing, channel_name),
                ]
                results = await asyncio.gather(*search_tasks)
                all_links = []
                for result in results:
                    if result:
                        all_links.extend(result)
                return all_links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في الويب: {e}")
            return []
    
    def _search_google(self, channel_name):
        """البحث في Google باستخدام googlesearch"""
        try:
            from googlesearch import search
            query = f"{channel_name} m3u8 live stream"
            links = []
            for url in search(query, num_results=5):
                if '.m3u8' in url or '.m3u' in url:
                    links.append(url)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Google: {e}")
            return []
    
    def _search_duckduckgo(self, channel_name):
        """البحث في DuckDuckGo"""
        try:
            import requests
            query = f"{channel_name} m3u8 live"
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في DuckDuckGo: {e}")
        return []
    
    def _search_bing(self, channel_name):
        """البحث في Bing"""
        try:
            import requests
            query = f"{channel_name} m3u8"
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Bing: {e}")
        return []
    
    # ============================================================
    # 3. البحث في تليجرام (محاكاة)
    # ============================================================
    
    async def _search_telegram(self, channel_name):
        """البحث في قنوات تليجرام (محاكاة باستخدام t.me)"""
        try:
            # محاولة جلب من t.me (الواجهة العامة)
            links = []
            for channel in self.telegram_sources[:3]:
                try:
                    url = f"https://t.me/s/{channel}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                links.extend(matches)
                                logger.info(f"✅ تم العثور على روابط في قناة {channel}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في قناة {channel}: {e}")
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في تليجرام: {e}")
            return []
    
    # ============================================================
    # 4. البحث الضبابي (Fuzzy Search)
    # ============================================================
    
    async def _fuzzy_search(self, channel_name):
        """البحث الضبابي باستخدام الاسم بالكامل"""
        try:
            # جلب قائمة القنوات من iptv-org
            url = "https://iptv-org.github.io/iptv/index.m3u"
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    # استخراج جميع أسماء القنوات
                    names = re.findall(r'#EXTINF:.*,([^\n]+)', content)
                    # البحث عن التطابقات الضبابية
                    matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=10)
                    links = []
                    for match, score in matches:
                        if score > 70:
                            # جلب الرابط لهذه القناة
                            pattern = rf'#EXTINF:.*,{re.escape(match)}.*\n(https?://[^\s]+)'
                            found = re.findall(pattern, content, re.IGNORECASE)
                            if found:
                                links.extend(found)
                                logger.info(f"🔍 تطابق ضبابي: {match} (نسبة {score}%)")
                    return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الضبابي: {e}")
        return []
    
    # ============================================================
    # 5. تنقية وترتيب النتائج
    # ============================================================
    
    def _deduplicate_links(self, links):
        """إزالة الروابط المكررة"""
        seen = set()
        unique = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique
    
    def _rank_links(self, links, query):
        """ترتيب الروابط حسب الجودة والأهمية"""
        scored = []
        query_lower = query.lower()
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # الروابط من مصادر موثوقة
            trusted = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv']
            for domain in trusted:
                if domain in link_lower:
                    score += 10
            
            # الروابط التي تحتوي على اسم القناة
            if query_lower in link_lower:
                score += 5
            
            # الروابط الآمنة (HTTPS)
            if link.startswith('https://'):
                score += 3
            
            # الروابط من GitHub (قد تكون مفتوحة المصدر)
            if 'github' in link_lower:
                score += 2
            
            scored.append((score, link))
        
        # ترتيب تنازلي حسب النقاط
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for score, link in scored]
    
    async def _quick_validate(self, links):
        """اختبار سريع للروابط (تحميل أول 1024 بايت)"""
        valid = []
        
        async with aiohttp.ClientSession() as session:
            for link in links:
                try:
                    headers = {'Range': 'bytes=0-1024'}
                    async with session.get(link, headers=headers, timeout=5) as response:
                        if response.status in [200, 206]:
                            # قراءة جزء صغير للتأكد من أنه ليس HTML
                            content = await response.read()
                            if b'<html' not in content and b'<body' not in content:
                                valid.append(link)
                                logger.info(f"✅ رابط صالح: {link[:50]}...")
                except Exception as e:
                    logger.warning(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:30]}")
                    continue
        
        return valid
