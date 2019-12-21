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


import os
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUiType

DialogUi, _ = loadUiType(os.path.join(os.path.dirname(__file__), '../ui/config.ui'))


class FilterConfigurationDialog(QDialog, DialogUi):
    def __init__(self, service, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.name.setText(service.name)
        self.crs.setCrs(QgsCoordinateReferenceSystem(service.crs))
        self.url.setText(service.url)

        self.remove_leading_digits.setChecked(service.remove_leading_digits)
        self.replace_underscore.setChecked(service.replace_underscore)
        self.break_camelcase.setChecked(service.break_camelcase)

        self.category_limit.setValue(service.category_limit)
        self.total_limit.setValue(service.total_limit)