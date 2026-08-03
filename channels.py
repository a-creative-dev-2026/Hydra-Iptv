# ============================================================
# روابط القنوات المباشرة حسب الدولة والتصنيف
# المصدر: iptv-org.github.io + قنوات محلية
# ============================================================

COUNTRY_CHANNELS = {
    # أفريقيا
    'ng': {'name': 'نيجيريا', 'url': 'https://iptv-org.github.io/iptv/countries/ng.m3u'},
    'eg': {'name': 'مصر', 'url': 'https://iptv-org.github.io/iptv/countries/eg.m3u'},
    'za': {'name': 'جنوب أفريقيا', 'url': 'https://iptv-org.github.io/iptv/countries/za.m3u'},
    'dz': {'name': 'الجزائر', 'url': 'https://iptv-org.github.io/iptv/countries/dz.m3u'},
    'ma': {'name': 'المغرب', 'url': 'https://iptv-org.github.io/iptv/countries/ma.m3u'},
    'tn': {'name': 'تونس', 'url': 'https://iptv-org.github.io/iptv/countries/tn.m3u'},
    'ly': {'name': 'ليبيا', 'url': 'https://iptv-org.github.io/iptv/countries/ly.m3u'},
    'sd': {'name': 'السودان', 'url': 'https://iptv-org.github.io/iptv/countries/sd.m3u'},
    'ke': {'name': 'كينيا', 'url': 'https://iptv-org.github.io/iptv/countries/ke.m3u'},
    'gh': {'name': 'غانا', 'url': 'https://iptv-org.github.io/iptv/countries/gh.m3u'},
    'et': {'name': 'إثيوبيا', 'url': 'https://iptv-org.github.io/iptv/countries/et.m3u'},
    'ao': {'name': 'أنغولا', 'url': 'https://iptv-org.github.io/iptv/countries/ao.m3u'},
    'tz': {'name': 'تنزانيا', 'url': 'https://iptv-org.github.io/iptv/countries/tz.m3u'},
    'ug': {'name': 'أوغندا', 'url': 'https://iptv-org.github.io/iptv/countries/ug.m3u'},
    'cm': {'name': 'الكاميرون', 'url': 'https://iptv-org.github.io/iptv/countries/cm.m3u'},
    'sn': {'name': 'السنغال', 'url': 'https://iptv-org.github.io/iptv/countries/sn.m3u'},
    'ml': {'name': 'مالي', 'url': 'https://iptv-org.github.io/iptv/countries/ml.m3u'},
    'bf': {'name': 'بوركينا فاسو', 'url': 'https://iptv-org.github.io/iptv/countries/bf.m3u'},
    'ne': {'name': 'النيجر', 'url': 'https://iptv-org.github.io/iptv/countries/ne.m3u'},
    'rw': {'name': 'رواندا', 'url': 'https://iptv-org.github.io/iptv/countries/rw.m3u'},
    'mg': {'name': 'مدغشقر', 'url': 'https://iptv-org.github.io/iptv/countries/mg.m3u'},
    'ci': {'name': 'ساحل العاج', 'url': 'https://iptv-org.github.io/iptv/countries/ci.m3u'},
    'cd': {'name': 'الكونغو الديمقراطية', 'url': 'https://iptv-org.github.io/iptv/countries/cd.m3u'},
    'zm': {'name': 'زامبيا', 'url': 'https://iptv-org.github.io/iptv/countries/zm.m3u'},
    'zw': {'name': 'زيمبابوي', 'url': 'https://iptv-org.github.io/iptv/countries/zw.m3u'},
    
    # آسيا (مختصر)
    'sa': {'name': 'السعودية', 'url': 'https://iptv-org.github.io/iptv/countries/sa.m3u'},
    'ae': {'name': 'الإمارات', 'url': 'https://iptv-org.github.io/iptv/countries/ae.m3u'},
    'qa': {'name': 'قطر', 'url': 'https://iptv-org.github.io/iptv/countries/qa.m3u'},
    'kw': {'name': 'الكويت', 'url': 'https://iptv-org.github.io/iptv/countries/kw.m3u'},
    'om': {'name': 'عمان', 'url': 'https://iptv-org.github.io/iptv/countries/om.m3u'},
    'bh': {'name': 'البحرين', 'url': 'https://iptv-org.github.io/iptv/countries/bh.m3u'},
    'jo': {'name': 'الأردن', 'url': 'https://iptv-org.github.io/iptv/countries/jo.m3u'},
    'lb': {'name': 'لبنان', 'url': 'https://iptv-org.github.io/iptv/countries/lb.m3u'},
    'sy': {'name': 'سوريا', 'url': 'https://iptv-org.github.io/iptv/countries/sy.m3u'},
    'iq': {'name': 'العراق', 'url': 'https://iptv-org.github.io/iptv/countries/iq.m3u'},
    'ps': {'name': 'فلسطين', 'url': 'https://iptv-org.github.io/iptv/countries/ps.m3u'},
    'ye': {'name': 'اليمن', 'url': 'https://iptv-org.github.io/iptv/countries/ye.m3u'},
    'tr': {'name': 'تركيا', 'url': 'https://iptv-org.github.io/iptv/countries/tr.m3u'},
    'ir': {'name': 'إيران', 'url': 'https://iptv-org.github.io/iptv/countries/ir.m3u'},
    'pk': {'name': 'باكستان', 'url': 'https://iptv-org.github.io/iptv/countries/pk.m3u'},
    'in': {'name': 'الهند', 'url': 'https://iptv-org.github.io/iptv/countries/in.m3u'},
    'cn': {'name': 'الصين', 'url': 'https://iptv-org.github.io/iptv/countries/cn.m3u'},
    'jp': {'name': 'اليابان', 'url': 'https://iptv-org.github.io/iptv/countries/jp.m3u'},
    'kr': {'name': 'كوريا الجنوبية', 'url': 'https://iptv-org.github.io/iptv/countries/kr.m3u'},
    'id': {'name': 'إندونيسيا', 'url': 'https://iptv-org.github.io/iptv/countries/id.m3u'},
    'my': {'name': 'ماليزيا', 'url': 'https://iptv-org.github.io/iptv/countries/my.m3u'},
    'sg': {'name': 'سنغافورة', 'url': 'https://iptv-org.github.io/iptv/countries/sg.m3u'},
    'ph': {'name': 'الفلبين', 'url': 'https://iptv-org.github.io/iptv/countries/ph.m3u'},
    'th': {'name': 'تايلاند', 'url': 'https://iptv-org.github.io/iptv/countries/th.m3u'},
    'vn': {'name': 'فيتنام', 'url': 'https://iptv-org.github.io/iptv/countries/vn.m3u'},
    
    # أوروبا (مختصر)
    'gb': {'name': 'المملكة المتحدة', 'url': 'https://iptv-org.github.io/iptv/countries/gb.m3u'},
    'fr': {'name': 'فرنسا', 'url': 'https://iptv-org.github.io/iptv/countries/fr.m3u'},
    'de': {'name': 'ألمانيا', 'url': 'https://iptv-org.github.io/iptv/countries/de.m3u'},
    'it': {'name': 'إيطاليا', 'url': 'https://iptv-org.github.io/iptv/countries/it.m3u'},
    'es': {'name': 'إسبانيا', 'url': 'https://iptv-org.github.io/iptv/countries/es.m3u'},
    'ru': {'name': 'روسيا', 'url': 'https://iptv-org.github.io/iptv/countries/ru.m3u'},
    'nl': {'name': 'هولندا', 'url': 'https://iptv-org.github.io/iptv/countries/nl.m3u'},
    'ch': {'name': 'سويسرا', 'url': 'https://iptv-org.github.io/iptv/countries/ch.m3u'},
    'be': {'name': 'بلجيكا', 'url': 'https://iptv-org.github.io/iptv/countries/be.m3u'},
    'se': {'name': 'السويد', 'url': 'https://iptv-org.github.io/iptv/countries/se.m3u'},
    'no': {'name': 'النرويج', 'url': 'https://iptv-org.github.io/iptv/countries/no.m3u'},
    'dk': {'name': 'الدنمارك', 'url': 'https://iptv-org.github.io/iptv/countries/dk.m3u'},
    'fi': {'name': 'فنلندا', 'url': 'https://iptv-org.github.io/iptv/countries/fi.m3u'},
    'pl': {'name': 'بولندا', 'url': 'https://iptv-org.github.io/iptv/countries/pl.m3u'},
    'cz': {'name': 'التشيك', 'url': 'https://iptv-org.github.io/iptv/countries/cz.m3u'},
    'hu': {'name': 'المجر', 'url': 'https://iptv-org.github.io/iptv/countries/hu.m3u'},
    'ro': {'name': 'رومانيا', 'url': 'https://iptv-org.github.io/iptv/countries/ro.m3u'},
    'bg': {'name': 'بلغاريا', 'url': 'https://iptv-org.github.io/iptv/countries/bg.m3u'},
    'gr': {'name': 'اليونان', 'url': 'https://iptv-org.github.io/iptv/countries/gr.m3u'},
    'pt': {'name': 'البرتغال', 'url': 'https://iptv-org.github.io/iptv/countries/pt.m3u'},
    'ie': {'name': 'أيرلندا', 'url': 'https://iptv-org.github.io/iptv/countries/ie.m3u'},
    'at': {'name': 'النمسا', 'url': 'https://iptv-org.github.io/iptv/countries/at.m3u'},
    'ua': {'name': 'أوكرانيا', 'url': 'https://iptv-org.github.io/iptv/countries/ua.m3u'},
    'hr': {'name': 'كرواتيا', 'url': 'https://iptv-org.github.io/iptv/countries/hr.m3u'},
    'sk': {'name': 'سلوفاكيا', 'url': 'https://iptv-org.github.io/iptv/countries/sk.m3u'},
    
    # أمريكا الشمالية
    'us': {'name': 'الولايات المتحدة', 'url': 'https://iptv-org.github.io/iptv/countries/us.m3u'},
    'ca': {'name': 'كندا', 'url': 'https://iptv-org.github.io/iptv/countries/ca.m3u'},
    'mx': {'name': 'المكسيك', 'url': 'https://iptv-org.github.io/iptv/countries/mx.m3u'},
    'cu': {'name': 'كوبا', 'url': 'https://iptv-org.github.io/iptv/countries/cu.m3u'},
    'do': {'name': 'جمهورية الدومينيكان', 'url': 'https://iptv-org.github.io/iptv/countries/do.m3u'},
    'gt': {'name': 'غواتيمالا', 'url': 'https://iptv-org.github.io/iptv/countries/gt.m3u'},
    'hn': {'name': 'هندوراس', 'url': 'https://iptv-org.github.io/iptv/countries/hn.m3u'},
    'sv': {'name': 'السلفادور', 'url': 'https://iptv-org.github.io/iptv/countries/sv.m3u'},
    'ni': {'name': 'نيكاراغوا', 'url': 'https://iptv-org.github.io/iptv/countries/ni.m3u'},
    'cr': {'name': 'كوستاريكا', 'url': 'https://iptv-org.github.io/iptv/countries/cr.m3u'},
    'pa': {'name': 'بنما', 'url': 'https://iptv-org.github.io/iptv/countries/pa.m3u'},
    'jm': {'name': 'جامايكا', 'url': 'https://iptv-org.github.io/iptv/countries/jm.m3u'},
    'ht': {'name': 'هايتي', 'url': 'https://iptv-org.github.io/iptv/countries/ht.m3u'},
    'tt': {'name': 'ترينيداد وتوباغو', 'url': 'https://iptv-org.github.io/iptv/countries/tt.m3u'},
    'pr': {'name': 'بورتوريكو', 'url': 'https://iptv-org.github.io/iptv/countries/pr.m3u'},
    'bs': {'name': 'باهاماس', 'url': 'https://iptv-org.github.io/iptv/countries/bs.m3u'},
    'bb': {'name': 'بربادوس', 'url': 'https://iptv-org.github.io/iptv/countries/bb.m3u'},
    'bz': {'name': 'بليز', 'url': 'https://iptv-org.github.io/iptv/countries/bz.m3u'},
    'gd': {'name': 'غرينادا', 'url': 'https://iptv-org.github.io/iptv/countries/gd.m3u'},
    'lc': {'name': 'سانت لوسيا', 'url': 'https://iptv-org.github.io/iptv/countries/lc.m3u'},
    'vc': {'name': 'سانت فنسنت والغرينادين', 'url': 'https://iptv-org.github.io/iptv/countries/vc.m3u'},
    'ag': {'name': 'أنتيغوا وباربودا', 'url': 'https://iptv-org.github.io/iptv/countries/ag.m3u'},
    'kn': {'name': 'سانت كيتس ونيفيس', 'url': 'https://iptv-org.github.io/iptv/countries/kn.m3u'},
    'dm': {'name': 'دومينيكا', 'url': 'https://iptv-org.github.io/iptv/countries/dm.m3u'},
    'cw': {'name': 'كوراساو', 'url': 'https://iptv-org.github.io/iptv/countries/cw.m3u'},
    
    # أمريكا الجنوبية
    'br': {'name': 'البرازيل', 'url': 'https://iptv-org.github.io/iptv/countries/br.m3u'},
    'ar': {'name': 'الأرجنتين', 'url': 'https://iptv-org.github.io/iptv/countries/ar.m3u'},
    'co': {'name': 'كولومبيا', 'url': 'https://iptv-org.github.io/iptv/countries/co.m3u'},
    'cl': {'name': 'تشيلي', 'url': 'https://iptv-org.github.io/iptv/countries/cl.m3u'},
    'pe': {'name': 'بيرو', 'url': 'https://iptv-org.github.io/iptv/countries/pe.m3u'},
    've': {'name': 'فنزويلا', 'url': 'https://iptv-org.github.io/iptv/countries/ve.m3u'},
    'ec': {'name': 'الإكوادور', 'url': 'https://iptv-org.github.io/iptv/countries/ec.m3u'},
    'bo': {'name': 'بوليفيا', 'url': 'https://iptv-org.github.io/iptv/countries/bo.m3u'},
    'py': {'name': 'باراغواي', 'url': 'https://iptv-org.github.io/iptv/countries/py.m3u'},
    'uy': {'name': 'أوروغواي', 'url': 'https://iptv-org.github.io/iptv/countries/uy.m3u'},
    'gy': {'name': 'غيانا', 'url': 'https://iptv-org.github.io/iptv/countries/gy.m3u'},
    'sr': {'name': 'سورينام', 'url': 'https://iptv-org.github.io/iptv/countries/sr.m3u'},
    
    # أوقيانوسيا
    'au': {'name': 'أستراليا', 'url': 'https://iptv-org.github.io/iptv/countries/au.m3u'},
    'nz': {'name': 'نيوزيلندا', 'url': 'https://iptv-org.github.io/iptv/countries/nz.m3u'},
    'pg': {'name': 'بابوا غينيا الجديدة', 'url': 'https://iptv-org.github.io/iptv/countries/pg.m3u'},
    'fj': {'name': 'فيجي', 'url': 'https://iptv-org.github.io/iptv/countries/fj.m3u'},
    'sb': {'name': 'جزر سليمان', 'url': 'https://iptv-org.github.io/iptv/countries/sb.m3u'},
    'vu': {'name': 'فانواتو', 'url': 'https://iptv-org.github.io/iptv/countries/vu.m3u'},
    'ws': {'name': 'ساموا', 'url': 'https://iptv-org.github.io/iptv/countries/ws.m3u'},
    'to': {'name': 'تونغا', 'url': 'https://iptv-org.github.io/iptv/countries/to.m3u'},
    'ki': {'name': 'كيريباس', 'url': 'https://iptv-org.github.io/iptv/countries/ki.m3u'},
    'fm': {'name': 'ميكرونيزيا', 'url': 'https://iptv-org.github.io/iptv/countries/fm.m3u'},
    'pw': {'name': 'بالاو', 'url': 'https://iptv-org.github.io/iptv/countries/pw.m3u'},
    'mh': {'name': 'جزر مارشال', 'url': 'https://iptv-org.github.io/iptv/countries/mh.m3u'},
    'nr': {'name': 'ناورو', 'url': 'https://iptv-org.github.io/iptv/countries/nr.m3u'},
    'tv': {'name': 'توفالو', 'url': 'https://iptv-org.github.io/iptv/countries/tv.m3u'},
}

