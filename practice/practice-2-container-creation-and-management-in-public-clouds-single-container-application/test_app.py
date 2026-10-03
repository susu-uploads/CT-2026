"""HTTP-проверка запущенного приложения: python test_app.py [URL]."""

import argparse
import json
import math
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


def get(base_url: str, path: str) -> tuple[int, str, bytes]:
    """Читает HTTP-ответ, включая тело ошибки 4xx."""
    try:
        response = urlopen(base_url.rstrip("/") + path, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers.get_content_type(), response.read()


def check(base_url: str) -> None:
    """Проверяет страницу, API, документацию и обработку ошибочного ввода."""
    status, content_type, body = get(base_url, "/")
    assert status == 200 and content_type == "text/html"
    assert "Калькулятор" in body.decode() and b'id="calculator"' in body
    status, _, body = get(base_url, "/health")
    assert status == 200 and json.loads(body) == {"status": "ok"}
    status, _, body = get(base_url, "/docs")
    assert status == 200 and b"swagger-ui" in body

    for operation, expected in [("add", 8), ("subtract", 4), ("multiply", 12), ("divide", 3)]:
        query = urlencode({"a": 6, "b": 2, "operation": operation})
        status, _, body = get(base_url, "/api/calculate?" + query)
        assert status == 200 and json.loads(body) == {"result": expected}, (operation, body)

    status, _, body = get(base_url, "/api/calculate?a=-1.5&b=0.2&operation=add")
    assert status == 200 and math.isclose(json.loads(body)["result"], -1.3)

    invalid_queries = [
        "a=abc&b=2&operation=add",
        "a=1&b=2&operation=unknown",
        "a=1&operation=add",
        "a=1&b=2",
    ]
    for value in ["nan", "inf", "-inf", "1e999"]:
        for field in ["a", "b"]:
            invalid_queries.append(urlencode({"a": 1, "b": 2, "operation": "add", field: value}))
    for query in invalid_queries:
        status, _, body = get(base_url, "/api/calculate?" + query)
        assert status == 422 and isinstance(json.loads(body)["detail"], list), (query, status, body)

    for query in [
        "a=1&b=0&operation=divide",
        "a=1&b=-0&operation=divide",
        "a=1e308&b=1e308&operation=add",
        "a=1e308&b=1e308&operation=multiply",
        "a=1e308&b=1e-308&operation=divide",
    ]:
        status, _, body = get(base_url, "/api/calculate?" + query)
        assert status == 400 and isinstance(json.loads(body)["detail"], str), (query, status, body)
    print(f"HTTP-проверки пройдены: {base_url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8000")
    check(parser.parse_args().url)
