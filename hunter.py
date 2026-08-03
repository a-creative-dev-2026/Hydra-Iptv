import asyncio
import aiohttp
import re
import time
import random
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class StableHunter:
    """
    الصياد المستقر - بحث عام عن أي قناة يطلبها المستخدم
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.session = None
        self.semaphore = asyncio.Semaphore(10)
        self.failed_links = set()
        
        # ============================================================
        # 🔥 المصادر الموثوقة (قوائم M3U المعروفة)
        # ============================================================
        self.m3u_sources = [
            'https://iptv-org.github.io/iptv/index.m3u',
            'https://iptv-org.github.io/iptv/index.nsfw.m3u',
            'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
            'https://raw.githubusercontent.com/ismailozgul/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/mhdzumair/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/azenv/IPTV/main/playlist.m3u',
            'https://iptv-org.github.io/iptv/countries/us.m3u',
            'https://iptv-org.github.io/iptv/countries/gb.m3u',
            'https://iptv-org.github.io/iptv/countries/fr.m3u',
            'https://iptv-org.github.io/iptv/countries/de.m3u',
            'https://iptv-org.github.io/iptv/countries/qa.m3u',
            'https://iptv-org.github.io/iptv/countries/sa.m3u',
            'https://iptv-org.github.io/iptv/countries/ae.m3u',
            'https://iptv-org.github.io/iptv/countries/eg.m3u',
            'https://iptv-org.github.io/iptv/countries/tn.m3u',
            'https://iptv-org.github.io/iptv/countries/ma.m3u',
            'https://iptv-org.github.io/iptv/countries/dz.m3u',
            'https://iptv-org.github.io/iptv/countries/jo.m3u',
            'https://iptv-org.github.io/iptv/countries/lb.m3u',
            'https://iptv-org.github.io/iptv/countries/kw.m3u',
        ]
        
        self.category_sources = [
            'https://iptv-org.github.io/iptv/categories/news.m3u',
            'https://iptv-org.github.io/iptv/categories/sports.m3u',
            'https://iptv-org.github.io/iptv/categories/movies.m3u',
            'https://iptv-org.github.io/iptv/categories/religious.m3u',
            'https://iptv-org.github.io/iptv/categories/kids.m3u',
            'https://iptv-org.github.io/iptv/categories/music.m3u',
        ]
        
        self.trusted_domains = [
            'amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv',
            'cloudfront.net', 'edgenextcdn.net'
        ]
        
        logger.info(f"🔥 تم تهيئة الصياد للبحث العام مع {len(self.m3u_sources)} مصدراً")
    
    # ============================================================
    # 🎯 الوظيفة الرئيسية - بحث عام
    # ============================================================
    
    async def hunt(self, channel_name, max_results=10):
        """بحث عام عن أي قناة يطلبها المستخدم"""
        logger.info(f"🔍 بدء البحث العام عن: {channel_name}")
        start_time = time.time()
        all_links = []
        
        # توليد كلمات بحث متعددة بناءً على اسم القناة
        keywords = self._generate_keywords(channel_name)
        logger.info(f"📝 كلمات البحث: {keywords}")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            tasks = []
            for url in self.m3u_sources:
                tasks.append(self._search_m3u(url, keywords))
            
            for url in self.category_sources:
                tasks.append(self._search_m3u(url, keywords))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    if result:
                        logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ خطأ: {str(result)[:50]}")
        
        unique_links = self._deduplicate(all_links)
        filtered_links = self._filter_by_keywords(unique_links, keywords)
        ranked_links = self._rank_links(filtered_links, channel_name)
        
        logger.info("🧪 جاري التحقق من الروابط...")
        validated = await self._validate_links(ranked_links[:20])
        
        final = self._select_best(validated, max_results)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 📡 البحث في قوائم M3U
    # ============================================================
    
    async def _search_m3u(self, url, keywords):
        try:
            if url in self.failed_links:
                return []
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            }
            
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self.failed_links.add(url)
                        return []
                    
                    content = await response.text()
                    links = []
                    
                    # ✅ بحث عام عن أي قناة
                    pattern = r'#EXTINF:[^\n]*,([^\n]*)\n(https?://[^\s]+)'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for name, url_link in matches:
                        name_lower = name.lower()
                        for keyword in keywords:
                            if keyword.lower().replace(' ', '') in name_lower.replace(' ', ''):
                                links.append(url_link)
                                break
                    
                    return links
        except Exception as e:
            logger.debug(f"⚠️ خطأ في {url[:50]}: {e}")
            self.failed_links.add(url)
            return []
    
    # ============================================================
    # 🧪 التحقق من الروابط
    # ============================================================
    
    async def _validate_links(self, links):
        valid = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            for link in links:
                if link in self.failed_links:
                    continue
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
                    }
                    
                    async with session.get(link, headers=headers, allow_redirects=True) as response:
                        if response.status in (200, 206):
                            content_type = response.headers.get('Content-Type', '').lower()
                            if 'mpegurl' in content_type or 'm3u8' in content_type or 'application/vnd.apple.mpegurl' in content_type:
                                valid.append(link)
                                logger.info(f"✅ صالح: {link[:40]}...")
                            else:
                                try:
                                    chunk = await response.content.read(1024)
                                    if b'#EXTM3U' in chunk or b'#EXTINF' in chunk:
                                        valid.append(link)
                                        logger.info(f"✅ صالح (M3U): {link[:40]}...")
                                except:
                                    pass
                except:
                    continue
        return valid
    
    # ============================================================
    # 🧠 توليد كلمات البحث العامة
    # ============================================================
    
    def _generate_keywords(self, channel_name):
        """توليد كلمات بحث متعددة لأي قناة"""
        keywords = [channel_name]
        name = channel_name.lower().strip()
        
        # إزالة الأرقام
        no_numbers = re.sub(r'\d+', '', name).strip()
        if no_numbers and no_numbers != name:
            keywords.append(no_numbers)
        
        # إزالة الكلمات الإضافية
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel']:
            if word in name:
                keywords.append(name.replace(word, '').strip())
        
        # ✅ أسماء بديلة عامة (لأي قناة)
        # يتم استبدال الأرقام بالكلمات
        if '1' in name:
            keywords.append(name.replace('1', 'one'))
        if '2' in name:
            keywords.append(name.replace('2', 'two'))
        if '3' in name:
            keywords.append(name.replace('3', 'three'))
        
        # ✅ إضافة صيغ مختلفة
        keywords.append(f"{name} live")
        keywords.append(f"{name} stream")
        
        return list(set(keywords))[:8]
    
    # ============================================================
    # 📊 ترتيب النتائج
    # ============================================================
    
    def _rank_links(self, links, query):
        scored = []
        query_lower = query.lower()
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            for domain in self.trusted_domains:
                if domain in link_lower:
                    score += 10
                    break
            
            if query_lower in link_lower:
                score += 8
            
            if link.startswith('https://'):
                score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for _, link in scored]
    
    def _select_best(self, links, max_results):
        if len(links) <= max_results:
            return links
        
        domains_seen = set()
        selected = []
        for link in links:
            domain = urlparse(link).netloc
            if domain not in domains_seen or len(selected) < 3:
                selected.append(link)
                domains_seen.add(domain)
            if len(selected) >= max_results:
                break
        
        return selected
    
    def _filter_by_keywords(self, links, keywords):
        filtered = []
        for link in links:
            link_lower = link.lower()
            for keyword in keywords:
                if keyword.lower().replace(' ', '') in link_lower.replace(' ', ''):
                    filtered.append(link)
                    break
        return filtered
    
    def _deduplicate(self, links):
        seen = set()
        unique = []
        for link in links:
            clean = link.split('?')[0]
            if clean not in seen:
                seen.add(clean)
                unique.append(link)
        return unique
