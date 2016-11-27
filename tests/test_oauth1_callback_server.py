from unittest import TestCase
import requests

from ubm.oauth1_callback_server import OAuthCallbackServer


class TestOAuthCallbackServer(TestCase):
    def test_wait_for_callback_url(self):
        callback_url = 'http://localhost:7777/callback?coucou=hello'
        server = OAuthCallbackServer('localhost', 7777)

        server.start()

        response = requests.get(callback_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'ok')

        self.assertEqual(server.wait_for_callback_url(), callback_url)

        server.stop()
