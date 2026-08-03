from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from proxy import SmartProxy
from config import Config
from channels import COUNTRY_CHANNELS, CATEGORIES, get_country_url, get_category_url
import logging

app = Flask(__name__)
CORS(app)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

proxy = SmartProxy()

# ============================================================
# جميع المسارات
# ============================================================

@app.route('/')
def index():
    local_count = len(proxy.local_channels) if hasattr(proxy, 'local_channels') else 0
    return jsonify({
        'name': 'Hydra IPTV Server',
        'version': '2.1.0',
        'description': 'خادم IPTV سريع بدون تقطيع مع دعم قائمة محلية',
        'features': [
            f'بث مباشر لأكثر من {local_count} قناة من القائمة المحلية',
            'دعم 126 دولة حول العالم',
            '15 تصنيف مختلف (رياضة، أخبار، أفلام...)',
            'بحث تلقائي عن الروابط المفقودة',
            'بروكسي ذكي مع تجاوز الأعطال',
            'قائمة تشغيل محلية مدمجة (playlist.m3u8)'
        ],
        'endpoints': {
            'GET /': 'معلومات الخدمة',
            'GET /channel/<name>': 'بث قناة مباشرة',
            'GET /search/<name>': 'البحث عن قناة',
            'GET /playlist/local': 'قائمة القنوات المحلية الكاملة (m3u8)',
            'GET /playlist/local/json': 'قائمة القنوات المحلية كـ JSON',
            'GET /playlist/country/<code>': 'قائمة قنوات الدولة',
            'GET /playlist/category/<category>': 'قائمة قنوات التصنيف',
            'GET /countries/all': 'جميع دول العالم',
            'GET /categories/all': 'جميع التصنيفات'
        },
        'examples': {
            'channel': '/channel/Al%20Jazeera',
            'search': '/search/CNN',
            'playlist_local': '/playlist/local',
            'playlist_local_json': '/playlist/local/json',
            'playlist_country': '/playlist/country/tn',
            'playlist_category': '/playlist/category/sports',
            'countries': '/countries/all',
            'categories': '/categories/all'
        },
        'local_channels_count': local_count
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/channel/<channel_name>')
def stream_channel(channel_name):
    """بث قناة مباشرة"""
    logger.info(f"📺 طلب بث: {channel_name}")
    
    stream = proxy.get_stream(channel_name)
    
    if stream:
        return stream
    
    return jsonify({
        'error': f'لم يتم العثور على {channel_name}',
        'message': 'جاري البحث عن روابط جديدة...',
        'suggestion': f'استخدم /search/{channel_name} للبحث'
    }), 404, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/search/<channel_name>')
def search_channel(channel_name):
    """البحث عن قناة"""
    logger.info(f"🔍 طلب بحث: {channel_name}")
    
    # أولاً ابحث في القائمة المحلية
    local_results = proxy.search_local(channel_name)
    if local_results:
        # خذ أول نتيجة وأضفها للكاش
        first_name = next(iter(local_results))
        links = local_results[first_name]
        proxy.cache.set(channel_name, links)
        return jsonify({
            'found': True,
            'channel': channel_name,
            'matched_name': first_name,
            'links': links,
            'count': len(links),
            'source': 'local_playlist'
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    # ثم ابحث عبر المحرك الخارجي
    links = proxy.searcher.search_channel(channel_name)
    
    if links:
        proxy.cache.set(channel_name, links)
        return jsonify({
            'found': True,
            'channel': channel_name,
            'links': links,
            'count': len(links),
            'source': 'online_search'
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    return jsonify({
        'found': False,
        'channel': channel_name,
        'message': 'لم يتم العثور على روابط'
    }), 404, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/local')
def get_local_playlist():
    """إرجاع قائمة التشغيل المحلية الكاملة بصيغة m3u8"""
    content = proxy.get_local_playlist()
    if content:
        return Response(
            content,
            status=200,
            content_type='application/vnd.apple.mpegurl; charset=utf-8',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Content-Disposition': 'inline; filename="hydra_local.m3u8"'
            }
        )
    return jsonify({'error': 'القائمة المحلية غير متوفرة'}), 404, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/local/json')
def get_local_playlist_json():
    """إرجاع قائمة القنوات المحلية كـ JSON"""
    channels = proxy.local_channels
    return jsonify({
        'total': len(channels),
        'channels': {name: urls for name, urls in list(channels.items())[:500]},  # حد أقصى لتجنب الاستجابة الضخمة
        'note': 'عرض أول 500 قناة فقط. استخدم /playlist/local للحصول على الملف الكامل'
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/country/<country_code>')
def get_country_playlist(country_code):
    """جلب قائمة قنوات دولة معينة"""
    url = get_country_url(country_code)
    if not url:
        return jsonify({'error': 'دولة غير مدعومة'}), 404, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl; charset=utf-8',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}
    
    return jsonify({'error': 'فشل في جلب القائمة'}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/category/<category>')
def get_category_playlist(category):
    """جلب قائمة قنوات تصنيف معين"""
    url = get_category_url(category)
    if not url:
        return jsonify({'error': 'تصنيف غير مدعوم'}), 404, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl; charset=utf-8',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}
    
    return jsonify({'error': 'فشل في جلب القائمة'}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/countries/all')
def list_all_countries():
    """عرض جميع دول العالم"""
    return jsonify({
        'total': len(COUNTRY_CHANNELS),
        'countries': COUNTRY_CHANNELS
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/categories/all')
def list_all_categories():
    """عرض جميع التصنيفات"""
    return jsonify({
        'total': len(CATEGORIES),
        'categories': CATEGORIES
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/sports')
def list_sports_channels():
    """قائمة القنوات الرياضية (للتوافق مع الإصدارات السابقة)"""
    return jsonify({
        'channels': proxy.cache.cache,
        'count': len(proxy.cache.cache)
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/all_channels')
def list_all_channels():
    """جميع القنوات المسبقة (للتوافق مع الإصدارات السابقة)"""
    all_channels = {}
    
    for country_code, data in COUNTRY_CHANNELS.items():
        all_channels[country_code] = {
            'country': data['name'],
            'url': data['url']
        }
    
    all_channels['categories'] = CATEGORIES
    all_channels['local_count'] = len(proxy.local_channels)
    
    return jsonify(all_channels), 200, {'Content-Type': 'application/json; charset=utf-8'}

if __name__ == '__main__':
    print("🐍 Hydra IPTV Server v2.1")
    print("=" * 60)
    print(f"✅ السيرفر يعمل على: http://localhost:{Config.PORT}")
    print(f"🌍 عدد الدول: {len(COUNTRY_CHANNELS)} دولة")
    print(f"📂 عدد التصنيفات: {len(CATEGORIES)} تصنيف")
    print(f"📺 عدد القنوات المحلية: {len(proxy.local_channels)}")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )
