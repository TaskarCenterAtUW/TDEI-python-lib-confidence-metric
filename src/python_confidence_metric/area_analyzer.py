# area_analyzer.py file

import osmnx as ox
import pandas as pd
import dask_geopandas
import geopandas as gpd
import geonetworkx as gnx
from datetime import datetime
from shapely.ops import voronoi_diagram
from .osm_data_handler import OSMDataHandler
from shapely.geometry import Polygon, MultiPolygon
from .trust_score_calculator import TrustScoreAnalyzer
from .utils import compute_feature_indirect_trust, calculate_overall_trust_score


def _get_threshold_values(gdf):
    gdf2 = pd.json_normalize(gdf['indirect_values'])
    return {
        'poi_count': gdf2['poi_count'].mean(),
        'bldg_count': gdf2['bldg_count'].mean(),
        'road_count': gdf2['road_count'].mean(),
        'poi_users': gdf2['poi_users'].mean(),
        'road_users': gdf2['road_users'].mean(),
        'bldg_users': gdf2['bldg_users'].mean(),
        'poi_time': gdf2['poi_time'].mean(),
        'road_time': gdf2['road_time'].mean(),
        'bldg_time': gdf2['bldg_time'].mean(),
    }


def _initialize_columns(gdf):
    for col in ['direct_confirmations', 'direct_trust_score', 'time_trust_score', 'indirect_values']:
        gdf[col] = None
    return gdf


class AreaAnalyzer:
    def __init__(self, osm_data_handler: OSMDataHandler):
        self.DATE = datetime.now()
        self.PROJ = 'epsg:26910'
        self.SIDEWALK_FILTER = '["highway"~"footway|steps|living_street|path"]'
        self.osm_data_handler = osm_data_handler
        self.trust_score = TrustScoreAnalyzer(
            sidewalk=self.SIDEWALK_FILTER,
            osm_data_handler=self.osm_data_handler,
            date=self.DATE,
            proj=self.PROJ
        )
        self.gdf = None

    def calculate_area_confidence_score(self, file_path):
        # Read the GeoDataFrame from the file
        self.gdf = gpd.read_file(file_path)

        # Check if tiling is needed and create tiling if necessary
        self._create_tiling_if_needed()

        # Initialize columns
        self.gdf = _initialize_columns(gdf=self.gdf)

        # Convert to Dask GeoDataFrame
        df_dask = dask_geopandas.from_geopandas(self.gdf, npartitions=16, name='measures')

        # Apply processing to each feature
        output = df_dask.apply(
            self._process_feature,
            axis=1,
            meta=gpd.GeoDataFrame(
                {
                    'geometry': 'geometry',
                    'direct_confirmations': 'object',
                    'direct_trust_score': 'object',
                    'time_trust_score': 'object',
                    'indirect_values': 'object'
                },
                index=[0]
            )
        ).compute(scheduler='multiprocessing')

        # Calculate threshold values
        threshold_values = _get_threshold_values(gdf=output)

        # Calculate indirect trust scores and overall trust scores for each feature
        output['indirect_trust_score'] = output.apply(lambda x: compute_feature_indirect_trust(
            feature=x,
            thresholds=threshold_values
        ), axis=1)
        output['trust_score'] = output.apply(lambda x: calculate_overall_trust_score(feature=x), axis=1)

        # Calculate the mean trust score
        mean_trust_score = output['trust_score'].mean()
        return mean_trust_score

    def _create_tiling_if_needed(self):
        if len(self.gdf.index) == 1:
            gdf_roads_simplified = ox.graph.graph_from_polygon(
                self.gdf.geometry.loc[0], network_type='drive', simplify=True, retain_all=True
            )
            self.gdf = self._create_voronoi_diagram(gdf_edges=gdf_roads_simplified, bounds=self.gdf.geometry.loc[0])

    def _create_voronoi_diagram(self, gdf_edges, bounds):
        """
        Creates a Voronoi diagram based on simplified road geometry and specified bounds.
        """
        gdf_roads_simplified = gnx.graph_edges_to_gdf(gdf_edges)
        voronoi = voronoi_diagram(gdf_roads_simplified.boundary.unary_union, envelope=bounds)
        voronoi_gdf = gpd.GeoDataFrame({'geometry': voronoi.geoms})
        voronoi_gdf.set_crs(self.PROJ)
        voronoi_gdf_clipped = gpd.clip(voronoi_gdf, bounds)

        return voronoi_gdf_clipped

    def _process_feature(self, feature):
        poly = feature.geometry
        if isinstance(poly, Polygon) or isinstance(poly, MultiPolygon):
            measures = self.trust_score.get_measures_from_polygon(polygon=poly)
            feature['direct_trust_score'] = measures['direct_trust_score']
            feature['time_trust_score'] = measures['time_trust_score']
            feature['indirect_values'] = measures['indirect_values']
        return feature
