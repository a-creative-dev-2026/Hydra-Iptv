# ============================================================
# قنوات ثابتة موثوقة (تم اختبارها)
# ============================================================

STATIC_CHANNELS = {
    'Al Jazeera': {
        'url': 'https://live-hls-web-aje.getaj.net/AJE/index.m3u8',
        'country': 'qa',
        'category': 'news'
    },
    'Al Arabiya': {
        'url': 'https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8',
        'country': 'ae',
        'category': 'news'
    },
    'CNN': {
        'url': 'https://cnn-cnninternational-1-eu.rakuten.wurl.tv/63831a0c85fb46b5bf3b9fbd35a2331b.m3u8',
        'country': 'us',
        'category': 'news'
    },
    'BBC': {
        'url': 'https://vs-hls-push-ww-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_news_channel_hd/t=3840/v=pv14/b=5070016/main.m3u8',
        'country': 'uk',
        'category': 'news'
    },
    'Sky Sports': {
        'url': 'https://rpn.bozztv.com/gusa/gusa-tvssportsbureau/index.m3u8',
        'country': 'uk',
        'category': 'sports'
    },
    'beIN Sports 1': {
        'url': 'https://streams2.sofast.tv/v1/master/611d79b11b77e2f571934fd80ca1413453772ac7/e0b81a5c-6ab5-48cd-aaa9-f82de4ab5bf9/manifest.m3u8',
        'country': 'qa',
        'category': 'sports'
    },
    'beIN Sports 2': {
        'url': 'https://5c7b683162943.streamlock.net/live/ngrp:bahrainsportstwo_all/playlist.m3u8',
        'country': 'bh',
        'category': 'sports'
    },
}

# ============================================================
# روابط الدول الأساسية
# ============================================================

COUNTRY_CHANNELS = {
    'tn': {'name': 'تونس', 'url': 'https://iptv-org.github.io/iptv/countries/tn.m3u'},
    'sa': {'name': 'السعودية', 'url': 'https://iptv-org.github.io/iptv/countries/sa.m3u'},
    'eg': {'name': 'مصر', 'url': 'https://iptv-org.github.io/iptv/countries/eg.m3u'},
    'dz': {'name': 'الجزائر', 'url': 'https://iptv-org.github.io/iptv/countries/dz.m3u'},
    'ma': {'name': 'المغرب', 'url': 'https://iptv-org.github.io/iptv/countries/ma.m3u'},
    'ae': {'name': 'الإمارات', 'url': 'https://iptv-org.github.io/iptv/countries/ae.m3u'},
    'qa': {'name': 'قطر', 'url': 'https://iptv-org.github.io/iptv/countries/qa.m3u'},
    'kw': {'name': 'الكويت', 'url': 'https://iptv-org.github.io/iptv/countries/kw.m3u'},
    'bh': {'name': 'البحرين', 'url': 'https://iptv-org.github.io/iptv/countries/bh.m3u'},
    'om': {'name': 'عمان', 'url': 'https://iptv-org.github.io/iptv/countries/om.m3u'},
    'jo': {'name': 'الأردن', 'url': 'https://iptv-org.github.io/iptv/countries/jo.m3u'},
    'lb': {'name': 'لبنان', 'url': 'https://iptv-org.github.io/iptv/countries/lb.m3u'},
    'sy': {'name': 'سوريا', 'url': 'https://iptv-org.github.io/iptv/countries/sy.m3u'},
    'iq': {'name': 'العراق', 'url': 'https://iptv-org.github.io/iptv/countries/iq.m3u'},
    'ps': {'name': 'فلسطين', 'url': 'https://iptv-org.github.io/iptv/countries/ps.m3u'},
    'ye': {'name': 'اليمن', 'url': 'https://iptv-org.github.io/iptv/countries/ye.m3u'},
    'ly': {'name': 'ليبيا', 'url': 'https://iptv-org.github.io/iptv/countries/ly.m3u'},
    'sd': {'name': 'السودان', 'url': 'https://iptv-org.github.io/iptv/countries/sd.m3u'},
    'us': {'name': 'الولايات المتحدة', 'url': 'https://iptv-org.github.io/iptv/countries/us.m3u'},
    'gb': {'name': 'بريطانيا', 'url': 'https://iptv-org.github.io/iptv/countries/gb.m3u'},
    'fr': {'name': 'فرنسا', 'url': 'https://iptv-org.github.io/iptv/countries/fr.m3u'},
    'de': {'name': 'ألمانيا', 'url': 'https://iptv-org.github.io/iptv/countries/de.m3u'},
    'it': {'name': 'إيطاليا', 'url': 'https://iptv-org.github.io/iptv/countries/it.m3u'},
    'es': {'name': 'إسبانيا', 'url': 'https://iptv-org.github.io/iptv/countries/es.m3u'},
    'tr': {'name': 'تركيا', 'url': 'https://iptv-org.github.io/iptv/countries/tr.m3u'},
}

# ============================================================
# دوال مساعدة
# ============================================================

def get_static_channel(channel_name):
    return STATIC_CHANNELS.get(channel_name, {}).get('url')

def get_country_url(country_code):
    return COUNTRY_CHANNELS.get(country_code, {}).get('url')
