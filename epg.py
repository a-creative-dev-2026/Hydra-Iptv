import requests
import xml.etree.ElementTree as ET
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class EPG:
    def __init__(self):
        self.base_url = 'https://iptv-org.github.io/epg/guides/'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
    
    def get_channel_epg(self, channel_name, country_code=None, days=1):
        """جلب دليل البرامج لقناة معينة"""
        try:
            # بناء رابط الدليل
            if country_code:
                url = f"{self.base_url}{country_code}.xml"
            else:
                # محاولة العثور على القناة في جميع الأدلة
                url = f"{self.base_url}all.xml"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return None
            
            # تحليل XML
            root = ET.fromstring(response.content)
            programs = []
            
            # البحث عن القناة في ملف XML
            for channel in root.findall('.//channel'):
                display_name = channel.find('display-name')
                if display_name is not None and display_name.text:
                    if channel_name.lower() in display_name.text.lower():
                        # جلب البرامج لهذه القناة
                        channel_id = channel.get('id')
                        if channel_id:
                            for programme in root.findall(f".//programme[@channel='{channel_id}']"):
                                title = programme.find('title')
                                start = programme.get('start')
                                stop = programme.get('stop')
                                if title is not None and start is not None:
                                    programs.append({
                                        'title': title.text,
                                        'start': start,
                                        'stop': stop,
                                        'channel': display_name.text
                                    })
            
            return programs[:10]  # آخر 10 برامج
        except Exception as e:
            logger.error(f"❌ خطأ في جلب EPG: {e}")
            return None

    def get_simple_epg(self, channel_name, country_code=None):
        """الحصول على دليل مبسط (JSON)"""
        programs = self.get_channel_epg(channel_name, country_code)
        if not programs:
            return {'error': 'لم يتم العثور على دليل لهذه القناة'}
        
        return {
            'channel': channel_name,
            'programs': programs,
            'count': len(programs)
        }
