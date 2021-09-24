# -*- coding: utf-8 -*-
# Module: extras
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import re

import xbmc
import xbmcaddon
import xbmcvfs

import resources.lib.modules.channels as channels
import resources.lib.modules.channelmenus as channelmenus
from resources.lib import kodiutils


class Extra:

    def __init__(self, site):
        self.site = site
        self.iptvaddon = xbmcaddon.Addon("pvr.iptvsimple")
        self.channel = channels.Channel(self.site)
        self.channelmenu = channelmenus.ChannelMenu(self.site)
        self.export_path = kodiutils.create_folder(os.path.join(self.site.data_path, "iptv"))
        self.m3u_playlist = os.path.join(self.export_path, "%s_iptv.m3u" % self.site.id)
        self.xmltv_guide = os.path.join(self.export_path, "%s_iptv_guide.xml" % self.site.id)

    def load(self):
        if (self.site.addon.getSettingBool("exportchannels") and
                (not xbmcvfs.exists(self.m3u_playlist))):
            self.export_channels()
        if xbmcvfs.exists(self.m3u_playlist):
            if (self.site.addon.getSettingBool("exporttvguide") and
                    (not xbmcvfs.exists(self.xmltv_guide) or
                     not self.__is_created_today(self.xmltv_guide))):
                self.export_tv_guide()
            self.update_iptv_settings()

    @staticmethod
    def __is_created_today(spath):
        return kodiutils.get_date_from_timestamp(kodiutils.get_file_timestamp(spath)) == \
               kodiutils.get_date_from_timestamp()

    def export_channels(self):

        cd = self.site.request(self.channel.get_load_url(), output="json")

        if "data" in cd:
            monitor = xbmc.Monitor()
            xbmc.log("Running export channels")
            new_playlist = "%s.new" % self.m3u_playlist
            with open(new_playlist, "w") as m3u:
                m3u.write("#EXTM3U\n")

                i = 0
                while not monitor.abortRequested() and i < len(cd['data']):
                    c = cd['data'][i]
                    doublemap, live = self.channelmenu.get_channel_live_double(c['id'])
                    url = ""
                    try:
                        url = live['sources']['m3u8']['auto']
                    except KeyError:
                        pass

                    if url:
                        m3u.write('#EXTINF:0 tvg-id="smotrim_%sd%s" tvg-logo="%s" tvg-shift="%s" '
                                  'group-title="%s",%s\n' %
                                  (c['id'],
                                   doublemap['double_id'],
                                   self.channel.get_logo(c, "xxl"),
                                   self.site.addon.getSettingNumber("epgshift"),
                                   self.site.language(30022),
                                   c['title']))

                        m3u.write("%s\n" % url)
                        xbmc.log("Export channel %s:%s completed successfully" % (c['id'], c['title']))
                    else:
                        xbmc.log("Export channel %s:%s live stream not found, skipping ..." % (c['id'], c['title']))

                    if monitor.waitForAbort(1):
                        break

                    i = i + 1

                if monitor.abortRequested():
                    xbmc.log("Channel export cancelled by user action")
                    m3u.close()
                    xbmcvfs.delete(new_playlist)
                    return

            xbmcvfs.copy(new_playlist, self.m3u_playlist)
            xbmcvfs.delete(new_playlist)
            xbmc.log("Channel export complete")
        else:
            xbmc.log("Could not load channel list")

    def export_tv_guide(self):

        if not xbmcvfs.exists(self.m3u_playlist):
            return

        new_tvguide = "%s.new" % self.xmltv_guide

        xbmc.log("Start export of the channel TV guide")
        with open(new_tvguide, "w") as xmltv:
            xmltv.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            xmltv.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
            xmltv.write('<tv source-info-name="Smotrim">\n')
            monitor = xbmc.Monitor()

            with open(self.m3u_playlist, "r") as m3u:
                lines = m3u.readlines()
                i = 0
                while not monitor.abortRequested() and i < len(lines):
                    line = lines[i]
                    if not ("#EXTINF" in line):
                        i = i + 1
                        continue
                    ch = line.split(',')
                    match = re.search(r'(?<=tvg-id="smotrim_)(.*)("\stvg-logo)', ch[0])
                    if match is None:
                        i = i + 1
                        continue
                    chd = match.group(1)
                    xmltv.write('<channel id="smotrim_%s">\n' % chd)
                    xmltv.write('<display-name>%s</display-name>\n' % ch[1])
                    xmltv.write('</channel>\n')
                    chds = chd.split('d')
                    ch_id = chds[0]
                    double_id = chds[1]

                    xbmc.log("Load program for the channel %s:%s" % (ch_id, double_id))

                    programs = self.channelmenu.get_channel_tvguide(ch_id, double_id)
                    for p in programs:
                        ptitle = ""
                        try:
                            ptitle = p['title']
                            xmltv.write('<programme start="%s" stop="%s" channel="smotrim_%s">\n' %
                                        (self.__format_date(p['realDateStart']),
                                         self.__format_date(p['realDateEnd']),
                                         chd))
                            if p['brand']:
                                xmltv.write('<title>%s</title>\n' % p['brand']['title'])
                                xmltv.write('<desc>%s</desc>\n' % p['brand']['anons'])
                            else:
                                xmltv.write('<title>%s</title>\n' % ptitle)
                            if p['episode']:
                                xmltv.write('<sub-title>%s</sub-title>\n' % p['episode']['title'])
                            xmltv.write('<icon src="%s"/>\n' % self.channel.get_pic_from_element(p, "lw"))
                            xmltv.write('</programme>\n')
                        except Exception as e:
                            xbmc.log("Program [%s] ignored due to unexpected data format returned by server" %
                                     ptitle, xbmc.LOGDEBUG)

                    if monitor.waitForAbort(1):
                        break

                    i = i + 1

            xmltv.write('</tv>\n')

            if monitor.abortRequested():
                xbmc.log("Channel TV guide export cancelled by user action")
                xmltv.close()
                xbmcvfs.delete(new_tvguide)
                return

        xbmcvfs.copy(new_tvguide, self.xmltv_guide)
        xbmcvfs.delete(new_tvguide)
        xbmc.log("Channel TV guide export complete")

    def __format_date(self, s):
        return "%s%s%s%s%s%s 0000" % (s[6:10], s[3:5], s[0:2], s[11:13], s[14:16], s[17:19])

    def update_iptv_settings(self):
        if self.iptvaddon:
            if self.site.addon.getSettingBool("exportchannels"):
                self.iptvaddon.setSetting("m3uPathType", "2")
                self.iptvaddon.setSetting("m3uPath", self.m3u_playlist)
            if self.site.addon.getSettingBool("exporttvguide"):
                self.iptvaddon.setSetting("epgPathType", "2")
                self.iptvaddon.setSetting("epgPath", self.xmltv_guide)
