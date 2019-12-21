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

from qgis.core import Qgis, QgsMessageLog
from qgis.utils import iface

DEBUG = True


def info(message: str, level: Qgis.MessageLevel = Qgis.Info):
    QgsMessageLog.logMessage("{}: {}".format('SoLocator', message), "Locator bar", level)
    iface.messageBar().pushMessage('SoLocator', message, level)


def dbg_info(message: str):
    if DEBUG:
        QgsMessageLog.logMessage("{}: {}".format('SoLocator', message), "Locator bar", Qgis.Info)