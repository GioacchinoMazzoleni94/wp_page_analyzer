# wp_analyzer/lighthouse.py

import os
import json
import subprocess
from flask import Blueprint, request, jsonify
from .utils import run_lighthouse

bp = Blueprint('lighthouse', __name__)

@bp.route('', methods=['POST'])
def analyze_lighthouse():
    """
    Endpoint POST /analyze/lighthouse
    Riceve JSON { url, username?, password? } (le credenziali
    non vengono usate da Lighthouse, ma tenute per coerenza).
    Restituisce le metriche Lighthouse principali.
    """
    data = request.json or {}
    url = data.get('url', '').rstrip('/')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # path allo script performance.js all’interno della cartella static/js
    script_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'static', 'js', 'performance.mjs'
    )


    try:
        metrics = run_lighthouse(url, script_path)
        return jsonify(metrics)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.stderr.strip()}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
