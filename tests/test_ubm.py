from unittest import TestCase
from ubm.local_loader import LocalLoader
from ubm.flickr_uploader import FlickrUploader
from ubm.ubm import Ubm

from helper import test_conf, root_path, delete_test_data


class TestOAuthlib(TestCase):

    def setUp(self):
        self.loader = LocalLoader(FlickrUploader.SUPPORTED_IMAGE_FILE_TYPES)
        self.uploader = FlickrUploader(test_conf['flickr']['client_key'],
                                       test_conf['flickr']['client_secret'],
                                       test_conf['flickr']['resource_owner_key'],
                                       test_conf['flickr']['resource_owner_secret'])
        self.ubm = Ubm(self.loader, self.uploader)

    def test_upload(self):
        delete_test_data()
        self.ubm.upload(root_path)
