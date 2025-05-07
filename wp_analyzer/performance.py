# wp_analyzer/performance.py

import requests
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth

bp = Blueprint('performance', __name__)

@bp.route('', methods=['POST'])
def analyze_performance():
    """
    Analisi base di performance:
    restituisce status code, tempo di risposta e content length.
    """
    data = request.json or {}
    base = data.get('url', '').rstrip('/')
    if not base.startswith(('http://', 'https://')):
        base = 'https://' + base

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    try:
        resp = requests.get(base, auth=auth, timeout=30)
        return jsonify({
            'status_code': resp.status_code,
            'response_time_ms': int(resp.elapsed.total_seconds() * 1000),
            'content_length': int(resp.headers.get('Content-Length', len(resp.content)))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
