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

from qgis.PyQt.QtGui import QColor
from geomapfish_locator.qgissettingmanager import SettingManager, Scope, List, Integer, Color

pluginName = "geomapfsih_locator_plugin"


class Settings(SettingManager):
    def __init__(self):
        SettingManager.__init__(self, pluginName)
        self.add_setting(List('services', Scope.Global, []))

        self.add_setting(Integer('highlight_duration', Scope.Global, 8))

        self.add_setting(Integer('point_size', Scope.Global, 20))
        self.add_setting(Integer('line_width', Scope.Global, 4))
        self.add_setting(Color('polygon_color', Scope.Global, QColor(0, 100, 255, 200), allow_alpha=True))
        self.add_setting(Color('point_color', Scope.Global, QColor(255, 255, 50), allow_alpha=False))

