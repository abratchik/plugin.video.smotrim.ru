# -*- coding: utf-8 -*-
# Module: test_users
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import re
import shutil
import warnings

warnings.filterwarnings('ignore', message=r"Python 2 is no longer supported.*")

import unittest
import mock

from resources.lib.users import User
from resources.lib.smotrim import Smotrim

cwd = os.path.dirname(os.path.abspath(__file__))
web_api_url = "https://api.smotrim.ru/api/v1"
web_cdnapi_url = "https://cdnapi.smotrim.ru/api/v1"



def get_project_folder(fld, plugin_name):
    dpath = os.path.split(fld)
    if dpath[1] == plugin_name:
        return fld
    else:
        return get_project_folder(dpath[0], plugin_name)


class UsersTestCase(unittest.TestCase):

    @mock.patch('sys.argv', ["", "1", ""])
    def test_01_load(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "2", "?action=load&context=searches&url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_02_searches(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "2", "?action=search&context=brands&url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_03_search(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "4", "?action=load&context=articles&url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_04_news(self):
        self.run_plugin()

    @mock.patch('sys.argv',
                ["", "14", "?action=load&content=files&context=channels&url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_041_channels(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "2", "?action=search_by_tag&cache_expire=86400&content=files&context=brands&" +
                             "has_children=True&tagname=Documentary&tags=10000002&" +
                             "url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_05_documentary(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "8", "?action=search_by_tag&cache_expire=86400&content=movies&context=brands&" +
                             "has_children=False&tagname=Premieres&tags=2994&" +
                             "url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_06_premieres(self):
        self.run_plugin()

    @mock.patch('sys.argv', ["", "10", "?action=load&context=history&url=plugin%3a%2f%2fplugin.video.smotrim.ru%2f"])
    def test_07_history(self):
        self.run_plugin()

    def run_plugin(self):
        user = User()
        self.assertIsNotNone(user, "Constructor User() failed!")
        smotrim = Smotrim()
        smotrim.api_host = "api.smotrim.ru"
        smotrim.cdnapi_host = "cdnapi.smotrim.ru"
        smotrim.api_url = web_api_url
        smotrim.cdnapi_url = web_cdnapi_url
        self.project_dir = get_project_folder(cwd, smotrim.id)

        smotrim.path = self.project_dir
        smotrim.data_path = os.path.join(self.project_dir, "data")
        smotrim.history_path = os.path.join(smotrim.data_path, "history")

        if not os.path.exists(smotrim.history_path):
            os.makedirs(smotrim.history_path)

        self.resource_file = os.path.join(self.project_dir, "resources", "language", "resource.language.ru_ru",
                                          "strings.po")
        smotrim.language = self.localized_string
        self.assertIsNotNone(smotrim, "Constructor Smotrim() failed!")
        user.watch(smotrim)
        shutil.rmtree(smotrim.data_path)

    def localized_string(self, id):
        with open(self.resource_file, 'r') as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                if "#%s" % id in line:
                    return (re.findall(r"(?<=msgstr.).*", lines[index + 2])[0][1:-1]).decode('utf-8')
        self.fail("Fail to find resource string %s" % id)


if __name__ == '__main__':
    unittest.main()
