# wp_analyzer/accessibility.py

import requests
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

bp = Blueprint('accessibility', __name__)

@bp.route('', methods=['POST'])
def analyze_accessibility():
    """
    Analizza l'accessibilità della pagina:
    - Verifica alt mancanti per le immagini
    - Input senza label
    - Link senza testo
    - Skip link
    - Conteggio landmark e headings
    """
    data = request.json or {}
    url = data.get('url', '').rstrip('/')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    try:
        resp = requests.get(url, auth=auth, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Immagini senza alt
        imgs = soup.find_all('img')
        missing_alt_list = [img.get('src', '') for img in imgs if not img.get('alt')]
        missing_alt = len(missing_alt_list)

        # Campi form senza label
        fields = soup.find_all(['input', 'textarea', 'select'])
        missing_labels = 0
        for f in fields:
            fid = f.get('id')
            if not (fid and soup.find('label', {'for': fid})):
                missing_labels += 1

        # Link vuoti e skip-link
        links = soup.find_all('a')
        empty_links = 0
        empty_links_list = []
        skip_links = 0
        for a in links:
            href = a.get('href', '') or ''
            text = a.get_text(strip=True)
            if href.startswith('#'):
                skip_links += 1
            if not text:
                empty_links += 1
                empty_links_list.append(href)

        # Landmark e headings
        landmarks = sum(len(soup.find_all(tag)) for tag in ['header', 'nav', 'main', 'aside', 'footer'])
        headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}

        return jsonify({
            'total_images': len(imgs),
            'missing_alt': missing_alt,
            'missing_labels': missing_labels,
            'empty_links': empty_links,
            'empty_links_list': empty_links_list,
            'skip_links': skip_links,
            'landmarks': landmarks,
            'headings': headings,
            'missing_alt_list': missing_alt_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
