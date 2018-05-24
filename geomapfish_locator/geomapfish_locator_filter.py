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

from PyQt5.QtCore import pyqtSignal, QUrl, QUrlQuery, QByteArray
from PyQt5.QtWidgets import QDialog
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.uic import loadUiType

from qgis.core import Qgis, QgsMessageLog, QgsLocatorFilter, QgsLocatorResult, QgsRectangle, \
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsGeometry, QgsWkbTypes
from osgeo import ogr

from .qgissettingmanager.setting_dialog import SettingDialog, UpdateMode
from .network_access_manager import NetworkAccessManager, RequestsException, RequestsExceptionUserAbort
from .settings import Settings


DialogUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), 'ui/config.ui'))


class ConfigDialog(QDialog, DialogUi, SettingDialog):
    def __init__(self):
        settings = Settings()
        QDialog.__init__(self)
        SettingDialog.__init__(self, setting_manager=settings, mode=UpdateMode.DialogAccept)
        self.setupUi(self)
        self.settings = settings
        self.init_widgets()


class GeomapfishLocatorFilter(QgsLocatorFilter):

    USER_AGENT = b'Mozilla/5.0 QGIS NominatimLocatorFilter'

    def __init__(self, iface, rubber_slot):
        self.iface = iface
        self.reply = None
        self.settings = Settings()
        self.rubberSlot = rubber_slot
        super().__init__()

    def name(self):
        return self.__class__.__name__

    def clone(self):
        return GeomapfishLocatorFilter(self.iface, self.rubber_slot)

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
        ConfigDialog().exec_()

    @staticmethod
    def url_with_param(url, params):
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        return url

    def fetchResults(self, search, context, feedback):

        self.feedback = feedback

        self.info("start GMF locator search...")

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

        r = self.url_with_param(url, params)
        self.info(r.url())

        nam = NetworkAccessManager()
        self.feedback.canceled.connect(nam.abort)
        try:
            (response, content) = nam.request(r.url().toString(), headers=headers, blocking=True)
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
        #self.info(data)

        features = data['features']
        for f in features:
            json_geom = json.dumps(f['geometry'])
            ogr_geom = ogr.CreateGeometryFromJson(json_geom)
            wkt = ogr_geom.ExportToWkt()
            geometry = QgsGeometry.fromWkt(wkt)
            self.info('---------')
            self.info(QgsWkbTypes.geometryDisplayString(geometry.type()))
            self.info(f.keys())
            self.info('{} {}'.format(f['properties']['layer_name'], f['properties']['label']))
            #self.info(f['bbox'])
            #self.info(f['geometry'])
            if geometry is None:
                continue
            result = QgsLocatorResult()
            result.filter = self
            result.displayString = f['properties']['label']
            result.group = f['properties']['layer_name']
            result.userData = geometry
            self.resultFetched.emit(result)

    def triggerResult(self, result):
        # need to forward the result to the plugin class which runs on main thread
        # while the filter runs on another thread
        self.rubber_slot(result)

    def info(self, msg=""):
        QgsMessageLog.logMessage('{} {}'.format(self.__class__.__name__, msg), 'QgsLocatorFilter', Qgis.Info)
