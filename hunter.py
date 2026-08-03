import asyncio
import aiohttp
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class LinkHunter:
    """صياد الروابط المتطور - دقة عالية، 5 بثوث، جودات متعددة"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=25)
        self.session = None
        
        # وكلاء User-Agent للتناوب
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # قنوات تليجرام
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB', 'iptv_m3u',
            'm3u8_live', 'iptv_channels', 'free_iptv'
        ]
        
        # مواقع معروفة
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
        
        # معلمات الجودة
        self.quality_params = [
            'FHD', 'HD', 'SD', '1080p', '720p', '480p',
            'high', 'medium', 'low', '4k', '2k'
        ]
    
    async def hunt(self, channel_name, max_results=15):
        """الصيد الرئيسي - بحث دقيق مع جودات متعددة"""
        logger.info(f"🔍 بدء الصيد المتقدم عن: {channel_name}")
        all_links = []
        exact_name = channel_name.strip()
        
        # 1. البحث في المصادر الرئيسية (مع دقة عالية)
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            tasks = [
                self._search_iptv_org_exact(exact_name),
                self._search_github_exact(exact_name),
                self._search_world_iptv_exact(exact_name),
                self._search_web_exact(exact_name),
                self._search_telegram_exact(exact_name),
                self._search_pastebin_exact(exact_name),
                self._search_reddit_exact(exact_name),
                self._search_multiple_qualities(exact_name),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ خطأ: {str(result)[:50]}")
        
        # 2. تنقية وترتيب النتائج (دقة عالية)
        unique_links = self._deduplicate_links(all_links)
        filtered_links = self._filter_exact_match(unique_links, exact_name)
        ranked_links = self._rank_links(filtered_links, exact_name)
        
        # 3. ضمان 5 بثوث على الأقل
        if len(ranked_links) < 5:
            logger.info(f"🔄 تم العثور على {len(ranked_links)} فقط، جاري البحث الموسع...")
            more_links = await self._extended_search(exact_name)
            if more_links:
                ranked_links.extend(more_links)
                ranked_links = self._deduplicate_links(ranked_links)
        
        # 4. اختبار عميق للروابط (تحقق من الصلاحية)
        logger.info("🧪 جاري اختبار الروابط...")
        valid_links = await self._deep_validate(ranked_links[:15])
        
        # 5. إضافة جودات متعددة إذا أمكن
        if valid_links:
            enhanced_links = await self._enhance_with_qualities(valid_links, exact_name)
            if len(enhanced_links) >= 5:
                valid_links = enhanced_links
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {exact_name}")
        return valid_links[:15]
    
    # ============================================================
    # 1. البحث الدقيق (باستخدام الاسم الكامل)
    # ============================================================
    
    async def _search_iptv_org_exact(self, channel_name):
        """البحث في iptv-org بدقة عالية"""
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
                        # البحث عن الاسم الدقيق مع tvg-id
                        patterns = [
                            rf'#EXTINF:.*tvg-name="{re.escape(channel_name)}".*\n(https?://[^\s]+)',
                            rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)',
                            rf'#EXTINF:.*tvg-id="[^"]*{re.escape(channel_name)}[^"]*".*\n(https?://[^\s]+)',
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    async def _search_github_exact(self, channel_name):
        """البحث في GitHub بدقة عالية"""
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
    
    async def _search_world_iptv_exact(self, channel_name):
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
    # 2. البحث الدقيق في الويب
    # ============================================================
    
    async def _search_web_exact(self, channel_name):
        """البحث الدقيق في محركات البحث"""
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                loop = asyncio.get_event_loop()
                queries = [
                    f'"{channel_name}" m3u8 live',
                    f'"{channel_name}" iptv link',
                    f'"{channel_name}" channel stream',
                ]
                tasks = [
                    loop.run_in_executor(executor, self._search_google_query, q)
                    for q in queries
                ]
                results = await asyncio.gather(*tasks)
                all_links = []
                for result in results:
                    if result:
                        all_links.extend(result)
                return all_links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في الويب: {e}")
            return []
    
    def _search_google_query(self, query):
        """البحث في Google بعلامات اقتباس (دقة عالية)"""
        try:
            from googlesearch import search
            links = []
            for url in search(query, num_results=5):
                if '.m3u8' in url or '.m3u' in url:
                    links.append(url)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Google: {e}")
            return []
    
    # ============================================================
    # 3. البحث في تليجرام بدقة
    # ============================================================
    
    async def _search_telegram_exact(self, channel_name):
        """البحث في قنوات تليجرام"""
        try:
            links = []
            for channel in self.telegram_sources[:4]:
                try:
                    url = f"https://t.me/s/{channel}"
                    headers = self._get_random_headers()
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            # تصفية النتائج لتشمل اسم القناة
                            filtered = [
                                link for link in matches
                                if channel_name.lower() in link.lower()
                            ]
                            if filtered:
                                links.extend(filtered)
                                logger.info(f"✅ تم العثور على روابط في قناة {channel}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في قناة {channel}: {e}")
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في تليجرام: {e}")
            return []
    
    # ============================================================
    # 4. البحث عن جودات متعددة
    # ============================================================
    
    async def _search_multiple_qualities(self, channel_name):
        """البحث عن جودات متعددة للقناة"""
        try:
            links = []
            quality_variants = [
                f"{channel_name} FHD",
                f"{channel_name} HD",
                f"{channel_name} 1080p",
                f"{channel_name} 720p",
            ]
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, self._search_google_query, q)
                    for q in quality_variants
                ]
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result:
                        links.extend(result)
            
            # إضافة معلمات الجودة للروابط
            enhanced = []
            for link in links:
                for quality in self.quality_params:
                    if quality.lower() in link.lower():
                        enhanced.append(link)
                        break
            
            return enhanced
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث عن الجودات: {e}")
            return []
    
    # ============================================================
    # 5. البحث الموسع (للوصول إلى 5 بثوث)
    # ============================================================
    
    async def _extended_search(self, channel_name):
        """بحث موسع لضمان 5 بثوث"""
        try:
            links = []
            # مصادر إضافية
            extra_sources = [
                f"https://www.google.com/search?q={quote_plus(channel_name)}+m3u8+stream",
                f"https://www.bing.com/search?q={quote_plus(channel_name)}+m3u8",
            ]
            
            for url in extra_sources:
                headers = self._get_random_headers()
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        # تصفية لتشمل اسم القناة
                        filtered = [
                            link for link in matches
                            if channel_name.lower().replace(' ', '') in link.lower().replace(' ', '')
                        ]
                        links.extend(filtered)
            
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الموسع: {e}")
            return []
    
    # ============================================================
    # 6. تحسين الروابط بجودات متعددة
    # ============================================================
    
    async def _enhance_with_qualities(self, links, channel_name):
        """محاولة إضافة جودات متعددة للروابط"""
        enhanced = []
        base_links = links[:5]  # خذ أول 5 روابط
        
        # أضفها كما هي
        enhanced.extend(base_links)
        
        # حاول إضافة نسخ بجودة مختلفة
        for link in base_links:
            # تعديل معلمات الجودة
            base_url = link.split('?')[0]
            for quality in ['FHD', 'HD', 'SD']:
                if quality.lower() not in base_url.lower():
                    quality_link = f"{base_url}?quality={quality}"
                    enhanced.append(quality_link)
        
        # أزل التكرار
        return self._deduplicate_links(enhanced)[:15]
    
    # ============================================================
    # 7. تصفية دقيقة (للقناة نفسها)
    # ============================================================
    
    def _filter_exact_match(self, links, channel_name):
        """تصفية الروابط لتشمل القناة المطلوبة فقط"""
        filtered = []
        channel_words = set(channel_name.lower().split())
        
        for link in links:
            link_lower = link.lower()
            # احسب عدد الكلمات المتطابقة
            match_count = sum(1 for word in channel_words if word in link_lower)
            # إذا تطابقت أكثر من 2 كلمات أو كانت النسبة عالية
            if match_count >= 2 or channel_name.lower() in link_lower:
                filtered.append(link)
        
        return filtered
    
    # ============================================================
    # 8. اختبار عميق للروابط
    # ============================================================
    
    async def _deep_validate(self, links):
        """اختبار عميق للروابط"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for link in links:
                try:
                    headers = self._get_random_headers()
                    # اختبار HEAD أولاً
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301, 403]:
                            # اختبار GET مع Range
                            headers['Range'] = 'bytes=0-2048'
                            async with session.get(link, headers=headers) as get_response:
                                if get_response.status in [200, 206, 403]:
                                    content = await get_response.read()
                                    if b'<html' not in content and b'<body' not in content:
                                        valid.append(link)
                                        logger.info(f"✅ رابط صالح: {link[:50]}...")
                                    elif len(content) < 5000:
                                        valid.append(link)
                                        logger.info(f"✅ رابط محتمل: {link[:50]}...")
                except Exception as e:
                    continue
        
        return valid
    
    # ============================================================
    # 9. دوال مساعدة
    # ============================================================
    
    def _get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def _deduplicate_links(self, links):
        seen = set()
        unique = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique
    
    def _rank_links(self, links, query):
        scored = []
        query_lower = query.lower()
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 20
            
            if query_lower in link_lower:
                score += 15
            
            if link.startswith('https://'):
                score += 5
            
            if 'github' in link_lower:
                score += 3
            
            # نقاط إضافية للجودة
            for quality in ['fhd', '1080p', 'hd']:
                if quality in link_lower:
                    score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for score, link in scored]
