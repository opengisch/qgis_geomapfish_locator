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
import re
import unicodedata

DEBUG = True

PLUGIN_NAME = "Geomapfish Locator Filters"


def info(message: str, level: Qgis.MessageLevel = Qgis.Info):
    QgsMessageLog.logMessage("{}: {}".format(PLUGIN_NAME, message), "Locator bar", level)
    iface.messageBar().pushMessage('Geomapfish Locator', message, level)


def dbg_info(message: str):
    if DEBUG:
        QgsMessageLog.logMessage("{}: {}".format(PLUGIN_NAME, message), "Locator bar", Qgis.Info)


def slugify(text: str) -> str:
    # https://stackoverflow.com/q/5574042/1548052
    slug = unicodedata.normalize('NFKD', text)
    # slug = slug.encode('ascii', 'ignore').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    slug = re.sub(r'[-]+', '-', slug)
    return slug
