# geometry_processor.py file

import geopandas as gpd
import geonetworkx as gnx
from shapely.ops import voronoi_diagram


class GeometryProcessor:
    def __init__(self, proj='epsg:26910'):
        self.proj = proj

    def create_voronoi_diagram(self, gdf_edges, bounds):
        gdf_roads_simplified = gnx.graph_edges_to_gdf(gdf_edges)
        voronoi = voronoi_diagram(gdf_roads_simplified.boundary.unary_union, envelope=bounds)
        voronoi_gdf = gpd.GeoDataFrame({'geometry': voronoi.geoms})
        voronoi_gdf.set_crs(self.proj)
        voronoi_gdf_clipped = gpd.clip(voronoi_gdf, bounds)
        return voronoi_gdf_clipped
