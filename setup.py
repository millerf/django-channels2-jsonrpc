import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-channels2-jsonrpc',
    version='1.4.0',
    packages=find_packages(),
    install_requires=[
          'channels'
      ],
    include_package_data=True,
    license='MIT License',
    description='A JSON-RPC implementation for Django channels 2 consumers.',
    long_description='Works with django channels. See README on gihub repo',
    url='https://github.com/millerf/django-channels2-jsonrpc/',
    author='Fabien Millerand - MILLER/f',
    author_email='fab@millerf.com',
    tests_require=['django', 'channels'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)