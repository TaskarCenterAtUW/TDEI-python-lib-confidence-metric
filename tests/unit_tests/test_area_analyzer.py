import os
import unittest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
from unittest.mock import patch, MagicMock
from src.python_confidence_metric.trust_score_calculator import TrustScoreAnalyzer
from src.python_confidence_metric.area_analyzer import AreaAnalyzer, _initialize_columns, _get_threshold_values

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
        # self.area_analyzer.trust_score = TrustScoreAnalyzer(
        #     sidewalk='["highway"~"footway|steps|living_street|path"]',
        #     osm_data_handler=self.mock_osm_data_handler,
        #     date=datetime.now(),
        #     proj='epsg:26910'
        # )
        # self.area_analyzer.trust_score.get_measures_from_polygon = MagicMock()
        # self.area_analyzer.trust_score.get_measures_from_polygon.return_value = self.mock_measures

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

    @patch.object(TrustScoreAnalyzer, 'get_measures_from_polygon', return_value=MagicMock())
    def test_process_feature(self, mock_get_measures_from_polygon):
        # Create a valid GeoDataFrame with Polygon geometries for testing
        data = {'geometry': [Polygon([(0, 0), (1, 1), (1, 0)])]}
        gdf = gpd.GeoDataFrame(data, crs=self.PROJ)

        # Test the method
        result = self.area_analyzer._process_feature(gdf)

        # Assert calls and results
        mock_get_measures_from_polygon.assert_called_once()
        self.assertIsInstance(result, gpd.GeoDataFrame)
        self.assertTrue(result['geometry'].apply(lambda x: x.geom_type in ['Polygon', 'MultiPolygon']).any())

    @patch.object(AreaAnalyzer, '_process_feature', return_value=MagicMock())
    @patch.object(AreaAnalyzer, '_create_tiling_if_needed', return_value=MagicMock())
    @patch('src.python_confidence_metric.area_analyzer._initialize_columns', return_value=MagicMock())
    @patch('dask_geopandas.from_geopandas', return_value=MagicMock())
    @patch('src.python_confidence_metric.area_analyzer._get_threshold_values', return_value=MagicMock())
    def test_calculate_area_confidence_score(self, mock_get_threshold_values, mock_from_geopandas,
                                             mock_initialize_columns, mock_create_tiling_if_needed,
                                             mock_process_feature):
        self.area_analyzer.calculate_area_confidence_score(file_path=TEST_FILE)

        mock_get_threshold_values.assert_called_once()
        mock_from_geopandas.assert_called_once()
        mock_initialize_columns.assert_called_once()
        mock_create_tiling_if_needed.assert_called_once()


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


class TestInitializeColumns(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
