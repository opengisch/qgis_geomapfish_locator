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


import os
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QSettings, QTranslator, pyqtSlot, QObject
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgisInterface
from geomapfish_locator.core.locator_filter import GeomapfishLocatorFilter
from geomapfish_locator.core.old_version_import import old_version_import
from geomapfish_locator.core.settings import Settings
from geomapfish_locator.core.service import Service

DEBUG = True


class GeomapfishLocatorPlugin(QObject):

    plugin_name = "&Geomapfish Locator Filters"

    def __init__(self, iface: QgisInterface):
        QObject.__init__(self)
        self.iface = iface
        self.locator_filters = []
        self.settings = Settings()
        menu_action = QAction(QCoreApplication.translate('Geomapfish', 'Add new service'), self.iface.mainWindow())
        self.iface.addPluginToMenu(self.plugin_name, menu_action)
        self.menu_actions = [menu_action]

        for definition in self.settings.value('services'):
            self.add_service(Service(definition))

        import_service = old_version_import()
        if import_service:
            self.add_service(import_service)

        # initialize translation
        qgis_locale = QLocale(QSettings().value('locale/userLocale'))
        locale_path = os.path.join(os.path.dirname(__file__), 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'geomapfish_locator', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

    def add_locator_menu_action(self, locator_filter: GeomapfishLocatorFilter):
        action = QAction(locator_filter.service.name, self.iface.mainWindow())
        action.triggered.connect(lambda _: locator_filter.openConfigWidget())
        self.iface.addPluginToMenu(self.plugin_name, action)
        self.menu_actions.append(action)

    def add_service(self, service):
        for locator_filter in self.locator_filters:
            if service.name == locator_filter.service.name:
                service.name = QCoreApplication.translate('Geomapfish', '{service} copy'.format(service=service.name))

        locator_filter = GeomapfishLocatorFilter(service, self.iface)
        locator_filter.changed.connect(self.filter_changed)
        self.add_locator_menu_action(locator_filter)
        self.iface.registerLocatorFilter(locator_filter)
        self.locator_filters.append(locator_filter)
        self.save_services()

    def initGui(self):
        pass

    def unload(self):
        for menu_action in self.menu_actions:
            self.iface.removePluginMenu(self.plugin_name, menu_action)
        for locator_filter in self.locator_filters:
            self.iface.deregisterLocatorFilter(locator_filter)

    def save_services(self):
        services = []
        for locator_filter in self.locator_filters:
            services.append(locator_filter.service.as_dict())
        self.settings.set_value('services', services)

    def refresh_menu(self):
        for menu_action in self.menu_actions[1:]:
            self.iface.removePluginMenu(self.plugin_name, menu_action)
        for locator_filter in self.locator_filters:
            self.add_locator_menu_action(locator_filter)

    @pyqtSlot()
    def filter_changed(self):
        self.refresh_menu()
        self.save_services()
