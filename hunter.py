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
    """صياد الروابط المتطور - أسرع، أوسع، أكثر دقة"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.session = None
        self.semaphore = asyncio.Semaphore(20)  # للتحكم في عدد الطلبات المتزامنة
        
        # وكلاء User-Agent متنوعون
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        
        # 🔥 مصادر جديدة للبحث (مواقع بث، منتديات، مستودعات)
        self.sources = {
            'iptv_org': 'https://iptv-org.github.io/iptv/index.m3u',
            'iptv_org_nsfw': 'https://iptv-org.github.io/iptv/index.nsfw.m3u',
            'free_tv': 'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'iptv_hub': 'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'world_iptv': 'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
            'iptv_github': 'https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u',
        }
        
        # قنوات تليجرام
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB', 'iptv_m3u',
            'm3u8_live', 'iptv_channels', 'free_iptv',
            'iptv_playlist', 'm3u_streams'
        ]
        
        # 🔥 مواقع بث مباشر (جديدة)
        self.streaming_sites = [
            'https://pastebin.com',
            'https://telegra.ph',
            'https://t.me',
            'https://github.com',
            'https://www.reddit.com/r/IPTV',
            'https://www.reddit.com/r/m3u8',
            'https://www.reddit.com/r/FreeIPTV',
            'https://www.reddit.com/r/IPTVpro',
            'https://www.reddit.com/r/IPTVreviews',
        ]
    
    async def hunt(self, channel_name, max_results=20):
        """الصيد الرئيسي - سريع ودقيق"""
        logger.info(f"🔍 بدء الصيد عن: {channel_name}")
        all_links = []
        start_time = time.time()
        
        # توليد أسماء بديلة
        variants = self._generate_variants(channel_name)
        logger.info(f"📝 عدد المتغيرات: {len(variants)}")
        
        # 🔥 البحث في المصادر مع Semaphore للتحكم في التوازي
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 1. البحث في القوائم الرئيسية (أسرع)
            list_tasks = [
                self._fetch_playlist(url, variants[:3])
                for url in self.sources.values()
            ]
            
            # 2. البحث في الويب (أوسع)
            web_tasks = [
                self._search_web(variant) for variant in variants[:2]
            ]
            
            # 3. البحث في تليجرام
            telegram_tasks = [
                self._search_telegram(variant) for variant in variants[:2]
            ]
            
            # 4. البحث في مواقع البث
            stream_tasks = [
                self._search_streaming_sites(variant) for variant in variants[:2]
            ]
            
            # تنفيذ جميع المهام بالتوازي
            all_results = await asyncio.gather(
                *list_tasks,
                *web_tasks,
                *telegram_tasks,
                *stream_tasks,
                return_exceptions=True
            )
            
            # جمع النتائج
            for result in all_results:
                if isinstance(result, list):
                    all_links.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ خطأ: {str(result)[:50]}")
        
        # 5. إذا لم نجد نتائج كافية، استخدم Fuzzy Search
        if len(all_links) < 5:
            logger.info("🔄 جاري البحث الضبابي (Fuzzy Search)...")
            fuzzy_links = await self._fuzzy_search(channel_name)
            if fuzzy_links:
                all_links.extend(fuzzy_links)
        
        # 6. تصفية وترتيب النتائج
        unique_links = self._deduplicate(all_links)
        ranked_links = self._rank_by_quality(unique_links, channel_name)
        
        # 7. 🔥 اختبار سريع وفعال للروابط
        logger.info("🧪 جاري اختبار الروابط (فحص سريع)...")
        valid_links = await self._quick_validate(ranked_links[:20])
        
        # 8. 🔥 ضمان الجودة: اختيار أفضل 5 روابط مع جودات مختلفة
        final_links = self._select_best_quality(valid_links, channel_name)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final_links)} رابط صالح في {elapsed:.2f} ثانية")
        return final_links[:max_results]
    
    # ============================================================
    # 🔥 1. جلب القوائم الرئيسية (أسرع مصدر)
    # ============================================================
    
    async def _fetch_playlist(self, url, variants):
        """جلب قائمة M3U والبحث فيها"""
        try:
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._extract_links(content, variants)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في {url[:50]}: {e}")
        return []
    
    def _extract_links(self, content, variants):
        """استخراج الروابط من محتوى M3U"""
        links = []
        for variant in variants:
            pattern = rf'#EXTINF:.*,.*{re.escape(variant)}.*\n(https?://[^\s]+)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            links.extend(matches)
        return links
    
    # ============================================================
    # 🔥 2. البحث في الويب (أوسع)
    # ============================================================
    
    async def _search_web(self, query):
        """البحث في الويب"""
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                loop = asyncio.get_event_loop()
                search_queries = [
                    f'"{query}" m3u8 live',
                    f'"{query}" iptv link',
                    f'"{query}" stream',
                ]
                tasks = [
                    loop.run_in_executor(executor, self._search_google, q)
                    for q in search_queries
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
                                if query.lower().replace(' ', '') in link.lower().replace(' ', ''):
                                    links.append(link)
                            if links:
                                logger.info(f"✅ روابط من قناة {channel}")
            except:
                pass
        return links
    
    # ============================================================
    # 🔥 4. البحث في مواقع البث (جديد)
    # ============================================================
    
    async def _search_streaming_sites(self, query):
        """البحث في مواقع البث المتخصصة"""
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
                                logger.info(f"✅ روابط من {site[:30]}")
            except:
                pass
        return links
    
    # ============================================================
    # 🔥 5. البحث الضبابي (Fuzzy Search)
    # ============================================================
    
    async def _fuzzy_search(self, channel_name):
        """بحث ضبابي للعثور على تطابقات قريبة"""
        try:
            url = "https://iptv-org.github.io/iptv/index.m3u"
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        names = re.findall(r'#EXTINF:.*,([^\n]+)', content)
                        matches = process.extract(channel_name, names, scorer=fuzz.ratio, limit=25)
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
    # 🔥 6. اختبار سريع وفعال للروابط
    # ============================================================
    
    async def _quick_validate(self, links):
        """اختبار سريع باستخدام HEAD فقط لتسريع العملية"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for link in links:
                try:
                    headers = self._get_headers()
                    async with session.head(link, headers=headers, allow_redirects=True) as response:
                        if response.status in [200, 206, 302, 301]:
                            valid.append(link)
                            logger.debug(f"✅ صالح: {link[:40]}...")
                        elif response.status == 403:
                            # 403 قد يكون حجباً جغرافياً، نحتفظ به كخيار
                            valid.append(link)
                            logger.debug(f"⚠️ محجوب: {link[:40]}...")
                except:
                    # حتى لو فشل HEAD، قد يكون الرابط صالحاً
                    if '.m3u8' in link:
                        valid.append(link)
        
        return valid
    
    # ============================================================
    # 🔥 7. اختيار أفضل الروابط حسب الجودة
    # ============================================================
    
    def _select_best_quality(self, links, channel_name):
        """اختيار 5 روابط بأعلى جودة"""
        quality_map = {
            'fhd': 5, '1080p': 5, '4k': 5,
            'hd': 4, '720p': 4,
            'sd': 3, '480p': 3,
            'low': 2, '360p': 2,
        }
        
        scored = []
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # جودة عالية
            for key, value in quality_map.items():
                if key in link_lower:
                    score += value
                    break
            
            # مصادر موثوقة
            trusted = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
            for domain in trusted:
                if domain in link_lower:
                    score += 3
            
            # HTTPS
            if link.startswith('https://'):
                score += 2
            
            scored.append((score, link))
        
        # ترتيب تنازلي
        scored.sort(reverse=True, key=lambda x: x[0])
        selected = [link for _, link in scored]
        
        # 🔥 إرجاع 5 روابط على الأقل (مع تنوع في الجودة)
        if len(selected) < 5:
            # إذا كان عدد الروابط أقل من 5، نعيد كل ما وجد
            return selected
        
        # اختيار أفضل 5 مع تنوع
        final = []
        # أولاً: أفضل رابطين
        final.extend(selected[:2])
        # ثانياً: روابط من مصادر مختلفة (تنوع)
        seen_domains = set()
        for link in selected[2:]:
            domain = link.split('/')[2] if len(link.split('/')) > 2 else ''
            if domain not in seen_domains:
                final.append(link)
                seen_domains.add(domain)
            if len(final) >= 5:
                break
        
        return final
    
    # ============================================================
    # 🔥 8. تصنيف الروابط حسب الجودة
    # ============================================================
    
    def _rank_by_quality(self, links, query):
        """ترتيب الروابط حسب الجودة والأهمية"""
        scored = []
        query_lower = query.lower()
        trusted_domains = ['amagi.tv', 'akamaized.net', 'streamlock.net', 'sofast.tv', 'cloudfront.net', 'edgenextcdn.net']
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # جودة
            for quality in ['fhd', '1080p', 'hd', '720p']:
                if quality in link_lower:
                    score += 5
            
            # مصادر موثوقة
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 10
            
            # تطابق مع الاستعلام
            if query_lower in link_lower:
                score += 8
            
            # HTTPS
            if link.startswith('https://'):
                score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for _, link in scored]
    
    # ============================================================
    # 🔥 9. دوال مساعدة
    # ============================================================
    
    def _generate_variants(self, channel_name):
        """توليد أسماء بديلة للقناة"""
        variants = [channel_name]
        name = channel_name.lower().strip()
        
        # إزالة الأرقام
        no_numbers = re.sub(r'\d+', '', name).strip()
        if no_numbers and no_numbers != name:
            variants.append(no_numbers)
        
        # إزالة الكلمات الإضافية
        for word in ['hd', 'fhd', 'uhd', '4k', 'tv', 'channel']:
            if word in name:
                variants.append(name.replace(word, '').strip())
        
        # أسماء بديلة معروفة
        if 'mbc' in name:
            variants.extend(['mbc1', 'mbc 1 hd', 'mbc one'])
        if 'bein' in name:
            variants.extend(['beIN', 'beIN 1', 'beIN HD'])
        
        return list(set(variants))[:5]  # حد أقصى 5 متغيرات
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
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
