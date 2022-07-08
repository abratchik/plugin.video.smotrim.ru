# -*- coding: utf-8 -*-
# Module: articles
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.modules.pages as pages

from ..kodiutils import clean_html

import xbmcgui


class Article(pages.Page):

    def create_root_li(self):
        return {'id': "articles",
                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30301),
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url, action="load", context="articles", url=self.site.url),
                'info': {'plot': self.site.language(30301)},
                'art': {'icon': self.site.get_media("news.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    def set_context_title(self):
        self.site.context_title = self.site.language(30301)

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/articles',
                                 limit=self.limit,
                                 offset=self.offset)

    def create_element_li(self, element=None):
        return {'id': element['id'],
                'is_folder': False,
                'is_playable': True if element['videos'] else False,
                'label': "[COLOR=FF00FFFF]%s[/COLOR] %s" % (self.site.language(30302), element['title'])
                if element['videos'] else element['title'],
                'url': self.site.get_url(self.site.url,
                                         action="play",
                                         context="articles",
                                         articles=element['id'],
                                         url=self.site.url),
                'info': {'title': element['title'],
                         'mediatype': "video",
                         'plot': clean_html(element['body']),
                         'plotoutline': element['anons'],
                         'dateadded': element['datePub']
                         },
                'art': {'fanart': self.get_pic_from_element(element, 'hd'),
                        'icon': self.get_pic_from_element(element, 'lw'),
                        'thumb': self.get_pic_from_element(element, 'lw'),
                        'poster': self.get_pic_from_element(element, 'it')
                        }
                }

    def play(self):
        articles = self.site.request(self.site.get_url(self.site.api_url + '/articles/' + self.params['articles']),
                                     output="json")
        xbmcgui.Dialog().textviewer(articles['data']['title'], clean_html(articles['data']['body']))
        if articles['data']['videos']:
            spath = self.get_video_url(articles['data']['videos'][0]['sources'])
            self.play_url(spath)
