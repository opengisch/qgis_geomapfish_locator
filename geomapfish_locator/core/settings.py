# -*- coding: utf-8 -*-
"""
/***************************************************************************

 QGIS Geomapfish Locator Plugin
 Copyright (C) 2019 Denis Rouzaud

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 """

from geomapfish_locator.qgissettingmanager import SettingManager, Scope, List, Integer

pluginName = "geomapfsih_locator_plugin"


class Settings(SettingManager):
    def __init__(self):
        SettingManager.__init__(self, pluginName)
        self.add_setting(List('services', Scope.Global, []))

        self.add_setting(Integer('highlight_duration', Scope.Global, 8))

