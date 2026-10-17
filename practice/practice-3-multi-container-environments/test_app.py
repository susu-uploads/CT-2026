"""HTTP-проверки запущенного приложения. --capacity требует пустой тестовой БД."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def request(base, path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = Request(base.rstrip('/') + path, data=payload,
                  headers={'Content-Type': 'application/json'})
    try:
        response = urlopen(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        body = response.read()
        return response.status, body


def check(base, capacity=False):
    assert request(base, '/')[0] == 200
    assert request(base, '/health')[0] == 200
    for text in ['', '   ', 'x' * 501, None, 12]:
        assert request(base, '/api/notes', {'text': text})[0] == 422
    assert request(base, '/api/notes', {})[0] == 422
    assert request(base, '/api/notes', {'text': 'ok', 'extra': 1})[0] == 422
    note = 'Проверка ' + uuid4().hex[:8]
    assert request(base, '/api/notes', {'text': '  ' + note + '  '})[0] == 201
    notes = json.loads(request(base, '/api/notes')[1])['notes']
    assert notes[-1] == note
    html = '<img src=x onerror=alert(1)>'
    assert request(base, '/api/notes', {'text': html})[0] == 201
    assert json.loads(request(base, '/api/notes')[1])['notes'][-2:] == [note, html]
    if capacity:
        assert len(notes) == 1, 'Capacity check requires empty isolated database'
        for i in range(97):
            assert request(base, '/api/notes', {'text': str(i)})[0] == 201
        with ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(lambda i: request(base, '/api/notes', {'text': str(i)})[0], range(16)))
        assert codes.count(201) == 1 and codes.count(409) == 15, codes
        assert len(json.loads(request(base, '/api/notes')[1])['notes']) == 100
    print('HTTP-проверки пройдены:', base, 'capacity=' + str(capacity))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8003')
    parser.add_argument('--capacity', action='store_true')
    args = parser.parse_args()
    check(args.url, args.capacity)
