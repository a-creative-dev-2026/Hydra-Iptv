import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from proxy import SmartProxy
from config import Config
from channels import COUNTRY_CHANNELS, CATEGORIES, get_country_url, get_category_url
from epg import EPG

# ✅ استيراد scheduler مع التعامل مع الخطأ
try:
    from scheduler import start_scheduler
except ImportError:
    def start_scheduler():
        logging.warning("⚠️ scheduler.py غير موجود، تم تعطيل المجدول")
        return None

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
epg = EPG()

# بدء المجدول (إذا كان متوفراً)
scheduler = start_scheduler()

# ============================================================
# المسارات (نفسها كما في السابق، مع إضافة /stats)
# ============================================================

@app.route('/')
def index():
    return jsonify({
        'name': 'Hydra IPTV Server',
        'version': '3.1.0',
        'description': 'خادم IPTV مع بحث متقدم، EPG، وكاش ذكي',
        'features': [
            'دعم 193 دولة حول العالم',
            '31 تصنيفاً مختلفاً',
            'بحث ضبابي (Fuzzy Search)',
            'دليل برامج EPG',
            'تحقق دوري من صحة الروابط',
            'كاش باستخدام Redis (مع fallback JSON)',
            'بروكسي ذكي مع تجاوز الأعطال'
        ],
        'endpoints': {
            'GET /': 'معلومات الخدمة',
            'GET /channel/<name>': 'بث قناة مباشرة',
            'GET /search/<name>': 'بحث عن قناة (مع Fuzzy Search)',
            'GET /playlist/country/<code>': 'قائمة قنوات الدولة',
            'GET /playlist/category/<category>': 'قائمة قنوات التصنيف',
            'GET /playlist/local': 'القائمة المحلية',
            'GET /epg/<channel_name>': 'دليل برامج القناة',
            'GET /epg/country/<country_code>': 'دليل برامج الدولة',
            'GET /stats': 'إحصائيات الكاش'
        },
        'examples': {
            'channel': '/channel/Al%20Jazeera',
            'search': '/search/bein%20sport',
            'playlist_country': '/playlist/country/tn',
            'playlist_category': '/playlist/category/sports',
            'epg_channel': '/epg/Al%20Jazeera',
            'epg_country': '/epg/country/qa',
            'stats': '/stats'
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
            return Response(response.text, status=200, content_type='application/vnd.apple.mpegurl')
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
            return Response(response.text, status=200, content_type='application/vnd.apple.mpegurl')
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

@app.route('/epg/<channel_name>')
@limiter.limit("10 per minute")
def get_epg(channel_name):
    country_code = request.args.get('country')
    result = epg.get_simple_epg(channel_name, country_code)
    return jsonify(result)

@app.route('/epg/country/<country_code>')
@limiter.limit("5 per minute")
def get_country_epg(country_code):
    try:
        url = f"https://iptv-org.github.io/epg/guides/{country_code}.xml"
        import requests as req
        response = req.get(url, timeout=15)
        if response.status_code == 200:
            return Response(response.text, status=200, content_type='application/xml')
    except Exception as e:
        logger.error(f"❌ خطأ في جلب EPG: {e}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'لم يتم العثور على الدليل'}), 404

@app.route('/stats')
def get_stats():
    stats = proxy.get_cache_stats()
    stats['total_countries'] = len(COUNTRY_CHANNELS)
    stats['total_categories'] = len(CATEGORIES)
    stats['status'] = 'running'
    return jsonify(stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🐍 Hydra IPTV Server v3.1.0")
    print("=" * 60)
    print(f"✅ السيرفر يعمل على: http://0.0.0.0:{port}")
    print(f"🌍 عدد الدول: {len(COUNTRY_CHANNELS)} دولة")
    print(f"📂 عدد التصنيفات: {len(CATEGORIES)} تصنيف")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
