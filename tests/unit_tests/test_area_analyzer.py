import os
import math
import unittest
import pandas as pd
import geopandas as gpd
from datetime import datetime
from shapely.geometry import Polygon, MultiPolygon, Point
from unittest.mock import patch, MagicMock
from src.osw_confidence_metric.trust_score_calculator import TrustScoreAnalyzer
from src.osw_confidence_metric.area_analyzer import AreaAnalyzer, _initialize_columns, _get_threshold_values

sample_data = {'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]}
sample_gdf = gpd.GeoDataFrame(sample_data)

# Define a mock file path for testing
mock_file_path = 'mock_file.geojson'

current_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, '../')))
parent_dir = os.path.dirname(current_dir)
TEST_FILE = os.path.join(parent_dir, 'src/assets/caphill_mini.geojson')


class TestAreaAnalyzer(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_measures = {
            'direct_trust_score': 0.75,
            'time_trust_score': 0.90,
            'indirect_values': {'poi_count': 5, 'road_count': 10}
        }
        self.mock_osm_data_handler = MagicMock()
        self.mock_trust_score_handler = MagicMock()
        self.area_analyzer = AreaAnalyzer(osm_data_handler=self.mock_osm_data_handler)
        self.PROJ = 'epsg:26910'

    def test_initialization(self):
        self.assertIsInstance(self.area_analyzer.osm_data_handler, MagicMock)
        self.assertEqual(self.area_analyzer.PROJ, 'epsg:26910')
        self.assertEqual(self.area_analyzer.DATE.date(), datetime.now().date())

    @patch('geonetworkx.graph_edges_to_gdf')
    @patch('shapely.ops.voronoi_diagram')
    @patch('geopandas.clip')
    def test_create_voronoi_diagram(self, mock_clip, mock_voronoi_diagram, mock_graph_edges_to_gdf):
        # Set up mock data for gdf_edges and bounds
        mock_gdf_edges = MagicMock()
        mock_bounds = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])  # Example bounding polygon

        # Mock the return value of geonetworkx.graph_edges_to_gdf
        mock_gdf = gpd.GeoDataFrame({'geometry': [mock_bounds]})
        mock_graph_edges_to_gdf.return_value = mock_gdf

        # Mock the return value of shapely.ops.voronoi_diagram
        mock_voronoi_geoms = [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]  # Example Voronoi diagram geometries
        mock_voronoi_gdf = gpd.GeoDataFrame({'geometry': [MultiPolygon(mock_voronoi_geoms)]})
        mock_voronoi_diagram.return_value = mock_voronoi_gdf

        # Mock the return value of geopandas.clip
        mock_clipped_gdf = gpd.GeoDataFrame({'geometry': [mock_bounds]})
        mock_clip.return_value = mock_clipped_gdf

        # Call the method
        result = self.area_analyzer._create_voronoi_diagram(mock_gdf_edges, mock_bounds)

        # Assert calls and results
        mock_graph_edges_to_gdf.assert_called_once()
        mock_clip.assert_called_once()
        self.assertIsInstance(result, gpd.GeoDataFrame)

    @patch('osmnx.graph.graph_from_polygon')
    @patch.object(AreaAnalyzer, '_create_voronoi_diagram')
    def test_create_tiling_if_needed(self, mock_create_voronoi_diagram, mock_graph_from_polygon):
        # Set up mock data
        mock_gdf = gpd.GeoDataFrame({'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]})  # Example GeoDataFrame
        mock_gdf_edges = MagicMock()  # Example graph_from_polygon result
        mock_bounds = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])  # Example bounds

        # Mock the return value of osmnx.graph_from_polygon
        mock_graph_from_polygon.return_value = mock_gdf_edges

        # Mock the return value of _create_voronoi_diagram
        mock_create_voronoi_diagram.return_value = MagicMock()  # Example Voronoi diagram GeoDataFrame

        # Set the GeoDataFrame in the area_analyzer
        self.area_analyzer.gdf = mock_gdf

        # Call the method
        self.area_analyzer._create_tiling_if_needed()

        # Assert calls and results
        mock_graph_from_polygon.assert_called_once_with(
            mock_gdf.geometry.loc[0], network_type='drive', simplify=True, retain_all=True
        )
        mock_create_voronoi_diagram.assert_called_once_with(
            gdf_edges=mock_gdf_edges, bounds=mock_gdf.geometry.loc[0]
        )
        self.assertIsNotNone(self.area_analyzer.gdf)

    @patch.object(TrustScoreAnalyzer, 'get_measures_from_polygon',
                  return_value={'direct_trust_score': 0.5, 'time_trust_score': 0.7,
                                'indirect_values': {'some_key': 'some_value'}})
    def test_process_feature(self, mock_get_measures_from_polygon):
        # Create a valid GeoDataFrame with Polygon geometries for testing
        coords = [
            (-122.32020611852897, 47.6195210148756),
            (-122.32021005772235, 47.620102439817686),
            (-122.3192147446495, 47.62007823266089),
            (-122.31924141598212, 47.61904150994083),
            (-122.32020611852897, 47.6195210148756)
        ]
        poly = Polygon(coords)
        data = {
            'geometry': [poly],
            'direct_confirmations': None,
            'direct_trust_score': None,
            'time_trust_score': None,
            'indirect_values': None
        }
        gdf = gpd.GeoDataFrame(data, crs=self.PROJ)

        # Test the method
        result = self.area_analyzer._process_feature(gdf.iloc[0])

        # Assert calls and results
        mock_get_measures_from_polygon.assert_called_once_with(polygon=poly)

    @patch('geopandas.read_file')
    @patch.object(AreaAnalyzer, '_create_tiling_if_needed')
    @patch('dask_geopandas.from_geopandas')
    @patch('src.osw_confidence_metric.area_analyzer._get_threshold_values')
    @patch('src.osw_confidence_metric.area_analyzer.compute_feature_indirect_trust')
    @patch('src.osw_confidence_metric.area_analyzer.calculate_overall_trust_score')
    def test_calculate_area_confidence_score(
            self, mock_calc_overall, mock_compute_indirect, mock_get_threshold, mock_dask_gdf, mock_tiling,
            mock_read_file
    ):
        # Mock GeoDataFrame
        mock_gdf = gpd.GeoDataFrame({
            'geometry': [Point(1, 1)],
            'direct_trust_score': [0.5],
            'time_trust_score': [0.7],
            'indirect_values': [{'some_key': 'some_value'}],
            'trust_score': [0.9]
        })
        mock_read_file.return_value = mock_gdf
        mock_get_threshold.return_value = {"poi_count": 1.0}
        mock_compute_indirect.side_effect = lambda feature, thresholds: 0.8
        mock_calc_overall.side_effect = lambda feature: 0.9
        mock_dask_gdf.return_value.apply.return_value.compute.return_value = mock_gdf

        # Call the method
        result = self.area_analyzer.calculate_area_confidence_score('mock_file.geojson')

        # Assertions
        mock_read_file.assert_called_once_with('mock_file.geojson')
        mock_tiling.assert_called_once()
        mock_get_threshold.assert_called_once()
        mock_compute_indirect.assert_called()
        mock_calc_overall.assert_called()
        self.assertAlmostEqual(result, 0.9, places=2)

    @patch.object(TrustScoreAnalyzer, 'get_measures_from_polygon', return_value={})
    def test_process_feature_invalid_geometry(self, mock_get_measures_from_polygon):
        # Create a mock feature with invalid geometry
        invalid_feature = MagicMock()
        invalid_feature.geometry = "InvalidGeometry"  # Mimic the invalid geometry scenario

        # Call the method
        result = self.area_analyzer._process_feature(invalid_feature)

        # Verify that get_measures_from_polygon was not called
        mock_get_measures_from_polygon.assert_not_called()

        # Assert that the result is the same as the input feature
        self.assertEqual(result, invalid_feature)

    @patch('geopandas.read_file')
    @patch.object(AreaAnalyzer, '_create_tiling_if_needed')
    def test_calculate_area_confidence_score_gdf_none(self, mock_tiling, mock_read_file):
        # Setup: Mock read_file to return a valid GeoDataFrame initially
        mock_read_file.return_value = gpd.GeoDataFrame({'geometry': []})

        # Mock _create_tiling_if_needed to set gdf to None
        def mock_tiling_effect():
            self.area_analyzer.gdf = None

        mock_tiling.side_effect = mock_tiling_effect

        # Call the method
        result = self.area_analyzer.calculate_area_confidence_score('mock_file.geojson')

        # Assertions
        mock_read_file.assert_called_once_with('mock_file.geojson')
        mock_tiling.assert_called_once()
        self.assertEqual(result, 0, "The method should return 0 when gdf is None.")


