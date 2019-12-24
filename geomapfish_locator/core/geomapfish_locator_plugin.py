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


DEBUG = True



import os
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QSettings, QTranslator
from qgis.gui import QgisInterface
from geomapfish_locator.core.locator_filter import GeomapfishLocatorFilter
from geomapfish_locator.core.old_version_import import old_version_import


class GeomapfishLocatorPlugin:

    def __init__(self, iface: QgisInterface):
        self.iface = iface
        self.locator_filters = {}

        import_service = old_version_import()
        if import_service:
            self.add_service(import_service)

        # self.gmf_filter = GeomapfishLocatorFilter(iface)
        # self.iface.registerLocatorFilter(self.gmf_filter)

        # initialize translation
        qgis_locale = QLocale(QSettings().value('locale/userLocale'))
        locale_path = os.path.join(os.path.dirname(__file__), 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'geomapfish_locator', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

    def add_service(self, service):
        if service.name in self.locator_filters:
            # todo unload or skip
            pass

        locator_filter = GeomapfishLocatorFilter(service)
        self.iface.registerLocatorFilter(locator_filter)
        self.locator_filters[service.name] = locator_filter

    def initGui(self):
        pass

    def unload(self):
        for locator_filter in self.locator_filters.values():
            self.iface.deregisterLocatorFilter(locator_filter)
