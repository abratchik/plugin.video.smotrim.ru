# -*- coding: utf-8 -*-
# Module: episodes
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json

import resources.lib.modules.pages as pages

from ..utils import clean_html


class Episode(pages.Page):

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/episodes',
                                 brands=self.params['brands'],
                                 limit=self.limit,
                                 offset=self.offset)

    def set_context_title(self):
        if 'data' in self.data:
            self.site.context_title = self.data['data'][0]['brandTitle'] \
                if len(self.data['data']) > 0 else self.site.language(30040)

    def get_nav_url(self, offset=0):
        return self.site.get_url(self.site.url,
                                 action="load",
                                 context="episodes",
                                 content=self.params['content'],
                                 brands=self.params['brands'],
                                 limit=self.limit, offset=offset + 1, url=self.site.url)

    def create_element_li(self, element):
        is_audio = element['countAudios'] > 0
        return {'id': element['id'],
                'label': element['combinedTitle'],
                'is_folder': False,
                'is_playable': True,
                'url': self.site.get_url(self.site.url,
                                         action="play",
                                         context="episodes",
                                         brands=element['brandId'],
                                         episodes=element['id'],
                                         is_audio=is_audio,
                                         url=self.site.url),
                'info': {'title': element['combinedTitle'],
                         'tvshowtitle': element['brandTitle'],
                         'mediatype': "episode",
                         'plot': clean_html(element['body']),
                         'plotoutline': element['anons'],
                         'episode': element['series'],
                         'sortepisode': element['series'],
                         'dateadded': element['dateRec']
                         } if not is_audio else
                {'mediatype': "music",
                 'title': element['title'],
                 'plot': "%s[CR]%s" % (element['title'], element['anons'])},
                'art': {'fanart': self.get_pic_from_plist(element['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(element['pictures'], 'vhdr')
                        }
                }

    def play(self):

        if json.loads(self.params['is_audio'].lower()):
            audios = self.site.request(
                self.site.get_url(self.site.api_url + '/audios', episodes=self.params['episodes']), output="json")
            spath = audios['data'][0]['sources']['mp3']
        else:
            videos = self.site.request(
                self.site.get_url(self.site.api_url + '/videos', episodes=self.params['episodes']), output="json")
            spath = videos['data'][0]['sources']['m3u8']['auto']

        self.play_url(spath)