class TestGetThresholdValues(unittest.TestCase):

    def test_get_threshold_values(self):
        # Create a sample GeoDataFrame with indirect_values
        sample_data = {
            'indirect_values': [
                {'poi_count': 10, 'bldg_count': 20, 'road_count': 30, 'poi_users': 40, 'road_users': 50,
                 'bldg_users': 60, 'poi_time': 70, 'road_time': 80, 'bldg_time': 90},
                {'poi_count': 15, 'bldg_count': 25, 'road_count': 35, 'poi_users': 45, 'road_users': 55,
                 'bldg_users': 65, 'poi_time': 75, 'road_time': 85, 'bldg_time': 95},
            ]
        }
        sample_gdf = pd.DataFrame(sample_data)

        # Call the _get_threshold_values function
        threshold_values = _get_threshold_values(sample_gdf)

        # Define the expected threshold values based on the means
        expected_threshold_values = {
            'poi_count': (10 + 15) / 2,
            'bldg_count': (20 + 25) / 2,
            'road_count': (30 + 35) / 2,
            'poi_users': (40 + 45) / 2,
            'road_users': (50 + 55) / 2,
            'bldg_users': (60 + 65) / 2,
            'poi_time': (70 + 75) / 2,
            'road_time': (80 + 85) / 2,
            'bldg_time': (90 + 95) / 2,
        }

        # Assert that the computed threshold values match the expected values
        self.assertEqual(threshold_values, expected_threshold_values)

    def test_empty_gdf(self):
        # Create an empty DataFrame with the correct schema and structure for 'indirect_values'
        empty_gdf = pd.DataFrame({
            'indirect_values': [
                {'poi_count': None, 'bldg_count': None, 'road_count': None,
                 'poi_users': None, 'road_users': None, 'bldg_users': None,
                 'poi_time': None, 'road_time': None, 'bldg_time': None}
            ]  # A placeholder structure with None values
        })

        # Call the function
        result = _get_threshold_values(empty_gdf)

        # Expected result with NaN values for each metric
        expected_result = {
            'poi_count': float('nan'),
            'bldg_count': float('nan'),
            'road_count': float('nan'),
            'poi_users': float('nan'),
            'road_users': float('nan'),
            'bldg_users': float('nan'),
            'poi_time': float('nan'),
            'road_time': float('nan'),
            'bldg_time': float('nan'),
        }

        # Check each value in the result
        for key in expected_result:
            self.assertTrue(math.isnan(result[key]), f"Value for {key} should be NaN")


