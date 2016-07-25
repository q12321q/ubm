"""
.. module:: localloader
   :platform: Unix, Windows
   :synopsis: Get images and album from a local file structure.

.. moduleauthor:: q12321q <q12321q@gmail.com>

"""
import logging
import os
import os.path
from ubm.photo import Photo
from ubm.album import Album


class LocalLoader:
    """Get images and album from a local file structure.

    """
    def __init__(self, image_file_type):
        """This function does something.

        :param image_file_type: Set of eligible image file extension.
        :type image_file_type: Set.

        """
        self.logger = logging.getLogger(__name__)
        self.image_file_type = image_file_type

    def load(self, root_path):
        """Build from the file structure a list of album and photos.

        :param root_path: root directory where to find the image files.
        :type root_path: str.
        :returns: List of Photo -- List of eligible photo linked with a album.

        """
        albums = {}
        photos = []
        for filename in self._image_files(root_path):
            photo = Photo()
            photo.key = self._photo_key(filename)
            photo.filename = os.path.join(root_path, filename)
            photos.append(photo)

            album_key = self._album_key(filename)
            if album_key is not None:
                if album_key not in albums:
                    albums[album_key] = Album()
                    albums[album_key].key = album_key
                    albums[album_key].title = self._album_name(filename)
                photo.album = albums[album_key]
        return photos

    def _image_files(self, root_path):
        """Get eligible image files.

        :param root_path: root directory where to find image files.
        :type name: str.
        :returns:  generator -- eligible image files.

        """
        for root, dirs, files in os.walk(root_path):
            for file in files:
                filename, file_extension = os.path.splitext(file)
                if file_extension is not None and len(file_extension) > 0:
                    file_extension = file_extension[1:].lower()
                if file_extension in self.image_file_type:
                    yield os.path.relpath(os.path.join(root, file), root_path)

    def _split_dir(self, path):
        """Split a file or directory path parts to a list.

        :param path: file or directory path to split.
        :type path: str.
        :returns: List -- List of the path parts.

        """
        split = []
        while path is not None and path != '':
            head, tail = os.path.split(path)
            split.insert(0, tail)
            path = head
        return split

    def _album_name(self, filename):
        split = self._split_dir(os.path.dirname(filename))
        if len(split) == 0:
            return None
        return ', '.join(split)

    def _album_key(self, filename):
        split = self._split_dir(os.path.dirname(filename))
        if len(split) == 0:
            return None
        return '|'.join(split)

    def _photo_key(self, filename):
        split = self._split_dir(filename)
        if len(split) == 0:
            return None
        return '|'.join(split)
