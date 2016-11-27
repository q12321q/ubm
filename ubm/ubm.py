import argparse
import yaml
import logging
from ubm.setup_logging import setup_logging
from ubm.local_loader import LocalLoader
from ubm.flickr_uploader import FlickrUploader

# Setup global logging
setup_logging()


class Ubm(object):

    def __init__(self, loader, uploader):
        self.logger = logging.getLogger(__name__)
        self.loader = loader
        self.uploader = uploader

    def upload(self, root_path):
        self.uploader.upload(self.loader.load(root_path))


def main(args=None):
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("-c",
                        "--conf",
                        required=True,
                        help="configuration file")
    if args is not None:
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()

    with open(args.conf, 'r') as conf_file:
        conf = yaml.load(conf_file)

        loader = LocalLoader(FlickrUploader.SUPPORTED_IMAGE_FILE_TYPES)
        uploader = FlickrUploader(conf['flickr']['client_key'],
                                  conf['flickr']['client_secret'],
                                  conf['flickr']['resource_owner_key'],
                                  conf['flickr']['resource_owner_secret'])
        ubm = Ubm(loader, uploader)
        ubm.upload(conf['root_path'])
# config= None
# for loc in os.curdir, os.path.expanduser("~"), "/etc/myproject", os.environ.get("MYPROJECT_CONF"):
#     try: 
#         with open(os.path.join(loc,"myproject.conf")) as source:
#             config.readfp( source )
#     except IOError:
#         pass
if __name__ == '__main__':
    main()
