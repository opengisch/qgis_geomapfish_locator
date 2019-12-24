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
from qgis.PyQt.QtCore import QUrl, QUrlQuery, QTimer, pyqtSlot, pyqtSignal

from qgis.core import Qgis, QgsMessageLog, QgsLocatorFilter, QgsLocatorResult, QgsApplication, \
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand, QgisInterface
from osgeo import ogr

from geomapfish_locator.core.network_access_manager import NetworkAccessManager, RequestsException, RequestsExceptionUserAbort
from geomapfish_locator.core.service import Service
from geomapfish_locator.core.utils import slugify
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
        self.rubber_band = None
        self.iface = None
        self.map_canvas = None
        self.current_timer = None
        self.transform = None

        # only get map_canvas on main thread, not when cloning
        if iface is not None:
            self.iface = iface
            self.map_canvas = iface.mapCanvas()
            self.map_canvas.destinationCrsChanged.connect(self.create_transform)

            self.rubber_band = QgsRubberBand(self.map_canvas)
            self.rubber_band.setColor(QColor(255, 255, 50, 200))
            self.rubber_band.setIcon(self.rubber_band.ICON_CIRCLE)
            self.rubber_band.setIconSize(15)
            self.rubber_band.setWidth(4)
            self.rubber_band.setBrushStyle(Qt.NoBrush)

            self.create_transform()

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
            self.create_transform()
            self.changed.emit()

    def create_transform(self):
        srv_crs_authid = self.service.crs
        src_crs = QgsCoordinateReferenceSystem(srv_crs_authid)
        assert src_crs.isValid()
        dst_crs = self.map_canvas.mapSettings().destinationCrs()
        self.transform = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())

    @staticmethod
    def url_with_param(url, params) -> str:
        url = QUrl(url)
        q = QUrlQuery(url)
        for key, value in params.items():
            q.addQueryItem(key, value)
        url.setQuery(q)
        return url.url()

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
        if self.rubber_band:
            self.rubber_band.reset(QgsWkbTypes.PointGeometry)
        if self.current_timer is not None:
            self.current_timer.timeout.disconnect(self.clear_results)
            self.current_timer.stop()
            self.current_timer.deleteLater()
            self.current_timer = None

    def fetchResults(self, search, context, feedback):
        try:
            self.dbg_info("start GMF locator search...")

            url = self.service.url

            if url == "":
                self.emit_bad_configuration()
                return

            params = {
                'query': search,
                'limit': str(self.service.total_limit),
                'partitionlimit': str(self.service.category_limit)
            }

            if len(search) < 2:
                return

            headers = {b'User-Agent': self.USER_AGENT}

            url = self.url_with_param(url, params)
            self.dbg_info(url)

            nam = NetworkAccessManager(self.service.authid)
            feedback.canceled.connect(nam.abort)
            (response, content) = nam.request(url, headers=headers, blocking=True)
            self.handle_response(response, content)

        except RequestsExceptionUserAbort:
            pass
        except RequestsException as err:
            self.emit_bad_configuration(str(err))
            self.info(err)
        except Exception as e:
            self.info(str(e), Qgis.Critical)
            #exc_type, exc_obj, exc_traceback = sys.exc_info()
            #filename = os.path.split(exc_traceback.tb_frame.f_code.co_filename)[1]
            #self.info('{} {} {}'.format(exc_type, filename, exc_traceback.tb_lineno), Qgis.Critical)
            #self.info(traceback.print_exception(exc_type, exc_obj, exc_traceback), Qgis.Critical)

        finally:
            self.finished.emit()

    def handle_response(self, response, content):
        try:
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
                if Qgis.QGIS_VERSION_INT >= 30100:
                    result.group = self.beautify_group(f['properties']['layer_name'])
                result.userData = geometry
                self.resultFetched.emit(result)

        except Exception as e:
            self.info(str(e), Qgis.Critical)
            #exc_type, exc_obj, exc_traceback = sys.exc_info()
            #filename = os.path.split(exc_traceback.tb_frame.f_code.co_filename)[1]
            #self.info('{} {} {}'.format(exc_type, filename, exc_traceback.tb_lineno), Qgis.Critical)
            # self.info(traceback.print_exception(exc_type, exc_obj, exc_traceback), Qgis.Critical)

    def triggerResult(self, result):
        self.clear_results()
        if result.userData == FilterNotConfigured:
            self.openConfigWidget()
            if self.iface and hasattr(self.iface, 'invalidateLocatorResults'):
                # from QGIS 3.2 iface has invalidateLocatorResults
                self.iface.invalidateLocatorResults()
            return

        # this should be run in the main thread, i.e. mapCanvas should not be None
        geometry = result.userData
        geometry.transform(self.transform)

        self.rubber_band.reset(geometry.type())
        self.rubber_band.addGeometry(geometry, None)
        rect = geometry.boundingBox()
        rect.scale(1.5)
        self.map_canvas.setExtent(rect)
        self.map_canvas.refresh()

        self.current_timer = QTimer()
        self.current_timer.timeout.connect(self.clear_results)
        self.current_timer.setSingleShot(True)
        self.current_timer.start(5000)

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

