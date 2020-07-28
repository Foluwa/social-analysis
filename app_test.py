"""
    Unnit test
"""
import unittest
import json
from app import app


# Flask app test class
class AppCase(unittest.TestCase):

    # Confirm setup was correct
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='json/text')
        self.assertEqual(response.status_code, 200)

    #
    def test_twitter_analyse_sentiment(self):
        tester = app.test_client(self)
        payload = json.dumps({
            "data": "HapticsNG"
        })
        response = tester.post('/v1/api/analyse', headers={"Content-Type": "application/json"}, data=payload)
        self.assertEqual(200, response.status_code)

    #
    def test_get_collection_names(self):
        tester = app.test_client(self)
        response = tester.get('/get/collection', headers={"Content-Type": "application/json"})
        self.assertEqual(200, response.status_code)

    #
    def previous_searches_collection(self):
        tester = app.test_client(self)
        response = tester.get('/get-previous-values/id')
        self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
