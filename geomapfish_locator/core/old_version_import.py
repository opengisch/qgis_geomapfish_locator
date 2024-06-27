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

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsSettings
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

from .service import Service
from .utils import dbg_info, info


def old_version_import() -> Service:
    settings = QgsSettings()
    if settings.contains("plugins/geomapfsih_locator_plugin/geomapfish_url"):
        definition = dict()
        definition["name"] = settings.value(
            "plugins/geomapfsih_locator_plugin/filter_name", "geomapfish", type=str
        )
        definition["url"] = settings.value(
            "plugins/geomapfsih_locator_plugin/geomapfish_url", "", type=str
        )
        definition["crs"] = settings.value(
            "plugins/geomapfsih_locator_plugin/geomapfish_crs", "", type=str
        )

        definition["remove_leading_digits"] = settings.value(
            "plugins/geomapfsih_locator_plugin/remove_leading_digits", True, type=bool
        )
        definition["replace_underscore"] = settings.value(
            "plugins/geomapfsih_locator_plugin/replace_underscore", True, type=bool
        )
        definition["break_camelcase"] = settings.value(
            "plugins/geomapfsih_locator_plugin/break_camelcase", True, type=bool
        )

        definition["category_limit"] = settings.value(
            "plugins/geomapfsih_locator_plugin/category_limit", 8, type=int
        )
        definition["total_limit"] = settings.value(
            "plugins/geomapfsih_locator_plugin/total_limit", 50, type=int
        )

        user = settings.value("plugins/geomapfsih_locator_plugin/geomapfish_user", "", type=str)
        pwd = settings.value("plugins/geomapfsih_locator_plugin/geomapfish_pass", "", type=str)

        info(f"importing old service: {definition}")

        if user:
            reply = QMessageBox.question(
                None,
                "Geomapfish Locator",
                QCoreApplication.translate(
                    "Geomapfish Locator",
                    "User and password were saved in clear text in former Geomapfish plugin. "
                    "Would you like to use QGIS authentication to store these credentials? "
                    "If not, they will be removed.",
                ),
            )
            if reply == QMessageBox.Yes:
                config = QgsAuthMethodConfig("Basic")
                config.setName("geomapfish_{}".format(definition["name"]))
                config.setConfig("username", user)
                config.setConfig("password", pwd)
                QgsApplication.authManager().storeAuthenticationConfig(config)
                definition["authid"] = config.id()
                dbg_info(f"created new auth id: {config.id()}")
            else:
                drop_keys()
                return None

        drop_keys()
        return Service(definition)

    else:
        return None


def drop_keys():
    settings = QgsSettings()

    settings.remove("plugins/geomapfsih_locator_plugin/filter_name")
    settings.remove("plugins/geomapfsih_locator_plugin/geomapfish_url")
    settings.remove("plugins/geomapfsih_locator_plugin/geomapfish_crs")

    settings.remove("plugins/geomapfsih_locator_plugin/remove_leading_digits")
    settings.remove("plugins/geomapfsih_locator_plugin/replace_underscore")
    settings.remove("plugins/geomapfsih_locator_plugin/break_camelcase")

    settings.remove("plugins/geomapfsih_locator_plugin/category_limit")
    settings.remove("plugins/geomapfsih_locator_plugin/total_limit")

    settings.remove("plugins/geomapfsih_locator_plugin/geomapfish_user")
    settings.remove("plugins/geomapfsih_locator_plugin/geomapfish_pass")
