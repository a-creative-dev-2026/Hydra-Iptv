import asyncio
from hunter import LinkHunter
import logging

logger = logging.getLogger(__name__)

class ChannelSearcher:
    def __init__(self):
        self.hunter = LinkHunter()
    
    def search_channel(self, channel_name, country=None):
        """الواجهة الرئيسية للبحث (متزامنة)"""
        logger.info(f"🔍 بدء البحث عن: {channel_name}")
        
        try:
            # محاولة الحصول على حلقة الأحداث الحالية
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # إذا لم تكن هناك حلقة أحداث، ننشئ واحدة جديدة
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.hunter.hunt(channel_name))
                loop.close()
                return result
            else:
                # إذا كانت هناك حلقة أحداث بالفعل، نستخدم run_in_executor
                # لتشغيل البحث في خيط منفصل (لتجنب تعطل الحلقة)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_hunt_sync, channel_name
                    )
                    return future.result(timeout=30)
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return []
    
    def _run_hunt_sync(self, channel_name):
        """تنفيذ البحث بشكل متزامن داخل خيط منفصل"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.hunter.hunt(channel_name))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ خطأ في البحث المتزامن: {e}")
            return []
