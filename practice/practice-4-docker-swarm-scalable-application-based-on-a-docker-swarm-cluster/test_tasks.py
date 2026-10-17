"""Проверки чистого CSV-вычисления без Redis."""
import unittest
from tasks import top_n


class CSVTests(unittest.TestCase):
    def test_stable_numeric_sort(self):
        value = top_n(b'name,value\na,10\nb,2\nc,10\n', 'value', 2)
        self.assertEqual([row['name'] for row in value['rows']], ['a', 'c'])

    def test_bom_and_quoted_fields(self):
        value = top_n('\ufeffname,value\n"a,b",2\n'.encode(), 'value', 3)
        self.assertEqual(value['rows'], [{'name': 'a,b', 'value': '2'}])

    def test_invalid_csv(self):
        for data in [b'', b'a,a\n1,2', b'value\nNaN', b'value\nInfinity', b'value\n"oops']:
            with self.subTest(data=data):
                self.assertIn('error', top_n(data, 'value', 3))

    def test_row_limit(self):
        self.assertIn('error', top_n(b'value\n'+b'1\n'*50001, 'value', 1))

    def test_empty_table(self):
        self.assertEqual(top_n(b'value\n', 'value', 1)['rows'], [])


if __name__ == '__main__':
    unittest.main()
