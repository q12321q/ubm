from unittest import TestCase
import configparser

from ubm.flickr_uploader import FlickrUploader


class TestFlickrUploader(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = configparser.ConfigParser()
        cls.config.read('/home/q12321q/dev/ubm/ubm/tests/data/test.conf')

        cls.client_key = '8972a563ca68983ae26dfdf3c3a7a214'
        cls.client_secret = '122b5cd56355995e'

        cls.resource_owner_key = '72157671285635295-23b07a9848749bd5'
        cls.resource_owner_secret = '9c557e31908da136'

    def setUp(self):
        self.uploader = FlickrUploader(self.client_key,
                                       self.client_secret,
                                       self.resource_owner_key,
                                       self.resource_owner_secret)

    def test_find_key_from_desc(self):
        self.assertIsNone(self.uploader.find_key_from_desc(''))
        self.assertIsNone(
            self.uploader.find_key_from_desc('safasdf dsafa  asdfas f'))
        self.assertIsNone(
            self.uploader.find_key_from_desc('safasdf {UBM}  asdfas f'))
        self.assertEqual(self.uploader.find_key_from_desc(
                            self.uploader.generate_desc('coucou')),
                         'coucou')
        self.assertEqual(self.uploader.find_key_from_desc(
                            '_%s_' % self.uploader.generate_desc('coucou')),
                         'coucou')

    def test_init_cache(self):
        self.uploader.init_cache()
