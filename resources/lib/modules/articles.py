# -*- coding: utf-8 -*-
# Module: articles
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc

import resources.lib.modules.pages as pages
import resources.lib.rssbuilder as rssbuilder
import resources.lib.smotrim as smotrim
import resources.lib.users as users

from ..kodiutils import clean_html, get_url

import xbmcgui


class Article(pages.Page):

    def create_root_li(self):
        return self.create_menu_li("news", 30301, is_folder=True, is_playable=False,
                                   url=get_url(self.site.url, action="load", context="articles", url=self.site.url),
                                   info={'plot': self.site.language(30301)})

    def set_context_title(self):
        self.site.context_title = self.site.language(30301)

    def get_load_url(self):
        return get_url(self.site.api_url + '/articles',
                       sort='date',
                       limit=self.limit,
                       offset=self.offset)

    def create_element_li(self, element=None):
        return {'id': element['id'],
                'is_folder': False,
                'is_playable': True if element['videos'] else False,
                'label': "[COLOR=FF00FFFF]%s[/COLOR] %s" % (self.site.language(30302), element['title'])
                if element['videos'] else element['title'],
                'url': get_url(self.site.url,
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
                'art': {'fanart': pages.get_pic_from_element(element, 'hd'),
                        'icon': pages.get_pic_from_element(element, 'lw'),
                        'thumb': pages.get_pic_from_element(element, 'lw'),
                        'poster': pages.get_pic_from_element(element, 'it')
                        }
                }

    def play(self):
        articles = self.site.request(get_url(self.site.api_url + '/articles/' + self.params['articles']),
                                     output="json")
        xbmcgui.Dialog().textviewer(articles['data']['title'], clean_html(articles['data']['body']))
        if articles['data']['videos']:
            spath = self.get_video_url(articles['data']['videos'][0]['sources'])
            self.play_url(spath)


def get_RSS():
    xbmc.log("Smotrim.articles: getting RSS feed!", xbmc.LOGDEBUG)
    rb = rssbuilder.RSSBuilder()
    rb.create_RSS()
    site = smotrim.Smotrim()
    site.user = users.User()
    site.user.init_session(site)
    article = Article(site)
    article.limit = 30
    article.data = article.get_data_query()
    site.user.session.close()
    ch = rb.create_channel(site.language(30022), url="https://%s" % site.domain)

    if 'data' in article.data:
        for a in article.data['data']:
            rb.create_item(ch,
                           title=a.get('title', ""),
                           guid=a.get('guid', ""),
                           url=a.get('shareURL', ""),
                           description=a.get('anons', ""),
                           pubdate=a.get('datePub', ""))

    return rb.get_rss_xml()
