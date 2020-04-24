"""
    Unnit test
"""

from app import app
import unittest


class FlaskTestCase(unittest.TestCase):

    # Confirm setup was correct
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='json/text')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()

