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

DEBUG = False

from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from .geomapfish_locator_filter import GeomapfishLocatorFilter


class GeomapfishLocatorPlugin:

    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.gmf_filter = GeomapfishLocatorFilter(iface.mapCanvas())
        self.iface.registerLocatorFilter(self.gmf_filter)

    def initGui(self):
        pass

    def unload(self):
        self.iface.deregisterLocatorFilter(self.gmf_filter)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QgsApplication.translate('QGIS Locator Plugin', message)