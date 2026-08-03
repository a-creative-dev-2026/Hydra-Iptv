# في دالة get_country_playlist، قم بتعديل الجزء الخاص بالدمج:

@app.route('/playlist/country/<country_code>')
@limiter.limit("20 per minute")
def get_country_playlist(country_code):
    url = get_country_url(country_code)
    if not url:
        return jsonify({'error': 'دولة غير مدعومة'}), 404
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # ❌ إزالة الدمج الثقيل للقائمة المحلية
            # ✅ إعادة القائمة كما هي من iptv-org
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl; charset=utf-8',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        logger.error(f"❌ خطأ في جلب القائمة: {e}")
        return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'فشل في جلب القائمة'}), 500
