# -*- coding: utf-8 -*-
# Module: extras
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
from collections import defaultdict

import xbmc
import xbmcvfs

import resources.lib.modules.channels as channels
import resources.lib.modules.channelmenus as channelmenus
from resources.lib import kodiutils, iptvmanager


class Extra:

    def __init__(self, site):
        self.site = site
        self.channel = channels.Channel(self.site)
        self.channelmenu = channelmenus.ChannelMenu(self.site)
        self.export_path = kodiutils.create_folder(os.path.join(self.site.data_path, "iptv"))
        self.ch_playlist = os.path.join(self.export_path, "%s_iptv.json" % self.site.id)
        self.tv_guide = os.path.join(self.export_path, "%s_iptv_guide.json" % self.site.id)

        self.icon_path = os.path.join(self.site.path, "icon.png")

    def export_channels(self):

        if xbmcvfs.exists(self.ch_playlist) and self.__is_created_today(self.ch_playlist):
            with open(self.ch_playlist, "r") as f:
                return json.load(f)

        cd = self.site.request(self.channel.get_load_url(), output="json")

        chs = []

        if "data" in cd:
            monitor = xbmc.Monitor()
            xbmc.log("Running export channels")

            for c in cd['data']:
                doublemap, url = self.channelmenu.get_channel_live_double(c['id'])

                if url:

                    ch = {'id': "smotrim_%sd%s" % (c['id'], doublemap['double_id']),
                                'ch_id': c['id'],
                                'double_id': doublemap['double_id'],
                                'name': c['title'],
                                'logo': self.channel.get_logo(c, "xxl"),
                                'stream': url}

                    chs.append(ch)

                    xbmc.log("Export channel %s:%s completed successfully" %
                             (c['id'], c['title'].encode('utf-8', 'ignore')))
                else:
                    xbmc.log("Export channel %s:%s live stream not found, skipping ..." %
                             (c['id'], c['title'].encode('utf-8', 'ignore')))

                if monitor.waitForAbort(1):
                    break

            if monitor.abortRequested():
                xbmc.log("Channel export cancelled by user action")
            else:
                with open(self.ch_playlist, "w") as f:
                    json.dump(chs, f)

                xbmc.log("Channel export complete")
        else:
            xbmc.log("Could not load channel list")

        return chs

    def export_tv_guide(self):

        if xbmcvfs.exists(self.tv_guide) and self.__is_created_today(self.tv_guide):
            with open(self.tv_guide, "r") as f:
                return json.load(f)

        xbmc.log("Start export of the channel TV guide")

        epgs = defaultdict(list)

        monitor = xbmc.Monitor()

        with open(self.ch_playlist, "r") as f:
            chs = json.load(f)

        for ch in chs:

            xbmc.log("Load program for the channel %s" % ch['id'])

            programs = self.channelmenu.get_channel_tvguide(str(ch['ch_id']), ch['double_id'])

            for p in programs:
                ptitle = ""
                try:
                    pdesc = ""
                    if p['brand']:
                        ptitle = p['brand']['title']
                        pdesc = p['brand']['anons']
                    else:
                        ptitle = p['title']

                    epgs[ch['id']].append({'start': self.__format_date(p['realDateStart']),
                                           'stop': self.__format_date(p['realDateEnd']),
                                           'title': ptitle,
                                           'description': pdesc,
                                           'image': self.channel.get_pic_from_element(p, "lw"),
                                           'subtitle': p['episode']['title'] if p['episode'] else ""
                                           })


                except Exception as e:
                    xbmc.log("Program [%s] ignored due to unexpected data format returned by server" %
                             ptitle.encode('utf-8', 'ignore'), xbmc.LOGDEBUG)

            if monitor.waitForAbort(1):
                break

        if monitor.abortRequested():
            xbmc.log("Channel TV guide export cancelled by user action")
            return defaultdict(list)

        with open(self.tv_guide, "w") as f:
            json.dump(epgs, f)

        xbmc.log("Channel TV guide export complete")

        return epgs

    def __format_date(self, s):
        return "%s-%s-%sT%s:%s:%s+03:00" % (s[6:10], s[3:5], s[0:2], s[11:13], s[14:16], s[17:19])

    def send_channels(self):
        if 'port' in self.site.params:
            iptvmanager.IPTVManager(self).send_channels()

    def send_epg(self):
        if 'port' in self.site.params:
            iptvmanager.IPTVManager(self).send_epg()

    @staticmethod
    def __is_created_today(spath):
        return kodiutils.get_date_from_timestamp(kodiutils.get_file_timestamp(spath)) == \
               kodiutils.get_date_from_timestamp()
