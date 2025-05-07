# wp_analyzer/content.py

import os
import requests
from flask import Blueprint, request, jsonify
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from .utils import fetch_all


bp = Blueprint('content', __name__)

@bp.route('', methods=['POST'])
def analyze_content():
    d = request.json or {}
    base = d.get('url', '').rstrip('/')
    if not base.startswith(('http://', 'https://')):
        base = 'https://' + base
    auth = HTTPBasicAuth(d.get('username'), d.get('password')) if d.get('username') else None

    pages = []
    posts = []
    cpts = {}
    media_items = []
    archives_list = []
    errors = []

    # Pagine e Post
    try:
        pages = fetch_all(f"{base}/wp-json/wp/v2/pages", auth)
        posts = fetch_all(f"{base}/wp-json/wp/v2/posts", auth, params={'status':'publish'})
    except RequestException as e:
        errors.append(f"Pages/Posts error: {e}")

    # Custom Post Types
    try:
        # types endpoint ritorna un dict, non una lista
        types_resp = requests.get(f"{base}/wp-json/wp/v2/types", auth=auth, timeout=10)
        types_resp.raise_for_status()
        types_raw = types_resp.json()   # dict
        public_cpts = [
            k for k,v in types_raw.items()
            if isinstance(v, dict) and v.get('viewable') and k not in ('post','page')
        ]
        for pt in public_cpts:
            try:
                cpts[pt] = fetch_all(f"{base}/wp-json/wp/v2/{pt}", auth, params={'status':'publish'})
            except RequestException:
                cpts[pt] = []
                errors.append(f"CPT {pt} error")
    except RequestException as e:
        errors.append(f"Types error: {e}")


    # Media
    try:
        media = fetch_all(f"{base}/wp-json/wp/v2/media", auth)
        for m in media:
            size = ''
            try:
                head = requests.head(m['source_url'], timeout=5, allow_redirects=True)
                size = head.headers.get('Content-Length', '')
            except:
                pass
            media_items.append({
                'id': m['id'],
                'title': m['title']['rendered'],
                'link': m['source_url'],
                'status': 'media',
                'size': size
            })
    except RequestException as e:
        errors.append(f"Media error: {e}")

    # Archivi: categorie, tag, autori, date
    try:
        arch = {}
        cats = fetch_all(f"{base}/wp-json/wp/v2/categories", auth)
        for c in cats:
            link = f"{base}/category/{c['slug']}/"
            arch[link] = {'id':'', 'title':f"Categoria: {c['name']}", 'link':link, 'status':'archive'}

        tags = fetch_all(f"{base}/wp-json/wp/v2/tags", auth)
        for t in tags:
            link = f"{base}/tag/{t['slug']}/"
            arch[link] = {'id':'', 'title':f"Tag: {t['name']}", 'link':link, 'status':'archive'}

        users = fetch_all(f"{base}/wp-json/wp/v2/users", auth)
        for a in users:
            link = f"{base}/author/{a['slug']}/"
            arch[link] = {'id':'', 'title':f"Autore: {a['name']}", 'link':link, 'status':'archive'}

        dates = {p['date'].split('T')[0] for p in posts if 'date' in p}
        for mth in sorted({d[:7] for d in dates}):
            link = f"{base}/{mth}/"
            arch[link] = {'id':'', 'title':f"Archivio Mensile: {mth}", 'link':link, 'status':'archive'}
        for y in sorted({d.split('-')[0] for d in dates}):
            link = f"{base}/{y}/"
            arch[link] = {'id':'', 'title':f"Archivio Annuale: {y}", 'link':link, 'status':'archive'}

        archives_list = list(arch.values())
    except RequestException as e:
        errors.append(f"Archives error: {e}")

    # Raggruppa in categorie
    groups = [
        {'category':'Pagine', 'items': [
            {'id': p['id'], 'title': p['title']['rendered'], 'link': p['link'], 'status': p['status']}
            for p in pages
        ]},
        {'category':'Post', 'items': [
            {'id': p['id'], 'title': p['title']['rendered'], 'link': p['link'], 'status': p['status']}
            for p in posts
        ]}
    ]
    for pt, lst in cpts.items():
        groups.append({
            'category': f"CPT - {pt}",
            'items': [
                {'id': i['id'],
                 'title': i.get('title', {}).get('rendered', i.get('slug')),
                 'link': i.get('link', ''),
                 'status': i.get('status')}
                for i in lst
            ]
        })
    groups.append({'category':'Media Library', 'items': media_items})
    groups.append({'category':'Archivi', 'items': archives_list})

    summary = {
        'pages': len(pages),
        'posts': len(posts),
        'media': len(media_items),
        'cpts': {pt: len(lst) for pt, lst in cpts.items()},
        'archives': len(archives_list),
        'errors': errors
    }

    return jsonify({'groups': groups, 'summary': summary})
