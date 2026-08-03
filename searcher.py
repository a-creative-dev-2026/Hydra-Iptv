import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        
        # ✅ قائمة المصادر (مخفضة للسرعة)
        self.sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_world_iptv,
            self._search_iptv_hub,
            self._search_web_engines,
        ]
    
    def search_channel(self, channel_name, country=None):
        """البحث الشامل عن قناة مع توسيع الكلمات المفتاحية"""
        logger.info(f"🔍 جاري البحث الشامل عن: {channel_name}")
        all_links = []
        
        # ✅ استخراج الكلمات المفتاحية
        keywords = self._extract_keywords(channel_name)
        logger.info(f"🔑 الكلمات المفتاحية المستخرجة: {keywords}")
        
        # ✅ البحث باستخدام ThreadPoolExecutor مع عدد أقل من العمال
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(source_func, keywords): source_func.__name__
                for source_func in self.sources[:4]
            }
            for future in as_completed(futures):
                try:
                    links = future.result(timeout=15)
                    if links:
                        all_links.extend(links)
                        logger.info(f"✅ تم العثور على {len(links)} رابط من {futures[future]}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في المصدر {futures[future]}: {e}")
        
        # ✅ تصفية النتائج حسب الصلة
        filtered_links = self._filter_by_relevance(all_links, channel_name)
        unique_links = list(set(filtered_links))
        valid_links = self._validate_links(unique_links)
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============================================================
    # دالة استخراج الكلمات المفتاحية مع مرادفاتها
    # ============================================================
    
    def _extract_keywords(self, channel_name):
        """استخراج الكلمات المفتاحية من اسم القناة مع مرادفاتها"""
        keywords = []
        original = channel_name.lower().strip()
        
        # ✅ الكلمة الأساسية
        keywords.append(original)
        
        # ✅ إزالة الأرقام والرموز للحصول على الكلمة الجذرية
        base_name = re.sub(r'[^a-zA-Z\s]', '', original).strip()
        if base_name:
            keywords.append(base_name)
        
        # ✅ تقسيم إلى كلمات فردية
        words = original.split()
        for word in words:
            if len(word) > 2:
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
            'mbc': ['mbc', 'middle east broadcasting', 'mbc 1', 'mbc 2', 'mbc 3', 'mbc 4', 'mbc action', 'mbc max', 'mbc drama', 'mbc masr', 'mbc egypt'],
            'aljazeera': ['aljazeera', 'al jazeera', 'الجزيرة'],
            'cnn': ['cnn', 'cable news network'],
            'bbc': ['bbc', 'british broadcasting corporation'],
            'sky': ['sky', 'sky news', 'sky sports'],
            'fox': ['fox', 'fox sports', 'fox news'],
            'espn': ['espn', 'entertainment and sports programming network'],
        }
        
        # ✅ إضافة المرادفات بناءً على الكلمات الموجودة
        for word in words:
            for key, syns in synonyms.items():
                if key in word or word in key:
                    keywords.extend(syns)
        
        # ✅ إزالة التكرار
        keywords = list(set(keywords))
        return keywords
    
    # ============================================================
    # دالة تصفية النتائج حسب الصلة
    # ============================================================
    
    def _filter_by_relevance(self, links, original_query):
        """ترتيب النتائج حسب الصلة بالقناة المطلوبة"""
        if not links:
            return links
        
        # ✅ قائمة القنوات المطلوبة (جميع الإصدارات)
        target_variants = [
            # beIN Sports
            'beIN Sports 1', 'beIN Sports 2', 'beIN Sports 3',
            'beIN Sports Extra', 'beIN Sports Max', 'beIN Sports Max 1',
            'beIN Sports HD', 'beIN Sports Arabic', 'beIN Sports English',
            'beIN Sports French', 'beIN Sports 4K', 'beIN Sports News',
            # MBC
            'MBC 1', 'MBC 2', 'MBC 3', 'MBC 4', 'MBC Action',
            'MBC Max', 'MBC Drama', 'MBC Masr', 'MBC Egypt',
            # قنوات أخرى
            'Al Jazeera', 'CNN', 'BBC', 'Sky Sports', 'FOX Sports', 'ESPN'
        ]
        
        scored_links = []
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # ✅ الروابط من Amagi (جودة عالية) تحصل على نقاط إضافية
            if 'amagi.tv' in link_lower:
                score += 10
            
            # ✅ الروابط التي تحتوي على أي من الكلمات المفتاحية
            for variant in target_variants:
                if variant.lower().replace(' ', '') in link_lower.replace(' ', ''):
                    score += 5
            
            # ✅ الروابط الآمنة (HTTPS) تحصل على نقاط
            if link.startswith('https://'):
                score += 2
            
            scored_links.append((score, link))
        
        # ترتيب تنازلي حسب النقاط
        scored_links.sort(reverse=True, key=lambda x: x[0])
        return [link for score, link in scored_links]
    
    # ============================================================
    # مصادر البحث (جميعها معدلة للبحث عن الكلمات المفتاحية)
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
                    for keyword in keywords[:3]:
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
    # محركات البحث
    # ============================================================
    
    def _search_web_engines(self, keywords):
        try:
            links = []
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
