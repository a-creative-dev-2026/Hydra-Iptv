import asyncio
from hunter import SiteHunter
import logging

logger = logging.getLogger(__name__)

class ChannelSearcher:
    def __init__(self):
        self.hunter = SiteHunter()
        logger.info("✅ تم تهيئة صياد المواقع")
    
    def search_channel(self, channel_name, country=None):
        logger.info(f"🔍 بدء البحث عن: {channel_name}")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.hunter.hunt(channel_name))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return []
