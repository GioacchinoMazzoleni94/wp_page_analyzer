# wp_analyzer/users.py

from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from .utils import fetch_all

bp = Blueprint('users', __name__)

@bp.route('', methods=['POST'])
def analyze_users():
    """
    Estrae gli utenti registrati via WP REST API:
    Restituisce lista di oggetti { id, name, link }.
    """
    data = request.json or {}
    base = data.get('url', '').rstrip('/')
    if not base.startswith(('http://', 'https://')):
        base = 'https://' + base

    auth = None
    if data.get('username'):
        auth = HTTPBasicAuth(data['username'], data.get('password', ''))

    try:
        users = fetch_all(f"{base}/wp-json/wp/v2/users", auth)
        result = []
        for u in users:
            result.append({
                'id': u.get('id'),
                'name': u.get('name', ''),
                'link': f"{base}/author/{u.get('slug', '')}/"
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
