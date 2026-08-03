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
        
        # ✅ قائمة المصادر (مرتبة حسب الأهمية)
        self.sources = [
            self._search_iptv_org,
            self._search_free_tv,
            self._search_github,
            self._search_world_iptv,
            self._search_iptv_hub,
            self._search_web_engines,
        ]
    
    def search_channel(self, channel_name, country=None):
        """البحث الشامل عن قناة مع تحسين الدقة"""
        logger.info(f"🔍 جاري البحث الشامل عن: {channel_name}")
        all_links = []
        
        # ✅ استخراج الكلمات المفتاحية الرئيسية
        primary_keyword = channel_name.strip()
        keywords = self._extract_keywords(primary_keyword)
        logger.info(f"🔑 الكلمات المفتاحية: {keywords}")
        
        # ✅ البحث في جميع المصادر
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(source_func, keywords): source_func.__name__
                for source_func in self.sources[:5]
            }
            for future in as_completed(futures):
                try:
                    links = future.result(timeout=15)
                    if links:
                        all_links.extend(links)
                        logger.info(f"✅ تم العثور على {len(links)} رابط من {futures[future]}")
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في المصدر {futures[future]}: {e}")
        
        # ✅ تصفية النتائج بدقة عالية
        filtered_links = self._filter_by_relevance(all_links, primary_keyword)
        
        # ✅ إزالة التكرار
        unique_links = list(dict.fromkeys(filtered_links))  # يحافظ على الترتيب
        
        # ✅ التحقق من صحة الروابط (اختبار سريع)
        valid_links = self._validate_links(unique_links)
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============================================================
    # 🎯 دالة التصفية الذكية (القلب النابض للدقة)
    # ============================================================
    
    def _filter_by_relevance(self, links, query):
        """ترتيب النتائج حسب الدقة والتطابق مع الاستعلام"""
        if not links:
            return links
        
        # ✅ تحضير الاستعلام للبحث
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        # ✅ قائمة الكلمات التي تشير إلى نتائج غير مرغوب فيها
        unwanted_keywords = ['radio', 'cnbc', 'indonesia', 'podcast', 'audio']
        
        scored_links = []
        for link in links:
            score = 0
            link_lower = link.lower()
            
            # ✅ 1. نقاط للتطابق التام (الاسم الكامل)
            if query_lower in link_lower:
                score += 50
            # ✅ 2. نقاط للتطابق مع كل كلمة من الاستعلام
            for word in query_words:
                if word in link_lower:
                    score += 10
            
            # ✅ 3. نقاط إضافية للمصادر الموثوقة
            trusted_domains = ['amagi.tv', 'iptv-org', 'github.io', 'streamlock.net', 'sofast.tv']
            for domain in trusted_domains:
                if domain in link_lower:
                    score += 20
            
            # ✅ 4. نقاط للروابط الآمنة (HTTPS)
            if link.startswith('https://'):
                score += 5
            
            # ✅ 5. خصم النقاط للروابط غير المرغوب فيها
            for unwanted in unwanted_keywords:
                if unwanted in link_lower:
                    score -= 30  # خصم كبير لتقليل ظهورها
            
            # ✅ 6. خصم النقاط للروابط التي تحوي "m3u8" بشكل صحيح (نعطيها أفضلية)
            if '.m3u8' in link_lower:
                score += 3
            
            scored_links.append((score, link))
        
        # ✅ ترتيب تنازلي حسب النقاط
        scored_links.sort(reverse=True, key=lambda x: x[0])
        
        # ✅ إرجاع الروابط ذات النقاط الموجبة فقط (أو كلها إذا كانت النقاط صفراً)
        filtered = [link for score, link in scored_links if score > 0]
        if not filtered:
            # إذا لم تكن هناك روابط ذات نقاط موجبة، نرجع أول 5 روابط
            filtered = [link for _, link in scored_links[:5]]
        
        return filtered
    
    # ============================================================
    # 🔑 استخراج الكلمات المفتاحية مع مرادفات
    # ============================================================
    
    def _extract_keywords(self, channel_name):
        """استخراج الكلمات المفتاحية مع مرادفاتها"""
        keywords = []
        original = channel_name.lower().strip()
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
            'mbc': ['mbc', 'middle east broadcasting', 'mbc 1', 'mbc 2', 'mbc 3', 'mbc action', 'mbc max', 'mbc drama', 'mbc masr'],
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
    # 📡 مصادر البحث (جميعها معدلة للبحث عن الكلمات المفتاحية)
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
    
    def _search_web_engines(self, keywords):
        try:
            links = []
            primary_keyword = keywords[0] if keywords else "tv"
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
    # ✅ التحقق من صحة الروابط
    # ============================================================
    
    def _validate_links(self, links):
        valid = []
        for link in links[:10]:  # اختبر أول 10 روابط فقط للسرعة
            try:
                response = self.session.head(link, timeout=3, allow_redirects=True)
                if response.status_code in [200, 206, 302, 301]:
                    valid.append(link)
                    logger.info(f"✅ رابط صالح: {link[:50]}...")
            except Exception as e:
                logger.warning(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:30]}")
                continue
        return valid
