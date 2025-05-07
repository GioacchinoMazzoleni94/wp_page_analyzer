# wp_analyzer/security.py

import requests
import json
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from .utils import get_tls_days

bp = Blueprint('security', __name__)

@bp.route('', methods=['POST'])
def analyze_security():
    """
    Analizza header di sicurezza HTTP:
    - HSTS, CSP
    - HttpOnly e Secure cookie
    - X-Frame-Options, X-XSS-Protection, Referrer-Policy
    - Scadenza certificato TLS
    - Server header
    """
    data = request.json or {}
    url = data.get('url', '').rstrip('/')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    try:
        resp = requests.head(url, auth=auth, timeout=10)
        headers = resp.headers

        # HSTS
        hsts = 'Strict-Transport-Security' in headers
        hsts_val = headers.get('Strict-Transport-Security', '')
        max_age = None
        for part in hsts_val.split(';'):
            if 'max-age' in part:
                max_age = part.split('=', 1)[1].strip()

        # CSP
        csp = 'Content-Security-Policy' in headers

        # Cookie flags
        raw_cookies = headers.get('Set-Cookie', '')
        cookies = [c.strip() for c in raw_cookies.split(',') if c]
        http_only = sum('httponly' in c.lower() for c in cookies)
        cookie_secure = any('secure' in c.lower() for c in cookies)

        # Other headers
        xfo = headers.get('X-Frame-Options', '')
        xss = headers.get('X-XSS-Protection', '')
        referrer_policy = headers.get('Referrer-Policy', '')

        # TLS days
        hostname = url.split('//', 1)[-1].split('/', 1)[0]
        tls_days = get_tls_days(hostname)

        server_header = headers.get('Server', '')

        return jsonify({
            'hsts': hsts,
            'hsts_max_age': max_age,
            'csp': csp,
            'http_only': http_only,
            'cookie_secure': cookie_secure,
            'xfo': xfo,
            'xss': xss,
            'referrer_policy': referrer_policy,
            'tls_days': tls_days,
            'server_header': server_header
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
