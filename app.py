from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from proxy import SmartProxy
from config import Config
from channels import COUNTRY_CHANNELS, SPORTS_CHANNELS

app = Flask(__name__)
CORS(app)

# تهيئة البروكسي
proxy = SmartProxy()

# قائمة الدول
COUNTRIES = {code: data['name'] for code, data in COUNTRY_CHANNELS.items()}

@app.route('/')
def index():
    return jsonify({
        'name': 'Hydra IPTV Server',
        'version': '2.0.0',
        'description': 'خادم IPTV سريع بدون تقطيع',
        'features': [
            'بث مباشر لأكثر من 100 قناة مسبقة',
            'دعم 24 دولة',
            'قنوات رياضية متخصصة',
            'بحث تلقائي عن الروابط المفقودة',
            'بروكسي ذكي مع تجاوز الأعطال'
        ],
        'endpoints': {
            'GET /': 'معلومات الخدمة',
            'GET /channel/<name>': 'بث قناة مباشرة',
            'GET /search/<name>': 'البحث عن قناة',
            'GET /playlist/<country>': 'قائمة قنوات الدولة',
            'GET /countries': 'قائمة الدول المدعومة',
            'GET /sports': 'قائمة القنوات الرياضية',
            'GET /all_channels': 'جميع القنوات المسبقة'
        },
        'examples': {
            'channel': '/channel/beIN%20Sports%201',
            'search': '/search/beIN%20Sports',
            'playlist': '/playlist/tn'
        }
    })

@app.route('/channel/<channel_name>')
def stream_channel(channel_name):
    """بث قناة مباشرة"""
    print(f"📺 طلب بث: {channel_name}")
    
    stream = proxy.get_stream(channel_name)
    
    if stream:
        return stream
    
    return jsonify({
        'error': f'لم يتم العثور على {channel_name}',
        'message': 'جاري البحث عن روابط جديدة...',
        'suggestion': f'استخدم /search/{channel_name} للبحث'
    }), 404

@app.route('/search/<channel_name>')
def search_channel(channel_name):
    """البحث عن قناة"""
    print(f"🔍 طلب بحث: {channel_name}")
    
    links = proxy.searcher.search_channel(channel_name)
    
    if links:
        # حفظ في الكاش
        proxy.cache.set(channel_name, links)
        return jsonify({
            'found': True,
            'channel': channel_name,
            'links': links,
            'count': len(links)
        })
    
    return jsonify({
        'found': False,
        'channel': channel_name,
        'message': 'لم يتم العثور على روابط'
    })

@app.route('/playlist/<country_code>')
def country_playlist(country_code):
    """قائمة قنوات الدولة"""
    if country_code not in COUNTRY_CHANNELS:
        return jsonify({'error': 'دولة غير مدعومة'}), 404
    
    try:
        # جلب قائمة القنوات من الكاش أو من المصدر
        channels = proxy.get_channels_by_country(country_code)
        
        if not channels:
            return jsonify({'error': 'لا توجد قنوات لهذه الدولة'}), 404
        
        # إنشاء ملف M3U
        m3u_content = "#EXTM3U\n"
        for name, url in channels.items():
            m3u_content += f'#EXTINF:-1,{name}\n'
            m3u_content += f'{url}\n'
        
        return Response(
            m3u_content,
            status=200,
            content_type='application/vnd.apple.mpegurl',
            headers={'Access-Control-Allow-Origin': '*'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/countries')
def list_countries():
    """قائمة الدول المدعومة"""
    return jsonify({
        'countries': COUNTRIES,
        'count': len(COUNTRIES)
    })

@app.route('/sports')
def list_sports_channels():
    """قائمة القنوات الرياضية"""
    return jsonify({
        'channels': SPORTS_CHANNELS,
        'count': len(SPORTS_CHANNELS)
    })

@app.route('/all_channels')
def list_all_channels():
    """جميع القنوات المسبقة"""
    all_channels = {}
    
    # إضافة قنوات الدول
    for country_code, data in COUNTRY_CHANNELS.items():
        all_channels[country_code] = {
            'country': data['name'],
            'channels': data['channels']
        }
    
    # إضافة القنوات الرياضية
    all_channels['sports'] = {
        'country': 'رياضة',
        'channels': SPORTS_CHANNELS
    }
    
    return jsonify(all_channels)

@app.route('/channel', methods=['POST'])
def add_channel():
    """إضافة قناة جديدة"""
    data = request.json
    
    if not data or 'name' not in data or 'url' not in data:
        return jsonify({'error': 'يجب توفير name و url'}), 400
    
    success = proxy.add_channel(data['name'], data['url'])
    
    return jsonify({
        'success': success,
        'channel': data['name'],
        'url': data['url']
    })

if __name__ == '__main__':
    print("🐍 Hydra IPTV Server v2.0")
    print("=" * 50)
    print(f"✅ السيرفر يعمل على: http://localhost:{Config.PORT}")
    print(f"📺 مثال: http://localhost:{Config.PORT}/channel/beIN%20Sports%201")
    print(f"🔍 بحث: http://localhost:{Config.PORT}/search/beIN%20Sports")
    print(f"📋 قائمة الدول: http://localhost:{Config.PORT}/countries")
    print("=" * 50)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )
