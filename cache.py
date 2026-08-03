import json
import time
import os
from threading import Lock, Timer
import logging

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, ttl=3600, cache_file='cache.json', debounce_seconds=5):
        self.ttl = ttl
        self.cache_file = cache_file
        self.debounce_seconds = debounce_seconds
        self.lock = Lock()
        self.cache = {}
        self._dirty = False
        self._timer = None
        self._load_from_disk()
    
    def _load_from_disk(self):
        if os.path.exists(self.cache_file) and os.path.getsize(self.cache_file) > 0:
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
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
            self.cache = {}
            self._save_to_disk()
    
    def _save_to_disk(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            self._dirty = False
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حفظ الكاش: {e}")
    
    def _schedule_save(self):
        """جدولة حفظ الكاش بعد فترة قصيرة (debounce)"""
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self.debounce_seconds, self._save_to_disk)
        self._timer.daemon = True
        self._timer.start()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if time.time() - entry['timestamp'] < self.ttl:
                    return entry['data']
                else:
                    del self.cache[key]
                    self._dirty = True
                    self._schedule_save()
            return None
    
    def set(self, key, value):
        with self.lock:
            self.cache[key] = {
                'data': value,
                'timestamp': time.time()
            }
            self._dirty = True
            self._schedule_save()  # ✅ كتابة متأخرة بدلاً من الكتابة الفورية
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self._dirty = True
            self._schedule_save()
    
    def remove(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self._dirty = True
                self._schedule_save()
    
    def force_save(self):
        """حفظ فوري (يستخدم عند الإغلاق)"""
        if self._timer:
            self._timer.cancel()
        if self._dirty:
            self._save_to_disk()
