import json
import time
import os
from threading import Lock
import logging

# ✅ استيراد Redis اختياري (إذا لم يكن مثبتاً، يستخدم JSON)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, ttl=3600, cache_file='cache.json', use_redis=True):
        self.ttl = ttl
        self.cache_file = cache_file
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.lock = Lock()
        self.redis_client = None
        
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    password=os.getenv('REDIS_PASSWORD', ''),
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("✅ تم الاتصال بـ Redis بنجاح")
                self.cache = {}
            except Exception as e:
                logger.warning(f"⚠️ فشل الاتصال بـ Redis، استخدام JSON: {e}")
                self.use_redis = False
                self._load_from_disk()
        else:
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
        except Exception as e:
            logger.warning(f"⚠️ خطأ في حفظ الكاش: {e}")
    
    def get(self, key):
        if self.use_redis and self.redis_client:
            try:
                data = self.redis_client.get(f"hydra:{key}")
                if data:
                    return json.loads(data)
                return None
            except:
                pass
        
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
        if self.use_redis and self.redis_client:
            try:
                data = {'data': value, 'timestamp': time.time()}
                self.redis_client.setex(f"hydra:{key}", self.ttl, json.dumps(data))
                return
            except:
                pass
        
        with self.lock:
            self.cache[key] = {'data': value, 'timestamp': time.time()}
            self._save_to_disk()
    
    def remove(self, key):
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(f"hydra:{key}")
                return
            except:
                pass
        
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self._save_to_disk()
    
    def get_all(self):
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys("hydra:*")
                result = {}
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        key_name = key.replace("hydra:", "")
                        result[key_name] = json.loads(data)
                return result
            except:
                pass
        return self.cache
