# أضف هذه الدوال الجديدة بدل القديمة

def _search_github_api(self, channel_name):
    """البحث في مستودعات GitHub باستخدام واجهة API"""
    try:
        # البحث في مستودع iptv-org مباشرة (أكثر موثوقية)
        url = f"https://raw.githubusercontent.com/iptv-org/iptv/master/playlist.m3u"
        response = self.session.get(url, timeout=15)
        if response.status_code == 200:
            pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            return matches
    except:
        pass
    
    # محاولة البحث في مستودعات أخرى
    repos = [
        'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
        'https://raw.githubusercontent.com/iptv-hub/iptv-hub/main/playlist.m3u'
    ]
    for repo in repos:
        try:
            response = self.session.get(repo, timeout=10)
            if response.status_code == 200:
                pattern = rf'#EXTINF:.*,.*{re.escape(channel_name)}.*\n(https?://[^\s]+)'
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    return matches
        except:
            continue
    return []

def _search_web_alternative(self, channel_name):
    """استخدام محركات بحث بديلة (بدلاً من Google)"""
    try:
        # استخدام DuckDuckGo (أقل حجباً)
        url = f"https://html.duckduckgo.com/html/?q={channel_name.replace(' ', '+')}+m3u8+live"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = self.session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            return matches
    except:
        pass
    
    # استخدام Yandex كبديل
    try:
        url = f"https://yandex.com/search/?text={channel_name.replace(' ', '+')}+m3u8"
        response = self.session.get(url, timeout=10)
        if response.status_code == 200:
            pattern = r'(https?://[^\s"\']+\.m3u8[^\s"\']*)'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            return matches
    except:
        pass
    
    return []
