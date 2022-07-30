# -*- coding: utf-8 -*-
# Module: persons
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import re

import xbmc

import resources.lib.modules.pages as pages
import resources.lib.smotrim as smotrim
import resources.lib.users as users
from resources.lib import kodiutils
from resources.lib.kodiutils import get_url

CONTEXT = "persons"
CONTEXT_LIMIT = 20


class Person(pages.Page):

    def __init__(self, site):
        super(Person, self).__init__(site)
        self.cache_enabled = True
        self.persons_path = kodiutils.create_folder(os.path.join(self.site.data_path, 'persons'))

    def get_load_url(self):
        return get_url(baseurl=self.site.api_url + "/%s" % CONTEXT,
                       brands=self.params.get('brands', 0),
                       offset=self.offset,
                       limit=CONTEXT_LIMIT)

    def download_brand_persons(self):
        brand_id = self.params.get('brand_id', "")
        xbmc.log("Smotrim: start downloading actor thumbnails (%s)" % brand_id)

        self.cache_file = get_brand_persons_file_name(brand_id)
        self.data = self.get_data_query()
        self.cache_data()

        xbmc.log("Smotrim: thumbnails downloaded")

    def cache_data(self):
        if self.cache_enabled and not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w+') as f:
                json.dump(self.data, f)

    def get_cache_filename_prefix(self):
        return get_brand_persons_file_name_prefix(self.params.get("brands", 0))


def get_brand_persons_file_name_prefix(brand_id) -> str:
    return os.path.join(CONTEXT, "brand_%s" % brand_id)


def get_brand_persons_file_name(brand_id) -> str:
    return os.path.join(smotrim.get_data_path(), "%s_%s_%s.json" % (get_brand_persons_file_name_prefix(brand_id),
                                                                    CONTEXT_LIMIT, 0))


def get_persons_path(data_path="") -> str:
    if not data_path:
        data_path = smotrim.get_data_path()
    return kodiutils.create_folder(os.path.join(data_path, CONTEXT))


def get_brand_persons_from_cache(brand_id) -> list:
    if brand_id:
        fname = get_brand_persons_file_name(brand_id)
        xbmc.log("persons.get_brand_persons_from_cache fname=%s" % fname, xbmc.LOGDEBUG)

        if not os.path.exists(fname):
            site = smotrim.Smotrim()
            site.params['brand_id'] = brand_id
            site.user = users.User()
            site.user.init_session(site)
            person = Person(site)
            person.download_brand_persons()
            site.user.session.close()
            return person.data.get("data", [])

        if os.path.exists(fname):
            with open(fname, "r") as f:
                return json.load(f).get("data", [])
    return []


def get_person_remote_thumbnail_url(brand_id, person_name) -> str:
    m = re.match(r'(.+)(\s|\+)(.+)', person_name)
    if m:
        first_name = m.group(1)
        last_name = m.group(3)
        xbmc.log("persons.get_person_remote_thumbnail_url searching tumbnail for %s %s" % (first_name, last_name),
                 xbmc.LOGDEBUG)
        persons = get_brand_persons_from_cache(brand_id)
        xbmc.log("persons.get_person_remote_thumbnail_url found %s persons" % len(persons),
                 xbmc.LOGDEBUG)
        try:
            person = next(p for p in persons if p.get('name', "") == first_name and p.get('surname', "") == last_name )
            xbmc.log("persons.get_person_remote_thumbnail_url found %s %s" % (person.get('name', ""),
                                                                              person.get('surname', "")), xbmc.LOGDEBUG)
            return pages.get_pic_from_element(person, "bq", append_headers=False)
        except StopIteration:
            return ""


def get_person_thumbnail(brand_id, person_name) -> str:
    return get_url("http://localhost:%s/brands/%s" % (smotrim.SERVER_PORT, brand_id), person_name=person_name)
