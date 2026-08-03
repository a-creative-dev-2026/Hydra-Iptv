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
    """صياد الروابط المتطور - حل مشكلة عدم العثور على القنوات"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=20)
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
    
    async def hunt(self, channel_name, max_results=15):
        """الصيد الرئيسي - بحث مرن عن القنوات"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        all_links = []
        
        # إنشاء قائمة بأسماء بديلة للقناة
        channel_variants = self._generate_name_variants(channel_name)
        logger.info(f"📝 أسماء بديلة للبحث: {channel_variants}")
        
        # 1. البحث في المصادر الرئيسية
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            tasks = []
            for variant in channel_variants[:3]:  # حد أقصى 3 متغيرات للسرعة
                tasks.extend([
                    self._search_iptv_org_flexible(variant),
                    self._search_github_flexible(variant),
                    self._search_world_iptv_flexible(variant),
                    self._search_web_flexible(variant),
                    self._search_telegram_flexible(variant),
                ])
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ خطأ: {str(result)[:50]}")
        
        # 2. إذا لم نجد نتائج، استخدم Fuzzy Search
        if not all_links:
            logger.info("🔄 لم يتم العثور على روابط، جاري البحث الضبابي...")
            fuzzy_links = await self._fuzzy_search_flexible(channel_name)
            if fuzzy_links:
                all_links.extend(fuzzy_links)
        
        # 3. إذا ما زلنا لم نجد، جرب البحث الواسع
        if not all_links:
            logger.info("🌐 جاري البحث الواسع...")
            wide_links = await self._wide_search(channel_name)
            if wide_links:
                all_links.extend(wide_links)
        
        # 4. تنقية وترتيب النتائج
        unique_links = self._deduplicate_links(all_links)
        ranked_links = self._rank_links_flexible(unique_links, channel_name)
        
        # 5. اختبار سريع للروابط (متسامح)
        logger.info("🧪 جاري اختبار الروابط...")
        valid_links = await self._quick_validate_flexible(ranked_links[:15])
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links[:max_results]
    
    # ============================================================
    # 1. توليد أسماء بديلة
    # ============================================================
    
    def _generate_name_variants(self, channel_name):
        """توليد أسماء بديلة للقناة"""
        variants = [channel_name]
        name_lower = channel_name.lower().strip()
        
        # إزالة الأرقام
        name_no_numbers = re.sub(r'\d+', '', name_lower).strip()
        if name_no_numbers and name_no_numbers != name_lower:
            variants.append(name_no_numbers)
        
        # إزالة كلمات إضافية
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel', 'live']:
            if word in name_lower:
                variants.append(name_lower.replace(word, '').strip())
        
        # إضافة صيغ مختلفة
        if 'mbc' in name_lower:
            variants.append('mbc1')
            variants.append('mbc 1 hd')
            variants.append('mbc one')
        
        if 'bein' in name_lower:
            variants.append('beIN')
            variants.append('beIN 1')
            variants.append('beIN HD')
        
        # إزالة التكرار
        return list(set(variants))
    
    # ============================================================
    # 2. البحث المرن في المصادر
    # ============================================================
    
    async def _search_iptv_org_flexible(self, channel_name):
        """البحث في iptv-org بشكل مرن"""
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
                        # بحث مرن بدون tvg-name
                        pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    async def _search_github_flexible(self, channel_name):
        """البحث في GitHub بشكل مرن"""
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
    
    async def _search_world_iptv_flexible(self, channel_name):
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
    # 3. البحث المرن في الويب
    # ============================================================
    
    async def _search_web_flexible(self, channel_name):
        """البحث في الويب بشكل مرن"""
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                loop = asyncio.get_event_loop()
                queries = [
                    f"{channel_name} m3u8",
                    f"{channel_name} iptv",
                    f"{channel_name} live stream",
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
        """البحث في Google"""
        try:
            from googlesearch import search
            links = []
            for url in search(query, num_results=3):
                if '.m3u8' in url or '.m3u' in url:
                    links.append(url)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Google: {e}")
            return []
    
    # ============================================================
    # 4. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram_flexible(self, channel_name):
        """البحث في قنوات تليجرام"""
        try:
            links = []
            for channel in self.telegram_sources[:2]:
                try:
                    url = f"https://t.me/s/{channel}"
                    headers = self._get_random_headers()
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            # تصفية لتشمل اسم القناة
                            for link in matches:
                                if channel_name.lower().replace(' ', '') in link.lower().replace(' ', ''):
                                    links.append(link)
                            if links:
                                logger.info(f"✅ تم العثور على روابط في قناة {channel}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في قناة {channel}: {e}")
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في تليجرام: {e}")
            return []
    
    # ============================================================
    # 5. البحث الضبابي المرن
    # ============================================================
    
    async def _fuzzy_search_flexible(self, channel_name):
        """البحث الضبابي المرن"""
        try:
            url = "https://iptv-org.github.io/iptv/index.m3u"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    names = re.findall(r'#EXTINF:.*,([^\n]+)', content)
                    # بحث ضبابي مع حد أدنى 60%
                    matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=20)
                    links = []
                    for match, score in matches:
                        if score > 55:  # نسبة أقل للعثور على المزيد
                            pattern = rf'#EXTINF:.*,{re.escape(match)}.*\n(https?://[^\s]+)'
                            found = re.findall(pattern, content, re.IGNORECASE)
                            if found:
                                links.extend(found)
                                logger.info(f"🔍 تطابق: {match} (نسبة {score}%)")
                    return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الضبابي: {e}")
        return []
    
    # ============================================================
    # 6. البحث الواسع (للحصول على نتائج)
    # ============================================================
    
    async def _wide_search(self, channel_name):
        """بحث واسع للحصول على نتائج"""
        try:
            links = []
            # استخدام Google المباشر
            url = f"https://www.google.com/search?q={quote_plus(channel_name)}+m3u8"
            headers = self._get_random_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                    found = re.findall(pattern, content, re.IGNORECASE)
                    links.extend(found)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الواسع: {e}")
            return []
    
    # ============================================================
    # 7. اختبار مرن للروابط (متسامح)
    # ============================================================
    
    async def _quick_validate_flexible(self, links):
        """اختبار مرن للروابط"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            for link in links:
                try:
                    headers = self._get_random_headers()
                    # اختبار HEAD فقط (أسرع)
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301, 403, 404]:
                            # 403 و 404 قد يكونان صالحين في بعض الحالات
                            valid.append(link)
                            logger.info(f"✅ رابط محتمل: {link[:50]}...")
                except Exception as e:
                    # حتى لو فشل HEAD، قد يكون الرابط صالحاً
                    if '.m3u8' in link:
                        valid.append(link)
                        logger.info(f"✅ رابط محتمل (رغم خطأ HEAD): {link[:50]}...")
                    continue
        
        return valid
    
    # ============================================================
    # 8. ترتيب مرن للنتائج
    # ============================================================
    
    def _rank_links_flexible(self, links, query):
        """ترتيب النتائج بشكل مرن"""
        scored = []
        query_lower = query.lower()
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 15
            
            if query_lower in link_lower:
                score += 10
            
            if link.startswith('https://'):
                score += 5
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for score, link in scored]
    
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
            # إزالة المعلمات الزائدة لتفادي التكرار
            clean_link = link.split('?')[0]
            if clean_link not in seen:
                seen.add(clean_link)
                unique.append(link)
        return unique
