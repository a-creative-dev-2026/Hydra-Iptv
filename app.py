import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from proxy import SmartProxy
from config import Config
from channels import COUNTRY_CHANNELS, CATEGORIES, get_country_url, get_category_url

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

proxy = SmartProxy()

@app.route('/')
def index():
    return jsonify({
        'name': 'Hydra IPTV Server',
        'version': '3.0.0',
        'description': 'خادم IPTV مع بحث متقدم في الدول والتصنيفات',
        'features': [
            'دعم 126 دولة حول العالم',
            '15 تصنيف مختلف (رياضة، أخبار، أفلام...)',
            'بحث متقدم في مصادر متعددة',
            'بروكسي ذكي مع تجاوز الأعطال'
        ],
        'endpoints': {
            'GET /': 'معلومات الخدمة',
            'GET /channel/<name>': 'بث قناة مباشرة',
            'GET /search/<name>': 'بحث عن قناة',
            'GET /playlist/country/<code>': 'قائمة قنوات الدولة',
            'GET /playlist/category/<category>': 'قائمة قنوات التصنيف',
            'GET /playlist/local': 'القائمة المحلية'
        },
        'examples': {
            'channel': '/channel/Al%20Jazeera',
            'search': '/search/MBC%201',
            'playlist_country': '/playlist/country/tn',
            'playlist_category': '/playlist/category/sports'
        }
    })

@app.route('/channel/<channel_name>')
@limiter.limit("10 per minute")
def stream_channel(channel_name):
    logger.info(f"📺 طلب بث: {channel_name}")
    stream = proxy.get_stream(channel_name)
    if stream:
        return stream
    return jsonify({'error': f'لم يتم العثور على {channel_name}'}), 404

@app.route('/search/<channel_name>')
@limiter.limit("5 per 30 seconds")
def search_channel(channel_name):
    logger.info(f"🔍 طلب بحث: {channel_name}")
    links = proxy.searcher.search_channel(channel_name)
    if links:
        proxy.cache.set(channel_name, links)
        return jsonify({
            'found': True,
            'channel': channel_name,
            'links': links,
            'count': len(links)
        })
    return jsonify({'found': False, 'channel': channel_name}), 404

@app.route('/playlist/country/<country_code>')
@limiter.limit("20 per minute")
def get_country_playlist(country_code):
    url = get_country_url(country_code)
    if not url:
        return jsonify({'error': 'دولة غير مدعومة'}), 404
    try:
        import requests as req
        response = req.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl'
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'فشل في جلب القائمة'}), 500

@app.route('/playlist/category/<category>')
@limiter.limit("20 per minute")
def get_category_playlist(category):
    url = get_category_url(category)
    if not url:
        return jsonify({'error': 'تصنيف غير مدعوم'}), 404
    try:
        import requests as req
        response = req.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl'
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'فشل في جلب القائمة'}), 500

@app.route('/playlist/local')
def get_local_playlist():
    try:
        with open('playlist.m3u8', 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, content_type='application/vnd.apple.mpegurl')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🐍 Hydra IPTV Server v3.0")
    print("=" * 60)
    print(f"✅ السيرفر يعمل على: http://0.0.0.0:{port}")
    print(f"🌍 عدد الدول: {len(COUNTRY_CHANNELS)} دولة")
    print(f"📂 عدد التصنيفات: {len(CATEGORIES)} تصنيف")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
