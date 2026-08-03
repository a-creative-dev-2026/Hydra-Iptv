import asyncio
import aiohttp
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class LinkHunter:
    """صياد الروابط المتطور - التركيز على الصلاحية والجودة"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=20)
        self.session = None
        self.semaphore = asyncio.Semaphore(15)
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # 🔥 مصادر متعددة للبحث
        self.sources = {
            'iptv_org': 'https://iptv-org.github.io/iptv/index.m3u',
            'iptv_org_nsfw': 'https://iptv-org.github.io/iptv/index.nsfw.m3u',
            'free_tv': 'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'iptv_hub': 'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'world_iptv': 'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
            'github_iptv': 'https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u',
        }
        
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB', 'iptv_m3u',
            'm3u8_live', 'iptv_channels', 'free_iptv',
            'iptv_playlist', 'm3u_streams', 'iptv_m3u8'
        ]
        
        self.streaming_sites = [
            'https://pastebin.com', 'https://telegra.ph', 'https://t.me',
            'https://github.com', 'https://www.reddit.com/r/IPTV',
            'https://www.reddit.com/r/m3u8', 'https://www.reddit.com/r/FreeIPTV',
            'https://www.reddit.com/r/IPTVpro', 'https://www.reddit.com/r/IPTVreviews',
        ]
    
    async def hunt(self, channel_name, max_results=15):
        """الصيد الرئيسي - مع اختبار صارم للصلاحية"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        all_links = []
        start_time = time.time()
        
        variants = self._generate_variants(channel_name)
        logger.info(f"📝 متغيرات البحث: {len(variants)}")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 🔥 البحث في جميع المصادر بالتوازي
            tasks = []
            
            # 1. القوائم الرئيسية
            for url in self.sources.values():
                tasks.append(self._fetch_playlist(url, variants[:4]))
            
            # 2. الويب
            for variant in variants[:3]:
                tasks.append(self._search_web(variant))
                tasks.append(self._search_telegram(variant))
                tasks.append(self._search_streaming(variant))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
        
        # 3. Fuzzy Search إذا كانت النتائج قليلة
        if len(all_links) < 5:
            logger.info("🔄 جاري البحث الضبابي...")
            fuzzy_links = await self._fuzzy_search(channel_name)
            if fuzzy_links:
                all_links.extend(fuzzy_links)
        
        # 4. تنقية
        unique = self._deduplicate(all_links)
        
        # 🔥 5. اختبار صارم للصلاحية (الخطوة الأهم)
        logger.info("🧪 جاري اختبار صلاحية الروابط (قد يستغرق قليلاً)...")
        valid_links = await self._strict_validate(unique[:30])
        
        # 6. ترتيب حسب الجودة
        ranked = self._rank_by_quality(valid_links, channel_name)
        
        # 7. اختيار أفضل 5 روابط على الأقل
        final = self._select_best(ranked, channel_name)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final[:15]
    
    # ============================================================
    # 🔥 1. جلب القوائم
    # ============================================================
    
    async def _fetch_playlist(self, url, variants):
        try:
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._extract_links(content, variants)
        except:
            pass
        return []
    
    def _extract_links(self, content, variants):
        links = []
        for variant in variants:
            pattern = rf'#EXTINF:.*,.*{re.escape(variant)}.*\n(https?://[^\s]+)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            links.extend(matches)
        return links
    
    # ============================================================
    # 🔥 2. البحث في الويب
    # ============================================================
    
    async def _search_web(self, query):
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                loop = asyncio.get_event_loop()
                qs = [f'"{query}" m3u8', f'"{query}" iptv', f'"{query}" stream']
                tasks = [loop.run_in_executor(executor, self._search_google, q) for q in qs]
                results = await asyncio.gather(*tasks)
                all_links = []
                for result in results:
                    if result:
                        all_links.extend(result)
                return all_links
        except:
            return []
    
    def _search_google(self, query):
        try:
            from googlesearch import search
            links = []
            for url in search(query, num_results=5):
                if '.m3u8' in url or '.m3u' in url:
                    links.append(url)
            return links
        except:
            return []
    
    # ============================================================
    # 🔥 3. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram(self, query):
        links = []
        for channel in self.telegram_sources[:3]:
            try:
                url = f"https://t.me/s/{channel}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for link in matches:
                                if query.lower().replace(' ', '') in link.lower().replace(' ', ''):
                                    links.append(link)
            except:
                pass
        return links
    
    # ============================================================
    # 🔥 4. البحث في مواقع البث
    # ============================================================
    
    async def _search_streaming(self, query):
        links = []
        for site in self.streaming_sites[:3]:
            try:
                url = f"{site}/search?q={quote_plus(query)}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                links.extend(matches)
            except:
                pass
        return links
    
    # ============================================================
    # 🔥 5. البحث الضبابي
    # ============================================================
    
    async def _fuzzy_search(self, channel_name):
        try:
            url = "https://iptv-org.github.io/iptv/index.m3u"
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        names = re.findall(r'#EXTINF:.*,([^\n]+)', content)
                        matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=30)
                        links = []
                        for match, score in matches:
                            if score > 60:
                                pattern = rf'#EXTINF:.*,{re.escape(match)}.*\n(https?://[^\s]+)'
                                found = re.findall(pattern, content, re.IGNORECASE)
                                if found:
                                    links.extend(found)
                                    logger.info(f"🔍 تطابق: {match} ({score}%)")
                        return links
        except:
            pass
        return []
    
    # ============================================================
    # 🔥 6. اختبار صارم للصلاحية (الأهم)
    # ============================================================
    
    async def _strict_validate(self, links):
        """اختبار فعلي للروابط - تحميل جزء من البث"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            for link in links:
                try:
                    headers = self._get_headers()
                    headers['Range'] = 'bytes=0-2048'
                    
                    async with session.get(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206]:
                            content = await response.read()
                            # التأكد من أنه ليس HTML
                            if b'<html' not in content[:100] and b'<body' not in content[:100]:
                                valid.append(link)
                                logger.info(f"✅ رابط صالح: {link[:40]}...")
                            elif b'#EXTM3U' in content:
                                valid.append(link)
                                logger.info(f"✅ رابط M3U صالح: {link[:40]}...")
                        elif response.status == 403:
                            # 403 قد يكون حجباً جغرافياً، نحتفظ به كخيار
                            valid.append(link)
                            logger.info(f"⚠️ رابط محجوب (قد يعمل): {link[:40]}...")
                except Exception as e:
                    logger.debug(f"❌ فشل: {link[:40]}... - {str(e)[:20]}")
                    continue
        
        return valid
    
    # ============================================================
    # 🔥 7. ترتيب حسب الجودة
    # ============================================================
    
    def _rank_by_quality(self, links, query):
        scored = []
        query_lower = query.lower()
        quality_keywords = ['fhd', '1080p', 'hd', '720p', '4k']
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # الجودة
            for quality in quality_keywords:
                if quality in link_lower:
                    score += 5
                    break
            
            # المصادر الموثوقة
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 8
                    break
            
            # تطابق الاسم
            if query_lower in link_lower:
                score += 6
            
            # HTTPS
            if link.startswith('https://'):
                score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for _, link in scored]
    
    # ============================================================
    # 🔥 8. اختيار أفضل الروابط (5 على الأقل)
    # ============================================================
    
    def _select_best(self, links, query):
        """اختيار 5 روابط على الأقل مع تنوع في المصادر"""
        if len(links) >= 5:
            # خذ أفضل 5
            return links[:5]
        elif len(links) >= 3:
            # إذا كانت 3-4، أضف بعض الروابط الاحتياطية (حتى لو كانت أقل جودة)
            return links
        else:
            # إذا كانت أقل من 3، حاول إضافة روابط إضافية من البحث الموسع
            return links
    
    # ============================================================
    # 🔥 9. دوال مساعدة
    # ============================================================
    
    def _generate_variants(self, channel_name):
        variants = [channel_name]
        name = channel_name.lower().strip()
        
        no_numbers = re.sub(r'\d+', '', name).strip()
        if no_numbers and no_numbers != name:
            variants.append(no_numbers)
        
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel']:
            if word in name:
                variants.append(name.replace(word, '').strip())
        
        if 'mbc' in name:
            variants.extend(['mbc1', 'mbc 1 hd', 'mbc one'])
        if 'bein' in name:
            variants.extend(['beIN', 'beIN 1', 'beIN HD'])
        
        return list(set(variants))[:5]
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Connection': 'keep-alive',
        }
    
    def _deduplicate(self, links):
        seen = set()
        unique = []
        for link in links:
            clean = link.split('?')[0]
            if clean not in seen:
                seen.add(clean)
                unique.append(link)
        return unique
