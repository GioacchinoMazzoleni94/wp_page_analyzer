# wp_analyzer/seo.py

import requests
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from .utils import fetch_all, compute_seo_score

bp = Blueprint('seo', __name__)

def seo_analyze_page(url, auth=None):
    """
    Estrae title, meta description, headings e calcola un punteggio SEO di base.
    """
    try:
        resp = requests.get(url, auth=auth, timeout=10)
        resp.raise_for_status()
    except Exception:
        return {
            'title_tag': '',
            'meta_desc': '',
            'headings': {},
            'score': 0,
            'canonical': '',
            'og': {},
            'twitter': {}
        }

    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.title.string.strip() if soup.title and soup.title.string else ''
    meta_desc = (soup.find('meta', {'name': 'description'}) or {}).get('content', '').strip()
    headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}

    seo = {
        'title_tag': title_tag,
        'meta_desc': meta_desc,
        'headings': headings
    }
    seo['score'] = compute_seo_score(seo)
    seo['canonical'] = (soup.find('link', rel='canonical') or {}).get('href', '')
    seo['og'] = {
        tag['property']: tag.get('content', '')
        for tag in soup.find_all('meta', property=lambda p: p and p.startswith('og:'))
    }
    seo['twitter'] = {
        tag['name']: tag.get('content', '')
        for tag in soup.find_all('meta', attrs={'name': lambda n: n and n.startswith('twitter:')})
    }
    return seo

@bp.route('', methods=['POST'])
def analyze_seo():
    """
    POST JSON { url, username?, password? }
    Restituisce una lista di oggetti SEO per ogni pagina e post pubblicato.
    """
    data = request.json or {}
    base = data.get('url', '').rstrip('/')
    if not base.startswith(('http://', 'https://')):
        base = 'https://' + base

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    # Recupera tutte le pagine e i post pubblici
    pages = fetch_all(f"{base}/wp-json/wp/v2/pages", auth)
    posts = fetch_all(f"{base}/wp-json/wp/v2/posts", auth, params={'status': 'publish'})

    result = []
    for item in pages + posts:
        seo = seo_analyze_page(item['link'], auth)
        result.append({
            'id': item.get('id'),
            'title': item.get('title', {}).get('rendered', ''),
            'link': item.get('link', ''),
            'title_tag': seo['title_tag'],
            'meta_desc': seo['meta_desc'],
            'headings': seo['headings'],
            'score': seo['score'],
            'canonical': seo['canonical'],
            'og': seo['og'],
            'twitter': seo['twitter']
        })

    return jsonify(result)
