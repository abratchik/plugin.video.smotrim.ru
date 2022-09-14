# -*- coding: utf-8 -*-
# Module: podcasts
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.modules.pages as pages
from resources.lib.kodiutils import get_url


class Podcast(pages.Page):
    def __init__(self, site):
        super(Podcast, self).__init__(site)
        self.cache_enabled = True
        self.context = "podcasts"

    def create_root_li(self):
        return self.create_menu_li("podcasts", 30070, is_folder=True, is_playable=False,
                                   url=get_url(self.site.url,
                                               action="load",
                                               context="podcasts",
                                               content="albums",
                                               cache_expire="86400",
                                               url=self.site.url),
                                   info={'plot': self.site.language(30070)})

    def set_context_title(self):
        self.site.context_title = self.site.language(30070)

    def get_load_url(self):
        return get_url(self.site.api_url + '/rubrics',
                       limit=self.limit,
                       offset=self.offset)

    def create_element_li(self, element):
        bp = self.parse_body(element, 'anons')
        return {'id': element['id'],
                'label': "[B]%s[/B]" % element['title'],
                'is_folder': True,
                'is_playable': False,
                'url': get_url(self.site.url,
                               action="load",
                               context="audios",
                               content="musicvideos",
                               rubrics=element['id'],
                               cache_expire=str(self.cache_expire),
                               url=self.site.url),
                'info': {'title': element.get('title'),
                         'sorttitle': element.get('title'),
                         'originaltitle': element.get('title'),
                         'plot': bp.get('plot', []),
                         'artist': bp.get('cast', []),
                         'cast': bp.get('cast', []),
                         'director': bp.get('director'),
                         'writer': bp.get('writer'),
                         'plotoutline': bp.get('plot', [])
                         },
                'art': {'thumb': pages.get_pic_from_element(element, "lw"),
                        'icon': pages.get_pic_from_element(element, "lw"),
                        'fanart': pages.get_pic_from_element(element, "hd"),
                        'poster': pages.get_pic_from_element(element, "it")
                        }
                }

    def get_element_by_id(self, id):
        response = self.site.request(get_url("%s/rubrics/%s" % (self.site.api_url, str(id))), "json")
        return response.get('data', {})

    def get_nav_url(self, offset=0):
        return get_url(self.site.url,
                       action="load",
                       context=self.context,
                       content="albums",
                       limit=self.limit,
                       offset=offset,
                       url=self.site.url)

    def get_cache_filename_prefix(self):
        return self.context
