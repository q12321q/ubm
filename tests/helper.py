import os.path
import yaml

from ubm.flickr_api import FlickrAPI

data_root = os.path.join(os.path.dirname(__file__), 'data')
root_path = os.path.join(data_root, 'root_path')

test_conf = None
with open(os.path.join(data_root, 'testconf.yaml'), 'r') as stream:
    test_conf = yaml.load(stream)


def delete_test_data():
    api = FlickrAPI(test_conf['flickr']['client_key'],
                    test_conf['flickr']['client_secret'],
                    test_conf['flickr']['resource_owner_key'],
                    test_conf['flickr']['resource_owner_secret'])
    # Delete photos with the ubm_test tags
    test_photos = api.search_photos({
        'user_id': 'me',
        'tags': test_conf['test_tag']
    })
    for photo in test_photos:
        api.delete_photo(photo['id'])

    # Delete photosets with a title starting with ubm_test
    photosets = api.get_photosets()
    for photoset in photosets:
        if photoset['title']['_content'].startswith(test_conf['test_tag']):
            api.delete_photoset(photoset['id'])
