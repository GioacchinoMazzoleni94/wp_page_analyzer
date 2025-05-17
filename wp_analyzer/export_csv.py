import csv
from io import StringIO
from flask import Blueprint, request, make_response

bp = Blueprint('export_csv', __name__)

@bp.route('/download_csv', methods=['POST'])
def download_csv():
    data = request.json or {}
    groups = data.get('groups', [])

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['category', 'id', 'title', 'link', 'status'])
    for group in groups:
        category = group.get('category', '')
        for item in group.get('items', []):
            writer.writerow([
                category,
                item.get('id', ''),
                item.get('title', ''),
                item.get('link', ''),
                item.get('status', '')
            ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Disposition'] = 'attachment; filename=content.csv'
    resp.mimetype = 'text/csv'
    return resp
