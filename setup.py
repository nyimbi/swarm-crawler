#!/usr/bin/env python

from importlib import import_module

import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test


def package_env(file_name, strict=False):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path) or strict:
        return open(file_path).read()
    else:
        return ''

PROJECT = 'swarm-crawler'

VERSION = package_env('VERSION')
URL = package_env('URL')

AUTHOR_AND_EMAIL = [v.strip('>').strip() for v \
                    in package_env('AUTHOR').split('<mailto:')]

if len(AUTHOR_AND_EMAIL) == 2:
    AUTHOR, AUTHOR_EMAIL = AUTHOR_AND_EMAIL
else:
    AUTHOR = AUTHOR_AND_EMAIL
    AUTHOR_EMAIL = ''

DESC = "swarm application to extract meaningful texts from any site"


class TestRunner(test):
    def run(self, *args, **kwargs):
        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(self.\
                                                distribution.install_requires)
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)
        from test import run
        run()

if __name__ == '__main__':
    setup(
        cmdclass={"test": TestRunner},
        name=PROJECT,
        version=VERSION,
        description=DESC,
        long_description=package_env('README.rst'),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        license=package_env('LICENSE'),
        packages=['swarm_crawler', ] + ['.'.join(('swarm_crawler', e)) \
                    for e in find_packages('swarm_crawler')],
        package_dir={
                     'swarm_crawler': 'swarm_crawler'},
        include_package_data=True,
        zip_safe=False,
        test_suite='test',
        install_requires=[
                         'swarm',
                         'swarm-http',
                         'lxml',
                         'breadability',
                         'cliff',
                         'datrie',
                         ],
        tests_require=[],
        entry_points={
            'console_scripts': [
                'crawler = swarm_crawler.main:main'
                ],
            'swarm_crawler.commands': [
                'serve = swarm_crawler.commands.server:Web',
                'start_text = swarm_crawler.commands.start:StartText',
                'start = swarm_crawler.commands.start:StartDataset',
                'start_datasource = swarm_crawler.commands.start:StartDatasource',

                'restore_list = swarm_crawler.commands.crawl:RestoreList',
                'restore = swarm_crawler.commands.crawl:Restore',

                'dataset_list = swarm_crawler.commands.dataset:DatasetList',
                'dataset_info = swarm_crawler.commands.dataset:DatasetInfo',
                'dataset_delete = swarm_crawler.commands.dataset:DeleteDataset',
                'dataset_backup = swarm_crawler.commands.dataset:DatasetBackup',

                'datasource_create = swarm_crawler.commands.datasource:CreateDatasource',
                'datasource_delete = swarm_crawler.commands.datasource:DeleteDatasource',
                ],

            },
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
        ],
    )