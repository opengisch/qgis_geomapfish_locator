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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qgis.core import QgsApplication
from qgis.gui import QgsRubberBand
from .geomapfish_locator_filter import GeomapfishLocatorFilter

# some magic numbers to be able to zoom to more or less defined levels
ADDRESS = 1000
STREET = 1500
ZIP = 3000
PLACE = 30000
CITY = 120000
ISLAND = 250000
COUNTRY = 4000000


class GeomapfishLocatorPlugin:

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()

        self.rubber = QgsRubberBand(self.mapCanvas)
        self.rubber.setColor(QColor(255, 255, 50, 200))
        self.rubber.setIcon(self.rubber.ICON_CIRCLE)
        self.rubber.setIconSize(15)
        self.rubber.setWidth(4)
        self.rubber.setBrushStyle(Qt.NoBrush)

        self.gmf_filter = GeomapfishLocatorFilter(self.iface, self.rubber_slot)
        self.iface.registerLocatorFilter(self.gmf_filter)

    def initGui(self):
        pass

    def unload(self):
        self.iface.deregisterLocatorFilter(self.gmf_filter)

    def rubber_slot(self, result):
        srv_crs_authid = self.settings.value('geomapfish_crs')
        #srv_crs_authid = int(srv_crs_authid.replace('EPSG:', ''))

        geometry = result.userData

        self.rubber.reset(geometry.type())
        self.rubber.addGeometry(geometry, None)
        self.zoom_to_rubberband()

        self.info("UserClick: {}".format(result.displayString))
        doc = result.userData
        extent = doc['boundingbox']
        # "boundingbox": ["52.641015", "52.641115", "5.6737302", "5.6738302"]
        rect = QgsRectangle(float(extent[2]), float(extent[0]), float(extent[3]), float(extent[1]))
        dest_crs = QgsProject.instance().crs()
        results_crs = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.PostgisCrsId)
        transform = QgsCoordinateTransform(results_crs, dest_crs, QgsProject.instance())
        r = transform.transformBoundingBox(rect)
        self.iface.mapCanvas().setExtent(r, False)
        # map the result types to generic GeocoderLocator types to determine the zoom
        # BUT only if the extent < 100 meter (as for other objects it is probably ok)
        # mmm, some objects return 'type':'province', but extent is point
        scale_denominator = self.ZIP  # defaulting to something
        # TODO add other types?
        if doc['type'] in ['house', 'information']:
            scale_denominator = self.ADDRESS
        elif doc['type'] in ['way', 'motorway_junction', 'cycleway']:
            scale_denominator = self.STREET
        elif doc['type'] in ['postcode']:
            scale_denominator = self.ZIP
        elif doc['type'] in ['city']:
            scale_denominator = self.CITY
        elif doc['type'] in ['island']:
            scale_denominator = self.ISLAND
        elif doc['type'] in ['administrative']:  # ?? can also be a city etc...
            scale_denominator = self.COUNTRY

        self.iface.mapCanvas().zoomScale(scale_denominator)
        self.iface.mapCanvas().refresh()

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