from unittest import TestCase
import os
import os.path
import configparser

from ubm.local_loader import LocalLoader
from ubm.flickr_uploader import FlickrUploader


class TestLocalLoader(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = configparser.ConfigParser()
        cls.root_path = '/home/q12321q/dev/ubm/ubm/tests/data/root_path'

    def setUp(self):
        self.loader = LocalLoader(FlickrUploader.SUPPORTED_IMAGE_FILE_TYPES)

    def test_image_files(self):
        file_count = 0
        file_presence = False
        for filename in self.loader._image_files(self.root_path):
            if filename == os.path.join('test_encoding_ÛÜÝÎÏÐ', '1000px-ASCII-Table-wide.svg.png'):
                file_presence = True
            file_count += 1

        self.assertEqual(file_count, 8)
        self.assertTrue(file_presence, "'1000px-ASCII-Table-wide.svg.png' is found")

    def test_split_dir(self):
        self.assertListEqual(self.loader._split_dir(''), [])
        testValue = ['qasd']
        self.assertListEqual(self.loader._split_dir(os.path.join(*testValue)), testValue)
        testValue = ['sdfds', 'qasd']
        self.assertListEqual(self.loader._split_dir(os.path.join(*testValue)), testValue)

    def test_album_name(self):
        self.assertIsNone(self.loader._album_name(''))
        self.assertIsNone(self.loader._album_name('test.png'))
        self.assertEqual(self.loader._album_name('coucou/test.png'),
                         'coucou')
        self.assertEqual(self.loader._album_name('hello/coucou/test.png'),
                         'hello, coucou')

    def test_album_key(self):
        self.assertIsNone(self.loader._album_key(''))
        self.assertIsNone(self.loader._album_key('test.png'))
        self.assertEqual(self.loader._album_key('coucou/test.png'),
                         'coucou')
        self.assertEqual(self.loader._album_key('hello/coucou/test.png'),
                         'hello|coucou')


