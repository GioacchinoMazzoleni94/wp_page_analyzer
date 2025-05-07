# wp_analyzer/reports.py

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response

bp = Blueprint('reports', __name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

@bp.route('/<domain>', methods=['GET'])
def list_reports(domain):
    """
    Lista i report salvati per un dominio.
    """
    dom_dir = os.path.join(REPORTS_DIR, domain)
    if not os.path.isdir(dom_dir):
        return jsonify([])
    files = sorted(os.listdir(dom_dir), reverse=True)
    return jsonify([{
        'filename': f,
        'timestamp': f.replace('.json', '')
    } for f in files])

@bp.route('/<domain>', methods=['POST'])
def save_report(domain):
    """
    Salva un report JSON per un dominio.
    """
    data = request.json or {}
    dom_dir = os.path.join(REPORTS_DIR, domain)
    os.makedirs(dom_dir, exist_ok=True)
    ts = datetime.utcnow().isoformat().replace(':', '-')
    filename = f"{ts}.json"
    path = os.path.join(dom_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'saved': True, 'filename': filename})

@bp.route('/<domain>/<filename>', methods=['DELETE'])
def delete_report(domain, filename):
    """
    Elimina un report specifico.
    """
    path = os.path.join(REPORTS_DIR, domain, filename)
    if os.path.isfile(path):
        os.remove(path)
        return jsonify({'deleted': True})
    else:
        return jsonify({'deleted': False}), 404

@bp.route('/<domain>/<filename>', methods=['GET'])
def download_report(domain, filename):
    """
    Scarica un report specifico come JSON.
    """
    path = os.path.join(REPORTS_DIR, domain, filename)
    if not os.path.isfile(path):
        return jsonify({'error': 'Not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    resp = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    resp.mimetype = 'application/json'
    return resp
