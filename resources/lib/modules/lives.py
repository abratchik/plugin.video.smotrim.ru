# -*- coding: utf-8 -*-
# Module: lives
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


import resources.lib.modules.pages as pages
import resources.lib.streamextractor as se


class Live(pages.Page):

    def create_root_li(self):
        return {'id': "lives",
                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30224),
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url, action="load", context="lives", url=self.site.url),
                'info': {'plot': self.site.language(30224)},
                'art': {'icon': self.site.get_media("lives.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    # def get_load_url(self):
    #     return self.site.get_url(self.site.api_url + '/lives', time="now")

    def get_data_query(self):
        data = {'data': []}
        groups = self.site.request(self.site.addon.getSetting("liveapi_url"), output="json")
        data['data'].extend(groups[0]['items'])

        return data

    def set_context_title(self):
        self.site.context_title = self.site.language(30224)

    # def create_element_li(self, element):
    #     return {'id': element['id'],
    #             'label': element['title'],
    #             'is_folder': False,
    #             'is_playable': True,
    #             'url': self.site.get_url(self.site.url,
    #                                      action="play",
    #                                      context="lives",
    #                                      path=element['streams']['rtmp'][0]['uri'],
    #                                      url=self.site.url),
    #             'info': {'plot': element['title']},
    #             'art': {'icon': self.get_logo(element['channels'], "xxl"),
    #                     'fanart': self.site.get_media("background.jpg")}
    #             }

    def create_element_li(self, element):
        return {'id': element['id'],
                'label': element['title'],
                'is_folder': False,
                'is_playable': True,
                'url': self.site.get_url(self.site.url,
                                         action="play",
                                         context="lives",
                                         path=element['source'],
                                         url=self.site.url),
                'info': {'plot': element['title']},
                'art': {'icon': self.site.get_media("lives.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    def play(self):
        path = self.params['path']

        vid = se.getVideoInfo(path)

        if vid is None:
            spath = path
        else:
            spath = vid.streamURL()

        self.play_url(spath)
