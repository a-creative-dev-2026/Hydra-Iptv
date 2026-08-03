import re
import time
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from fake_useragent import UserAgent
from config import Config
import logging

logger = logging.getLogger(__name__)
ua = UserAgent()

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        self.telegram_client = None
        self._init_telegram()
        
        self.sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_world_iptv,
            self._search_iptv_hub,
            self._search_telegram_channels,
            self._search_web_engines,
            self._search_known_sites,
        ]
    
    def _init_telegram(self):
        try:
            if Config.TELEGRAM_API_ID and Config.TELEGRAM_API_HASH:
                self.telegram_client = TelegramClient(
                    'hydra_iptv_session',
                    Config.TELEGRAM_API_ID,
                    Config.TELEGRAM_API_HASH
                )
                logger.info("✅ تم تهيئة عميل تليجرام")
            else:
                logger.warning("⚠️ مفاتيح تليجرام غير متوفرة")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة تليجرام: {e}")
            self.telegram_client = None
    
    def search_channel(self, channel_name, country=None):
        """البحث الشامل عن قناة مع توسيع الكلمات المفتاحية"""
        logger.info(f"🔍 جاري البحث الشامل عن: {channel_name}")
        all_links = []
        
        # ✅ استخراج الكلمات المفتاحية من اسم القناة
        keywords = self._extract_keywords(channel_name)
        logger.info(f"🔑 الكلمات المفتاحية المستخرجة: {keywords}")
        
        # البحث باستخدام الكلمات المفتاحية
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(source_func, keywords): source_func.__name__
                for source_func in self.sources[:4]
            }
            for future in as_completed(futures):
                try:
                    links = future.result(timeout=20)
                    if links:
                        all_links.extend(links)
                        logger.info(f"✅ تم العثور على {len(links)} رابط من {futures[future]}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في المصدر {futures[future]}: {e}")
        
        # إذا لم تكن النتائج كافية، جرب المصادر المتبقية
        if len(all_links) < 5:
            for source_func in self.sources[4:]:
                try:
                    links = source_func(keywords)
                    if links:
                        all_links.extend(links)
                        logger.info(f"✅ تم العثور على {len(links)} رابط من {source_func.__name__}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في {source_func.__name__}: {e}")
        
        # ✅ تصفية الروابط حسب الصلة (ترتيب النتائج)
        filtered_links = self._filter_by_relevance(all_links, channel_name)
        
        unique_links = list(set(filtered_links))
        valid_links = self._validate_links(unique_links)
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============================================================
    # دالة استخراج الكلمات المفتاحية (الأساسية)
    # ============================================================
    
    def _extract_keywords(self, channel_name):
        """استخراج الكلمات المفتاحية من اسم القناة مع مرادفاتها"""
        keywords = []
        original = channel_name.lower().strip()
        
        # ✅ إضافة الكلمات الأساسية
        keywords.append(original)
        
        # ✅ إزالة الأرقام والرموز للحصول على الكلمة الجذرية
        base_name = re.sub(r'[^a-zA-Z\s]', '', original).strip()
        if base_name:
            keywords.append(base_name)
        
        # ✅ تقسيم إلى كلمات فردية
        words = original.split()
        for word in words:
            if len(word) > 2:  # تجاهل الكلمات القصيرة جداً
                keywords.append(word)
        
        # ✅ مرادفات للقنوات الشهيرة
        synonyms = {
            'bein': ['bein', 'be in', 'bein sports', 'beIN', 'beIN Sports'],
            'sports': ['sports', 'sport', 'sp'],
            'extra': ['extra', 'xtra'],
            'max': ['max', 'maximum'],
            'hd': ['hd', 'high definition'],
            'arabic': ['arabic', 'arab', 'ar'],
            'english': ['english', 'eng', 'en'],
            'french': ['french', 'fra', 'fr'],
            '1': ['1', 'one', '01'],
            '2': ['2', 'two', '02'],
            '3': ['3', 'three', '03'],
        }
        
        # ✅ إضافة المرادفات بناءً على الكلمات الموجودة
        for word in words:
            for key, syns in synonyms.items():
                if key in word or word in key:
                    keywords.extend(syns)
        
        # ✅ إزالة التكرار
        keywords = list(set(keywords))
        logger.info(f"🔑 الكلمات المفتاحية النهائية: {keywords}")
        return keywords
    
    # ============================================================
    # دالة تصفية النتائج حسب الصلة
    # ============================================================
    
    def _filter_by_relevance(self, links, original_query):
        """ترتيب النتائج حسب الصلة بالقناة المطلوبة"""
        if not links:
            return links
        
        # قائمة القنوات المطلوبة (جميع إصدارات beIN)
        target_variants = [
            'beIN Sports 1', 'beIN Sports 2', 'beIN Sports 3',
            'beIN Sports Extra', 'beIN Sports Max', 'beIN Sports Max 1',
            'beIN Sports HD', 'beIN Sports Arabic', 'beIN Sports English',
            'beIN Sports French', 'beIN Sports 4K', 'beIN Sports News'
        ]
        
        # ترتيب النتائج حسب الأفضلية
        scored_links = []
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # الروابط من Amagi (جودة عالية) تحصل على نقاط إضافية
            if 'amagi.tv' in link_lower:
                score += 10
            
            # الروابط التي تحتوي على 'beIN' أو 'bein' تحصل على نقاط
            if 'bein' in link_lower or 'be in' in link_lower:
                score += 5
            
            # الروابط التي تحتوي على '1', '2', '3', 'extra', 'max' تحصل على نقاط
            for variant in target_variants:
                if variant.lower().replace(' ', '') in link_lower.replace(' ', ''):
                    score += 3
            
            # الروابط الآمنة (HTTPS) تحصل على نقاط
            if link.startswith('https://'):
                score += 2
            
            scored_links.append((score, link))
        
        # ترتيب تنازلي حسب النقاط
        scored_links.sort(reverse=True, key=lambda x: x[0])
        
        # إرجاع الروابط فقط (مع الحفاظ على الترتيب)
        return [link for score, link in scored_links]
    
    # ============================================================
    # دوال البحث (جميعها معدلة للبحث عن الكلمات المفتاحية)
    # ============================================================
    
    def _search_iptv_org(self, keywords):
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=8)
                if response.status_code == 200:
                    # ✅ البحث عن أي كلمة مفتاحية
                    for keyword in keywords[:3]:  # استخدم أول 3 كلمات للسرعة
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
            return []
    
    def _search_free_tv(self, keywords):
        try:
            url = "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                links = []
                for keyword in keywords[:3]:
                    pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
                return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في Free-TV: {e}")
        return []
    
    def _search_github(self, keywords):
        try:
            urls = [
                "https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u",
                "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
                "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=8)
                if response.status_code == 200:
                    for keyword in keywords[:3]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في GitHub: {e}")
        return []
    
    def _search_world_iptv(self, keywords):
        try:
            url = "https://romaxa55.github.io/world_ip_tv/output/index.m3u"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                links = []
                for keyword in keywords[:3]:
                    pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
                return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في World IPTV: {e}")
        return []
    
    def _search_iptv_hub(self, keywords):
        try:
            url = "https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u"
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                links = []
                for keyword in keywords[:3]:
                    pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                    matches = re.findall(pattern, response.text, re.IGNORECASE)
                    links.extend(matches)
                return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في IPTV-Hub: {e}")
        return []
    
    # ============================================================
    # البحث في تليجرام (مُحسّن)
    # ============================================================
    
    def _search_telegram_channels(self, keywords):
        if not self.telegram_client:
            return []
        
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            all_links = []
            
            # البحث في أول قناة فقط (IPTV442WEB) للسرعة
            target_channels = Config.TELEGRAM_CHANNELS[:1]
            
            for channel in target_channels:
                try:
                    messages = loop.run_until_complete(
                        self._fetch_telegram_messages(channel, limit=10)
                    )
                    if messages:
                        links = self._extract_links_from_text(messages)
                        if links:
                            all_links.extend(links)
                            logger.info(f"✅ تم العثور على {len(links)} رابط من قناة {channel}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في قناة {channel}: {e}")
                    continue
            
            return all_links
        except Exception as e:
            logger.error(f"❌ خطأ في البحث في تليجرام: {e}")
            return []
    
    async def _fetch_telegram_messages(self, channel_name, limit=10):
        try:
            await self.telegram_client.start()
            entity = await self.telegram_client.get_entity(channel_name)
            history = await self.telegram_client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            return [msg.message for msg in history.messages if msg.message]
        except Exception as e:
            logger.warning(f"⚠️ خطأ في جلب رسائل {channel_name}: {e}")
            return []
    
    def _extract_links_from_text(self, messages):
        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
        all_links = []
        for text in messages:
            if text:
                links = re.findall(pattern, text, re.IGNORECASE)
                all_links.extend(links)
        return list(set(all_links))
    
    # ============================================================
    # محركات البحث والمواقع المعروفة
    # ============================================================
    
    def _search_web_engines(self, keywords):
        try:
            links = []
            # استخدم أول كلمة مفتاحية للبحث
            primary_keyword = keywords[0] if keywords else "beIN Sports"
            ddg_url = f"https://html.duckduckgo.com/html/?q={primary_keyword.replace(' ', '+')}+m3u8"
            response = self.session.get(ddg_url, timeout=8)
            if response.status_code == 200:
                pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                ddg_links = re.findall(pattern, response.text, re.IGNORECASE)
                links.extend(ddg_links)
            return list(set(links))
        except Exception as e:
            logger.warning(f"⚠️ خطأ في محركات البحث: {e}")
            return []
    
    def _search_known_sites(self, keywords):
        try:
            links = []
            primary_keyword = keywords[0] if keywords else "beIN Sports"
            for site in Config.KNOWN_SITES[:3]:
                try:
                    url = f"{site}/search?q={primary_keyword.replace(' ', '+')}"
                    response = self.session.get(url, timeout=8)
                    if response.status_code == 200:
                        pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
                        found = re.findall(pattern, response.text, re.IGNORECASE)
                        if found:
                            links.extend(found)
                except:
                    continue
            return list(set(links))
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث في المواقع: {e}")
            return []
    
    # ============================================================
    # دوال مساعدة
    # ============================================================
    
    def _validate_links(self, links):
        valid = []
        for link in links[:8]:
            try:
                response = self.session.head(link, timeout=3, allow_redirects=True)
                if response.status_code in [200, 206, 302, 301]:
                    valid.append(link)
                    logger.info(f"✅ رابط صالح: {link[:50]}...")
            except:
                continue
        return valid
