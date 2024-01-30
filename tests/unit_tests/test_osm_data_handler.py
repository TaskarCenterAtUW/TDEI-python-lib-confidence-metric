import unittest
from unittest.mock import patch, MagicMock
from src.osw_confidence_metric.osm_data_handler import OSMDataHandler


class TestOSMDataHandler(unittest.TestCase):

    def setUp(self):
        patcher = patch('src.osw_confidence_metric.osm_data_handler.OsmApi')
        self.mock_osm_api_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_osm_api = MagicMock()
        self.mock_osm_api_class.return_value = self.mock_osm_api
        self.mock_osm_api.WayHistory.return_value = 'Mocked Way History'
        self.mock_osm_api.Map.return_value = 'Mocked Map Data'
        self.mock_osm_api.NodeHistory.return_value = 'Mocked Node History'
        self.mock_osm_api.RelationHistory.return_value = 'Mocked Relation History'

    def test_initialization_with_credentials(self):
        username = 'user'
        password = 'pass'
        handler = OSMDataHandler(username, password)
        self.assertIsNotNone(handler.api)

    def test_get_way_history_valid_osmid(self):
        osmid = 12345
        handler = OSMDataHandler()
        result = handler.get_way_history(osmid)
        self.mock_osm_api.WayHistory.assert_called_once_with(osmid)
        self.assertEqual(result, 'Mocked Way History')

    def test_get_way_history(self):
        osmid = 12345
        handler = OSMDataHandler()
        result = handler.get_way_history(osmid)
        self.mock_osm_api.WayHistory.assert_called_once_with(osmid)
        self.assertEqual(result, 'Mocked Way History')

    def test_get_map_data(self):
        bounding_params = [0, 1, 2, 3]
        handler = OSMDataHandler()
        result = handler.get_map_data(bounding_params=bounding_params)
        self.mock_osm_api.Map.assert_called_once()
        self.assertEqual(result, 'Mocked Map Data')

    def test_get_item_history_node(self):
        osmid = 12345
        item = {'element_type': 'node', 'osmid': osmid}
        handler = OSMDataHandler()
        result = handler.get_item_history(item=item)
        self.mock_osm_api.NodeHistory.assert_called_once_with(osmid)
        self.assertEqual(result, 'Mocked Node History')

    def test_get_item_history_way(self):
        osmid = 12345
        item = {'element_type': 'way', 'osmid': osmid}
        handler = OSMDataHandler()
        result = handler.get_item_history(item=item)
        self.mock_osm_api.WayHistory.assert_called_once_with(osmid)
        self.assertEqual(result, 'Mocked Way History')

    def test_get_item_history_relation(self):
        osmid = 12345
        item = {'element_type': 'relation', 'osmid': osmid}
        handler = OSMDataHandler()
        result = handler.get_item_history(item=item)
        self.mock_osm_api.RelationHistory.assert_called_once_with(osmid)
        self.assertEqual(result, 'Mocked Relation History')

    def test_get_item_history_invalid_type(self):
        osmid = 12345
        item = {'element_type': 'invalid_type', 'osmid': osmid}
        handler = OSMDataHandler()
        result = handler.get_item_history(item=item)
        self.assertIsNone(result)

    def test_get_item_history_invalid_item(self):
        item = {}
        handler = OSMDataHandler()
        result = handler.get_item_history(item=item)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
