import asyncio
from hunter import SmartHunter
import logging
import os

logger = logging.getLogger(__name__)

class ChannelSearcher:
    def __init__(self):
        # 🔥 يمكنك إضافة مصادرك الخاصة هنا
        custom_sources = [
            # مثال: 'https://example.com/your-playlist.m3u',
            # 'https://example.com/another-source.m3u',
            # 'https://example.com/page-with-links',
        ]
        
        # يمكنك أيضاً جلب المصادر من متغيرات البيئة
        env_sources = os.getenv('CUSTOM_SOURCES', '')
        if env_sources:
            custom_sources.extend(env_sources.split(','))
        
        self.hunter = SmartHunter(custom_sources=custom_sources)
        logger.info(f"✅ تم تهيئة الباحث مع {len(custom_sources)} مصدراً مخصصاً")
    
    def search_channel(self, channel_name, country=None, deep_level=2):
        """
        البحث عن قناة
        - deep_level: 1 (سطحي) أو 2 (معمق) أو 3 (فائق العمق)
        """
        logger.info(f"🔍 بدء البحث عن: {channel_name} (المستوى: {deep_level})")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.hunter.hunt(channel_name, max_results=10, deep_level=deep_level)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return []
