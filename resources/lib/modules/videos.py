# -*- coding: utf-8 -*-
# Module: videos
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import time

import resources.lib.modules.pages as pages

from ..utils import upnext_signal

import xbmc


class Video(pages.Page):

    def __init__(self, site):
        super(Video, self).__init__(site)
        self.cache_enabled = True

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/videos/',
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
                                 context="videos",
                                 content=self.params['content'],
                                 brands=self.params['brands'],
                                 limit=self.limit, offset=offset, url=self.site.url)

    def create_element_li(self, element):
        return {'id': element['id'],
                'label': element['combinedTitle'],
                'is_folder': False,
                'is_playable': True,
                'url': self.get_play_url(element),
                'info': {'title': element['combinedTitle'],
                         'tvshowtitle': element['brandTitle'],
                         'mediatype': "episode",
                         'episode': element['series'],
                         'plotoutline': element['combinedTitle'],
                         'plot': element['anons'],
                         'duration': element['duration'],
                         'dateadded': self.format_date(element['dateRec']),
                         },
                'art': {'fanart': self.get_pic_from_plist(element['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(element['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(element['pictures'], 'vhdr')
                        }
                }

    def get_play_url(self, element):
        return self.site.get_url(self.site.url,
                                 action="play",
                                 context="videos",
                                 brands=element['brandId'],
                                 videos=element['id'],
                                 offset=self.offset,
                                 limit=self.limit,
                                 spath=element['sources']['m3u8']['auto'],
                                 url=self.site.url)

    def play(self):
        # videos = self.site.request(self.site.api_url + '/videos/' + self.params['videos'], output="json")
        # spath = videos['data']['sources']['m3u8']['auto']

        spath = self.params['spath']

        this_video, next_video = self.get_next_video()
        if 'combinedTitle' in next_video:
            xbmc.log("Next video is %s" % next_video['combinedTitle'])
            upnext_signal(sender=self.site.id, next_info=self.get_next_info(this_video, next_video))

        self.play_url(spath)

    def get_cache_filename_prefix(self):
        return "brand_videos_%s" % self.params['brands']

    def get_next_video(self):
        self.offset = self.params['offset'] if 'offset' in self.params else 0
        self.limit = self.get_limit_setting()

        self.cache_file = self.get_cache_filename()

        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r+') as f:
                self.data = json.load(f)
            for i, video in enumerate(self.data['data']):
                if str(video['id']) == self.params['videos'] and (i < self.limit - 1):
                    return self.data['data'][i], self.data['data'][i + 1]

            xbmc.log("Reached page bottom, loading next page?")
            return {}, {}
        else:
            return {}, {}

    def get_next_info(self, this_video, next_video):
        return {'current_episode': self.create_next_info(this_video),
                'next_episode': self.create_next_info(next_video),
                'play_url': self.get_play_url(next_video)}

    def create_next_info(self, video):
        return {'episodeid': video['id'],
                'tvshowid': self.params['brands'],
                'title': video['title'],
                'art': {'thumb': self.get_pic_from_plist(video['pictures'], 'lw'),
                        'fanart': self.get_pic_from_plist(video['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(video['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(video['pictures'], 'vhdr')
                        },
                'episode': video['series'],
                'showtitle': video['brandTitle'],
                'runtime': video['duration']
                }
