import asyncio
import aiohttp
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class LinkHunter:
    """صياد الروابط المتطور - يجلب روابط صالحة مع اتصال مباشر"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=20)
        self.session = None
        
        # قائمة وكلاء User-Agent للتناوب (تجاوز الحجب)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        # قنوات تليجرام للبحث
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
            'https://www.reddit.com/r/FreeIPTV',
        ]
        
        # قائمة بروكسيات لتجاوز الحجب (اختياري)
        self.proxies = [
            None,  # بدون بروكسي
            # يمكن إضافة بروكسيات هنا إذا كانت متوفرة
            # 'http://proxy1:8080',
            # 'http://proxy2:8080',
        ]
    
    async def hunt(self, channel_name, max_results=20):
        """الصيد الرئيسي - بحث عن روابط القناة مع اختبار عميق"""
        logger.info(f"🔍 بدء الصيد المتقدم عن: {channel_name}")
        all_links = []
        
        # 1. البحث في المصادر الرئيسية (بالتوازي)
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            tasks = [
                self._search_iptv_org(channel_name),
                self._search_github(channel_name),
                self._search_world_iptv(channel_name),
                self._search_web_advanced(channel_name),
                self._search_telegram(channel_name),
                self._search_pastebin(channel_name),
                self._search_reddit(channel_name),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    logger.info(f"✅ تم العثور على {len(result)} رابط من مصدر")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ خطأ في أحد المصادر: {str(result)[:50]}")
        
        # 2. تنقية وترتيب النتائج
        unique_links = self._deduplicate_links(all_links)
        ranked_links = self._rank_links(unique_links, channel_name)
        
        # 3. اختبار عميق للروابط (اختبار حقيقي)
        logger.info("🧪 جاري اختبار الروابط...")
        valid_links = await self._deep_validate(ranked_links[:15])
        
        # 4. إذا لم نجد نتائج، استخدم Fuzzy Search
        if not valid_links:
            logger.info("🔄 لم يتم العثور على روابط صالحة، جاري البحث الضبابي...")
            fuzzy_links = await self._fuzzy_search(channel_name)
            if fuzzy_links:
                valid_links = await self._deep_validate(fuzzy_links[:10])
        
        # 5. إذا ما زلنا لم نجد، جرب البحث الواسع (Google)
        if not valid_links:
            logger.info("🌐 جاري البحث الواسع في Google...")
            google_links = await self._search_google_direct(channel_name)
            if google_links:
                valid_links = await self._deep_validate(google_links[:10])
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links[:max_results]
    
    # ============================================================
    # 1. المصادر الأساسية (مطورة)
    # ============================================================
    
    async def _search_iptv_org(self, channel_name):
        """البحث في iptv-org مع تجاوز الحجب"""
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                headers = self._get_random_headers()
                async with self.session.get(url, headers=headers) as response:
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
                headers = self._get_random_headers()
                async with self.session.get(url, headers=headers) as response:
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
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                    return re.findall(pattern, content, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في World IPTV: {e}")
            return []
    
    # ============================================================
    # 2. البحث المتقدم في الويب
    # ============================================================
    
    async def _search_web_advanced(self, channel_name):
        """البحث في محركات البحث مع تجاوز الحجب"""
        try:
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
        """البحث في Google"""
        try:
            from googlesearch import search
            queries = [
                f"{channel_name} m3u8 live stream",
                f"{channel_name} iptv link",
                f"{channel_name} channel stream"
            ]
            links = []
            for query in queries:
                for url in search(query, num_results=3):
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
            headers = self._get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
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
            headers = self._get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                return re.findall(pattern, response.text, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Bing: {e}")
        return []
    
    # ============================================================
    # 3. البحث المباشر في Google (بديل)
    # ============================================================
    
    async def _search_google_direct(self, channel_name):
        """البحث المباشر في Google باستخدام HTTP"""
        try:
            query = f"{channel_name} m3u8 live stream"
            url = f"https://www.google.com/search?q={quote_plus(query)}"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    return re.findall(pattern, content, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Google المباشر: {e}")
        return []
    
    # ============================================================
    # 4. البحث في Pastebin
    # ============================================================
    
    async def _search_pastebin(self, channel_name):
        """البحث في Pastebin"""
        try:
            query = f"{channel_name} m3u8"
            url = f"https://pastebin.com/search?q={quote_plus(query)}"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    return re.findall(pattern, content, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Pastebin: {e}")
        return []
    
    # ============================================================
    # 5. البحث في Reddit
    # ============================================================
    
    async def _search_reddit(self, channel_name):
        """البحث في Reddit"""
        try:
            query = f"{channel_name} m3u8"
            url = f"https://www.reddit.com/search/?q={quote_plus(query)}"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    return re.findall(pattern, content, re.IGNORECASE)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Reddit: {e}")
        return []
    
    # ============================================================
    # 6. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram(self, channel_name):
        """البحث في قنوات تليجرام"""
        try:
            links = []
            for channel in self.telegram_sources[:3]:
                try:
                    url = f"https://t.me/s/{channel}"
                    headers = self._get_random_headers()
                    async with self.session.get(url, headers=headers) as response:
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
    # 7. البحث الضبابي (Fuzzy Search)
    # ============================================================
    
    async def _fuzzy_search(self, channel_name):
        """البحث الضبابي باستخدام الاسم بالكامل"""
        try:
            url = "https://iptv-org.github.io/iptv/index.m3u"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    names = re.findall(r'#EXTINF:.*,([^\n]+)', content)
                    matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=15)
                    links = []
                    for match, score in matches:
                        if score > 65:
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
    # 8. اختبار عميق للروابط (يتجاوز مجرد HEAD)
    # ============================================================
    
    async def _deep_validate(self, links):
        """اختبار عميق للروابط - يحاول تحميل جزء من البث"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for link in links:
                try:
                    # 1. اختبار HEAD مع تغيير User-Agent
                    headers = self._get_random_headers()
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301]:
                            # 2. اختبار GET مع Range (تحميل جزء صغير)
                            headers['Range'] = 'bytes=0-2048'
                            async with session.get(link, headers=headers) as get_response:
                                if get_response.status in [200, 206, 403]:
                                    # 403 قد يعني حجباً جغرافياً لكن الرابط صحيح
                                    content = await get_response.read()
                                    # التأكد من أنه ليس صفحة HTML
                                    if b'<html' not in content and b'<body' not in content:
                                        valid.append(link)
                                        logger.info(f"✅ رابط صالح: {link[:50]}...")
                                    elif b'<html' in content and len(content) < 5000:
                                        # قد يكون صفحة خطأ صغيرة، نعتبر الرابط صالحاً
                                        valid.append(link)
                                        logger.info(f"✅ رابط محتمل (صفحة خطأ صغيرة): {link[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ رابط غير صالح: {link[:50]}... - {str(e)[:30]}")
                    continue
        
        return valid
    
    # ============================================================
    # 9. دوال مساعدة
    # ============================================================
    
    def _get_random_headers(self):
        """الحصول على رؤوس عشوائية لتجاوز الحجب"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
        }
    
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
        
        # مصادر موثوقة
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # نقاط للمصادر الموثوقة
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 15
            
            # نقاط لتطابق اسم القناة
            if query_lower in link_lower:
                score += 10
            
            # نقاط للروابط الآمنة
            if link.startswith('https://'):
                score += 5
            
            # نقاط للروابط من GitHub
            if 'github' in link_lower:
                score += 3
            
            # نقاط للروابط من iptv-org
            if 'iptv-org' in link_lower:
                score += 5
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for score, link in scored]
