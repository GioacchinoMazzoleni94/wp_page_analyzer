import os
import io
import csv
import json
import ssl
import socket
import requests
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Directory per i report salvati
REPORTS_DIR = 'reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

def fetch_all(endpoint, auth=None, params=None):
    """Recupera tutte le pagine di un endpoint WP REST con paginazione."""
    items = []
    page = 1
    params = params.copy() if params else {}
    while True:
        params.update({'per_page': 100, 'page': page})
        r = requests.get(endpoint, auth=auth, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(r.headers.get('X-WP-TotalPages', 0))
        if page >= total_pages:
            break
        page += 1
    return items

def get_tls_days(hostname):
    """Ritorna i giorni mancanti alla scadenza del certificato TLS."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                exp = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                return (exp - datetime.utcnow()).days
    except Exception:
        return None

def compute_seo_score(seo):
    """Calcola un punteggio SEO di base."""
    score = 0
    if seo.get('title_tag'):
        score += 20
    desc = seo.get('meta_desc', '')
    if 50 <= len(desc) <= 160:
        score += 20
    if seo.get('headings', {}).get('h1', 0) >= 1:
        score += 20
    levels = sum(1 for v in seo.get('headings', {}).values() if v > 0)
    score += min(levels * 5, 40)
    return min(score, 100)

def seo_analyze(link, auth=None):
    """Estrae title, meta, headings e calcola SEO score di una pagina."""
    try:
        r = requests.get(link, auth=auth, timeout=10)
        r.raise_for_status()
    except:
        return {
            'title_tag':'', 'meta_desc':'', 'headings':{}, 'score':0,
            'canonical':'', 'og':{}, 'twitter':{}
        }
    soup = BeautifulSoup(r.text, 'html.parser')
    seo = {
        'title_tag': soup.title.string.strip() if soup.title and soup.title.string else '',
        'meta_desc': (soup.find('meta', {'name':'description'}) or {}).get('content','').strip(),
        'headings': {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1,7)}
    }
    seo['score'] = compute_seo_score(seo)
    seo['canonical'] = (soup.find('link', rel='canonical') or {}).get('href','')
    seo['og'] = {m['property']: m.get('content','') 
                 for m in soup.find_all('meta', property=lambda p:p and p.startswith('og:'))}
    seo['twitter'] = {m['name']: m.get('content','') 
                      for m in soup.find_all('meta', attrs={'name': lambda n:n and n.startswith('twitter:')})}
    return seo

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze/content', methods=['POST'])
def analyze_content():
    d = request.json or {}
    base = d.get('url','').rstrip('/')
    if not base.startswith(('http://','https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    pages = posts = []
    cpts = {}
    media_items = []
    archives_list = []
    errors = []

    # Pagine e Post
    try:
        pages = fetch_all(f"{base}/wp-json/wp/v2/pages", auth)
        posts = fetch_all(f"{base}/wp-json/wp/v2/posts", auth, params={'status':'publish'})
    except RequestException as e:
        errors.append(f"Pages/Posts error: {e}")

    # Custom Post Types
    try:
        types_raw = requests.get(f"{base}/wp-json/wp/v2/types", auth=auth, timeout=10).json()
        public_cpts = [k for k,v in types_raw.items() if v.get('viewable') and k not in ('post','page')]
        for pt in public_cpts:
            try:
                cpts[pt] = fetch_all(f"{base}/wp-json/wp/v2/{pt}", auth, params={'status':'publish'})
            except RequestException:
                cpts[pt] = []
                errors.append(f"CPT {pt} error")
    except RequestException as e:
        errors.append(f"Types error: {e}")

    # Media
    try:
        media = fetch_all(f"{base}/wp-json/wp/v2/media", auth)
        for m in media:
            size = ''
            try:
                head = requests.head(m['source_url'], timeout=5, allow_redirects=True)
                size = head.headers.get('Content-Length','')
            except:
                pass
            media_items.append({
                'id': m['id'],
                'title': m['title']['rendered'],
                'link': m['source_url'],
                'status': 'media',
                'size': size
            })
    except RequestException as e:
        errors.append(f"Media error: {e}")

    # Archivi: categorie, tag, autori, date
    try:
        arch = {}
        cats = fetch_all(f"{base}/wp-json/wp/v2/categories", auth)
        for c in cats:
            link = f"{base}/category/{c['slug']}/"
            arch[link] = {'id':'','title':f"Categoria: {c['name']}",'link':link,'status':'archive'}
        tags = fetch_all(f"{base}/wp-json/wp/v2/tags", auth)
        for t in tags:
            link = f"{base}/tag/{t['slug']}/"
            arch[link] = {'id':'','title':f"Tag: {t['name']}",'link':link,'status':'archive'}
        users = fetch_all(f"{base}/wp-json/wp/v2/users", auth)
        for a in users:
            link = f"{base}/author/{a['slug']}/"
            arch[link] = {'id':'','title':f"Autore: {a['name']}",'link':link,'status':'archive'}
        dates = {p['date'].split('T')[0] for p in posts if 'date' in p}
        for mth in sorted({d[:7] for d in dates}):
            link = f"{base}/{mth}/"
            arch[link] = {'id':'','title':f"Archivio Mensile: {mth}",'link':link,'status':'archive'}
        for y in sorted({d.split('-')[0] for d in dates}):
            link = f"{base}/{y}/"
            arch[link] = {'id':'','title':f"Archivio Annuale: {y}",'link':link,'status':'archive'}
        archives_list = list(arch.values())
    except RequestException as e:
        errors.append(f"Archives error: {e}")

    # Raggruppa
    groups = [
        {'category':'Pagine', 'items': [
            {'id':p['id'], 'title':p['title']['rendered'], 'link':p['link'], 'status':p['status']} 
            for p in pages
        ]},
        {'category':'Post', 'items': [
            {'id':p['id'], 'title':p['title']['rendered'], 'link':p['link'], 'status':p['status']} 
            for p in posts
        ]}
    ]
    for pt, lst in cpts.items():
        groups.append({
            'category':f"CPT - {pt}",
            'items': [
                {'id':i['id'], 'title': i.get('title',{}).get('rendered',i.get('slug')), 
                 'link': i.get('link',''), 'status': i.get('status')}
                for i in lst
            ]
        })
    groups.append({'category':'Media Library', 'items': media_items})
    groups.append({'category':'Archivi', 'items': archives_list})

    summary = {
        'pages': len(pages),
        'posts': len(posts),
        'media': len(media_items),
        'cpts': {pt: len(lst) for pt, lst in cpts.items()},
        'archives': len(archives_list),
        'errors': errors
    }

    return jsonify({'groups': groups, 'summary': summary})

@app.route('/analyze/seo', methods=['POST'])
def analyze_seo():
    d = request.json or {}
    base = d.get('url','').rstrip('/')
    if not base.startswith(('http://','https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    pages = fetch_all(f"{base}/wp-json/wp/v2/pages", auth)
    posts = fetch_all(f"{base}/wp-json/wp/v2/posts", auth, params={'status':'publish'})

    seo_list = []
    for item in pages + posts:
        seo = seo_analyze(item['link'], auth)
        seo_list.append({
            'id': item['id'],
            'title': item['title']['rendered'],
            'link': item['link'],
            'title_tag': seo['title_tag'],
            'meta_desc': seo['meta_desc'],
            'headings': seo['headings'],
            'score': seo['score'],
            'canonical': seo['canonical'],
            'og': seo['og'],
            'twitter': seo['twitter']
        })
    return jsonify(seo_list)

@app.route('/analyze/performance', methods=['POST'])
def analyze_performance():
    d = request.json or {}
    base = d.get('url','').rstrip('/')
    if not base.startswith(('http://','https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    r = requests.get(base, auth=auth, timeout=30)
    return jsonify({
        'status_code': r.status_code,
        'response_time_ms': int(r.elapsed.total_seconds() * 1000),
        'content_length': int(r.headers.get('Content-Length', len(r.content)))
    })

@app.route('/analyze/accessibility', methods=['POST'])
def analyze_accessibility():
    d = request.json or {}
    url = d.get('url','').rstrip('/')
    if not url.startswith(('http://','https://')):
        url = 'https://' + url
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    try:
        r = requests.get(url, auth=auth, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        imgs = soup.find_all('img')
        missing_alt_list = [img.get('src','') for img in imgs if not img.get('alt')]
        missing_alt = len(missing_alt_list)

        fields = soup.find_all(['input','textarea','select'])
        missing_labels = sum(
            0 if (fid := f.get('id')) and soup.find('label', {'for': fid}) else 1
            for f in fields
        )

        links = soup.find_all('a')
        empty_links = sum(1 for a in links if not a.get_text(strip=True))
        skip_links = sum(1 for a in links if a.get('href','').startswith('#'))

        landmarks = sum(len(soup.find_all(tag)) for tag in ['header','nav','main','aside','footer'])
        headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1,7)}

        return jsonify({
            'total_images': len(imgs),
            'missing_alt': missing_alt,
            'missing_labels': missing_labels,
            'empty_links': empty_links,
            'landmarks': landmarks,
            'skip_links': skip_links,
            'headings': headings,
            'missing_alt_list': missing_alt_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/security', methods=['POST'])
def analyze_security():
    d = request.json or {}
    url = d.get('url','').rstrip('/')
    if not url.startswith(('http://','https://')):
        url = 'https://' + url
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    try:
        r = requests.head(url, auth=auth, timeout=10)
        h = r.headers

        hsts = 'Strict-Transport-Security' in h
        hsts_val = h.get('Strict-Transport-Security','')
        max_age = None
        for part in hsts_val.split(';'):
            if 'max-age' in part:
                max_age = part.split('=')[1].strip()

        csp = 'Content-Security-Policy' in h

        raw_cookies = r.headers.get('Set-Cookie','')
        cookies = [c.strip() for c in raw_cookies.split(',') if c]
        http_only = sum('httponly' in c.lower() for c in cookies)
        cookie_secure = any('secure' in c.lower() for c in cookies)

        tls_days = get_tls_days(urlparse(url).hostname)

        return jsonify({
            'hsts': hsts,
            'hsts_max_age': max_age,
            'csp': csp,
            'http_only': http_only,
            'cookie_secure': cookie_secure,
            'xfo': h.get('X-Frame-Options',''),
            'xss': h.get('X-XSS-Protection',''),
            'referrer_policy': h.get('Referrer-Policy',''),
            'tls_days': tls_days,
            'server_header': h.get('Server','')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze/theme-plugin', methods=['POST'])
def analyze_theme_plugin():
    d = request.json or {}
    base = d.get('url','').rstrip('/')
    if not base.startswith(('http://','https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    urls = d.get('urls', [base])
    themes, plugins = set(), set()
    for u in urls:
        try:
            r = requests.get(u, auth=auth, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for tag in soup.find_all(['link','script']):
                src = tag.get('href') or tag.get('src') or ''
                if '/wp-content/themes/' in src:
                    themes.add(src.split('/wp-content/themes/')[1].split('/')[0])
                if '/wp-content/plugins/' in src:
                    plugins.add(src.split('/wp-content/plugins/')[1].split('/')[0])
        except:
            continue
    return jsonify({'themes': sorted(themes), 'plugins': sorted(plugins)})

@app.route('/analyze/users', methods=['POST'])
def analyze_users():
    d = request.json or {}
    base = d.get('url','').rstrip('/')
    if not base.startswith(('http://','https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    try:
        users = fetch_all(f"{base}/wp-json/wp/v2/users", auth)
        result = [{
            'id': u['id'],
            'name': u.get('name',''),
            'link': f"{base}/author/{u.get('slug','')}/"
        } for u in users]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/analyze/broken', methods=['POST'])
def analyze_broken():
    groups = request.json.get('groups', [])
    broken = []
    for g in groups:
        for it in g.get('items', []):
            try:
                r = requests.head(it['link'], timeout=5)
                if r.status_code >= 400:
                    broken.append(it['link'])
            except:
                broken.append(it['link'])
    return jsonify(sorted(set(broken)))

@app.route('/download_csv', methods=['POST'])
def download_csv():
    groups = request.json.get('groups', [])
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(['Categoria','ID','Title','Link','Status','Size'])
    for g in groups:
        for it in g.get('items', []):
            writer.writerow([
                g['category'],
                it.get('id',''),
                it.get('title',''),
                it.get('link',''),
                it.get('status',''),
                it.get('size','')
            ])
    resp = make_response(sio.getvalue())
    resp.headers.update({
        'Content-Disposition': 'attachment; filename=content.csv',
        'Content-Type': 'text/csv'
    })
    return resp

@app.route('/reports/<domain>', methods=['GET'])
def list_reports(domain):
    dom_dir = os.path.join(REPORTS_DIR, domain)
    if not os.path.isdir(dom_dir):
        return jsonify([])
    files = sorted(os.listdir(dom_dir), reverse=True)
    return jsonify([{'filename': f, 'timestamp': f.replace('.json','')} for f in files])

@app.route('/reports/<domain>', methods=['POST'])
def save_report(domain):
    data = request.json or {}
    dom_dir = os.path.join(REPORTS_DIR, domain)
    os.makedirs(dom_dir, exist_ok=True)
    ts = datetime.utcnow().isoformat().replace(':','-')
    path = os.path.join(dom_dir, f"{ts}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'saved': True, 'filename': f"{ts}.json"})

@app.route('/reports/<domain>/<filename>', methods=['DELETE'])
def delete_report(domain, filename):
    path = os.path.join(REPORTS_DIR, domain, filename)
    if os.path.isfile(path):
        os.remove(path)
        return jsonify({'deleted': True})
    return jsonify({'deleted': False}), 404

if __name__ == '__main__':
    app.run(debug=False)
