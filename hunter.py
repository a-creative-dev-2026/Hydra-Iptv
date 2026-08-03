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

class SiteHunter:
    """
    صياد المواقع - يستخرج روابط البث مباشرة من الصفحات
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=20)
        self.session = None
        self.semaphore = asyncio.Semaphore(20)
        self.failed_links = set()
        
        # رؤوس المتصفح لتجنب الحجب
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # ============================================================
        # 🌐 مواقع البث المباشر (التي أرسلتها)
        # ============================================================
        self.streaming_sites = {
            # Yacine TV
            'yacinetv': {
                'domains': ['yacinetv.com', 'yacinetv.live'],
                'type': 'yacine',
                'search_url': 'https://yacinetv.com/search?q={query}',
            },
            # Ostora TV
            'ostora': {
                'domains': ['ostora.tv'],
                'type': 'ostora',
                'search_url': 'https://ostora.tv/search?q={query}',
            },
            # Yalla Shoot
            'yallashoot': {
                'domains': ['yallashoot.com', 'yallashoot-live.com', 'yallashoot-new.com', 
                           'yallashoot-pro.com', 'yallashoot-plus.com', 'yallashoot-online.com',
                           'yallashoot-tv.com', 'yallashoot.net', 'yallashootlivetv.com'],
                'type': 'yalla',
                'search_url': 'https://www.yallashoot.com/search?q={query}',
            },
            # General Pro
            'generalpro': {
                'domains': ['generalpro.app', 'generalpro.tv', 'generalpro.live', 
                           'generalprosports.com', 'generalprofootball.com'],
                'type': 'general',
                'search_url': 'https://generalpro.app/search?q={query}',
            },
            # Koora Live
            'koora': {
                'domains': ['koralive.com', 'kooorastar.com'],
                'type': 'koora',
                'search_url': 'https://www.koralive.com/search?q={query}',
            },
            # BeIN Match
            'beinmatch': {
                'domains': ['beinmatch.com'],
                'type': 'beinmatch',
                'search_url': 'https://www.beinmatch.com/search?q={query}',
            },
            # Sport Plus
            'sportplus': {
                'domains': ['sportplustv.com', 'livefootballtv.com'],
                'type': 'sportplus',
                'search_url': 'https://sportplustv.com/search?q={query}',
            },
        }
        
        # ============================================================
        # 🔥 قوائم M3U (مصادر إضافية)
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
            'https://raw.githubusercontent.com/Kodi-n-Playlist/iptv/main/playlist.m3u',
        ]
        
        # ============================================================
        # 📡 قنوات تليجرام
        # ============================================================
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB', 'iptv_m3u',
            'm3u8_live', 'iptv_channels', 'free_iptv',
            'iptv_playlist', 'm3u_streams', 'iptv_m3u8',
        ]
        
        logger.info(f"🔥 تم تهيئة صياد المواقع مع {len(self.streaming_sites)} موقعاً")
    
    # ============================================================
    # 🎯 الوظيفة الرئيسية
    # ============================================================
    
    async def hunt(self, channel_name, max_results=10):
        """الصيد الشامل - استخراج الروابط من المواقع"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        start_time = time.time()
        all_links = []
        
        # توليد كلمات البحث
        keywords = self._generate_keywords(channel_name)
        logger.info(f"📝 كلمات البحث: {keywords}")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 1. البحث في قوائم M3U
            tasks = [self._search_m3u(url, keywords) for url in self.m3u_sources[:8]]
            
            # 2. البحث في تليجرام
            for keyword in keywords[:3]:
                tasks.append(self._search_telegram(keyword))
            
            # 3. 🔥 البحث في المواقع (الجزء الأهم)
            for site_name, site_info in self.streaming_sites.items():
                for keyword in keywords[:3]:
                    tasks.append(self._search_site(site_info, keyword))
            
            # تنفيذ المهام بالتوازي
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ خطأ: {str(result)[:50]}")
        
        # 4. تنقية وترتيب
        unique_links = self._deduplicate(all_links)
        filtered_links = self._filter_by_keywords(unique_links, keywords)
        ranked_links = self._rank_links(filtered_links, channel_name)
        
        # 5. اختبار سريع (HEAD فقط لتسريع العملية)
        logger.info("🧪 جاري التحقق من الروابط...")
        validated = await self._quick_validate(ranked_links[:20])
        
        # 6. اختيار أفضل النتائج
        final = self._select_best(validated, max_results)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 🌐 1. البحث في موقع معين (استخراج الروابط)
    # ============================================================
    
    async def _search_site(self, site_info, keyword):
        """البحث في موقع معين واستخراج روابط البث"""
        links = []
        try:
            # جرب جميع النطاقات المرتبطة بالموقع
            for domain in site_info['domains']:
                try:
                    # 1. جلب صفحة البحث
                    search_url = site_info['search_url'].format(query=quote_plus(keyword))
                    headers = self._get_headers()
                    
                    async with self.semaphore:
                        async with self.session.get(search_url, headers=headers) as response:
                            if response.status != 200:
                                continue
                            
                            content = await response.text()
                            
                            # 2. استخراج الروابط حسب نوع الموقع
                            site_type = site_info['type']
                            
                            if site_type == 'yacine':
                                links.extend(await self._extract_yacine(content))
                            elif site_type == 'ostora':
                                links.extend(await self._extract_ostora(content))
                            elif site_type == 'yalla':
                                links.extend(await self._extract_yalla(content))
                            elif site_type == 'general':
                                links.extend(await self._extract_general(content))
                            elif site_type == 'koora':
                                links.extend(await self._extract_koora(content))
                            elif site_type == 'beinmatch':
                                links.extend(await self._extract_beIN(content))
                            elif site_type == 'sportplus':
                                links.extend(await self._extract_sportplus(content))
                            else:
                                # استخراج عام (لأي موقع)
                                links.extend(await self._extract_generic(content))
                            
                            # 3. إذا لم نجد روابط، حاول البحث عن iframes
                            if not links:
                                iframe_links = await self._extract_iframes(content)
                                for iframe_url in iframe_links:
                                    # جلب محتوى الإطار
                                    async with self.semaphore:
                                        async with self.session.get(iframe_url, headers=headers) as iframe_response:
                                            if iframe_response.status == 200:
                                                iframe_content = await iframe_response.text()
                                                links.extend(await self._extract_generic(iframe_content))
                except Exception as e:
                    logger.debug(f"⚠️ خطأ في {domain}: {e}")
                    continue
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في الموقع: {e}")
        
        return links
    
    # ============================================================
    # 📄 2. دوال استخراج خاصة بكل موقع
    # ============================================================
    
    async def _extract_yacine(self, content):
        """استخراج روابط من Yacine TV"""
        links = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # البحث عن روابط البث في الصفحة
        for script in soup.find_all('script'):
            if script.string:
                # البحث عن روابط M3U8 في JavaScript
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                links.extend(matches)
        
        # البحث في الروابط العادية
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.m3u8' in href:
                links.append(href)
        
        return links
    
    async def _extract_ostora(self, content):
        """استخراج روابط من Ostora TV"""
        # Ostora يستخدم نفس نمط Yacine
        return await self._extract_yacine(content)
    
    async def _extract_yalla(self, content):
        """استخراج روابط من Yalla Shoot"""
        links = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Yalla Shoot يضع البث في iframes غالباً
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if src:
                links.append(src)
        
        # البحث عن روابط مباشرة
        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        links.extend(matches)
        
        return links
    
    async def _extract_general(self, content):
        """استخراج روابط من General Pro"""
        return await self._extract_yalla(content)
    
    async def _extract_koora(self, content):
        """استخراج روابط من Koora Live"""
        links = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # البحث عن روابط البث المضمنة
        for script in soup.find_all('script'):
            if script.string:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                links.extend(matches)
        
        # البحث في iframes
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if src and 'm3u8' in src:
                links.append(src)
        
        return links
    
    async def _extract_beIN(self, content):
        """استخراج روابط من BeIN Match"""
        # BeIN Match قد يحتوي على روابط مشفرة
        return await self._extract_generic(content)
    
    async def _extract_sportplus(self, content):
        """استخراج روابط من Sport Plus"""
        return await self._extract_generic(content)
    
    async def _extract_generic(self, content):
        """استخراج روابط من أي صفحة"""
        links = []
        # البحث عن روابط M3U8
        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        links.extend(matches)
        
        # البحث عن روابط بث أخرى
        pattern2 = r'(https?://[^\s"\']+\.m3u[^\s"\']*)'
        matches2 = re.findall(pattern2, content, re.IGNORECASE)
        links.extend(matches2)
        
        return links
    
    async def _extract_iframes(self, content):
        """استخراج روابط iframes من الصفحة"""
        soup = BeautifulSoup(content, 'html.parser')
        iframes = []
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if src:
                # تأكد من أن الرابط كامل
                if src.startswith('//'):
                    src = 'https:' + src
                if src.startswith('/'):
                    src = urljoin('https://' + self._get_domain(content), src)
                iframes.append(src)
        return iframes
    
    def _get_domain(self, content):
        """استخراج النطاق من المحتوى (مساعدة)"""
        # محاولة استخراج النطاق من المحتوى
        match = re.search(r'https?://([^/]+)', content)
        if match:
            return match.group(1)
        return 'example.com'
    
    # ============================================================
    # 📡 3. البحث في قوائم M3U
    # ============================================================
    
    async def _search_m3u(self, url, keywords):
        """البحث في قائمة M3U"""
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
    # 📡 4. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram(self, keyword):
        """البحث في قنوات تليجرام"""
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
    # 🧪 5. اختبار سريع للروابط
    # ============================================================
    
    async def _quick_validate(self, links):
        """اختبار سريع باستخدام HEAD"""
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
                            logger.info(f"⚠️ محجوب (قد يعمل): {link[:40]}...")
                except:
                    pass
        return valid
    
    # ============================================================
    # 📊 6. ترتيب النتائج واختيار الأفضل
    # ============================================================
    
    def _rank_links(self, links, query):
        """ترتيب حسب الجودة والمصدر"""
        scored = []
        query_lower = query.lower()
        quality_map = {'fhd': 10, '1080p': 10, '4k': 10, 'hd': 8, '720p': 8, 'sd': 5}
        trusted = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            for key, val in quality_map.items():
                if key in link_lower:
                    score += val
                    break
            for domain in trusted:
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
    # 🧠 7. توليد كلمات البحث الذكية
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
    # 🛠️ 8. دوال مساعدة
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
