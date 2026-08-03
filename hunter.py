import asyncio
import aiohttp
import re
import time
import random
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor
import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class MegaHunter:
    """
    الصياد الشامل - يبحث في كل مكان
    - قوائم M3U (أكثر من 30 مصدراً)
    - تليجرام (أكثر من 20 قناة)
    - منتديات Reddit
    - محركات البحث (Google, DuckDuckGo, Bing)
    - خدمات مشاركة النصوص (Pastebin, Telegra.ph)
    - توليد روابط بديلة
    - اختبار عميق بثلاث طرق
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.session = None
        self.semaphore = asyncio.Semaphore(30)
        self.failed_links = set()
        
        # ============================================================
        # 🔥 المصادر الأساسية (قوائم M3U حقيقية - محدثة)
        # ============================================================
        self.m3u_sources = [
            # المصادر الرئيسية (قد تعمل أو لا، لكننا نجربها)
            'https://iptv-org.github.io/iptv/index.m3u',
            'https://iptv-org.github.io/iptv/index.nsfw.m3u',
            'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
            # مصادر بديلة (تعمل غالباً)
            'https://raw.githubusercontent.com/ismailozgul/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/mhdzumair/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/jaydenmb/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/emirbey/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/matthew1981/m3u/main/playlist.m3u',
            'https://raw.githubusercontent.com/azenv/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/Kodi-n-Playlist/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/kayleekay/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/samirsam/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u',
            # مصادر جديدة (من مشاريع أخرى)
            'https://raw.githubusercontent.com/billybonk/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/kingy444/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/MikiBzh/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/sn7696/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/LaVieEnCode/IPTV/main/playlist.m3u',
            'https://raw.githubusercontent.com/nikooo777/iptv/main/playlist.m3u',
            'https://raw.githubusercontent.com/junguler/m3u/main/playlist.m3u',
            'https://raw.githubusercontent.com/matthuisman/iptv/main/playlist.m3u',
        ]
        
        # ============================================================
        # 📡 قنوات تليجرام (مصادر حقيقية)
        # ============================================================
        self.telegram_sources = [
            'iptv_links',
            'm3u8_files',
            'beIN_Sports_links',
            'live_tv_channels',
            'IPTV442WEB',
            'iptv_m3u',
            'm3u8_live',
            'iptv_channels',
            'free_iptv',
            'iptv_playlist',
            'm3u_streams',
            'iptv_m3u8',
            'iptv_world',
            'iptv_links_4k',
            'm3u_links',
            'iptv_plus',
            'iptv_hd',
            'iptv_4k',
            'iptv_arabic',
            'iptv_sports',
        ]
        
        # ============================================================
        # 🌐 منتديات Reddit (مصادر حقيقية)
        # ============================================================
        self.reddit_sources = [
            'IPTV',
            'm3u8',
            'FreeIPTV',
            'IPTVpro',
            'IPTVreviews',
            'IPTV_links',
            'IPTV_community',
            'IPTV_share',
            'IPTV_find',
        ]
        
        # ============================================================
        # 📝 خدمات مشاركة النصوص (مصادر حقيقية)
        # ============================================================
        self.paste_sources = [
            'https://pastebin.com',
            'https://telegra.ph',
            'https://t.me',
            'https://github.com',
            'https://gitlab.com',
            'https://bitbucket.org',
        ]
        
        # ============================================================
        # 🌐 مصادر البث المباشر (من القائمة التي أرسلتها)
        # ============================================================
        self.streaming_sites = [
            # Yacine TV
            'https://yacinetv.com',
            'https://yacinetv.live',
            # Ostora TV
            'https://ostora.tv',
            # Yalla Shoot
            'https://www.yallashoot.com',
            'https://www.yallashoot-live.com',
            'https://www.yallashoot-new.com',
            'https://www.yallashoot-pro.com',
            'https://www.yallashoot-plus.com',
            'https://www.yallashoot-online.com',
            'https://www.yallashoot-tv.com',
            'https://www.yallashoot.net',
            'https://www.yallashootlivetv.com',
            # General Pro
            'https://generalpro.app',
            'https://generalpro.tv',
            'https://generalpro.live',
            'https://generalprosports.com',
            'https://generalprofootball.com',
            # Sport Plus
            'https://sportplustv.com',
            'https://livefootballtv.com',
            # Koora Live
            'https://www.koralive.com',
            'https://www.kooorastar.com',
            # BeIN Match
            'https://www.beinmatch.com',
            # منصات رسمية
            'https://www.dazn.com',
            'https://www.tod.tv',
            'https://connect.beinsports.com',
            'https://www.skysports.com/watch',
            'https://www.espn.com/watch/',
            'https://www.bbc.co.uk/iplayer',
            'https://www.fifa.com/fifaplus/en',
            'https://www.sbs.com.au/ondemand',
            'https://www.sonyliv.com',
            'https://www.hotstar.com',
            'https://www.fubo.tv',
            'https://tv.youtube.com',
            'https://www.hulu.com/live-sports',
            'https://www.peacocktv.com',
            'https://www.foxsports.com',
            'https://www.livesoccertv.com',
            'https://www.wheresthematch.com',
            'https://play.stream2watch.com',
            'https://www.footybite.tv',
            'https://buffstreams.is',
            'https://www.vipleague.la',
            'https://www.viprow.nu',
        ]
        
        # ============================================================
        # 🔍 كلمات البحث (ذكية)
        # ============================================================
        self.quality_keywords = ['FHD', 'HD', 'SD', '1080p', '720p', '4k', 'UHD']
        self.trusted_domains = [
            'amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv',
            'cloudfront.net', 'edgenextcdn.net', 'cdn3.wowza.com'
        ]
        
        logger.info(f"🔥 تم تهيئة الصياد الشامل مع {len(self.m3u_sources)} مصدر M3U و {len(self.telegram_sources)} قناة تليجرام")
    
    # ============================================================
    # 🎯 الوظيفة الرئيسية
    # ============================================================
    
    async def hunt(self, channel_name, max_results=10):
        """الصيد الشامل عن القناة"""
        logger.info(f"🔍 بدء الصيد الشامل عن: {channel_name}")
        start_time = time.time()
        all_links = []
        
        # توليد كلمات البحث الذكية
        keywords = self._generate_keywords(channel_name)
        logger.info(f"📝 كلمات البحث: {keywords}")
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 1. البحث في قوائم M3U
            tasks = [self._search_m3u(url, keywords) for url in self.m3u_sources[:15]]
            
            # 2. البحث في تليجرام
            for keyword in keywords[:3]:
                tasks.append(self._search_telegram(keyword))
            
            # 3. البحث في Reddit
            for keyword in keywords[:2]:
                tasks.append(self._search_reddit(keyword))
            
            # 4. البحث في خدمات النصوص
            for keyword in keywords[:2]:
                tasks.append(self._search_paste(keyword))
            
            # 5. البحث في مواقع البث المباشر
            for site in self.streaming_sites[:10]:
                tasks.append(self._search_streaming_site(site, keywords))
            
            # 6. البحث في محركات البحث
            tasks.append(self._search_web(keywords[0] if keywords else channel_name))
            
            # 7. توليد روابط بديلة
            if keywords:
                tasks.append(self._generate_alternative_links(keywords[0]))
            
            # تنفيذ جميع المهام بالتوازي
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
                    logger.info(f"✅ تم العثور على {len(result)} رابط")
                elif isinstance(result, Exception):
                    logger.debug(f"⚠️ خطأ: {str(result)[:50]}")
        
        # 8. تنقية وترتيب
        unique_links = self._deduplicate(all_links)
        filtered_links = self._filter_by_keywords(unique_links, keywords)
        ranked_links = self._rank_links(filtered_links, channel_name)
        
        # 9. اختبار عميق (ثلاث طرق)
        logger.info("🧪 جاري الاختبار العميق للروابط...")
        validated = await self._deep_validate(ranked_links[:20])
        
        # 10. اختيار أفضل النتائج
        final = self._select_best(validated, max_results)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 📡 1. البحث في قوائم M3U
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
    # 📡 2. البحث في تليجرام
    # ============================================================
    
    async def _search_telegram(self, keyword):
        """البحث في قنوات تليجرام"""
        links = []
        for channel in self.telegram_sources[:5]:
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
    # 📡 3. البحث في Reddit
    # ============================================================
    
    async def _search_reddit(self, keyword):
        """البحث في منتديات Reddit"""
        links = []
        for subreddit in self.reddit_sources[:3]:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search/.json?q={quote_plus(keyword)}&restrict_sr=1"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for post in data.get('data', {}).get('children', []):
                                text = post.get('data', {}).get('selftext', '')
                                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                                matches = re.findall(pattern, text, re.IGNORECASE)
                                links.extend(matches)
            except:
                pass
        return links
    
    # ============================================================
    # 📡 4. البحث في خدمات النصوص
    # ============================================================
    
    async def _search_paste(self, keyword):
        """البحث في خدمات مشاركة النصوص"""
        links = []
        for site in self.paste_sources[:2]:
            try:
                url = f"{site}/search?q={quote_plus(keyword)}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            links.extend(matches)
            except:
                pass
        return links
    
    # ============================================================
    # 🌐 5. البحث في مواقع البث المباشر
    # ============================================================
    
    async def _search_streaming_site(self, site, keywords):
        """البحث في موقع بث مباشر"""
        links = []
        try:
            # جرب البحث في الموقع
            for keyword in keywords[:2]:
                url = f"{site}/search?q={quote_plus(keyword)}"
                headers = self._get_headers()
                async with self.semaphore:
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            # استخراج روابط M3U8
                            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            links.extend(matches)
                            
                            # استخراج روابط البث المضمنة (قد تكون في iframes أو src)
                            iframe_pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                            iframe_matches = re.findall(iframe_pattern, content, re.IGNORECASE)
                            links.extend(iframe_matches)
        except:
            pass
        return links
    
    # ============================================================
    # 🌐 6. البحث في محركات البحث
    # ============================================================
    
    async def _search_web(self, keyword):
        """البحث في محركات البحث"""
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                loop = asyncio.get_event_loop()
                queries = [
                    f'"{keyword}" m3u8 live',
                    f'"{keyword}" iptv link',
                    f'"{keyword}" stream'
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
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في الويب: {e}")
            return []
    
    def _search_google(self, query):
        """البحث في Google"""
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
    # 🔗 7. توليد روابط بديلة
    # ============================================================
    
    async def _generate_alternative_links(self, channel_name):
        """توليد روابط بديلة من نفس النطاق"""
        try:
            base_url = "https://iptv-org.github.io/iptv/index.m3u"
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(base_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        alternatives = []
                        for match in matches:
                            base = match.split('?')[0]
                            for quality in ['FHD', 'HD', 'SD']:
                                if quality.lower() not in base.lower():
                                    alt = f"{base}?quality={quality}"
                                    alternatives.append(alt)
                        return alternatives
        except:
            pass
        return []
    
    # ============================================================
    # 🧪 8. اختبار عميق (ثلاث طرق)
    # ============================================================
    
    async def _deep_validate(self, links):
        """اختبار الروابط بثلاث طرق"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as session:
            for link in links:
                if link in self.failed_links:
                    continue
                
                try:
                    headers = self._get_headers()
                    
                    # 1. اختبار HEAD
                    try:
                        async with session.head(link, headers=headers, allow_redirects=True) as resp:
                            if resp.status in [200, 206, 302, 301]:
                                valid.append(link)
                                logger.info(f"✅ صالح (HEAD): {link[:40]}...")
                                continue
                            elif resp.status == 403:
                                valid.append(link)
                                logger.info(f"⚠️ محجوب (قد يعمل): {link[:40]}...")
                                continue
                    except:
                        pass
                    
                    # 2. اختبار GET مع Range
                    try:
                        headers['Range'] = 'bytes=0-1024'
                        async with session.get(link, headers=headers, allow_redirects=True) as resp:
                            if resp.status in [200, 206]:
                                content = await resp.read()
                                if b'<html' not in content[:100] and b'<body' not in content[:100]:
                                    valid.append(link)
                                    logger.info(f"✅ صالح (Range): {link[:40]}...")
                                    continue
                    except:
                        pass
                    
                    # 3. اختبار GET عادي
                    try:
                        async with session.get(link, headers=headers, timeout=3) as resp:
                            if resp.status in [200, 206]:
                                valid.append(link)
                                logger.info(f"✅ صالح (GET): {link[:40]}...")
                    except:
                        pass
                        
                except Exception as e:
                    self.failed_links.add(link)
                    logger.debug(f"❌ فشل: {link[:40]}... - {str(e)[:20]}")
                    continue
        
        return valid
    
    # ============================================================
    # 📊 9. ترتيب النتائج واختيار الأفضل
    # ============================================================
    
    def _rank_links(self, links, query):
        """ترتيب حسب الجودة والمصدر"""
        scored = []
        query_lower = query.lower()
        
        quality_map = {
            'fhd': 10, '1080p': 10, '4k': 10,
            'hd': 8, '720p': 8,
            'sd': 5, '480p': 5,
        }
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            for key, val in quality_map.items():
                if key in link_lower:
                    score += val
                    break
            
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
        """اختيار أفضل النتائج مع تنوع المصادر"""
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
    # 🧠 10. توليد كلمات بحث ذكية
    # ============================================================
    
    def _generate_keywords(self, channel_name):
        """توليد كلمات بحث متعددة"""
        keywords = [channel_name]
        name = channel_name.lower().strip()
        
        no_numbers = re.sub(r'\d+', '', name).strip()
        if no_numbers and no_numbers != name:
            keywords.append(no_numbers)
        
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel']:
            if word in name:
                keywords.append(name.replace(word, '').strip())
        
        # أسماء بديلة معروفة
        if 'mbc' in name:
            keywords.extend(['mbc1', 'mbc 1 hd', 'mbc one', 'mbc 1 live'])
        if 'bein' in name:
            keywords.extend(['beIN', 'beIN 1', 'beIN HD', 'beIN Sports', 'beIN 1 HD'])
        if 'aljazeera' in name or 'الجزيرة' in name:
            keywords.extend(['al jazeera', 'aljazeera', 'الجزيرة', 'aljazeera live'])
        if 'cnn' in name:
            keywords.extend(['CNN', 'cnn live', 'cable news network', 'CNN HD'])
        if 'bbc' in name:
            keywords.extend(['BBC', 'bbc live', 'bbc news', 'BBC HD'])
        
        # ترجمة عربية
        arabic_map = {
            'mbc': 'ام بي سي',
            'bein': 'بي إن',
            'aljazeera': 'الجزيرة',
            'cnn': 'سي إن إن',
            'bbc': 'بي بي سي',
            'sky': 'سكاي',
        }
        for eng, arb in arabic_map.items():
            if eng in name:
                keywords.append(arb)
        
        return list(set(keywords))[:8]
    
    def _filter_by_keywords(self, links, keywords):
        """تصفية الروابط حسب الكلمات المفتاحية"""
        filtered = []
        for link in links:
            link_lower = link.lower()
            for keyword in keywords:
                if keyword.lower().replace(' ', '') in link_lower.replace(' ', ''):
                    filtered.append(link)
                    break
        return filtered
    
    # ============================================================
    # 🛠️ 11. دوال مساعدة
    # ============================================================
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]),
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
