import unittest
import networkx as nx
import geopandas as gpd
from datetime import datetime
from unittest.mock import patch, Mock
from shapely.geometry import Polygon, LineString
from src.python_confidence_metric.trust_score_calculator import TrustScoreAnalyzer


class MockOSMDataHandler:
    def get_way_history(self, osmid):
        return {
            'osmid': osmid,
            'versions': [1, 2, 3],
            'direct_confirmations': [4, 5, 6],
            'changes_to_tags': [7, 8, 9],
            'rollbacks': [10, 11, 12],
            'user_count': [13, 14, 15],
            'days_since_last_edit': [16, 17, 18],
            'tags': [19, 20, 21]
        }


class TestTrustScoreAnalyzer(unittest.TestCase):

    def setUp(self):
        # Create a TrustScoreAnalyzer instance with mock data
        sidewalk = lambda x: True  # Mock sidewalk filter
        self.osm_data_handler = MockOSMDataHandler()  # Mock OSMDataHandler
        date = datetime(2024, 1, 16)  # Mock date
        self.trust_score_analyzer = TrustScoreAnalyzer(sidewalk, self.osm_data_handler, date)

    def test_get_measures_from_polygon_empty_graph(self):
        # Create a sample polygon for testing
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

        # Mock an empty graph (ValueError will be raised)
        def mock_graph_from_polygon(*args, **kwargs):
            raise ValueError("Empty graph")

        # Replace the actual method with the mock method
        original_graph_from_polygon = self.trust_score_analyzer._analyze_sidewalk_features
        self.trust_score_analyzer._analyze_sidewalk_features = mock_graph_from_polygon

        # Call the get_measures_from_polygon method
        measures = self.trust_score_analyzer.get_measures_from_polygon(polygon)

        # Assert that the returned measures dictionary contains None values
        self.assertIsNone(measures['direct_trust_score'])
        self.assertIsNone(measures['time_trust_score'])
        self.assertIsNone(measures['indirect_values'])

        # Restore the original method
        self.trust_score_analyzer._analyze_sidewalk_features = original_graph_from_polygon

    @patch('src.python_confidence_metric.trust_score_calculator._initialize_gdf_columns')
    @patch('src.python_confidence_metric.trust_score_calculator._prepare_dask_dataframe')
    @patch('geonetworkx.graph_edges_to_gdf')
    def test_analyze_sidewalk_features(self, mock_graph_edges_to_gdf, mock_prepare_dask_dataframe,
                                       mock_initialize_gdf_columns):
        # Create a sample graph
        sample_graph = nx.Graph()

        # Create a sample GeoDataFrame and Dask DataFrame
        sample_gdf = Mock()
        sample_df_dask = Mock()

        # Mock the return values of functions
        mock_graph_edges_to_gdf.return_value = sample_gdf
        mock_prepare_dask_dataframe.return_value = sample_df_dask
        mock_initialize_gdf_columns.return_value = sample_gdf

        # Call the _analyze_sidewalk_features function
        result = self.trust_score_analyzer._analyze_sidewalk_features(sample_graph)

        # Check if the mock functions were called with the expected arguments
        mock_graph_edges_to_gdf.assert_called_once_with(sample_graph)
        mock_prepare_dask_dataframe.assert_called_once_with(gdf=sample_gdf)

        # Check if the result matches the expected result
        self.assertEqual(result, (0, 0))

    @patch('src.python_confidence_metric.trust_score_calculator._initialize_gdf_columns')
    @patch('src.python_confidence_metric.trust_score_calculator._prepare_dask_dataframe')
    @patch('geonetworkx.graph_edges_to_gdf')
    def test_analyze_sidewalk_features_non_empty_graph(self, mock_graph_edges_to_gdf, mock_prepare_dask_dataframe,
                                                       mock_initialize_gdf_columns):
        # Create a non-empty graph with a single edge
        G = nx.Graph()
        G.add_edge(1, 2, osmid=12345, geometry=LineString([(0, 0), (1, 1)]))

        # Create sample GeoDataFrame
        sample_gdf = Mock()

        # Mock the return values and methods
        mock_graph_edges_to_gdf.return_value = sample_gdf
        mock_initialize_gdf_columns.return_value = sample_gdf
        mock_prepare_dask_dataframe.return_value = sample_gdf

        # Call the _analyze_sidewalk_features method with the non-empty graph
        result = self.trust_score_analyzer._analyze_sidewalk_features(G)

        # Check if the mock methods were called with the expected arguments
        mock_graph_edges_to_gdf.assert_called_once_with(G)
        mock_initialize_gdf_columns.assert_called_once_with(gdf=sample_gdf)
        mock_prepare_dask_dataframe.assert_called_once_with(gdf=sample_gdf)

        # In this simple mock scenario, you can set expected values based on your logic
        expected_direct_trust_score = 0
        expected_time_trust_score = 0
        self.assertEqual(result, (expected_direct_trust_score, expected_time_trust_score))

    @patch('src.python_confidence_metric.trust_score_calculator.TrustScoreAnalyzer._calculate_statistics_for_edge')
    @patch('src.python_confidence_metric.trust_score_calculator.TrustScoreAnalyzer._filter_historical_data_by_date')
    def test_compute_edge_statistics(self, mock_filter_historical_data_by_date, mock_calculate_statistics_for_edge):
        # Create a sample feature row
        sample_feature = gpd.GeoDataFrame(
            {'osmid': [1], 'versions': [1], 'direct_confirmations': [2], 'changes_to_tags': [3],
             'rollbacks': [4], 'user_count': [5], 'days_since_last_edit': [6], 'tags': [7]})

        # Create sample historical information
        sample_historical_info = {
            'versions': 1,
            'direct_confirmations': 2,
            'changes_to_tags': 3,
            'rollbacks': 4,
            'user_count': 5,
            'days_since_last_edit': 6,
            'tags': 7
        }

        # Create sample edge statistics
        sample_edge_statistics = {
            'versions': 3,
            'direct_confirmations': 15,
            'changes_to_tags': 24,
            'rollbacks': 33,
            'user_count': 42,
            'days_since_last_edit': 51,
            'tags': 60
        }

        mock_filter_historical_data_by_date.return_value = sample_historical_info
        mock_calculate_statistics_for_edge.return_value = sample_edge_statistics

        # Call the _compute_edge_statistics method
        self.trust_score_analyzer._compute_edge_statistics(feature=sample_feature)

        # Check if the mock methods were called with the expected arguments
        mock_calculate_statistics_for_edge.assert_called_once_with(historical_info=sample_historical_info)

    @patch('src.python_confidence_metric.utils.calculate_user_interaction_stats')
    @patch('src.python_confidence_metric.utils.calculate_direct_confirmations')
    @patch('src.python_confidence_metric.utils.count_tag_changes')
    @patch('src.python_confidence_metric.utils.check_for_rollbacks')
    @patch('src.python_confidence_metric.utils.count_tags')
    def test_calculate_statistics_for_edge(self, mock_count_tags, mock_check_for_rollbacks,
                                           mock_count_tag_changes, mock_calculate_direct_confirmations,
                                           mock_calculate_user_interaction_stats):
        # Define mock return values
        mock_calculate_user_interaction_stats.return_value = (5, 10)
        mock_calculate_direct_confirmations.return_value = 6
        mock_count_tag_changes.return_value = 4
        mock_check_for_rollbacks.return_value = 2
        mock_count_tags.return_value = 3

        historical_info = {
            'edge1': {
                'user': 'user1',
                'version': 1,
                'direct_confirmation': 2,
                'change_to_tag': 3,
                'rollback': 5,
                'day_since_last_edit': 6,
                'tag': {
                    'nd': 'test_nd',
                    'footway': 'test_footway',
                    'highway': 'test_highway',
                    'surface': 'test_surface',
                },
                'timestamp': datetime(2024, 1, 16)
            },
            'edge2': {
                'user': 'user2',
                'version': 2,
                'direct_confirmation': 3,
                'change_to_tag': 4,
                'rollback': 6,
                'day_since_last_edit': 7,
                'tag': {
                    'crossing': 'test_crossing',
                    'lit': 'test_lit',
                    'width': 'test_width',
                },
                'timestamp': datetime(2024, 1, 15)
            },
            'edge3': {
                'user': 'user3',
                'version': 3,
                'direct_confirmation': 4,
                'change_to_tag': 5,
                'rollback': 7,
                'day_since_last_edit': 8,
                'tag': {
                    'tactile_paving': 'test_tactile_paving',
                    'access': 'test_access',
                    'step_count': 'test_step_count',
                },
                'timestamp': datetime(2024, 1, 17)
            }
        }

        result = self.trust_score_analyzer._calculate_statistics_for_edge(historical_info=historical_info)
        expected_result = {
            'versions': 3,
            'direct_confirmations': 0,
            'changes_to_tags': 12,
            'rollbacks': False,
            'user_count': 3,
            'days_since_last_edit': -1,
            'tags': 3
        }
        self.assertEqual(result, expected_result)

    def test_data_before_and_after_cutoff(self):
        historical_info = {
            'data1': {'timestamp': datetime(2024, 1, 15)},
            'data2': {'timestamp': datetime(2024, 1, 17)}
        }
        expected_result = {
            'data1': {'timestamp': datetime(2024, 1, 15)}
        }
        result = self.trust_score_analyzer._filter_historical_data_by_date(historical_info=historical_info)
        self.assertEqual(result, expected_result)

    def test_all_data_before_cutoff(self):
        historical_info = {
            'data1': {'timestamp': datetime(2024, 1, 14)},
            'data2': {'timestamp': datetime(2024, 1, 15)}
        }
        result = self.trust_score_analyzer._filter_historical_data_by_date(historical_info)
        self.assertEqual(result, historical_info)

    def test_all_data_after_cutoff(self):
        historical_info = {
            'data1': {'timestamp': datetime(2024, 1, 17)},
            'data2': {'timestamp': datetime(2024, 1, 18)}
        }
        result = self.trust_score_analyzer._filter_historical_data_by_date(historical_info)
        self.assertEqual(result, {})

    def test_empty_historical_info(self):
        historical_info = {}
        result = self.trust_score_analyzer._filter_historical_data_by_date(historical_info)
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
