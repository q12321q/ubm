from requests_oauthlib import OAuth1Session
from unittest import TestCase

client_key = '8972a563ca68983ae26dfdf3c3a7a214'
client_secret = '122b5cd56355995e'

resource_owner_key = '72157671285635295-23b07a9848749bd5'
resource_owner_secret = '9c557e31908da136'

class TestOAuthlib(TestCase):
    def test_authentication(self):
        request_token_url = 'https://www.flickr.com/services/oauth/request_token?oauth_callback=http://localhost:7777/oauthcb/'

        # Using OAuth1Session
        oauth = OAuth1Session(client_key, client_secret=client_secret)
        fetch_response = oauth.fetch_request_token(request_token_url)

        resource_owner_key = fetch_response.get('oauth_token')
        self.assertIsNotNone(resource_owner_key)
        self.assertGreater(len(resource_owner_key), 5)
        resource_owner_secret = fetch_response.get('oauth_token_secret')
        self.assertIsNotNone(resource_owner_secret)
        self.assertGreater(len(resource_owner_key), 5)

        # Obtain authorization from the user
        base_authorization_url = 'https://www.flickr.com/services/oauth/authorize'

        authorization_url = oauth.authorization_url(base_authorization_url)
        print('Please go here and authorize,', authorization_url)

        verifier = input('Please input the verifier')
        self.assertIsNotNone(verifier)
        self.assertGreater(len(verifier), 5)

        access_token_url = 'https://www.flickr.com/services/oauth/access_token'

        oauth = OAuth1Session(client_key,
                              client_secret=client_secret,
                              resource_owner_key=resource_owner_key,
                              resource_owner_secret=resource_owner_secret,
                              verifier=verifier)


        oauth_tokens = oauth.fetch_access_token(access_token_url)
        resource_owner_key = oauth_tokens.get('oauth_token')
        self.assertIsNotNone(resource_owner_key)
        self.assertGreater(len(resource_owner_key), 5)
        resource_owner_secret = oauth_tokens.get('oauth_token_secret')
        self.assertIsNotNone(resource_owner_secret)
        self.assertGreater(len(resource_owner_key), 5)


        protected_url = 'https://api.flickr.com/services/rest?format=json&method=flickr.test.login'

        # Using OAuth1Session
        oauth = OAuth1Session(client_key,
                              resource_owner_key=resource_owner_key,
                              client_secret=client_secret,
                              resource_owner_secret=resource_owner_secret)
        r = oauth.get(protected_url)
        print(r.text)

    # def test_authentication2(self):
    #     url = 'https://api.flickr.com/services/rest'
    #     client = requests_oauthlib.OAuth1(client_key,
    #                                       client_secret=client_secret)
    #     params = {'method': 'flickr.test.login', 'format': 'json'}
    #     response = requests.get(url, params=params, auth=client)
    #     import pdb
    #     pdb.set_trace()
    #     print(response.text)
    #
    # def test_connection2(self):
    #     flickr = 'http://up.flickr.com/services/upload/'
    #     client = requests_oauthlib.OAuth1('your_client_key', '....')
    #     data = {'title': 'sometitle', 'description': '...'}
    #     raw = requests.Request('POST', flickr, data=data, auth=client)
    #     prepared = raw.prepare()
    #     auth = {'Authorization': prepared.headers.get('Authorization')}
    #     requests.post(flickr,
    #                   data=data,
    #                   headers=auth,
    #                   files=(('photo', '/home/you/photo.jpg'),))
    #     prepared.headers.get('Authorization')
