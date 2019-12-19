# -*- coding: utf-8 -*-
# -----------------------------------------------------------
#
# QGIS Geomapfish Locator Plugin
# Copyright (C) 2018 Denis Rouzaud
#
# -----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------

from geomapfish_locator.qgissettingmanager import SettingManager, Scope, Bool, String, Integer

pluginName = "geomapfsih_locator_plugin"


class Settings(SettingManager):
    def __init__(self):
        SettingManager.__init__(self, pluginName)

        # change filter name
        self.add_setting(String("filter_name", Scope.Global, ''))

        # beautify group names
        self.add_setting(Bool("remove_leading_digits", Scope.Global, True))
        self.add_setting(Bool("replace_underscore", Scope.Global, True))
        self.add_setting(Bool("break_camelcase", Scope.Global, True))

        # connection settings
        self.add_setting(String("geomapfish_url", Scope.Global, ''))
        self.add_setting(String("geomapfish_crs", Scope.Global, 'EPSG:3857'))
        self.add_setting(String("geomapfish_user", Scope.Global, ''))
        self.add_setting(String("geomapfish_pass", Scope.Global, ''))

        # number of results
        self.add_setting(Integer("category_limit", Scope.Global, 8))
        self.add_setting(Integer("total_limit", Scope.Global, 50))
