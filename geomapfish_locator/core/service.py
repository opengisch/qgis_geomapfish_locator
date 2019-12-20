

class Service:
    def __init__(self, definition: dict):
        self.name = definition['name']
        self.url = definition['url']
        self.crs = definition['crs']

        self.category_limit = definition.get('category_limit', True)
        self.total_limit = definition.get('total_limit', True)

        # beautify group names
        self.remove_leading_digits = definition.get('remove_leading_digits', True)
        self.replace_underscore = definition.get('replace_underscore', True)
        self.break_camelcase = definition.get('break_camelcase', True)

