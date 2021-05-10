# -*- coding: utf-8 -*-
# Module: home
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.modules.pages as pages
import resources.lib.modules.brands as brands
import resources.lib.modules.articles as articles
import resources.lib.modules.lives as lives
import resources.lib.modules.channels as channels
import resources.lib.modules.history as histories


class Home(pages.Page):

    def get_data_query(self):
        brand = brands.Brand(self.site)
        article = articles.Article(self.site)
        channel = channels.Channel(self.site)
        live = lives.Live(self.site)
        history = histories.History(self.site)

        home_menu = [brand.create_search_li(),
                     article.create_root_li(),
                     channel.create_root_li(),
                     live.create_root_li()]

        home_menu.extend(list(brand.create_search_by_tag_lis()))

        if self.site.addon.getSettingBool("addhistory"):
            home_menu.append(history.create_root_li())

        return {'data': home_menu}

    def set_context_title(self):
        self.site.context_title = self.site.language(30300)
