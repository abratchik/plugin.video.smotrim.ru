# -*- coding: utf-8 -*-
# Module: boxes
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import os
import re

import resources.lib.modules.pages as pages
from resources.lib.kodiutils import get_url
import resources.lib.modules.brands as brands
import resources.lib.modules.videos as videos
import resources.lib.modules.audios as audios
import resources.lib.modules.articles as articles


class Box(pages.Page):
    def __init__(self, site):
        super(Box, self).__init__(site)
        self.cache_enabled = True
        self.alias = self.params.get('alias', 'tabbar-menu')
        self.brand = brands.Brand(site)
        self.brand.cache_expire = 86400
        self.video = videos.Video(site)
        self.video.cache_expire = 86400
        self.audio = audios.Audio(site)
        self.audio.cache_expire = 86400
        self.article = articles.Article(site)
        self.article.cache_expire = 1800

    def create_root_li(self):
        return self.create_menu_li("boxes", 30080, is_folder=True, is_playable=True,
                                   url=get_url(self.site.url,
                                               action="load",
                                               context="boxes",
                                               title=self.site.language(30080),
                                               content="files",
                                               alias="tabbar-menu",
                                               url=self.site.url),
                                   info={'plot': self.site.language(30081)}
                                   )

    def get_nav_url(self, offset=0):
        return get_url(self.site.url,
                       action="load",
                       context="boxes",
                       content=self.params.get('content'),
                       title=self.params.get('title', self.site.language(30080)),
                       pic_id=self.params.get('pic_id'),
                       offset=offset,
                       alias=self.params.get('alias'),
                       url=self.site.url)

    def get_load_url(self):
        return get_url('%s/boxes/%s' % (self.site.api_url, self.alias))

    def get_data_query(self):
        if self.is_cache_available():
            return self.get_data_from_cache()
        else:
            response = self.site.request(self.get_load_url(), output="json")
            data = {'data': response['data'].get('content', [])}
            # pagination = response['data'].get('pagination', {})
            # if pagination:
            #     data['pagination'] = pagination
            for c in data['data']:
                if c.get('type') == "brand":
                    c['data'] = self.brand.get_element_by_id(c.get('id'))
                elif c.get('type') == "episode-video":
                    c['data'] = self.video.get_element_by_id(c.get('id'))
                elif c.get('type') == "episode-audio":
                    c['data'] = self.audio.get_element_by_id(c.get('id'))
                elif c.get('type') == "article":
                    c['data'] = self.article.get_element_by_id(c.get('id'))

            return data

    def create_element_li(self, element):

        if element.get('typeName') == "adv" or element.get('template') == "promo":
            return {}

        if element.get('type') == "brand":
            return self.brand.create_element_li(element.get('data'))

        if element.get('type') == "episode-video":
            return self.video.create_element_li(element.get('data'))

        if element.get('type') == "episode-audio":
            return self.audio.create_element_li(element.get('data'))

        if element.get('type') == "article":
            return self.article.create_element_li(element.get('data'))

        picId = 0
        if element.get('pictures', []):
            picId = element['pictures'][0]
        elif self.params.get('pic_id'):
            picId = self.params.get('pic_id')

        if picId:
            art = {'thumb': self.get_pic_from_id(picId, "it"),
                   'icon': self.get_pic_from_id(picId, "it"),
                   'fanart': self.get_pic_from_id(picId, "hd"),
                   'poster': self.get_pic_from_id(picId, "it")
                   }
        else:
            art = {}

        link_alias = element.get('alias', '')
        if element.get('type') == "link" or link_alias:
            if link_alias == "":
                link_alias = self.get_alias_from_url(element.get('url', ''))
            if link_alias:
                return {'id': "box%s" % element.get('id'),
                        'label': "[B]%s[/B]" % element.get('title', ''),
                        'is_folder': True,
                        'is_playable': False,
                        'url': get_url(self.site.url,
                                       action="load",
                                       context="boxes",
                                       content=self.get_content_type(element.get('template')),
                                       title=element.get('title'),
                                       pic_id=picId,
                                       alias=link_alias,
                                       url=self.site.url),
                        'info': {'plot': element.get('fullTitle', element.get('title', ''))},
                        'art': art
                        }

        return {}

    def set_context_title(self):
        self.site.context_title = self.params.get('title', self.site.language(30080))

    def get_cache_filename(self):
        return os.path.join(self.site.data_path, "boxes_%s_%s_%s.json" % (self.alias, self.limit, self.offset))

    @staticmethod
    def get_alias_from_url(url):
        m = re.match(r'.*\/pick\/(.*)\?', url)
        if m:
            return m.group(1)
        else:
            return ""

    @staticmethod
    def get_content_type(templ):
        if templ == "brandsFeed":
            return "videos"
        elif templ == "videos":
            return "videos"
        elif templ == "audios":
            return "musicvideos"
        else:
            return "files"
