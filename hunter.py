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

class SmartHunter:
    """
    صياد ذكي متعدد الطبقات
    - يبحث في مصادر مخصصة (ترسلها أنت)
    - يستخرج الروابط من الصفحات والقوائم
    - يبحث بعمق في الطبقات الفرعية
    - يختبر الروابط بثلاث طرق
    """
    
    def __init__(self, custom_sources=None):
        """
        custom_sources: قائمة بروابط (قوائم M3U، صفحات، ملفات) تريد البحث فيها
        """
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.session = None
        self.semaphore = asyncio.Semaphore(20)  # 20 طلب متزامن
        
        # مصادر ثابتة (افتراضية)
        self.default_sources = [
            'https://iptv-org.github.io/iptv/index.m3u',
            'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u',
            'https://romaxa55.github.io/world_ip_tv/output/index.m3u',
        ]
        
        # دمج المصادر المخصصة مع الافتراضية
        self.sources = list(set((custom_sources or []) + self.default_sources))
        
        # قنوات تليجرام (للبحث السريع)
        self.telegram_sources = [
            'iptv_links', 'm3u8_files', 'beIN_Sports_links',
            'live_tv_channels', 'IPTV442WEB'
        ]
        
        # الكلمات المفتاحية الذكية
        self.keywords_pool = {}
        
        logger.info(f"🔧 تم تهيئة الصياد الذكي مع {len(self.sources)} مصدراً")
    
    # ============================================================
    # 🎯 الوظيفة الرئيسية
    # ============================================================
    
    async def hunt(self, channel_name, max_results=10, deep_level=2):
        """
        البحث العميق عن القناة
        - channel_name: اسم القناة
        - max_results: الحد الأقصى للنتائج
        - deep_level: عدد طبقات البحث (1 = سطحي، 2 = معمق)
        """
        logger.info(f"🔍 بدء الصيد العميق عن: {channel_name}")
        start_time = time.time()
        
        # 1. توليد كلمات بحث ذكية
        keywords = self._generate_keywords(channel_name)
        logger.info(f"📝 كلمات البحث: {keywords}")
        
        all_links = []
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # 2. البحث في المصادر (طبقة أولى)
            tasks = []
            for url in self.sources:
                tasks.append(self._search_source(url, keywords, deep_level))
            
            # 3. البحث في تليجرام
            for keyword in keywords[:3]:
                tasks.append(self._search_telegram(keyword))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_links.extend(result)
        
        # 4. تنقية وترتيب
        unique_links = self._deduplicate(all_links)
        ranked_links = self._rank_links(unique_links, channel_name)
        
        # 5. اختبار عميق (ثلاث طرق)
        logger.info("🧪 جاري الاختبار العميق للروابط...")
        validated = await self._deep_validate(ranked_links[:20])
        
        # 6. اختيار أفضل النتائج
        final = self._select_best(validated, max_results)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ تم العثور على {len(final)} رابط صالح في {elapsed:.2f} ثانية")
        return final
    
    # ============================================================
    # 🔍 1. البحث في مصدر معين (مع إمكانية التعمق)
    # ============================================================
    
    async def _search_source(self, url, keywords, deep_level):
        """البحث في مصدر واحد (قائمة أو صفحة)"""
        try:
            headers = self._get_headers()
            async with self.semaphore:
                async with self.session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return []
                    
                    content = await response.text()
                    links = []
                    
                    # استخراج الروابط المباشرة
                    for keyword in keywords[:4]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        links.extend(matches)
                    
                    # استخراج روابط M3U8 من الصفحة (حتى لو لم تكن في قائمة)
                    if not links and deep_level > 1:
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        # تصفية حسب الكلمات المفتاحية
                        for match in matches:
                            for keyword in keywords:
                                if keyword.lower().replace(' ', '') in match.lower().replace(' ', ''):
                                    links.append(match)
                                    break
                    
                    # إذا كان المستوى أعمق، حاول استخراج روابط فرعية
                    if deep_level > 1 and not links:
                        # استخراج جميع الروابط من الصفحة
                        all_urls = re.findall(r'(https?://[^\s"\']+)', content)
                        # اختر 5 روابط عشوائية للبحث فيها (تجنب التكرار)
                        import random
                        for sub_url in random.sample(all_urls, min(5, len(all_urls))):
                            if sub_url != url and 'm3u' in sub_url.lower():
                                sub_links = await self._search_source(sub_url, keywords, deep_level-1)
                                if sub_links:
                                    links.extend(sub_links)
                    
                    return links
        except Exception as e:
            logger.debug(f"⚠️ خطأ في {url[:50]}: {e}")
            return []
    
    # ============================================================
    # 📡 2. البحث في تليجرام
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
    # 🧠 3. توليد كلمات بحث ذكية
    # ============================================================
    
    def _generate_keywords(self, channel_name):
        """توليد كلمات بحث متعددة (إنجليزية، عربية، مرادفات)"""
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
        
        # أسماء بديلة معروفة
        if 'mbc' in name:
            keywords.extend(['mbc1', 'mbc 1 hd', 'mbc one'])
        if 'bein' in name:
            keywords.extend(['beIN', 'beIN 1', 'beIN HD', 'beIN Sports'])
        if 'aljazeera' in name or 'الجزيرة' in name:
            keywords.extend(['al jazeera', 'aljazeera', 'الجزيرة'])
        if 'cnn' in name:
            keywords.extend(['CNN', 'cnn live', 'cable news network'])
        
        # ترجمة عربية (إذا كانت إنجليزية)
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
        
        # إزالة التكرار
        return list(set(keywords))[:8]
    
    # ============================================================
    # 🧪 4. اختبار عميق (ثلاث طرق)
    # ============================================================
    
    async def _deep_validate(self, links):
        """اختبار الروابط بثلاث طرق: HEAD، Range، تحميل جزئي"""
        valid = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            for link in links:
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
                                # محجوب لكن قد يعمل
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
                    
                    # 3. اختبار GET عادي مع مهلة قصيرة
                    try:
                        async with session.get(link, headers=headers, timeout=3) as resp:
                            if resp.status in [200, 206]:
                                valid.append(link)
                                logger.info(f"✅ صالح (GET): {link[:40]}...")
                    except:
                        pass
                        
                except Exception as e:
                    logger.debug(f"❌ فشل: {link[:40]}... - {str(e)[:20]}")
                    continue
        
        return valid
    
    # ============================================================
    # 📊 5. ترتيب النتائج واختيار الأفضل
    # ============================================================
    
    def _rank_links(self, links, query):
        """ترتيب حسب الجودة والمصدر"""
        scored = []
        query_lower = query.lower()
        
        # معايير الجودة
        quality_map = {
            'fhd': 10, '1080p': 10, '4k': 10,
            'hd': 8, '720p': 8,
            'sd': 5, '480p': 5,
        }
        
        trusted_domains = [
            'amagi.tv', 'akamaized.net', 'streamlock.net',
            'sofast.tv', 'cloudfront.net', 'edgenextcdn.net'
        ]
        
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # الجودة
            for key, val in quality_map.items():
                if key in link_lower:
                    score += val
                    break
            
            # المصادر الموثوقة
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 10
                    break
            
            # تطابق الاسم
            if query_lower in link_lower:
                score += 8
            
            # HTTPS
            if link.startswith('https://'):
                score += 3
            
            scored.append((score, link))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [link for _, link in scored]
    
    def _select_best(self, links, max_results):
        """اختيار أفضل النتائج مع تنوع المصادر"""
        if len(links) <= max_results:
            return links
        
        # تنويع المصادر (لا نأخذ كل الروابط من نفس المصدر)
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
    # 🛠️ 6. دوال مساعدة
    # ============================================================
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