# ============================================================
# التصنيفات
# ============================================================

CATEGORIES = {
    'news': {'name': 'أخبار', 'url': 'https://iptv-org.github.io/iptv/categories/news.m3u'},
    'sports': {'name': 'رياضة', 'url': 'https://iptv-org.github.io/iptv/categories/sports.m3u'},
    'movies': {'name': 'أفلام', 'url': 'https://iptv-org.github.io/iptv/categories/movies.m3u'},
    'series': {'name': 'مسلسلات', 'url': 'https://iptv-org.github.io/iptv/categories/series.m3u'},
    'documentary': {'name': 'وثائقي', 'url': 'https://iptv-org.github.io/iptv/categories/documentary.m3u'},
    'religious': {'name': 'ديني', 'url': 'https://iptv-org.github.io/iptv/categories/religious.m3u'},
    'kids': {'name': 'أطفال', 'url': 'https://iptv-org.github.io/iptv/categories/kids.m3u'},
    'music': {'name': 'موسيقى', 'url': 'https://iptv-org.github.io/iptv/categories/music.m3u'},
    'entertainment': {'name': 'ترفيه', 'url': 'https://iptv-org.github.io/iptv/categories/entertainment.m3u'},
    'cooking': {'name': 'طبخ', 'url': 'https://iptv-org.github.io/iptv/categories/cooking.m3u'},
    'lifestyle': {'name': 'نمط حياة', 'url': 'https://iptv-org.github.io/iptv/categories/lifestyle.m3u'},
    'travel': {'name': 'طبيعة وسفر', 'url': 'https://iptv-org.github.io/iptv/categories/travel.m3u'},
    'education': {'name': 'تعليم', 'url': 'https://iptv-org.github.io/iptv/categories/education.m3u'},
    'business': {'name': 'أعمال واقتصاد', 'url': 'https://iptv-org.github.io/iptv/categories/business.m3u'},
    'general': {'name': 'قنوات عامة', 'url': 'https://iptv-org.github.io/iptv/categories/general.m3u'},
}

