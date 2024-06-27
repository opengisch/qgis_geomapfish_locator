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
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.core import NULL
from qgis.gui import QgisInterface
from geomapfish_locator.core.locator_filter import GeomapfishLocatorFilter
from geomapfish_locator.core.old_version_import import old_version_import
from geomapfish_locator.core.settings import Settings
from geomapfish_locator.core.service import Service
from geomapfish_locator.core.utils import info
from geomapfish_locator.gui.geomapfish_settings_dialog import GeomapfishSettingsDialog
from geomapfish_locator.gui.filter_configuration_dialog import FilterConfigurationDialog

DEBUG = True


class GeomapfishLocatorPlugin(QObject):

    plugin_name = "&Geomapfish Locator Filters"

    def __init__(self, iface: QgisInterface):
        QObject.__init__(self)
        self.iface = iface
        self.locator_filters = []
        self.settings = Settings()
        menu_action_new = QAction(QCoreApplication.translate('Geomapfish', 'Add new service'), self.iface.mainWindow())
        menu_action_new.triggered.connect(self.new_service)
        self.iface.addPluginToMenu(self.plugin_name, menu_action_new)
        menu_action_settings = QAction(QCoreApplication.translate('Geomapfish', 'Settings'), self.iface.mainWindow())
        menu_action_settings.triggered.connect(self.show_settings)
        self.iface.addPluginToMenu(self.plugin_name, menu_action_settings)
        self.menu_entries = [menu_action_new, menu_action_settings]

        for definition in self.settings.value('services'):
            self.add_service(Service(definition))

        import_service = old_version_import()
        if import_service:
            self.add_service(import_service)

        # initialize translation
        qgis_locale = QLocale(
            str(QSettings().value("locale/userLocale")).replace(str(NULL), "en_CH")
        )
        locale_path = os.path.join(os.path.dirname(__file__), 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'geomapfish_locator', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        pass

    def add_locator_menu_action(self, locator_filter: GeomapfishLocatorFilter):
        menu = QMenu(locator_filter.service.name, self.iface.mainWindow())
        edit_action = menu.addAction(self.tr('edit'))
        edit_action.triggered.connect(lambda _: locator_filter.openConfigWidget())
        remove_action = menu.addAction(self.tr('remove'))
        remove_action.triggered.connect(lambda _: GeomapfishLocatorPlugin.remove_service(self, locator_filter, menu))
        self.iface.addPluginToMenu(self.plugin_name, menu.menuAction())
        self.menu_entries.append(menu)

    def new_service(self):
        service = Service()
        dlg = FilterConfigurationDialog(service)
        if dlg.exec_():
            if not dlg.service.is_valid():
                info("Service {}({}) is not valid".format(service.name, service.url))
            else:
                self.add_service(dlg.service.clone())

    def add_service(self, service):
        if not service.is_valid():
            info("Service {}({}) is not valid".format(service.name, service.url))
            return

        for locator_filter in self.locator_filters:
            if service.name == locator_filter.service.name:
                service.name = QCoreApplication.translate('Geomapfish', '{service} copy'.format(service=service.name))

        locator_filter = GeomapfishLocatorFilter(service, self.iface)
        locator_filter.changed.connect(self.filter_changed)
        self.add_locator_menu_action(locator_filter)
        self.iface.registerLocatorFilter(locator_filter)
        self.locator_filters.append(locator_filter)
        self.save_services()

    def remove_service(self, locator_filter, menu):
        reply = QMessageBox.question(
            self.iface.mainWindow(), self.plugin_name,
            self.tr('Are you sure to remove service "{}"'.format(locator_filter.service.name)),
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.iface.removePluginMenu(self.plugin_name, menu.menuAction())
            self.menu_entries.remove(menu)
            self.iface.deregisterLocatorFilter(locator_filter)
            self.locator_filters.remove(locator_filter)
            self.save_services()

    def unload(self):
        self.iface.invalidateLocatorResults()
        for menu_entry in self.menu_entries:
            if type(menu_entry) == QAction:
                self.iface.removePluginMenu(self.plugin_name, menu_entry)
            else:
                self.iface.removePluginMenu(self.plugin_name, menu_entry.menuAction())
        del self.menu_entries[:]
        for locator_filter in self.locator_filters:
            self.iface.deregisterLocatorFilter(locator_filter)
        self.locator_filters = {}

    def save_services(self):
        services = []
        for locator_filter in self.locator_filters:
            services.append(locator_filter.service.as_dict())
        self.settings.set_value('services', services)

    def refresh_menu(self):
        for menu_entry in self.menu_entries[1:]:
            if type(menu_entry) == QAction:
                self.iface.removePluginMenu(self.plugin_name, menu_entry)
            else:
                self.iface.removePluginMenu(self.plugin_name, menu_entry.menuAction())
        del self.menu_entries[1:]
        # use index based loop to avoid changing the variable used in the lambda !
        for i in range(len(self.locator_filters)):
            self.add_locator_menu_action(self.locator_filters[i])

    def show_settings(self, _):
        if GeomapfishSettingsDialog(self.iface.mainWindow()).exec_():
            for locator_filter in self.locator_filters:
                locator_filter.reset_rubberband()

    @pyqtSlot()
    def filter_changed(self):
        self.refresh_menu()
        self.save_services()