class TestInitializeColumns(unittest.TestCase):

    def test_initialize_columns_empty_gdf(self):
        empty_gdf = gpd.GeoDataFrame({'geometry': []})
        initialized_gdf = _initialize_columns(empty_gdf)
        expected_columns = ['direct_confirmations', 'direct_trust_score', 'time_trust_score', 'indirect_values']
        for col in expected_columns:
            self.assertIn(col, initialized_gdf.columns)
            self.assertTrue(initialized_gdf[col].isna().all())

    def test_initialize_columns(self):
        # Create a sample GeoDataFrame
        sample_data = {
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
            'other_column': [1, 2, 3]
        }
        sample_gdf = gpd.GeoDataFrame(sample_data)

        # Call the _initialize_columns function
        initialized_gdf = _initialize_columns(sample_gdf)

        # Check if the required columns are added and initialized to None
        expected_columns = ['direct_confirmations', 'direct_trust_score', 'time_trust_score', 'indirect_values']
        for col in expected_columns:
            self.assertTrue(col in initialized_gdf.columns)  # Check if column exists
            self.assertTrue(initialized_gdf[col].isna().all())  # Check if all values are None

    def test_initialize_columns_with_existing_data(self):
        sample_data = {'geometry': [Point(0, 0)], 'direct_trust_score': [0.5]}
        sample_gdf = gpd.GeoDataFrame(sample_data)

        # Call the function under test
        initialized_gdf = _initialize_columns(sample_gdf)

        # Check that the columns are added and initialized to None
        expected_columns = ['direct_confirmations', 'direct_trust_score', 'time_trust_score', 'indirect_values']
        for col in expected_columns:
            self.assertIn(col, initialized_gdf.columns, f"Column {col} should exist in the DataFrame")
            self.assertTrue(initialized_gdf[col].isna().all(), f"Column {col} should be initialized to None")


class TestAreaAnalyzerExceptions(unittest.TestCase):
    def setUp(self):
        self.mock_osm_data_handler = MagicMock()
        self.area_analyzer = AreaAnalyzer(osm_data_handler=self.mock_osm_data_handler)

    @patch('osmnx.graph.graph_from_polygon')
    def test_create_tiling_if_needed_graph_exception(self, mock_graph_from_polygon):
        # Setup: Mock graph_from_polygon to raise an exception
        mock_graph_from_polygon.side_effect = Exception("Graph creation failed")

        # Setup a mock GeoDataFrame with one geometry
        self.area_analyzer.gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        })

        # Call the method
        self.area_analyzer._create_tiling_if_needed()

        # Assert: gdf should be set to None due to the exception
        self.assertIsNone(self.area_analyzer.gdf)

    @patch.object(AreaAnalyzer, '_create_voronoi_diagram')
    @patch('osmnx.graph.graph_from_polygon')
    def test_create_tiling_if_needed_voronoi_exception(self, mock_graph_from_polygon, mock_create_voronoi_diagram):
        # Setup: Mock graph_from_polygon to return valid data
        mock_graph_from_polygon.return_value = MagicMock()

        # Mock _create_voronoi_diagram to raise an exception
        mock_create_voronoi_diagram.side_effect = Exception("Voronoi diagram creation failed")

        # Setup a mock GeoDataFrame with one geometry
        self.area_analyzer.gdf = gpd.GeoDataFrame({
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        })

        # Call the method
        self.area_analyzer._create_tiling_if_needed()

        # Assert: gdf should be set to None due to the exception
        self.assertIsNone(self.area_analyzer.gdf)

    def test_create_tiling_if_needed_no_geometry(self):
        # Setup: Mock gdf with no geometry
        self.area_analyzer.gdf = gpd.GeoDataFrame({'geometry': []})

        # Call the method
        self.area_analyzer._create_tiling_if_needed()

        # Assert: gdf should remain empty
        self.assertTrue(self.area_analyzer.gdf.empty)


if __name__ == '__main__':
    unittest.main()
