from enum import Enum
import webbrowser
import requests
import requests_oauthlib
import logging
from requests_oauthlib import OAuth1Session
import xml.etree.ElementTree as ET

from ubm.oauth1_callback_server import OAuthCallbackServer

REQUEST_TOKEN_URL = 'https://www.flickr.com/services/oauth/request_token'
AUTHORIZATION_URL = 'https://www.flickr.com/services/oauth/authorize'
ACCESS_TOKEN_URL = 'https://www.flickr.com/services/oauth/access_token'
API_URL = 'https://api.flickr.com/services/rest'
UPLOAD_API_URL = 'https://up.flickr.com/services/upload'


class Permission(Enum):
    read = 1
    write = 2
    delete = 3


def request_user_authorization(client_key,
                               client_secret,
                               perms=Permission.write):
    user_callback_url_host = 'localhost'
    user_callback_url_port = 7777
    user_callback_url = 'http://%s:%s/callback' % (
        user_callback_url_host,
        user_callback_url_port
    )

    # Obtain a request token
    oauth = OAuth1Session(client_key,
                          client_secret=client_secret,
                          callback_uri=user_callback_url)
    request_token_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)

    request_token = request_token_response.get('oauth_token')
    request_token_secret = request_token_response.get('oauth_token_secret')

    # Obtain authorization from the user
    authorization_url = oauth.authorization_url(AUTHORIZATION_URL)
    if perms is not None:
        authorization_url += '&perms=%s' % perms.name

    try:
        webbrowser.open(authorization_url)

        server = OAuthCallbackServer(user_callback_url_host,
                                     user_callback_url_port)
        server.start()

        callback_url_with_tokens = server.wait_for_callback_url()

        server.stop()

        oauth_response = oauth.parse_authorization_response(
                                      callback_url_with_tokens)
        verifier = oauth_response['oauth_verifier']
    except webbrowser.Error:
        print('Please go here and authorize %s' % authorization_url)
        verifier = input('Please input the verifier: ')

    # Obtain owner tokens from user verifier and request toekn
    oauth = OAuth1Session(client_key,
                          client_secret=client_secret,
                          resource_owner_key=request_token,
                          resource_owner_secret=request_token_secret,
                          verifier=verifier)

    oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    return {
        'resource_owner_key': oauth_tokens.get('oauth_token'),
        'resource_owner_secret': oauth_tokens.get('oauth_token_secret')
    }


class FlickrAPIError(Exception):
    def __init__(self, value, code=None, message=None):
        self.value = value
        self.code = code
        self.message = message

    def __str__(self):
        return repr(self.value)


class FlickrAPI(object):

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
                 resource_owner_key,
                 resource_owner_secret):
        self.logger = logging.getLogger(__name__)
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret

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
            raise FlickrAPIError(result,
                                 code=int(result['code']),
                                 message=result['message'])

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

    def get_photo_info(self, photo_id):
        return self.get('flickr.photos.getInfo',
                        'photo',
                        params={
                            'photo_id': photo_id
                        })

    def search_photos(self, params, extras=None):
        return self.get_collection('flickr.photos.search',
                                   'photos',
                                   'photo',
                                   params=params,
                                   extras=extras)

    def delete_photo(self, photo_id):
        return self.post('flickr.photos.delete',
                         None,
                         params={
                             'photo_id': photo_id
                         })

    def get_photos_not_in_set(self, extras=None):
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

    def delete_photoset(self, photoset_id):
        self.post('flickr.photosets.delete',
                  None,
                  params={
                      'photoset_id': photoset_id
                  })

    def add_photo_to_photoset(self, photoset_id, photo_id):
        return self.post('flickr.photosets.addPhoto',
                         None,
                         params={
                            'photoset_id': photoset_id,
                            'photo_id': photo_id
                         })

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
        result = requests.post(UPLOAD_API_URL,
                               data=_params,
                               headers=auth,
                               files=_files)
        xml = ET.fromstring(result.text)

        if xml.attrib['stat'] == 'ok':
            return {
                'photoid': xml[0].text
            }
        else:
            raise FlickrAPIError(result.text,
                                 code=int(xml[0].attrib['code']),
                                 message=xml[0].attrib['msg'])
