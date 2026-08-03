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
    """صياد الروابط - نسخة سريعة ومستقرة (تجنب 502)"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.session = None
        self.semaphore = asyncio.Semaphore(10)
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self.sources = {
            'iptv_org': 'https://iptv-org.github.io/iptv/index.m3u',
            'free_tv': 'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'iptv_hub': 'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'world_iptv': 'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
        }
        
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB'
        ]
    
    async def hunt(self, channel_name, max_results=10):
        """الصيد السريع - تجنب المهلة"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        all_links = []
        start_time = time.time()
        
        variants = self._generate_variants(channel_name)
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            tasks = []
            # قوائم رئيسية فقط (أسرع)
            for url in list(self.sources.values())[:3]:
                tasks.append(self._fetch_playlist(url, variants[:3]))
            
            # تليجرام (سريع)
            for variant in variants[:2]:
                tasks.append(self._search_telegram(variant))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
        
        # Fuzzy Search فقط إذا كان عدد الروابط أقل من 3
        if len(all_links) < 3:
            fuzzy_links = await self._fuzzy_search(channel_name)
            if fuzzy_links:
                all_links.extend(fuzzy_links)
        
        unique = self._deduplicate(all_links)
        
        # اختبار سريع (HEAD فقط + مهلة قصيرة)
        valid_links = await self._quick_validate(unique[:15])
        
        # ترتيب واختيار أفضل 5
        ranked = self._rank_by_quality(valid_links, channel_name)
        final = ranked[:5] if len(ranked) >= 5 else ranked
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 1. جلب القوائم (سريع)
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
    # 2. البحث في تليجرام (سريع)
    # ============================================================
    
    async def _search_telegram(self, query):
        links = []
        for channel in self.telegram_sources[:2]:
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
    # 3. البحث الضبابي
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
                        matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=20)
                        links = []
                        for match, score in matches:
                            if score > 60:
                                pattern = rf'#EXTINF:.*,{re.escape(match)}.*\n(https?://[^\s]+)'
                                found = re.findall(pattern, content, re.IGNORECASE)
                                if found:
                                    links.extend(found)
                        return links
        except:
            pass
        return []
    
    # ============================================================
    # 4. اختبار سريع (HEAD فقط)
    # ============================================================
    
    async def _quick_validate(self, links):
        """اختبار سريع باستخدام HEAD فقط (مهلة 3 ثوانٍ)"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            for link in links:
                try:
                    headers = self._get_headers()
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301]:
                            valid.append(link)
                            logger.info(f"✅ صالح: {link[:40]}...")
                        elif response.status == 403:
                            valid.append(link)  # محجوب لكن قد يعمل
                            logger.info(f"⚠️ محجوب: {link[:40]}...")
                except:
                    continue
        
        return valid
    
    # ============================================================
    # 5. ترتيب حسب الجودة
    # ============================================================
    
    def _rank_by_quality(self, links, query):
        scored = []
        query_lower = query.lower()
        quality_keywords = ['fhd', '1080p', 'hd', '720p']
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            for quality in quality_keywords:
                if quality in link_lower:
                    score += 5
                    break
            
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 8
                    break
            
            if query_lower in link_lower:
                score += 6
            
            if link.startswith('https://'):
                score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for _, link in scored]
    
    # ============================================================
    # 6. دوال مساعدة
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
            variants.extend(['mbc1', 'mbc 1 hd'])
        if 'bein' in name:
            variants.extend(['beIN', 'beIN 1'])
        
        return list(set(variants))[:4]
    
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
