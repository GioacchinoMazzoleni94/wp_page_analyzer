import json
from unittest.mock import patch, Mock
from wp_analyzer import create_app

app = create_app()


def test_download_csv():
    client = app.test_client()
    groups = [
        {'category': 'Pages', 'items': [
            {'id': 1, 'title': 'Home', 'link': 'http://example.com', 'status': 'publish'}
        ]}
    ]
    resp = client.post('/download_csv', json={'groups': groups})
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    data = resp.get_data(as_text=True)
    assert 'category,id,title,link,status' in data
    assert 'Pages,1,Home,http://example.com,publish' in data


def test_performance_endpoint():
    client = app.test_client()
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.elapsed.total_seconds.return_value = 0.1
    mock_resp.headers = {'Content-Length': '123'}
    with patch('requests.get', return_value=mock_resp):
        resp = client.post('/analyze/performance', json={'url': 'https://example.com'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status_code'] == 200
    assert data['content_length'] == 123
