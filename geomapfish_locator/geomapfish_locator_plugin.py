# -*- coding: utf-8 -*-
"""
/***************************************************************************

                                 QgisLocator

                             -------------------
        begin                : 2018-05-03
        copyright            : (C) 2018 by Denis Rouzaud
        email                : denis@opengis.ch
        git sha              : $Format:%H$
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

from qgis.core import QgsApplication
from .gmf_locator_filter import gmfLocatorFilter


class GeomapfishLocatorPlugin:

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.gmf_filter = GeomapfishLocatorFilter(self.iface)
        self.gmf_filter.failed.connect(self.show_issue)
        self.iface.registerLocatorFilter(self.gmf_filter)

    def show_issue(self, err):
        self.filter.info("showing issue???")  # never come here?
        self.iface.messageBar().pushWarning("Geomapfish Locator Error", '{}'.format(err))

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