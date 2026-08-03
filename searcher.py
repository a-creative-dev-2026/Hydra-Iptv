import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from config import Config
import logging

# ✅ إضافة مكتبة fuzzy search
try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("⚠️ مكتبة rapidfuzz غير مثبتة، سيتم تعطيل البحث الضبابي")

logger = logging.getLogger(__name__)
ua = UserAgent()

class ChannelSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        })
        
        # ✅ المصادر المستخدمة للبحث
        self.sources = [
            self._search_iptv_org,
            self._search_github,
            self._search_world_iptv,
        ]
    
    # ============================================================
    # ✅ البحث الرئيسي (مع Fuzzy Search)
    # ============================================================
    
    def search_channel(self, channel_name, country=None):
        """البحث عن قناة مع Fuzzy Search"""
        logger.info(f"🔍 جاري البحث عن: {channel_name}")
        all_links = []
        
        # 1. البحث الدقيق (Exact Search)
        exact_links = self._exact_search(channel_name)
        if exact_links:
            all_links.extend(exact_links)
            logger.info(f"✅ تم العثور على {len(exact_links)} رابط من البحث الدقيق")
        
        # 2. البحث بالكلمات المفتاحية (Keyword Search)
        keyword_links = self._keyword_search(channel_name)
        if keyword_links:
            all_links.extend(keyword_links)
            logger.info(f"✅ تم العثور على {len(keyword_links)} رابط من البحث بالكلمات المفتاحية")
        
        # 3. البحث الضبابي (Fuzzy Search)
        if FUZZY_AVAILABLE:
            fuzzy_links = self._fuzzy_search(channel_name)
            if fuzzy_links:
                all_links.extend(fuzzy_links)
                logger.info(f"✅ تم العثور على {len(fuzzy_links)} رابط من البحث الضبابي")
        
        # 4. إزالة التكرار والتحقق من الصحة
        unique_links = list(set(all_links))
        valid_links = self._validate_links(unique_links)
        
        logger.info(f"✅ تم العثور على {len(valid_links)} رابط صالح لـ {channel_name}")
        return valid_links
    
    # ============================================================
    # ✅ البحث الدقيق (Exact Search)
    # ============================================================
    
    def _exact_search(self, channel_name):
        """البحث عن الاسم المطابق تماماً"""
        try:
            keywords = self._extract_keywords(channel_name)
            all_links = []
            
            # البحث في المصادر
            for source_func in self.sources:
                try:
                    links = source_func(keywords[:1])  # استخدم الكلمة الأولى فقط
                    if links:
                        all_links.extend(links)
                except:
                    continue
            
            return all_links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الدقيق: {e}")
            return []
    
    # ============================================================
    # ✅ البحث بالكلمات المفتاحية
    # ============================================================
    
    def _keyword_search(self, channel_name):
        """البحث باستخدام الكلمات المفتاحية"""
        try:
            keywords = self._extract_keywords(channel_name)
            all_links = []
            
            # استخدام الكلمات المفتاحية للبحث
            for source_func in self.sources:
                try:
                    links = source_func(keywords[:3])  # استخدم أول 3 كلمات
                    if links:
                        all_links.extend(links)
                except:
                    continue
            
            return all_links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث بالكلمات المفتاحية: {e}")
            return []
    
    # ============================================================
    # ✅ البحث الضبابي (Fuzzy Search)
    # ============================================================
    
    def _fuzzy_search(self, channel_name):
        """البحث الضبابي باستخدام rapidfuzz"""
        if not FUZZY_AVAILABLE:
            return []
        
        try:
            # جلب جميع القنوات من المصادر
            all_channels = self._get_all_channels_from_sources()
            if not all_channels:
                return []
            
            # البحث عن أفضل التطابقات
            matches = process.extract(
                channel_name, 
                all_channels.keys(), 
                scorer=fuzz.ratio,
                limit=10
            )
            
            # جمع الروابط للتطابقات ذات النسبة > 70%
            links = []
            for match, score in matches:
                if score > 70:
                    links.extend(all_channels[match])
                    logger.info(f"🔍 تطابق ضبابي: {match} (نسبة {score}%)")
            
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في البحث الضبابي: {e}")
            return []
    
    def _get_all_channels_from_sources(self):
        """جلب جميع القنوات من المصادر (للبحث الضبابي)"""
        channels = {}
        try:
            # جلب من iptv-org
            response = self.session.get(
                "https://iptv-org.github.io/iptv/index.m3u",
                timeout=10
            )
            if response.status_code == 200:
                lines = response.text.splitlines()
                current_name = None
                for line in lines:
                    if line.startswith('#EXTINF'):
                        match = re.search(r',(.+)$', line)
                        if match:
                            current_name = match.group(1).strip()
                    elif line.startswith('http') and current_name:
                        if current_name not in channels:
                            channels[current_name] = []
                        channels[current_name].append(line.strip())
                        current_name = None
        except Exception as e:
            logger.warning(f"⚠️ خطأ في جلب القنوات للبحث الضبابي: {e}")
        
        return channels
    
    # ============================================================
    # ✅ مصادر البحث
    # ============================================================
    
    def _search_iptv_org(self, keywords):
        try:
            urls = [
                "https://iptv-org.github.io/iptv/index.m3u",
                "https://iptv-org.github.io/iptv/index.nsfw.m3u",
            ]
            links = []
            for url in urls:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    for keyword in keywords[:3]:
                        pattern = rf'#EXTINF:.*,.*{re.escape(keyword)}.*\n(https?://[^\s]+)'
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        links.extend(matches)
            return links
        except Exception as e:
            logger.warning(f"⚠️ خطأ في iptv-org: {e}")
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
                response = self.session.get(url, timeout=10)
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
            response = self.session.get(url, timeout=10)
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
    
    # ============================================================
    # ✅ دوال مساعدة
    # ============================================================
    
    def _extract_keywords(self, channel_name):
        keywords = []
        original = channel_name.lower().strip()
        keywords.append(original)
        
        base_name = re.sub(r'[^a-zA-Z\s]', '', original).strip()
        if base_name:
            keywords.append(base_name)
        
        for word in original.split():
            if len(word) > 2:
                keywords.append(word)
        
        return list(set(keywords))
    
    def _validate_links(self, links):
        valid = []
        for link in links[:8]:
            try:
                response = self.session.head(link, timeout=3, allow_redirects=True)
                if response.status_code in [200, 206, 302, 301]:
                    valid.append(link)
                    logger.info(f"✅ رابط صالح: {link[:50]}...")
            except Exception as e:
                logger.warning(f"❌ رابط غير صالح: {link[:50]}... - {str(e)[:30]}")
                continue
        return valid
