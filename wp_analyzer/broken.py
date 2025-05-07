# wp_analyzer/broken.py

import requests
from flask import Blueprint, request, jsonify

bp = Blueprint('broken', __name__)

@bp.route('', methods=['POST'])
def analyze_broken():
    """
    Verifica broken links:
    Riceve JSON { groups: [ { category, items: [ { link } ] } ] }
    Restituisce lista di URL con status >= 400 o errori di connessione.
    """
    data = request.json or {}
    groups = data.get('groups', [])
    broken = set()

    for g in groups:
        for it in g.get('items', []):
            url = it.get('link')
            try:
                # usa HEAD per minimizzare payload
                resp = requests.head(url, timeout=5)
                if resp.status_code >= 400:
                    broken.add(url)
            except Exception:
                broken.add(url)

    return jsonify(sorted(broken))
