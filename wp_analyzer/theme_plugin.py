# wp_analyzer/theme_plugin.py

import requests
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

bp = Blueprint('theme_plugin', __name__)

@bp.route('', methods=['POST'])
def analyze_theme_plugin():
    """
    Estrae i temi e i plugin caricati nelle pagine analizzate:
    - Scansiona link <link> e <script> per pattern /wp-content/themes/ e /wp-content/plugins/
    """
    data = request.json or {}
    base = data.get('url', '').rstrip('/')
    if not base.startswith(('http://', 'https://')):
        base = 'https://' + base

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    urls = data.get('urls', [base])
    themes = set()
    plugins = set()

    for u in urls:
        try:
            resp = requests.get(u, auth=auth, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Cerca nei tag link e script
            for tag in soup.find_all(['link', 'script']):
                src = tag.get('href') or tag.get('src') or ''
                if '/wp-content/themes/' in src:
                    # estrae il nome del tema
                    part = src.split('/wp-content/themes/')[1]
                    theme = part.split('/')[0]
                    themes.add(theme)
                if '/wp-content/plugins/' in src:
                    # estrae il nome del plugin
                    part = src.split('/wp-content/plugins/')[1]
                    plugin = part.split('/')[0]
                    plugins.add(plugin)
        except Exception:
            # Ignora errori su singole URL
            continue

    return jsonify({
        'themes': sorted(themes),
        'plugins': sorted(plugins)
    })
