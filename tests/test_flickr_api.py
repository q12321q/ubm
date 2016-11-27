from unittest import TestCase

from ubm.flickr_api import FlickrAPI, \
                           FlickrAPIError, \
                           request_user_authorization, \
                           Permission

from helper import test_conf, delete_test_data




class TestFlickrAPI(TestCase):

    def setUp(self):
        self.test_tag = test_conf['test_tag']
        self.api = FlickrAPI(test_conf['flickr']['client_key'],
                             test_conf['flickr']['client_secret'],
                             test_conf['flickr']['resource_owner_key'],
                             test_conf['flickr']['resource_owner_secret'])

    def test_request_user_authorization(self):
        auth = request_user_authorization(test_conf['flickr']['client_key'],
                                          test_conf['flickr']['client_secret'],
                                          perms=Permission.delete)
        resource_owner_key = auth['resource_owner_key']
        resource_owner_secret = auth['resource_owner_secret']
        self.assertIsNotNone(resource_owner_key)
        self.assertIsNotNone(resource_owner_secret)

    def test_test_login(self):
        test_login = self.api.test_login()
        self.assertIsNotNone(test_login)
        self.assertEqual(test_login['username']['_content'],
                         'z12321z12321z')

    def test_get_photosets(self):
        photosets = self.api.get_photosets()
        for photoset in photosets:
            print(photoset['title']['_content'])
            photos = self.api.get_photoset_photos(photoset['id'], {'tags'})
            for photo in photos:
                print('  (%s) %s' % (photo['id'], photo['title']))

    # def test_create_photoset(self):
    #     photoset = self.api.create_photoset('coucou from udm', '23795926983')

    def test_upload_photo(self):
        delete_test_data()
        # Upload a photo
        photo_title = 'test_ubm: upload photo test'
        uploaded_photo = self.api.upload_photo(
                '/home/q12321q/Pictures/SalamandraSalamandra_phot_Magura_National_Park_Agnieszka-and-DamianNowak.jpg',
                photo_title,
                tags={self.test_tag})

        self.assertIsNotNone(uploaded_photo['photoid'])

        # Check result
        searched_photo = self.api.get_photo_info(uploaded_photo['photoid'])

        self.assertEqual(searched_photo['id'],
                         uploaded_photo['photoid'],
                         'Ids are the same')

        # Delete uploaded photo
        self.api.delete_photo(uploaded_photo['photoid'])

        with self.assertRaises(FlickrAPIError) as flickrAPIError:
            self.api.get_photo_info(uploaded_photo['photoid'])

        self.assertEqual(flickrAPIError.exception.code, 1)
