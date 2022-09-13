# -*- coding: utf-8 -*-
# Module: home
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc

import resources.lib.modules.pages as pages
import resources.lib.modules.searches as searches
import resources.lib.modules.podcasts as podcasts
import resources.lib.modules.boxes as boxes
import resources.lib.modules.brands as brands
import resources.lib.modules.articles as articles
import resources.lib.modules.channels as channels
import resources.lib.modules.history as histories
from resources.lib.kodiutils import get_url


class Home(pages.Page):

    def get_data_query(self):
        search = searches.Search(self.site)
        brand = brands.Brand(self.site)
        podcast = podcasts.Podcast(self.site)
        article = articles.Article(self.site)
        channel = channels.Channel(self.site)
        box = boxes.Box(self.site)
        history = histories.History(self.site)

        home_menu = [search.create_root_li(),
                     self.create_fav_li(),
                     article.create_root_li(),
                     channel.create_root_li(),
                     box.create_root_li(),
                     podcast.create_root_li()]

        home_menu.extend(list(brand.create_search_by_tag_lis()))

        if self.site.addon.getSettingBool("addhistory"):
            home_menu.append(history.create_root_li())

        return {'data': home_menu}

    def set_context_title(self):
        self.site.context_title = self.site.language(30300)

    def create_fav_li(self):
        return self.create_menu_li("favorites", 30023, is_folder=False, is_playable=False,
                                   url=get_url(self.site.url, action="favorites", context="home", url=self.site.url),
                                   info={'plot': self.site.language(30023)})

    def favorites(self):
        xbmc.executebuiltin("ActivateWindow(Favourites)")

