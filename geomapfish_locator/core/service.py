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

import copy


class Service:
    def __init__(self, definition: dict = {}):
        self.name = definition.get("name")
        self.url = definition.get("url")
        self.crs = definition.get("crs")
        self.authid = definition.get("authid")

        self.category_limit = definition.get("category_limit", 8)
        self.total_limit = definition.get("total_limit", 40)

        # beautify group names
        self.remove_leading_digits = definition.get("remove_leading_digits", True)
        self.replace_underscore = definition.get("replace_underscore", True)
        self.break_camelcase = definition.get("break_camelcase", True)

    def is_valid(self):
        if not self.name or not self.url or not self.crs:
            return False
        return True

    def clone(self):
        return copy.deepcopy(self)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "crs": self.crs,
            "authid": self.authid,
            "category_limit": self.category_limit,
            "total_limit": self.total_limit,
            "remove_leading_digits": self.remove_leading_digits,
            "replace_underscore": self.replace_underscore,
            "break_camelcase": self.break_camelcase,
        }
