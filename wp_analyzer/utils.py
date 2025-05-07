# wp_analyzer/utils.py

import os
import ssl
import socket
import json
import subprocess
from datetime import datetime
import requests

def fetch_all(endpoint, auth=None, params=None):
    """
    Recupera tutti gli elementi paginati da un endpoint WordPress REST API.
    Restituisce una lista di oggetti JSON.
    """
    items = []
    page = 1
    params = params.copy() if params else {}
    while True:
        params.update({'per_page': 100, 'page': page})
        resp = requests.get(endpoint, auth=auth, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(resp.headers.get('X-WP-TotalPages', 0))
        if page >= total_pages:
            break
        page += 1
    return items

def get_tls_days(hostname):
    """
    Ritorna i giorni mancanti alla scadenza del certificato TLS di un hostname.
    """
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        exp_str = cert.get('notAfter')
        exp = datetime.strptime(exp_str, '%b %d %H:%M:%S %Y %Z')
        return (exp - datetime.utcnow()).days
    except Exception:
        return None

def compute_seo_score(seo):
    """
    Calcola un punteggio SEO di base sulla base di title, meta description e headings.
    """
    score = 0
    # Title presente?
    if seo.get('title_tag'):
        score += 20
    # Meta description 50-160 char
    desc = seo.get('meta_desc', '')
    if 50 <= len(desc) <= 160:
        score += 20
    # Almeno un H1?
    if seo.get('headings', {}).get('h1', 0) >= 1:
        score += 20
    # Numero di headings totali
    levels = sum(v for v in seo.get('headings', {}).values())
    score += min(levels * 5, 40)
    return min(score, 100)

def run_lighthouse(url, script_path):
    """
    Esegue lo script Node performance.js per generare metriche Lighthouse.
    Restituisce un dict con FCP, LCP, CLS, TBT, SI, TTI e punteggio.
    """
    result = subprocess.run(
        ['node', script_path, url],
        capture_output=True,
        text=True,
        timeout=120
    )
    result.check_returncode()
    return json.loads(result.stdout)
