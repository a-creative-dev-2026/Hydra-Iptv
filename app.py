@app.route('/countries/all')
def list_all_countries():
    """عرض جميع دول العالم"""
    from channels import ALL_COUNTRIES
    return jsonify({
        'total': len(ALL_COUNTRIES),
        'countries': ALL_COUNTRIES
    })

@app.route('/categories/all')
def list_all_categories():
    """عرض جميع التصنيفات"""
    from channels import CATEGORIES
    return jsonify({
        'total': len(CATEGORIES),
        'categories': CATEGORIES
    })

@app.route('/playlist/country/<country_code>')
def get_country_playlist(country_code):
    """جلب قائمة قنوات دولة معينة"""
    from channels import get_country_url
    import requests
    
    url = get_country_url(country_code)
    if not url:
        return jsonify({'error': 'دولة غير مدعومة'}), 404
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'فشل في جلب القائمة'}), 500

@app.route('/playlist/category/<category>')
def get_category_playlist(category):
    """جلب قائمة قنوات تصنيف معين"""
    from channels import get_category_url
    import requests
    
    url = get_category_url(category)
    if not url:
        return jsonify({'error': 'تصنيف غير مدعوم'}), 404
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return Response(
                response.text,
                status=200,
                content_type='application/vnd.apple.mpegurl',
                headers={'Access-Control-Allow-Origin': '*'}
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'فشل في جلب القائمة'}), 500
