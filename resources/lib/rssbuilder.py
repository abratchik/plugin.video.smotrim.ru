# -*- coding: utf-8 -*-
# Module: rssbuilder
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

import xbmc
import xbmcvfs

from resources.lib.smotrim import SERVER_ADDR

RSSFEEDS = "RssFeeds.xml"
RSSUPDATEINTERVAL = 30


class RSSBuilder():

    def __init__(self):
        self.et = None

    def create_RSS(self):
        self.et = ET.fromstring("<rss version='2.0' />")
        return self.et

    def get_rss_xml(self):
        return ET.tostring(self.et)

    def create_channel(self, title, url="", description=""):
        ch = self._add_element("channel", self.et)
        self._add_element("title", ch, title)
        self._add_element("link", ch, url)
        self._add_element("description", ch, description)
        return ch

    def create_item(self, ch, title, guid, url="", description="", pubdate=""):
        it = self._add_element("item", ch)
        self._add_element("title", it, txt=title)
        self._add_element("guild", it, txt=guid)
        self._add_element("link", it, txt=url)
        self._add_element("description", it, txt=description)
        if pubdate:
            self._add_element("pubDate", it, txt=pubdate)
        return it

    def add_news_to_rss(self, site, feed):
        rssfeeds = os.path.join(xbmcvfs.translatePath("special://userdata"), RSSFEEDS)
        rssurl = "http://%s:%s/articles" % (SERVER_ADDR, site.server_port)
        rssfeedsxml = self._load_xml_from_file(rssfeeds)

        if feed:
            modified = self._add_rss_feed(rssfeedsxml, rssurl)
        else:
            modified = self._remove_rss_feed(rssfeedsxml, rssurl)

        if modified:
            xbmc.log("News from Smotrim.ru added to RSS feed", xbmc.LOGDEBUG)
            self._backup_file(rssfeeds)
            self._save_pretty_xml(rssfeedsxml, rssfeeds)

            xbmc.executebuiltin('RefreshRSS')

    def _get_or_add_set_1(self, parent):
        set_1 = parent.find("set")
        if set_1 is None:
            set_1 = self._add_element("set", parent)
            set_1.attrib['id'] = "1"
        return set_1

    def _add_rss_feed(self, rssfeedsxml, rssurl):
        set_1 = self._get_or_add_set_1(rssfeedsxml)
        feeds = set_1.findall("feed")
        for f in feeds:
            if f.text == rssurl:
                return False
        feed = self._add_element("feed", None, txt=rssurl)
        set_1.insert(0, feed)
        feed.attrib['updateinterval'] = str(RSSUPDATEINTERVAL)
        return True

    def _remove_rss_feed(self, rssfeedsxml, rssurl):
        set_1 = self._get_or_add_set_1(rssfeedsxml)
        feeds = set_1.findall("feed")
        for f in feeds:
            if f.text == rssurl:
                set_1.remove(f)
                return True

        return False


    @staticmethod
    def _add_element(name, parent, txt=""):
        el = ET.Element(name) if (parent is None) else ET.SubElement(parent, name)
        if txt:
            el.text = txt
        return el

    @staticmethod
    def _load_xml_from_file(filename):
        if xbmcvfs.exists(filename):
            tree = ET.parse(filename)
            return tree.getroot()
        else:
            return ET.fromstring("<rssfeeds />")

    @staticmethod
    def _save_pretty_xml(element, output_xml):
        xml_string = minidom.parseString(ET.tostring(element)).toprettyxml()
        xml_string = os.linesep.join(
            [s for s in xml_string.splitlines() if s.strip() and not("<?xml" in s)])
        xbmc.log(xml_string, xbmc.LOGDEBUG)
        with open(output_xml, "w") as file_out:
            file_out.write(os.linesep.join(['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', xml_string]))


    @staticmethod
    def _backup_file(fpath):
        if xbmcvfs.exists(fpath):
            fpathbak = "%s.bak" % fpath
            if xbmcvfs.exists(fpathbak):
                xbmcvfs.delete(fpathbak)
            return xbmcvfs.copy(fpath, fpathbak)
        else:
            return False
