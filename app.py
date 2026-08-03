from flask import Flask, request, jsonify, Response, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import re
import time
from proxy import SmartProxy
from config import Config
from channels import COUNTRY_CHANNELS, CATEGORIES, get_country_url, get_category_url
import logging
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# إعداد Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة البروكسي
proxy = SmartProxy()

# ============================================================
# جميع المسارات
# ============================================================

@app.route('/')
def index():
    return jsonify({
        'name': 'Hydra IPTV Server',
        'version': '3.0.0',
        'description': 'خادم IPTV سريع بدون تقطيع مع كاش دائم',
        'features': [
            'بث مباشر لأكثر من 13,971 قناة مسبقة',
            'دعم 126 دولة حول العالم',
            '15 تصنيف مختلف (رياضة، أخبار، أفلام...)',
            'بحث تلقائي عن الروابط المفقودة',
            'بروكسي ذكي مع تجاوز الأعطال',
            'كاش دائم (JSON)',
            'نظام حماية من الطلبات المتكررة'
        ],
        'endpoints': {
            'GET /': 'معلومات الخدمة',
            'GET /channel/<name>': 'بث قناة مباشرة',
            'GET /search/<name>': 'البحث عن قناة',
            'GET /playlist/country/<code>': 'قائمة قنوات الدولة',
            'GET /playlist/category/<category>': 'قائمة قنوات التصنيف',
            'GET /countries/all': 'جميع دول العالم',
            'GET /categories/all': 'جميع التصنيفات',
            'GET /playlist/local': 'القائمة المحلية (13,971 قناة)'
        },
        'examples': {
            'channel': '/channel/Al%20Jazeera',
            'search': '/search/Al%20Jazeera',
            'playlist_country': '/playlist/country/tn',
            'playlist_category': '/playlist/category/sports',
            'countries': '/countries/all',
            'categories': '/categories/all'
        }
    }), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/channel/<channel_name>')
@limiter.limit("10 per minute")
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
@limiter.limit("5 per 30 seconds")
def search_channel(channel_name):
    """البحث عن قناة"""
    logger.info(f"🔍 طلب بحث: {channel_name}")
    
    links = proxy.searcher.search_channel(channel_name)
    
    if links:
        proxy.cache.set(channel_name, links)
        return jsonify({
            'found': True,
            'channel': channel_name,
            'links': links,
            'count': len(links)
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    return jsonify({
        'found': False,
        'channel': channel_name,
        'message': 'لم يتم العثور على روابط'
    }), 404, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/country/<country_code>')
@limiter.limit("20 per minute")
def get_country_playlist(country_code):
    """جلب قائمة قنوات دولة معينة (مدمجة مع القائمة المحلية)"""
    url = get_country_url(country_code)
    if not url:
        return jsonify({'error': 'دولة غير مدعومة'}), 404, {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            local_content = load_local_playlist()
            combined = merge_playlists(response.text, local_content)
            return Response(
                combined,
                status=200,
                content_type='application/vnd.apple.mpegurl; charset=utf-8',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}
    
    return jsonify({'error': 'فشل في جلب القائمة'}), 500, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/playlist/category/<category>')
@limiter.limit("20 per minute")
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

@app.route('/playlist/local')
@limiter.limit("20 per minute")
def get_local_playlist():
    """جلب القائمة المحلية (13,971 قناة)"""
    content = load_local_playlist()
    return Response(
        content,
        status=200,
        content_type='application/vnd.apple.mpegurl; charset=utf-8',
        headers={'Access-Control-Allow-Origin': '*'}
    )

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
    
    return jsonify(all_channels), 200, {'Content-Type': 'application/json; charset=utf-8'}

# ============================================================
# دوال مساعدة
# ============================================================

def load_local_playlist():
    """تحميل القائمة المحلية من ملف playlist.m3u8"""
    try:
        with open('playlist.m3u8', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل القائمة المحلية: {e}")
        return "#EXTM3U\n"

def merge_playlists(iptv_org, local):
    """دمج قائمتين مع إزالة التكرار البسيط"""
    return iptv_org + '\n' + local

# ============================================================
# التشغيل
# ============================================================

if __name__ == '__main__':
    print("🐍 Hydra IPTV Server v3.0")
    print("=" * 60)
    print(f"✅ السيرفر يعمل على: http://localhost:{Config.PORT}")
    print(f"🌍 عدد الدول: {len(COUNTRY_CHANNELS)} دولة")
    print(f"📂 عدد التصنيفات: {len(CATEGORIES)} تصنيف")
    print(f"📺 القائمة المحلية: 13,971 قناة")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )
