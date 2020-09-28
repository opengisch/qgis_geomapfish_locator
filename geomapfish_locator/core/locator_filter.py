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


import json
import re

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QUrl, QUrlQuery, QTimer, pyqtSlot, pyqtSignal, QByteArray
from qgis.PyQt.QtNetwork import QNetworkRequest

from qgis.core import Qgis, QgsMessageLog, QgsLocatorFilter, QgsLocatorResult, QgsApplication, \
    QgsCoordinateReferenceSystem, QgsGeometry, QgsWkbTypes, QgsBlockingNetworkRequest, QgsReferencedRectangle
from qgis.gui import QgsRubberBand, QgisInterface
from osgeo import ogr

from geomapfish_locator.core.service import Service
from geomapfish_locator.core.utils import slugify, dbg_info
from geomapfish_locator.core.settings import Settings
from geomapfish_locator.gui.filter_configuration_dialog import FilterConfigurationDialog

DEBUG = True


class FilterNotConfigured:
    pass


class GeomapfishLocatorFilter(QgsLocatorFilter):

    USER_AGENT = b'Mozilla/5.0 QGIS GeoMapFish Locator Filter'

    changed = pyqtSignal()

    def __init__(self, service: Service, iface: QgisInterface = None):
        super().__init__()
        self.service = service.clone()
        self.rubberband = None
        self.iface = None
        self.map_canvas = None
        self.current_timer = None
        self.settings = Settings()
        self.crs = QgsCoordinateReferenceSystem(self.service.crs)

        # only get map_canvas on main thread, not when cloning
        if iface is not None:
            self.iface = iface
            self.map_canvas = iface.mapCanvas()

            self.rubberband = QgsRubberBand(self.map_canvas)
            self.reset_rubberband()

    def name(self) -> str:
        return slugify(self.displayName())

    def clone(self):
        return GeomapfishLocatorFilter(self.service)

    def displayName(self) -> str:
        return self.service.name

    def prefix(self) -> str:
        return 'gmf'

    def hasConfigWidget(self) -> bool:
        return True

    def openConfigWidget(self, parent=None):
        cfg = FilterConfigurationDialog(self.service, parent)
        if cfg.exec_():
            self.service = cfg.service.clone()
            self.crs = QgsCoordinateReferenceSystem(self.service.c
            self.changed.emit()

    def reset_rubberband(self):
        # this should happen on main thread only!
        self.rubberband.setColor(self.settings.value('point_color'))
        self.rubberband.setIcon(self.rubberband.ICON_CIRCLE)
        self.rubberband.setIconSize(self.settings.value('point_size'))
        self.rubberband.setWidth(self.settings.value('line_width'))
        self.rubberband.setBrushStyle(Qt.NoBrush)

    @staticmethod
    def url_with_param(url, params) -> str:
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        return url

    def emit_bad_configuration(self, err=None):
        result = QgsLocatorResult()
        result.filter = self
        result.displayString = self.tr('Locator filter is not configured.')
        result.description = err if err else self.tr('Double-click to configure it.')
        result.userData = FilterNotConfigured
        result.icon = QgsApplication.getThemeIcon('mIconWarning.svg')
        self.resultFetched.emit(result)
        return

    @pyqtSlot()
    def clear_results(self):
        if self.rubberband:
            self.rubberband.reset(QgsWkbTypes.PointGeometry)
        if self.current_timer is not None:
            self.current_timer.timeout.disconnect(self.clear_results)
            self.current_timer.stop()
            self.current_timer.deleteLater()
            self.current_timer = None

    def fetchResults(self, search, context, feedback):
        self.dbg_info("start GMF locator search...")
        url = self.service.url
        if not url:
            self.emit_bad_configuration()
            return
        if len(search) < 2:
            return

        params = {
            'query': search,
            'limit': str(self.service.total_limit),
            'partitionlimit': str(self.service.category_limit)
        }
        url = self.url_with_param(url, params)
        self.dbg_info(url.url())

        _request = QNetworkRequest(url)
        _request.setRawHeader(b'User-Agent', self.USER_AGENT)
        request = QgsBlockingNetworkRequest()
        if self.service.authid:
            request.setAuthCfg(self.service.authid)

        response = request.get(_request, False, feedback)
        if response == QgsBlockingNetworkRequest.NoError:
            self.handle_response(request.reply().content())
        else:
            error_msg = request.reply().errorString()
            self.emit_bad_configuration(error_msg)
            self.info(error_msg, Qgis.Critical)
        self.finished.emit()

    def handle_response(self, content: QByteArray):
        try:
            data = json.loads(str(content.data(), encoding='utf-8'))
            # self.dbg_info(data)

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

        except Exception as e:
            self.info(str(e), Qgis.Critical)
            # exc_type, exc_obj, exc_traceback = sys.exc_info()
            # #filename = os.path.split(exc_traceback.tb_frame.f_code.co_filename)[1]
            # #self.info('{} {} {}'.format(exc_type, filename, exc_traceback.tb_lineno), Qgis.Critical)
            # self.info(traceback.print_exception(exc_type, exc_obj, exc_traceback), Qgis.Critical)

    def triggerResult(self, result):
        self.clear_results()
        if result.userData == FilterNotConfigured:
            self.openConfigWidget()
            self.iface.invalidateLocatorResults()
            return

        # this should be run in the main thread, i.e. mapCanvas should not be None
        geometry = result.userData
        # geometry.transform(self.transform)
        dbg_info(str(geometry.asWkt()))
        dbg_info(geometry.type())

        try:
            rect = QgsReferencedRectangle(geometry.boundingBox(), self.crs)
            rect.scale(4)
            self.map_canvas.setReferencedExtent(rect)
        except AttributeError:
            # QGIS < 3.10 handling
            from qgis.core import QgsCoordinateTransform, QgsProject
            transform = QgsCoordinateTransform(self.crs, self.map_canvas.mapSettings().destinationCrs(), QgsProject.instance())
            geometry.transform(transform)
            rect = geometry.boundingBox()
            rect.scale(4)
            self.map_canvas.setExtent(rect)

        self.map_canvas.refresh()

        if geometry.type() == QgsWkbTypes.PolygonGeometry:
            nflash = 16
            color1: QColor = self.settings.value('polygon_color')
            color2 = color1
            color1.setAlpha(200)
            color2.setAlpha(100)
            self.map_canvas.flashGeometries([geometry], self.crs, color1, color2, nflash, self.settings.value('highlight_duration')/nflash*1000)
        else:
            self.rubberband.reset(geometry.type())
            self.rubberband.addGeometry(geometry, self.crs)

            self.current_timer = QTimer()
            self.current_timer.timeout.connect(self.clear_results)
            self.current_timer.setSingleShot(True)
            self.current_timer.start(self.settings.value('highlight_duration')*1000)

    def beautify_group(self, group) -> str:
        if self.service.remove_leading_digits:
            group = re.sub('^[0-9]+', '', group)
        if self.service.replace_underscore:
            group = group.replace("_", " ")
        if self.service.break_camelcase:
            group = self.break_camelcase(group)
        return group

    def info(self, msg="", level=Qgis.Info):
        QgsMessageLog.logMessage('{} {}'.format(self.__class__.__name__, msg), 'QgsLocatorFilter', level)

    def dbg_info(self, msg=""):
        if DEBUG:
            self.info(msg)

    @staticmethod
    def break_camelcase(identifier) -> str:
        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
        return ' '.join([m.group(0) for m in matches])

