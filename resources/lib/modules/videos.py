# -*- coding: utf-8 -*-
# Module: videos
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.modules.pages as pages


class Video(pages.Page):

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/videos',
                                 brands=self.params['brands'],
                                 limit=self.limit,
                                 offset=self.offset,
                                 sort="date")

    def set_context_title(self):
        if 'data' in self.data:
            self.site.context_title = self.data['data'][0]['brandTitle'] \
                if len(self.data['data']) > 0 else self.site.language(30040)

    def get_nav_url(self, offset=0):
        return self.site.get_url(self.site.url,
                                 action="load",
                                 context="videos",
                                 content=self.params['content'],
                                 brands=self.params['brands'],
                                 limit=self.limit, offset=offset + 1, url=self.site.url)

    def create_element_li(self, element):
        return {'id': element['id'],
                'label': element['combinedTitle'],
                'is_folder': False,
                'is_playable': True,
                'url': self.site.get_url(self.site.url,
                                         action="play",
                                         context="videos",
                                         brands=element['brandId'],
                                         videos=element['id'],
                                         url=self.site.url),
                'info': {'title': element['combinedTitle'],
                         'tvshowtitle': element['brandTitle'],
                         'mediatype': "episode",
                         'plotoutline': element['combinedTitle'],
                         'plot': element['anons'],
                         'dateadded': element['dateRec']
                         },
                'art': {'fanart': self.get_pic_from_plist(element['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(element['pictures'], 'vhdr')
                        }
                }

    def play(self):
        videos = self.site.request(self.site.api_url + '/videos/' + self.params['videos'], output="json")
        spath = videos['data']['sources']['m3u8']['auto']

        self.play_url(spath)
