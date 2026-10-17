"""HTTP-проверки. --capacity выполнять только с остановленными worker и пустой очередью."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def request(base, path, data=None, column='value', n=2):
    headers = {}
    if data is not None:
        boundary = uuid4().hex
        body = bytearray()
        for key, value in [('column', column), ('n', str(n))]:
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode())
        body.extend(data)
        body.extend(f'\r\n--{boundary}--\r\n'.encode())
        data = bytes(body)
        headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
    try:
        response = urlopen(Request(base.rstrip('/')+path, data=data, headers=headers), timeout=20)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if response.headers.get_content_type() == 'application/json' else raw


def wait(base, job_id):
    for _ in range(150):
        code, value = request(base, '/jobs/' + job_id)
        assert code == 200, (code, value)
        if value['status'] in ('finished', 'failed'):
            return value
        time.sleep(.2)
    raise AssertionError('Job did not finish: ' + job_id)


def submit(base, data, **kwargs):
    code, value = request(base, '/jobs', data, **kwargs)
    assert code == 202, (code, value)
    return wait(base, value['job_id'])


def check(base):
    assert request(base, '/')[0] == 200
    assert request(base, '/health')[0] == 200
    assert 'instance' in request(base, '/instance')[1]
    assert request(base, '/jobs/' + uuid4().hex)[0] == 404
    assert request(base, '/jobs/not-an-id')[0] == 404
    data = b'name,value\na,3\nb,8\nc,8\nd,-2\n'
    result = submit(base, data)
    assert result['status'] == 'finished', result
    assert [r['name'] for r in result['result']['rows']] == ['b', 'c']
    result = submit(base, b'\xef\xbb\xbf' + data, n=100)
    assert [r['name'] for r in result['result']['rows']] == ['b', 'c', 'a', 'd']
    result = submit(base, b' value \n7\n', column=' value ')
    assert result['status'] == 'finished', result
    assert request(base, '/jobs', data, column='   ')[0] == 422
    for invalid, column in [(b'a,a\n1,2\n','a'), (b'a,\n1,2\n','a'), (data,'missing'),
                            (b'value\nNaN\n','value'), (b'value\nInfinity\n','value'),
                            (b'value\noops\n','value'), (b'value\n"unclosed\n','value'),
                            (b'value,x\n1\n','value'), (b'\xff','value'),
                            (b'value\n'+b'1\n'*50001,'value')]:
        result = submit(base, invalid, column=column)
        assert result['status'] == 'failed' and 'error' in result, result
    for n in [0, 101]:
        assert request(base, '/jobs', data, n=n)[0] == 422
    assert request(base, '/jobs', b'')[0] == 422
    assert request(base, '/jobs', b'x'*(5*1024*1024+1))[0] == 413
    print('CSV/API checks passed:', base)


def capacity(base):
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda _: request(base, '/jobs', b'value\n2\n'), range(16)))
    codes = [code for code, _ in responses]
    assert codes.count(202) == 10 and codes.count(429) == 6, codes
    print('Queue capacity passed: 10 accepted, 6 rejected')
    return [value['job_id'] for code, value in responses if code == 202]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8005')
    parser.add_argument('--capacity', action='store_true')
    args = parser.parse_args()
    if args.capacity:
        print(json.dumps(capacity(args.url)))
    else:
        check(args.url)
