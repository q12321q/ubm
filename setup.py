from setuptools import setup

setup(
    name='ubm',
    description=(
        "Upload Backup Media"),
    version='0.1',
    packages=['ubm'],
    zip_safe=False,
    install_requires=[
        'requests',
        'requests_oauthlib',
        'pyyaml',
        'bitmath'
    ],
    entry_points = {
        'console_scripts': [
        ]
    }
)
