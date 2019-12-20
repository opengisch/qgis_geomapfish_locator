
from qgis.core import QgsSettings

from .service import Service


def old_version_import() -> Service:

    if QgsSettings().contains('plugins/geomapfsih_locator_plugin/geomapfish_url'):
        definition = dict()
        definition['name'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/filter_name', 'geomapfish', type=str)
        definition['url'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/geomapfish_url', '', type=str)
        definition['crs'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/geomapfish_crs', '', type=str)

        definition['remove_leading_digits'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/remove_leading_digits', True, type=bool)
        definition['replace_underscore'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/replace_underscore', True, type=bool)
        definition['break_camelcase'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/break_camelcase', True, type=bool)

        definition['category_limit'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/category_limit', 8, type=int)
        definition['total_limit'] = QgsSettings().value('plugins/geomapfsih_locator_plugin/total_limit', 50, type=int)

        user = QgsSettings().value('plugins/geomapfsih_locator_plugin/geomapfish_user', '', type=str)
        pwd = QgsSettings().value('plugins/geomapfsih_locator_plugin/geomapfish_pass', '', type=str)

        # todo: handle user,pass

        # todo: delete old keys

        return Service(definition)

    else:
        return None



