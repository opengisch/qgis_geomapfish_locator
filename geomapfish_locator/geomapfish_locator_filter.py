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


import json
import os
import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QUrl, QUrlQuery, QByteArray
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUiType

from qgis.core import Qgis, QgsMessageLog, QgsLocatorFilter, QgsLocatorResult, QgsRectangle, \
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand
from osgeo import ogr

from .qgissettingmanager.setting_dialog import SettingDialog, UpdateMode
from .network_access_manager import NetworkAccessManager, RequestsException, RequestsExceptionUserAbort
from .settings import Settings

DEBUG=False

DialogUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), 'ui/config.ui'))


class ConfigDialog(QDialog, DialogUi, SettingDialog):
    def __init__(self, parent=None):
        settings = Settings()
        QDialog.__init__(self, parent)
        SettingDialog.__init__(self, setting_manager=settings, mode=UpdateMode.DialogAccept)
        self.setupUi(self)
        self.settings = settings
        self.init_widgets()


class GeomapfishLocatorFilter(QgsLocatorFilter):

    USER_AGENT = b'Mozilla/5.0 QGIS NominatimLocatorFilter'

    def __init__(self, map_canvas):
        super().__init__()
        self.rubber_band = None
        self.settings = Settings()
        self.reply = None

        if map_canvas is not None:
            self.map_canvas = map_canvas
            self.rubber_band = QgsRubberBand(map_canvas)
            self.rubber_band.setColor(QColor(255, 255, 50, 200))
            self.rubber_band.setIcon(self.rubber_band.ICON_CIRCLE)
            self.rubber_band.setIconSize(15)
            self.rubber_band.setWidth(4)
            self.rubber_band.setBrushStyle(Qt.NoBrush)

    def name(self):
        return self.__class__.__name__

    def clone(self):
        return GeomapfishLocatorFilter(None)

    def displayName(self):
        name = self.settings.value("filter_name")
        if name != '':
            return name
        return self.tr('Geomapfish service')

    def prefix(self):
        return 'gmf'

    def hasConfigWidget(self):
        return True

    def openConfigWidget(self, parent):
        ConfigDialog(parent).exec_()

    @staticmethod
    def url_with_param(url, params):
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        return url.url()

    def fetchResults(self, search, context, feedback):
        self.dbg_info("start GMF locator search...")

        if len(search) < 2:
            return

        if self.reply is not None and self.reply.isRunning():
            self.reply.abort()

        url = self.settings.value('geomapfish_url')
        params = {
            'query': search,
            'limit': str(self.settings.value('total_limit')),
            'partitionlimit': str(self.settings.value('category_limit'))
        }

        headers = {}
        headers = {b'User-Agent': self.USER_AGENT}
        if self.settings.value('geomapfish_user') != '':
            user = self.settings.value('geomapfish_user')
            password = self.settings.value('geomapfish_pass')
            auth_data = "{}:{}".format(user, password)
            b64 = QByteArray(auth_data.encode()).toBase64()
            headers[QByteArray('Authorization'.encode())] = QByteArray('Basic '.encode()) + b64

        url = self.url_with_param(url, params)
        self.dbg_info(url)

        nam = NetworkAccessManager()
        feedback.canceled.connect(nam.abort)
        try:
            (response, content) = nam.request(url, headers=headers, blocking=True)
            self.handle_response(response, content)
        except RequestsExceptionUserAbort:
            pass
        except RequestsException as err:
            self.info(err)

    def handle_response(self, response, content):
        if response.status_code != 200:
            self.info("Error with status code: {}".format(response.status_code))
            return

        data = json.loads(content.decode('utf-8'))
        #self.dbg_info(data)

        features = data['features']
        for f in features:
            json_geom = json.dumps(f['geometry'])
            ogr_geom = ogr.CreateGeometryFromJson(json_geom)
            wkt = ogr_geom.ExportToWkt()
            geometry = QgsGeometry.fromWkt(wkt)
            self.dbg_info('---------')
            self.dbg_info(QgsWkbTypes.geometryDisplayString(geometry.type()))
            self.dbg_info(f.keys())
            self.dbg_info('{} {}'.format(f['properties']['layer_name'], f['properties']['label']))
            self.dbg_info(f['bbox'])
            self.dbg_info(f['geometry'])
            if geometry is None:
                continue
            result = QgsLocatorResult()
            result.filter = self
            result.displayString = f['properties']['label']
            result.group = self.beautify_group(f['properties']['layer_name'])
            result.userData = geometry
            self.resultFetched.emit(result)

    def triggerResult(self, result):
        # this should be run in the main thread, i.e. mapCanvas should not be None
        geometry = result.userData

        srv_crs_authid = self.settings.value('geomapfish_crs')
        src_crs = QgsCoordinateReferenceSystem(srv_crs_authid)
        if src_crs.isValid():
            dst_crs = self.map_canvas.mapSettings().destinationCrs()
            tr = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())
            geometry.transform(tr)

        self.rubber_band.reset(geometry.type())
        self.rubber_band.addGeometry(geometry, None)
        rect = geometry.boundingBox()
        rect.scale(1.5)
        self.map_canvas.setExtent(rect)
        self.map_canvas.refresh()

    def beautify_group(self, group):
        if self.settings.value("remove_leading_digits"):
            group = re.sub('^\d+', '', group)
        if self.settings.value("replace_underscore"):
            group = group.replace("_", " ")
        if self.settings.value("break_camelcase"):
            group = self.break_camelcase(group)
        return group

    def info(self, msg="", level=Qgis.Info):
        QgsMessageLog.logMessage('{} {}'.format(self.__class__.__name__, msg), 'QgsLocatorFilter', level)

    def dbg_info(self, msg=""):
        if DEBUG:
            self.info(msg)

    @staticmethod
    def break_camelcase(identifier):
        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
        return ' '.join([m.group(0) for m in matches])

