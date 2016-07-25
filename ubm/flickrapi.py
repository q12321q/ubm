import webbrowser
import requests
import requests_oauthlib
import logging
from flask import Flask, request
from requests_oauthlib import OAuth1Session
import xml.etree.ElementTree as ET

REQUEST_TOKEN_URL = 'https://www.flickr.com/services/oauth/request_token'
AUTHORIZATION_URL = 'https://www.flickr.com/services/oauth/authorize'
ACCESS_TOKEN_URL = 'https://www.flickr.com/services/oauth/access_token'
API_URL = 'https://api.flickr.com/services/rest'
UPLOAD_API_URL = 'https://up.flickr.com/services/upload'

app = Flask(__name__)

class FlickrAPIError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

@app.route('/callback')
def receive_token():
    oauth_access_token = request.form['access_token']
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


class FlickrAPI:

    SUPPORTED_IMAGE_FILE_TYPES = {
        'jpeg',
        'jpg',
        'png',
        'gif'
    }

    SUPPORTED_VIDEO_FILE_TYPES = {
        'mp4',
        'avi',
        'wmv',
        'mov',
        'mpeg',
        '3gp',
        'm2ts',
        'ogg',
        'ogv'
    }

    def __init__(self,
                 client_key,
                 client_secret,
                 resource_owner_key=None,
                 resource_owner_secret=None):
        self.logger = logging.getLogger(__name__)
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret

    def request_owner_tokens(self):
        user_callback_url = 'http://localhost:7777/'

        # Obtain a request token
        oauth = OAuth1Session(self.client_key,
                              client_secret=self.client_secret,
                              callback_uri=user_callback_url)
        request_token_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)

        request_token = request_token_response.get('oauth_token')
        request_token_secret = request_token_response.get('oauth_token_secret')

        # Obtain authorization from the user
        authorization_url = oauth.authorization_url(AUTHORIZATION_URL)

        try:
            webbrowser.open(authorization_url)
            app.run(
              port=7777,
              host='localhost'
            )
        except webbrowser.Error:
            print('Please go here and authorize %s' % authorization_url)
            verifier = input('Please input the verifier: ')

        # Obtain owner tokens from user verifier and request toekn
        oauth = OAuth1Session(self.client_key,
                              client_secret=self.client_secret,
                              resource_owner_key=request_token,
                              resource_owner_secret=request_token_secret,
                              verifier=verifier)

        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        self.resource_owner_key = oauth_tokens.get('oauth_token')
        self.resource_owner_secret = oauth_tokens.get('oauth_token_secret')

    def session(self):
        """docstring for session"""
        return OAuth1Session(self.client_key,
                             resource_owner_key=self.resource_owner_key,
                             client_secret=self.client_secret,
                             resource_owner_secret=self.resource_owner_secret)

    def _call_api(self, http_method, api_method, key, params=None):
        _params = {
            'nojsoncallback': 1,
            'format': 'json',
            'method': api_method
        }

        if params is not None:
            _params.update(params)

        if http_method == 'GET':
            result = self.session().get(API_URL, params=_params).json()
        elif http_method == 'POST':
            result = self.session().post(API_URL, data=_params).json()
        else:
            raise Exception('Unsuported http method: %s' % http_method)

        if result['stat'] == 'ok':
            return result[key] if key is not None else None
        else:
            raise FlickrAPIError(result)

    def get(self, method, key, params=None, extras=None):
        _params = {}

        if params is not None:
            _params.update(params)

        if extras is not None:
            _params['extras'] = ','.join(extras)

        return self._call_api('GET', method, key, params=_params)

    def get_collection(self,
                       method,
                       key,
                       collection_key,
                       params=None,
                       extras=None):
        _params = {}

        if params is not None:
            _params.update(params)

        page = 1
        pages = 1
        while page <= pages:
            _params['page'] = page
            results = self.get(method, key, params=_params, extras=extras)

            for result in results[collection_key]:
                yield(result)

            pages = int(results['pages'])
            page += 1

    def post(self, method, key, params=None):
        return self._call_api('POST', method, key, params=params)

    ######################
    # API accessors
    ######################

    def test_login(self):
        return self.get('flickr.test.login', 'user')

    ######################
    # Photo
    ######################

    def get_photo_not_in_set(self, extras=None):
        return self.get_collection('flickr.photos.getNotInSet',
                                   'photos',
                                   'photo',
                                   extras=extras)
    ######################
    # Photoset
    ######################

    def get_photosets(self):
        return self.get_collection('flickr.photosets.getList',
                                   'photosets',
                                   'photoset')

    def get_photoset_photos(self, photoset_id, extras=None):
        return self.get_collection('flickr.photosets.getPhotos',
                                   'photoset',
                                   'photo', {
                                       'photoset_id': photoset_id
                                   },
                                   extras=extras)

    def create_photoset(self, title, primary_photo_id, desc=None):
        _params = {
            'title': title,
            'primary_photo_id': primary_photo_id
        }

        if desc is not None:
            _params['description'] = desc

        return self.post('flickr.photosets.create',
                         'photoset',
                         params=_params)

    def add_photo_to_photoset(self, photoset_id, photo_id):
        _params = {
            'photoset_id': photoset_id,
            'photo_id': photo_id
        }

        return self.post('flickr.photosets.addPhoto',
                         None,
                         params=_params)

    ######################
    # Upload photo
    ######################

    def upload_photo(self, filename, title=None, desc=None, tags=None):
        _params = {}

        if title is not None:
            _params['title'] = title

        if desc is not None:
            _params['description'] = desc

        if tags is not None:
            _params['tags'] = ','.join(tags)

        _files = {
            'photo': open(filename, 'rb')
        }

        # simulate a query without the files to get the auth param
        auth = requests_oauthlib.OAuth1(
                        self.client_key,
                        resource_owner_key=self.resource_owner_key,
                        client_secret=self.client_secret,
                        resource_owner_secret=self.resource_owner_secret)
        raw = requests.Request('POST', UPLOAD_API_URL, data=_params, auth=auth)
        prepared = raw.prepare()
        auth = {'Authorization': prepared.headers.get('Authorization')}

        # use the auth without the files param
        result = requests.post(UPLOAD_API_URL, data=_params, headers=auth, files=_files)
        xml = ET.fromstring(result.text)

        if xml.attrib['stat'] == 'ok':
            return {
                'photoid': xml[0].text
            }
        else:
            raise FlickrAPIError(result.text)

