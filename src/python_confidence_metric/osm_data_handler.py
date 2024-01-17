# osm_data_handler.py file

from osmapi import OsmApi


class OSMDataHandler:
    def __init__(self, username="", password=""):
        self.api = OsmApi(username=username, password=password)

    def get_way_history(self, osmid):
        return self.api.WayHistory(osmid)

    def get_map_data(self, bounding_params):
        return self.api.Map(
            min_lon=bounding_params[0],
            min_lat=bounding_params[1],
            max_lon=bounding_params[2],
            max_lat=bounding_params[3]
        )

    def get_item_history(self, item):
        if 'element_type' in item:
            item_type = item['element_type']
        else:
            return None
        id = item.get('osmid')

        if item_type == 'node':
            return self.api.NodeHistory(id)
        elif item_type == 'way':
            return self.api.WayHistory(id)
        elif item_type == 'relation':
            return self.api.RelationHistory(id)
        return None
