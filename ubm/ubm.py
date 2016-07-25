import logging
from ubm.setuplogging import setup_logging

# Setup global logging
setup_logging()


class Ubm:

    def __init__(self, loader, uploader):
        self.logger = logging.getLogger(__name__)
        self.loader = loader
        self.uploader = uploader

    def upload(self, root_path):
        self.uploader.upload(self.loader.load(root_path))
