"""Фоновое вычисление TOP-N без записи содержимого CSV в журналы."""
import csv
import io
from decimal import Decimal, InvalidOperation


def top_n(data: bytes, column: str, n: int):
    try:
        csv.field_size_limit(5 * 1024 * 1024)
        reader = csv.reader(io.StringIO(data.decode('utf-8-sig'), newline=''), strict=True)
        headers = next(reader, None)
        if not headers or any(not h.strip() for h in headers) or len(set(headers)) != len(headers):
            return {'error': 'Нужны уникальные непустые заголовки.'}
        if column not in headers:
            return {'error': 'Указанный столбец отсутствует.'}
        index = headers.index(column)
        rows = []
        for number, row in enumerate(reader, 1):
            if number > 50000:
                return {'error': 'Допускается не более 50 000 строк.'}
            if len(row) != len(headers):
                return {'error': 'Число полей строки не совпадает с заголовками.'}
            try:
                value = Decimal(row[index].strip())
            except InvalidOperation:
                return {'error': 'Столбец содержит нечисловое значение.'}
            if not value.is_finite():
                return {'error': 'Столбец содержит бесконечное значение или NaN.'}
            rows.append((value, row))
        rows.sort(key=lambda item: item[0], reverse=True)
        return {'columns': headers, 'rows': [dict(zip(headers, row)) for _, row in rows[:n]]}
    except (UnicodeError, csv.Error):
        return {'error': 'Нужен корректный CSV в UTF-8 с разделителем запятой.'}
