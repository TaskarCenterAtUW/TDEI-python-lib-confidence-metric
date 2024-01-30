import unittest
import pandas as pd
import geopandas as gpd
from datetime import datetime
from shapely.geometry import Polygon, Point
from unittest.mock import patch, MagicMock
from src.osw_confidence_metric.utils import compute_feature_indirect_trust, calculate_overall_trust_score, \
    calculate_indirect_trust_components_from_polygon, extract_features_from_polygon, extract_road_features_from_polygon, \
    aggregate_feature_statistics, calculate_user_interaction_stats, calculate_number_users_edited, \
    calculate_days_since_last_edit, calculate_direct_confirmations, get_relevant_tags, count_tag_changes, \
    check_for_rollbacks, count_tags, calculate_feature_trust_scores


class MockFeature:
    def __init__(self, indirect_values):
        self.indirect_values = indirect_values


class MockScoreFeature:
    def __init__(self, direct=0, indirect=0, time=0):
        self.direct_trust_score = direct
        self.indirect_trust_score = indirect
        self.time_trust_score = time


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.thresholds = {
            'road_time': 10,
            'road_users': 5,
            'poi_count': 3,
            'poi_users': 4,
            'poi_time': 2,
            'bldg_count': 7,
            'bldg_users': 6,
            'bldg_time': 1
        }
        self.proj = 'epsg:26910'
        self.date = datetime(2024, 1, 1)
        self.versions_threshold = 5
        self.direct_confirm_threshold = 3
        self.user_count_threshold = 10
        self.rollbacks_threshold = 2
        self.changes_to_tags_threshold = 4
        self.tags_threshold = 7
        self.days_since_last_edit_threshold = 30

    def test_compute_feature_indirect_trust_with_above_thresholds(self):
        feature = MockFeature({
            'road_users': 10,
            'road_time': 20,
            'poi_count': 30,
            'poi_users': 40,
            'poi_time': 50,
            'bldg_count': 60,
            'bldg_users': 70,
            'bldg_time': 80,
        })
        result = compute_feature_indirect_trust(feature=feature, thresholds=self.thresholds)
        self.assertEqual(result, 1)

    def test_compute_feature_indirect_trust_with_below_thresholds(self):
        feature = MockFeature({
            'road_time': 0,
            'road_users': 1,
            'poi_count': 2,
            'poi_users': 3,
            'poi_time': 3,
            'bldg_count': 3,
            'bldg_users': 3,
            'bldg_time': 3,
        })
        result = compute_feature_indirect_trust(feature=feature, thresholds=self.thresholds)
        self.assertEqual(result, 0)

    def test_compute_feature_indirect_trust_with_missing(self):
        feature = MockFeature({
            'road_time': None,
            'road_users': 1,
            'poi_count': 2,
            'poi_users': None,
            'poi_time': 3,
            'bldg_count': 3,
            'bldg_users': 3,
            'bldg_time': 3,
        })
        result = compute_feature_indirect_trust(feature=feature, thresholds=self.thresholds)
        self.assertEqual(result, 0)

    def test_calculate_overall_trust_score_with_scores_present(self):
        feature = MockScoreFeature(direct=0.8, indirect=0.6, time=.4)
        result = calculate_overall_trust_score(feature=feature)
        expected_score = (0.8 * 0.5) + (0.6 * 0.25) + (0.4 * 0.25)
        self.assertAlmostEqual(result, expected_score)

    def test_calculate_overall_trust_score_with_some_scores_missing(self):
        feature = MockScoreFeature(direct=0.8)
        result = calculate_overall_trust_score(feature=feature)
        expected_score = (0.8 * 0.5)
        self.assertEqual(result, expected_score)

    def test_calculate_overall_trust_score_with_all_scores_missing(self):
        feature = MockScoreFeature()
        result = calculate_overall_trust_score(feature=feature)
        self.assertEqual(result, 0)

    def test_calculate_overall_trust_score_with_negative_scores(self):
        feature = MockScoreFeature(direct=-0.5, indirect=-0.3, time=-0.2)
        result = calculate_overall_trust_score(feature=feature)
        expected_score = (-0.5 * 0.5) + (-0.3 * 0.25) + (-0.2 * 0.25)
        self.assertAlmostEqual(result, expected_score)

    @patch('src.osw_confidence_metric.utils.extract_features_from_polygon')
    @patch('src.osw_confidence_metric.utils.extract_road_features_from_polygon')
    @patch('src.osw_confidence_metric.utils.aggregate_feature_statistics')
    def test_calculate_indirect_trust_components_from_polygon(self, mock_aggregate_feature_statistics,
                                                              mock_extract_road_features_from_polygon,
                                                              mock_extract_features_from_polygon):
        # Setup mock return values
        mock_extract_features_from_polygon.return_value = MagicMock()
        mock_extract_road_features_from_polygon.return_value = MagicMock()
        mock_aggregate_feature_statistics.side_effect = [(10, '2024-01-01'), (20, '2024-01-01'), (30, '2024-01-01')]

        # Define test inputs
        polygon = 'valid_polygon'

        osm_data_handler = MagicMock()
        result = calculate_indirect_trust_components_from_polygon(polygon=polygon, proj=self.proj, date=self.date,
                                                                  osm_data_handler=osm_data_handler)
        expected_values = {
            'poi_count': len(mock_extract_features_from_polygon.return_value),
            'bldg_count': len(mock_extract_features_from_polygon.return_value),
            'road_count': len(mock_extract_road_features_from_polygon.return_value),
            'poi_users': 10,
            'road_users': 20,
            'bldg_users': 30,
            'poi_time': '2024-01-01',
            'road_time': '2024-01-01',
            'bldg_time': '2024-01-01',
        }
        self.assertEqual(result, expected_values)

    @patch('osmnx.features.features_from_polygon')
    def test_extract_features_from_polygon(self, mock_features_from_polygon):
        # Create a dummy GeoDataFrame
        dummy_gdf = gpd.GeoDataFrame({'geometry': [Polygon([(0, 0), (1, 1), (1, 0)])]}, crs=self.proj)

        # Set the mock to return the dummy GeoDataFrame when to_crs() is called
        mock_to_crs = MagicMock(return_value=dummy_gdf)
        mock_features_from_polygon.return_value.to_crs = mock_to_crs

        # Define test inputs
        polygon = Polygon([(0, 0), (1, 1), (1, 0)])
        tags = {'amenity': True}

        # Call the function
        result = extract_features_from_polygon(polygon=polygon, tags=tags, proj=self.proj)

        # Check the result is a GeoDataFrame
        self.assertIsInstance(result, gpd.GeoDataFrame)

    @patch('osmnx.features.features_from_polygon')
    def test_extract_features_from_polygon_failure(self, mock_features_from_polygon):
        # Create a dummy GeoDataFrame
        mock_features_from_polygon.side_effect = ValueError

        # Define test inputs
        polygon = Polygon([(0, 0), (1, 1), (1, 0)])
        tags = {'amenity': True}

        # Call the function
        result = extract_features_from_polygon(polygon=polygon, tags=tags, proj=self.proj)

        # Check the result is a GeoDataFrame
        expected_columns = list(tags.keys()) + ['geometry']
        self.assertIsInstance(result, gpd.GeoDataFrame)
        self.assertEqual(list(result.columns), expected_columns)
        self.assertTrue(result.empty)

    @patch('osmnx.graph.graph_from_polygon')
    @patch('geonetworkx.graph_edges_to_gdf')
    def test_extract_road_features_from_polygon(self, mock_graph_edges_to_gdf, mock_graph_from_polygon):
        # Setup mock return values
        mock_graph_from_polygon.return_value = MagicMock()  # Mocked graph object
        dummy_gdf = gpd.GeoDataFrame({'geometry': [Polygon([(0, 0), (1, 1), (1, 0)])]}, crs=self.proj)
        mock_graph_edges_to_gdf.return_value = dummy_gdf

        # Define test inputs
        polygon = Polygon([(0, 0), (1, 1), (1, 0)])

        # Call the function
        result = extract_road_features_from_polygon(polygon=polygon, proj=self.proj)

        # Check the result is a GeoDataFrame
        self.assertIsInstance(result, gpd.GeoDataFrame)

    @patch('osmnx.graph.graph_from_polygon')
    def test_extract_road_features_from_polygon_failure(self, mock_graph_from_polygon):
        # Set up the mock to raise ValueError
        mock_graph_from_polygon.side_effect = ValueError

        # Define test inputs
        polygon = Polygon([(0, 0), (1, 1), (1, 0)])  # Replace with a polygon that would cause an exception

        # Call the function and handle exceptions
        result = extract_road_features_from_polygon(polygon=polygon, proj=self.proj)

        # Check that result is an empty GeoDataFrame with specified columns
        expected_columns = ['u', 'v', 'osmid', 'highway', 'geometry']
        self.assertIsInstance(result, gpd.GeoDataFrame)
        self.assertEqual(list(result.columns), expected_columns)
        self.assertTrue(result.empty)

    @patch('src.osw_confidence_metric.osm_data_handler.OSMDataHandler')
    @patch('src.osw_confidence_metric.utils.calculate_user_interaction_stats')
    def test_aggregate_feature_statistics(self, mock_calculate_user_interaction_stats, mock_osm_data_handler):
        # Create a dummy GDF
        dummy_gdf = gpd.GeoDataFrame({'geometry': [Point(1, 1), Point(2, 2)]}, crs=self.proj)

        # Setup mock return values
        mock_osm_data_handler.return_value.get_item_history.return_value = {'dummy': 'data'}
        mock_calculate_user_interaction_stats.return_value = (10, 5)

        # Call the function
        result = aggregate_feature_statistics(gdf=dummy_gdf, date=self.date,
                                              osm_data_handler=mock_osm_data_handler.return_value)

        # Check the result
        expected_result = (10, 5)
        self.assertEqual(result, expected_result)

    @patch('src.osw_confidence_metric.osm_data_handler.OSMDataHandler')
    @patch('src.osw_confidence_metric.utils.calculate_user_interaction_stats')
    def test_aggregate_feature_statistics_with_incomplete_dataset(self, mock_calculate_user_interaction_stats,
                                                                  mock_osm_data_handler):
        # Create a dummy GDF
        dummy_gdf = gpd.GeoDataFrame({'geometry': [Point(1, 1), Point(2, 2)]}, crs=self.proj)

        # Setup mock return values
        mock_osm_data_handler.return_value.get_item_history.side_effect = [None, {'dummy': 'data'}]
        mock_calculate_user_interaction_stats.return_value = (10, 5)

        # Call the function
        result = aggregate_feature_statistics(gdf=dummy_gdf, date=self.date,
                                              osm_data_handler=mock_osm_data_handler.return_value)

        # Check the result
        expected_result = (10, 5)
        self.assertEqual(result, expected_result)

    @patch('src.osw_confidence_metric.utils.calculate_number_users_edited')
    @patch('src.osw_confidence_metric.utils.calculate_days_since_last_edit')
    def test_calculate_user_interaction_stats(self, mock_calculate_days_since_last_edit,
                                              mock_calculate_number_users_edited):
        # Setup mock return values
        mock_calculate_number_users_edited.return_value = 10
        mock_calculate_days_since_last_edit.return_value = 5

        # Define test inputs
        historical_info = {'dummy_data': 'value'}

        # Call the function
        user_count, days_since_last_edit = calculate_user_interaction_stats(historical_info=historical_info,
                                                                            date=self.date)

        # Check the results
        self.assertEqual(user_count, 10)
        self.assertEqual(days_since_last_edit, 5)

    def test_calculate_number_users_edited_for_unique_users(self):
        historical_info = {
            'edge1': {'user': 'user1'},
            'edge2': {'user': 'user2'},
            'edge3': {'user': 'user3'}
        }
        result = calculate_number_users_edited(historical_info=historical_info)
        self.assertEqual(result, 3)

    def test_calculate_number_users_edited_for_duplicate_users(self):
        historical_info = {
            'edge1': {'user': 'user1'},
            'edge2': {'user': 'user1'},
            'edge3': {'user': 'user3'}
        }
        result = calculate_number_users_edited(historical_info=historical_info)
        self.assertEqual(result, 2)

    def test_calculate_number_users_edited_for_empty_info(self):
        historical_info = {}
        result = calculate_number_users_edited(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_calculate_days_since_last_edit_multiple_dates(self):
        historical_info = {
            'edit1': {'timestamp': datetime(2023, 12, 1)},
            'edit2': {'timestamp': datetime(2023, 12, 5)},
            'edit3': {'timestamp': datetime(2023, 12, 27)}
        }
        result = calculate_days_since_last_edit(historical_info=historical_info, date=self.date)
        self.assertEqual(result, 5)

    def test_calculate_days_since_last_edit_single_date(self):
        historical_info = {
            'edit3': {'timestamp': datetime(2023, 12, 27)}
        }
        result = calculate_days_since_last_edit(historical_info=historical_info, date=self.date)
        self.assertEqual(result, 5)

    def test_calculate_days_since_last_edit_for_empty_historical_info(self):
        historical_info = {}

        result = calculate_days_since_last_edit(historical_info=historical_info, date=self.date)
        self.assertEqual(result, 0)

    def test_calculate_days_since_last_edit_current_date(self):
        historical_info = {
            'edit3': {'timestamp': self.date}
        }
        result = calculate_days_since_last_edit(historical_info=historical_info, date=self.date)
        self.assertEqual(result, 0)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_calculate_direct_confirmations(self, mock_get_relevant_tags):
        historical_info = {
            'edit1': {'user': 'user1', 'timestamp': datetime(2024, 1, 1), 'tags': 'tags1'},
            'edit2': {'user': 'user2', 'timestamp': datetime(2024, 2, 1), 'tags': 'tags1'}
        }
        mock_get_relevant_tags.side_effect = lambda edge: edge['tags']

        result = calculate_direct_confirmations(historical_info=historical_info)
        self.assertEqual(result, 1)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_calculate_no_direct_confirmations(self, mock_get_relevant_tags):
        historical_info = {
            'edit1': {'user': 'user1', 'timestamp': datetime(2024, 1, 1), 'tags': 'tags1'},
            'edit2': {'user': 'user1', 'timestamp': datetime(2024, 2, 1), 'tags': 'tags2'}
        }
        mock_get_relevant_tags.side_effect = lambda edge: edge['tags']
        result = calculate_direct_confirmations(historical_info=historical_info)
        self.assertEqual(result, 0)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_calculate_direct_confirmations_sith_single_entry(self, mock_get_relevant_tags):
        historical_info = {
            'edit1': {'user': 'user1', 'timestamp': datetime(2024, 1, 1), 'tags': 'tags1'}
        }
        mock_get_relevant_tags.return_value = 'tags1'
        result = calculate_direct_confirmations(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_get_relevant_tags(self):
        edge = {
            'nd': '123',
            'tag': {
                'footway': 'sidewalk',
                'highway': 'residential',
                'surface': 'asphalt',
                'crossing': 'zebra',
                'lit': 'yes',
                'width': '2.0',
                'tactile_paving': 'no',
                'access': 'yes',
                'step_count': '5'
            }
        }
        result = get_relevant_tags(edge=edge)
        expected_tags = {
            'nd': '123',
            'footway': 'sidewalk',
            'highway': 'residential',
            'surface': 'asphalt',
            'crossing': 'zebra',
            'lit': 'yes',
            'width': '2.0',
            'tactile_paving': 'no',
            'access': 'yes',
            'step_count': '5'
        }
        self.assertEqual(result, expected_tags)

    def test_get_relevant_tags_with_some_tags_missing(self):
        edge = {
            'nd': '123',
            'tag': {
                'highway': 'residential',
                'surface': 'asphalt'
            }
        }
        result = get_relevant_tags(edge=edge)
        self.assertEqual(result['nd'], '123')
        self.assertEqual(result['highway'], 'residential')
        self.assertEqual(result['surface'], 'asphalt')
        self.assertIsNone(result['footway'])
        self.assertIsNone(result['crossing'])

    def test_get_relevant_tags_with_no_relevant_tags(self):
        edge = {'nd': '123', 'tag': {}}
        result = get_relevant_tags(edge=edge)
        self.assertEqual(result['nd'], '123')
        self.assertIsNone(result['footway'])
        self.assertIsNone(result['highway'])
        self.assertIsNone(result['surface'])
        self.assertIsNone(result['crossing'])
        self.assertIsNone(result['lit'])
        self.assertIsNone(result['width'])
        self.assertIsNone(result['tactile_paving'])
        self.assertIsNone(result['access'])
        self.assertIsNone(result['step_count'])

    def test_get_relevant_tags_with_empty_edge(self):
        edge = {}
        result = get_relevant_tags(edge=edge)
        self.assertIsNone(result['nd'])
        self.assertIsNone(result['footway'])
        self.assertIsNone(result['highway'])
        self.assertIsNone(result['surface'])
        self.assertIsNone(result['crossing'])
        self.assertIsNone(result['lit'])
        self.assertIsNone(result['width'])
        self.assertIsNone(result['tactile_paving'])
        self.assertIsNone(result['access'])
        self.assertIsNone(result['step_count'])

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_count_tag_changes(self, mock_get_relevant_tags):
        # Setup mock return values for get_relevant_tags
        mock_get_relevant_tags.side_effect = [
            {'tag1': 'value1', 'tag2': 'value2'},
            {'tag1': 'value1', 'tag2': 'value3'},
            {'tag1': 'value1', 'tag2': 'value3'},
            {'tag1': 'value4', 'tag2': 'value3'}
        ]

        # Define test inputs
        historical_info = {
            'edit1': {'dummy_data': 'value'},
            'edit2': {'dummy_data': 'value'},
            'edit3': {'dummy_data': 'value'}
        }

        # Call the function
        result = count_tag_changes(historical_info=historical_info)
        self.assertEqual(result, 2)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_count_tag_changes_with_no_change(self, mock_get_relevant_tags):
        # Setup mock return values for get_relevant_tags
        mock_get_relevant_tags.side_effect = [
            {'tag1': 'value1', 'tag2': 'value2'},
            {'tag1': 'value1', 'tag2': 'value2'},
            {'tag1': 'value1', 'tag2': 'value2'},
            {'tag1': 'value1', 'tag2': 'value2'},
            {'tag1': 'value1', 'tag2': 'value2'},
        ]

        # Define test inputs
        historical_info = {
            'edit1': {'dummy_data': 'value'},
            'edit2': {'dummy_data': 'value'}
        }

        # Call the function
        result = count_tag_changes(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_count_tag_changes_with_empty_historical_info(self):
        # Define test inputs
        historical_info = {}
        # Call the function
        result = count_tag_changes(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_check_for_rollbacks(self):
        historical_info = {
            'edit1': {'visible': True},
            'edit2': {'visible': False}
        }
        result = check_for_rollbacks(historical_info=historical_info)
        self.assertEqual(result, 1)

    def test_check_for_rollbacks_no_rollback(self):
        historical_info = {
            'edit1': {'visible': True},
            'edit2': {'visible': True}
        }
        result = check_for_rollbacks(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_check_for_rollbacks_with_empty_historical_info(self):
        historical_info = {}
        result = check_for_rollbacks(historical_info=historical_info)
        self.assertEqual(result, 0)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_count_tags(self, mock_get_relevant_tags):
        mock_get_relevant_tags.return_value = {'tag1': 'value1', 'tag2': 'value2', 'tag3': None}
        historical_info = {
            'edit1': {'dummy_data': 'value'},
            'edit2': {'dummy_data': 'value'}
        }
        result = count_tags(historical_info=historical_info)
        self.assertEqual(result, 2)

    @patch('src.osw_confidence_metric.utils.get_relevant_tags')
    def test_count_tags_with_no_tags(self, mock_get_relevant_tags):
        mock_get_relevant_tags.return_value = {'tag1': None, 'tag2': None}
        historical_info = {
            'edit1': {'dummy_data': 'value'},
        }
        result = count_tags(historical_info=historical_info)
        self.assertEqual(result, 0)

    def test_calculate_feature_trust_scores(self):
        feature = pd.Series({
            'versions': 10,
            'direct_confirmations': 5,
            'user_count': 15,
            'rollbacks': 3,
            'changes_to_tags': 6,
            'tags': 8,
            'days_since_last_edit': 40
        })

        result = calculate_feature_trust_scores(
            feature=feature,
            versions_threshold=self.versions_threshold,
            direct_confirm_threshold=self.direct_confirm_threshold,
            changes_to_tags_threshold=self.changes_to_tags_threshold,
            rollbacks_threshold=self.rollbacks_threshold,
            tags_threshold=self.tags_threshold,
            user_count_threshold=self.user_count_threshold,
            days_since_last_edit_threshold=self.days_since_last_edit_threshold
        )
        self.assertAlmostEqual(result.direct_trust_score, 1.0)
        self.assertEqual(result.time_trust_score, 1)

    def test_calculate_feature_trust_scores_where_no_thresholds_met(self):
        feature = pd.Series({
            'versions': 2,
            'direct_confirmations': 1,
            'user_count': 5,
            'rollbacks': 0,
            'changes_to_tags': 2,
            'tags': 3,
            'days_since_last_edit': 10
        })

        result = calculate_feature_trust_scores(
            feature=feature,
            versions_threshold=self.versions_threshold,
            direct_confirm_threshold=self.direct_confirm_threshold,
            changes_to_tags_threshold=self.changes_to_tags_threshold,
            rollbacks_threshold=self.rollbacks_threshold,
            tags_threshold=self.tags_threshold,
            user_count_threshold=self.user_count_threshold,
            days_since_last_edit_threshold=self.days_since_last_edit_threshold
        )
        self.assertAlmostEqual(result.direct_trust_score, 0.0)
        self.assertEqual(result.time_trust_score, 0)


if __name__ == '__main__':
    unittest.main()
