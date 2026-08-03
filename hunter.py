import asyncio
import aiohttp
import re
import time
import random
import json
from urllib.parse import urlparse, quote_plus, urljoin
from bs4 import BeautifulSoup
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class MegaHunter:
    """
    الصياد المتكامل - يجمع بين:
    1. قوائم M3U الضخمة (أكثر من 50 مصدراً)
    2. مواقع البث المباشر (Yacine, Ostora, Yalla Shoot, General Pro, Koora, BeIN)
    3. قنوات تليجرام
    4. محركات البحث
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.session = None
        self.semaphore = asyncio.Semaphore(20)
        self.failed_links = set()
        
        # ============================================================
        # 🔥 1. قوائم M3U الضخمة (أكثر من 50 مصدراً)
        # ============================================================
        self.m3u_sources = [
            # المصادر الرئيسية (أكثر من 20,000 قناة)
            'https://iptv-org.github.io/iptv/index.m3u',
            'https://iptv-org.github.io/iptv/index.nsfw.m3u',
            'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
            
            # مستودعات GitHub (مصادر متعددة)
            'https://raw.githubusercontent.com/ismailozgul/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/mhdzumair/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/azenv/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/Kodi-n-Playlist/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/jaydenmb/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/emirbey/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/matthew1981/m3u/main/playlist.m3u',
            'https://raw.githubusercontent.com/kayleekay/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/samirsam/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/billybonk/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/kingy444/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/MikiBzh/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/sn7696/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/nikooo777/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/junguler/m3u/main/playlist.m3u',
            
            # قوائم حسب الدول (مصادر إضافية)
            'https://iptv-org.github.io/iptv/countries/us.m3u',
            'https://iptv-org.github.io/iptv/countries/gb.m3u',
            'https://iptv-org.github.io/iptv/countries/fr.m3u',
            'https://iptv-org.github.io/iptv/countries/de.m3u',
            'https://iptv-org.github.io/iptv/countries/it.m3u',
            'https://iptv-org.github.io/iptv/countries/es.m3u',
            'https://iptv-org.github.io/iptv/countries/tr.m3u',
            'https://iptv-org.github.io/iptv/countries/sa.m3u',
            'https://iptv-org.github.io/iptv/countries/ae.m3u',
            'https://iptv-org.github.io/iptv/countries/qa.m3u',
            'https://iptv-org.github.io/iptv/countries/eg.m3u',
            'https://iptv-org.github.io/iptv/countries/tn.m3u',
            'https://iptv-org.github.io/iptv/countries/ma.m3u',
            'https://iptv-org.github.io/iptv/countries/dz.m3u',
            'https://iptv-org.github.io/iptv/countries/jo.m3u',
            'https://iptv-org.github.io/iptv/countries/lb.m3u',
            'https://iptv-org.github.io/iptv/countries/kw.m3u',
            'https://iptv-org.github.io/iptv/countries/om.m3u',
            'https://iptv-org.github.io/iptv/countries/bh.m3u',
        ]
        
        # ============================================================
        # 🌐 2. مواقع البث المباشر (التي قدمتها)
        # ============================================================
        self.streaming_sites = [
            # Yacine TV
            'https://yacinetv.com',
            'https://yacinetv.live',
            # Ostora TV
            'https://ostora.tv',
            # Yalla Shoot (جميع النطاقات)
            'https://www.yallashoot.com',
            'https://www.yallashoot-live.com',
            'https://www.yallashoot-new.com',
            'https://www.yallashoot-pro.com',
            'https://www.yallashoot-plus.com',
            'https://www.yallashoot-online.com',
            'https://www.yallashoot-tv.com',
            'https://www.yallashoot.net',
            'https://www.yallashootlivetv.com',
            # General Pro (جميع النطاقات)
            'https://generalpro.app',
            'https://generalpro.tv',
            'https://generalpro.live',
            'https://generalprosports.com',
            'https://generalprofootball.com',
            'https://generalproapk.com',
            'https://generalprohd.com',
            'https://generalproplus.com',
            'https://generalprostream.com',
            'https://generalpromatch.com',
            # Koora Live
            'https://www.koralive.com',
            'https://www.kooorastar.com',
            # BeIN Match
            'https://www.beinmatch.com',
            # Sport Plus
            'https://sportplustv.com',
            'https://livefootballtv.com',
        ]
        
        # ============================================================
        # 📡 3. قنوات تليجرام
        # ============================================================
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB', 'iptv_m3u',
            'm3u8_live', 'iptv_channels', 'free_iptv',
            'iptv_playlist', 'm3u_streams', 'iptv_m3u8',
        ]
        
        # ============================================================
        # 📡 4. منصات رسمية
        # ============================================================
        self.official_sites = [
            'https://www.dazn.com',
            'https://www.tod.tv',
            'https://connect.beinsports.com',
            'https://www.skysports.com/watch',
            'https://www.espn.com/watch/',
            'https://www.bbc.co.uk/iplayer',
            'https://www.fifa.com/fifaplus/en',
            'https://www.sonyliv.com',
            'https://www.hotstar.com',
        ]
        
        # ============================================================
        # 🔍 إعدادات الجودة
        # ============================================================
        self.trusted_domains = [
            'amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv',
            'cloudfront.net', 'edgenextcdn.net', 'cdn3.wowza.com'
        ]
        
        logger.info(f"🔥 تم تهيئة الصياد المتكامل مع:")
        logger.info(f"  - {len(self.m3u_sources)} مصدر M3U")
        logger.info(f"  - {len(self.streaming_sites)} موقع بث مباشر")
        logger.info(f"  - {len(self.telegram_sources)} قناة تليجرام")
    
    # ============================================================
    # 🎯 الوظيفة الرئيسية
    # ============================================================
    
    async def hunt(self, channel_name, max_results=10):
        """الصيد المتكامل"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        start_time = time.time()
        all_links = []
        
        keywords = self._generate_keywords(channel_name)
        logger.info(f"📝 كلمات البحث: {keywords}")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 1. البحث في قوائم M3U
            tasks = [self._search_m3u(url, keywords) for url in self.m3u_sources[:15]]
            
            # 2. البحث في مواقع البث المباشر
            for site in self.streaming_sites[:10]:
                tasks.append(self._search_streaming_site(site, keywords))
            
            # 3. البحث في قنوات تليجرام
            for keyword in keywords[:3]:
                tasks.append(self._search_telegram(keyword))
            
            # 4. البحث في المنصات الرسمية
            for site in self.official_sites[:5]:
                tasks.append(self._search_official_site(site, keywords))
            
            # 5. البحث في محركات البحث
            tasks.append(self._search_web(keywords[0] if keywords else channel_name))
            
            # تنفيذ المهام بالتوازي
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    if result:
                        logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ خطأ: {str(result)[:50]}")
        
        # تنقية وترتيب
        unique_links = self._deduplicate(all_links)
        filtered_links = self._filter_by_keywords(unique_links, keywords)
        ranked_links = self._rank_links(filtered_links, channel_name)
        
        # اختبار سريع
        logger.info("🧪 جاري التحقق من الروابط...")
        validated = await self._quick_validate(ranked_links[:20])
        
        # اختيار أفضل النتائج
        final = self._select_best(validated, max_results)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 📡 1. البحث في قوائم M3U
    # ============================================================
    
    async def _search_m3u(self, url, keywords):
        try:
            if url in self.failed_links:
                return []
            
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self.failed_links.add(url)
                        return []
                    
                    content = await response.text()
                    links = []
                    
                    for keyword in keywords[:5]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
                    
                    return links
        except Exception as e:
            logger.debug(f"⚠️ خطأ في {url[:50]}: {e}")
            self.failed_links.add(url)
            return []
    
    # ============================================================
    # 🌐 2. البحث في مواقع البث المباشر
    # ============================================================
    
    async def _search_streaming_site(self, site, keywords):
        """البحث في موقع بث مباشر"""
        links = []
        try:
            for keyword in keywords[:3]:
                # محاولة البحث في الموقع
                search_url = f"{site}/search?q={quote_plus(keyword)}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # استخراج روابط M3U8
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            links.extend(matches)
                            
                            # استخراج روابط iframes
                            iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\']'
                            iframes = re.findall(iframe_pattern, content, re.IGNORECASE)
                            for iframe in iframes:
                                if iframe.startswith('//'):
                                    iframe = 'https:' + iframe
                                if iframe.startswith('/'):
                                    iframe = urljoin(site, iframe)
                                # جلب محتوى الإطار
                                iframe_links = await self._fetch_iframe(iframe, keywords)
                                links.extend(iframe_links)
        except Exception as e:
            logger.debug(f"⚠️ خطأ في {site}: {e}")
        return links
    
    async def _fetch_iframe(self, iframe_url, keywords):
        """جلب محتوى iframe واستخراج الروابط"""
        links = []
        try:
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(iframe_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
        except:
            pass
        return links
    
    # ============================================================
    # 📡 3. البحث في المنصات الرسمية
    # ============================================================
    
    async def _search_official_site(self, site, keywords):
        """البحث في المنصات الرسمية"""
        links = []
        try:
            for keyword in keywords[:2]:
                search_url = f"{site}/search?q={quote_plus(keyword)}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(search_url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            links.extend(matches)
        except:
            pass
        return links
    
    # ============================================================
    # 📡 4. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram(self, keyword):
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
                                if keyword.lower().replace(' ', '') in link.lower().replace(' ', ''):
                                    links.append(link)
            except:
                pass
        return links
    
    # ============================================================
    # 🌐 5. البحث في محركات البحث
    # ============================================================
    
    async def _search_web(self, keyword):
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                loop = asyncio.get_event_loop()
                queries = [
                    f'"{keyword}" m3u8 live',
                    f'"{keyword}" iptv',
                ]
                tasks = [
                    loop.run_in_executor(executor, self._search_google, q)
                    for q in queries
                ]
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
            for url in search(query, num_results=3):
                if '.m3u8' in url or '.m3u' in url:
                    links.append(url)
            return links
        except:
            return []
    
    # ============================================================
    # 🧪 6. اختبار سريع للروابط
    # ============================================================
    
    async def _quick_validate(self, links):
        valid = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for link in links:
                if link in self.failed_links:
                    continue
                try:
                    headers = self._get_headers()
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301]:
                            valid.append(link)
                            logger.info(f"✅ صالح: {link[:40]}...")
                        elif response.status == 403:
                            valid.append(link)
                            logger.info(f"⚠️ محجوب: {link[:40]}...")
                except:
                    pass
        return valid
    
    # ============================================================
    # 📊 7. ترتيب واختيار النتائج
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
    
    # ============================================================
    # 🧠 8. توليد كلمات البحث
    # ============================================================
    
    def _generate_keywords(self, channel_name):
        keywords = [channel_name]
        name = channel_name.lower().strip()
        
        no_numbers = re.sub(r'\d+', '', name).strip()
        if no_numbers and no_numbers != name:
            keywords.append(no_numbers)
        
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel']:
            if word in name:
                keywords.append(name.replace(word, '').strip())
        
        if 'mbc' in name:
            keywords.extend(['mbc1', 'mbc 1 hd', 'mbc one'])
        if 'bein' in name:
            keywords.extend(['beIN', 'beIN 1', 'beIN HD', 'beIN Sports'])
        if 'aljazeera' in name:
            keywords.extend(['al jazeera', 'aljazeera', 'الجزيرة'])
        if 'cnn' in name:
            keywords.extend(['CNN', 'cnn live'])
        if 'bbc' in name:
            keywords.extend(['BBC', 'bbc live'])
        
        return list(set(keywords))[:8]
    
    def _filter_by_keywords(self, links, keywords):
        filtered = []
        for link in links:
            link_lower = link.lower()
            for keyword in keywords:
                if keyword.lower().replace(' ', '') in link_lower.replace(' ', ''):
                    filtered.append(link)
                    break
        return filtered
    
    # ============================================================
    # 🛠️ 9. دوال مساعدة
    # ============================================================
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
