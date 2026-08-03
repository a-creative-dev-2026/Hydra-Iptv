import json
import time
import os
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, ttl=3600, cache_file='cache.json'):
        self.ttl = ttl
        self.cache_file = cache_file
        self.lock = Lock()
        self.cache = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """تحميل الكاش من الملف"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                # حذف المدخلات المنتهية صلاحيتها
                now = time.time()
                expired = [k for k, v in self.cache.items() if now - v['timestamp'] > self.ttl]
                for k in expired:
                    del self.cache[k]
                if expired:
                    self._save_to_disk()
                logger.info(f"✅ تم تحميل {len(self.cache)} مدخل من الكاش الدائم")
            except Exception as e:
                logger.warning(f"⚠️ خطأ في تحميل الكاش: {e}")
                self.cache = {}
        else:
            # إنشاء ملف الكاش الجديد
            self._save_to_disk()
    
    def _save_to_disk(self):
        """حفظ الكاش في الملف"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حفظ الكاش: {e}")
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry['timestamp'] < self.ttl:
                    return entry['data']
                else:
                    del self.cache[key]
                    self._save_to_disk()
            return None
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = {
                'data': value,
                'timestamp': time.time()
            }
            self._save_to_disk()
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self._save_to_disk()
    
    def remove(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self._save_to_disk()
    
    def get_all(self):
        """الحصول على جميع بيانات الكاش"""
        with self.lock:
            return self.cache