# ============================================================
# قنوات مشهورة
# ============================================================

POPULAR_CHANNELS = {
    'Al Jazeera': 'https://live-hls-web-aje.getaj.net/AJE/index.m3u8',
    'Al Jazeera Arabic': 'https://live-hls-v3-aja.getaj.net/AJA-V3/index.m3u8',
    'CNN': 'https://cnn-cnninternational-1-eu.rakuten.wurl.tv/63831a0c85fb46b5bf3b9fbd35a2331b.m3u8',
    'BBC': 'https://vs-hls-push-ww-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_news_channel_hd/t=3840/v=pv14/b=5070016/main.m3u8',
    'BBC One': 'https://vs-hls-push-uk-live.akamaized.net/x=4/i=urn:bbc:pips:service:bbc_one_hd/t=3840/v=pv14/b=5070016/main.m3u8',
    'Al Arabiya': 'https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8',
    'France 24': 'https://france24.com/en/live',
    'Russia Today': 'https://rt.com/live',
    'beIN Sports 1': 'https://beinsports.com/live',
    'beIN Sports 2': 'https://beinsports.com/live',
    'Sky Sports': 'https://skysports.com/live',
    'ESPN': 'https://espn.com/live',
    'FOX Sports': 'https://foxsports.com/live',
}

SPORTS_CHANNELS = {
    'beIN Sports 1': 'https://beinsports.com/live',
    'beIN Sports 2': 'https://beinsports.com/live',
    'Sky Sports': 'https://skysports.com/live',
    'ESPN': 'https://espn.com/live',
    'FOX Sports': 'https://foxsports.com/live',
}

# ============================================================
# دوال مساعدة
# ============================================================

def get_country_url(country_code):
    return COUNTRY_CHANNELS.get(country_code, {}).get('url')

def get_country_name(country_code):
    return COUNTRY_CHANNELS.get(country_code, {}).get('name', country_code.upper())

def get_category_url(category):
    return CATEGORIES.get(category, {}).get('url')

def get_all_countries():
    return COUNTRY_CHANNELS

def get_all_categories():
    return CATEGORIES

def get_country_codes():
    return list(COUNTRY_CHANNELS.keys())

def get_popular_channel_url(channel_name):
    return POPULAR_CHANNELS.get(channel_name)
