import html.parser
import os.path
import logging
import re
import bitmath
from ubm.flickr_api import FlickrAPI


class FlickrUploader(object):

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
                 resource_owner_secret=None,
                 tags=None):
        self.logger = logging.getLogger(__name__)
        self.flickrAPI = FlickrAPI(client_key,
                                   client_secret,
                                   resource_owner_key,
                                   resource_owner_secret)
        self.photo_cache = None
        self.album_cache = None
        self.photo_in_album_cache = None

        self.tags = tags
        if self.tags is None:
            self.tags = {'ubm'}

        self.key_regexp = re.compile(r'{UBM: "([^"]+)"}', re.IGNORECASE)

    def find_key_from_desc(self, desc):
        desc = html.parser.HTMLParser().unescape(desc)
        match = self.key_regexp.search(desc)
        return match.group(1) if match is not None else None

    def generate_desc(self, key):
        return "{UBM: \"%s\"}" % key

    def init_cache(self):
        self.logger.info('init cache...')
        # init album cache

        self.photo_cache = {}
        self.album_cache = {}
        self.photo_in_album_cache = {}

        photosets = self.flickrAPI.get_photosets()
        for photoset in photosets:
            album_key = self.find_key_from_desc(photoset['description']['_content'])
            if album_key is not None and album_key not in self.album_cache:
                self.album_cache[album_key] = photoset

            photos = self.flickrAPI.get_photoset_photos(photoset['id'], extras={'description'})
            for photo in photos:
                photo_key = self.find_key_from_desc(photo['description']['_content'])
                if photo_key is not None:
                    # and photo_key not in self.album_cache
                    self.photo_cache[photo_key] = photo
                    self.photo_in_album_cache[photo_key] = album_key

        # init photo cache for photo not in photoset
        photos = self.flickrAPI.get_photos_not_in_set(extras={'description'})
        for photo in photos:
            photo_key = self.find_key_from_desc(photo['description']['_content'])
            if photo_key is not None and photo_key not in self.album_cache:
                self.photo_cache[photo_key] = photo

    def photo_exists(self, photo):
        return photo.key in self.photo_cache

    def get_photo_id(self, photo):
        return self.photo_cache[photo.key]['id']

    def album_exists(self, album):
        return album.key in self.album_cache

    def get_album_id(self, album):
        return self.album_cache[album.key]['id']

    def photo_in_album_exists(self, photo):
        return photo.key in self.photo_in_album_cache

    def upload_photo(self, photo):
        desc = self.generate_desc(photo.key)

        result = self.flickrAPI.upload_photo(
                photo.filename,
                title=photo.title,
                desc=desc,
                tags=self.tags)

        self.photo_cache[photo.key] = {
            'id': result['photoid'],
            'title': photo.title,
            'description': desc
        }

    def create_album(self, album, photo):
        desc = self.generate_desc(album.key)
        photoset = self.flickrAPI.create_photoset(
                                album.title,
                                self.get_photo_id(photo),
                                desc=desc)
        self.album_cache[album.key] = {
            'id': photoset['id'],
            'title': album.title,
            'description': desc
        }
        self.photo_in_album_cache[photo.key] = album.key

    def add_photo_to_album(self, photo):
        self.logger.info('link photo %s to album %s',
                         photo.title, photo.album.title)
        self.flickrAPI.add_photo_to_photoset(self.get_album_id(photo.album),
                                             self.get_photo_id(photo))

    def upload(self, photos):
        if not photos:
            self.logger.info('Nothing to upload')
            return

        self.logger.info('Load user flickr data')
        self.init_cache()

        stats = self.compute_upload_stats(photos)

        def format_size(size):
            return bitmath.Byte(size) \
                          .best_prefix().format('{value:.2f} {unit}')

        self.logger.info('stats: photos %s/%s (%s/%s) album %s/%s' % (
                         stats['nb_photos_to_upload'],
                         stats['nb_photos'],
                         format_size(stats['size_photos_to_upload']),
                         format_size(stats['size_photos']),
                         stats['nb_album_to_create'],
                         stats['nb_album']))

        if stats['nb_photos_to_upload'] == 0:
            self.logger.info('Nothing to upload')
            return
        else:
            self.logger.info('Start uploading')

        for photo in photos:
            if not self.photo_exists(photo):
                photo_size = os.path.getsize(photo.filename)
                self.logger.info("Uploading photo: '%s' (%s)",
                                 photo.title,
                                 format_size(photo_size))

                self.upload_photo(photo)
            if photo.album is not None:
                if not self.album_exists(photo.album):
                    self.logger.info("Create album: '%s' with photo '%s'",
                                     photo.album.title,
                                     photo.title)
                    self.create_album(photo.album, photo)
                elif not self.photo_in_album_exists(photo):
                    self.logger.info("Link album: '%s' with photo '%s'",
                                     photo.album.title,
                                     photo.title)
                    self.add_photo_to_album(photo)

        self.logger.info('Done uploading')

    def compute_upload_stats(self, photos):
        nb_photos_to_upload = 0
        size_photos = 0
        size_photos_to_upload = 0
        nb_album_to_create = 0
        uniq_album = {}

        for photo in photos:
            size = os.path.getsize(photo.filename)
            size_photos += size
            if not self.photo_exists(photo):
                nb_photos_to_upload += 1
                size_photos_to_upload += size

            if photo.album is not None:
                uniq_album[photo.album.key] = photo.album
        for key, album in uniq_album.items():
            if not self.album_exists(album):
                nb_album_to_create += 1

        return {
            'nb_photos': len(photos),
            'size_photos': size_photos,
            'nb_photos_to_upload': nb_photos_to_upload,
            'size_photos_to_upload': size_photos_to_upload,
            'nb_album': len(uniq_album),
            'nb_album_to_create': nb_album_to_create
        }
