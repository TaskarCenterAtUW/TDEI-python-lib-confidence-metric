# trust_score_calculator.py file

import osmnx as ox
import pandas as pd
import dask_geopandas
import geonetworkx as gnx

from .utils import calculate_direct_confirmations, count_tag_changes, check_for_rollbacks, \
    calculate_user_interaction_stats, count_tags, calculate_feature_trust_scores, \
    calculate_indirect_trust_components_from_polygon


def _calculate_comprehensive_trust_scores(gdf):
    """
    Calculate the total trust score for a GeoDataFrame.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame for which to calculate trust scores.

    Returns:
        tuple: A tuple containing the mean direct trust score and the mean time trust score.
    """
    if gdf.empty:
        return 0, 0

    # Convert columns to numeric if they are not already.
    numeric_columns = ['versions', 'direct_confirmations', 'tags', 'user_count', 'days_since_last_edit']
    for col in numeric_columns:
        gdf[col] = pd.to_numeric(gdf[col], errors='coerce')

    gdf_dask = dask_geopandas.from_geopandas(gdf, npartitions=30)

    # Calculate thresholds for trust score calculation
    versions_threshold = gdf_dask['versions'].mean()
    direct_confirm_threshold = gdf_dask['direct_confirmations'].mean()
    changes_to_tags_threshold = 2
    rollbacks_threshold = 1
    tags_threshold = gdf_dask['tags'].mean()
    user_count_threshold = gdf_dask['user_count'].mean()

    gdf_dask['direct_trust_score'] = None
    gdf_dask['time_trust_score'] = None

    # calculations for time trust
    days_since_last_edit_threshold = gdf_dask['days_since_last_edit'].mean()

    meta = [
        ('u', 'int64'), ('v', 'int64'), ('osmid', 'int64'), ('geometry', 'geometry'),
        ('versions', 'object'), ('direct_confirmations', 'object'), ('changes_to_tags', 'object'),
        ('rollbacks', 'object'), ('tags', 'object'), ('user_count', 'object'),
        ('days_since_last_edit', 'object'), ('direct_trust_score', 'object'), ('time_trust_score', 'object')
    ]
    output = gdf_dask.apply(
        calculate_feature_trust_scores,
        args=(
            versions_threshold,
            direct_confirm_threshold,
            changes_to_tags_threshold,
            rollbacks_threshold,
            tags_threshold,
            user_count_threshold,
            days_since_last_edit_threshold
        ),
        axis=1,
        meta=meta
    ).compute(scheduler='multiprocessing')

    return output['direct_trust_score'].mean(), output['time_trust_score'].mean()


def _initialize_gdf_columns(gdf):
    columns_to_initialize = [
        'versions', 'direct_confirmations', 'changes_to_tags',
        'rollbacks', 'tags', 'user_count', 'days_since_last_edit'
    ]
    for col in columns_to_initialize:
        gdf[col] = None
    return gdf


def _prepare_dask_dataframe(gdf):
    return dask_geopandas.from_geopandas(
        gdf,
        npartitions=30
    )[['u', 'v', 'osmid', 'geometry', 'versions', 'direct_confirmations', 'changes_to_tags', 'rollbacks', 'tags',
       'user_count', 'days_since_last_edit']]


class TrustScoreAnalyzer:

    def __init__(self, sidewalk, osm_data_handler, date, proj='epsg:26910'):
        self.SIDEWALK = sidewalk
        self.osm_data_handler = osm_data_handler
        self.date = date
        self.proj = proj

    def get_measures_from_polygon(self, polygon):
        """
        Calculate trust scores and indirect values for a given polygon.

        Args:
            polygon (Polygon): A polygon for which to calculate the measures.

        Returns:
            dict: A dictionary containing direct trust score, time trust score, and indirect values.
        """
        try:
            graph = ox.graph.graph_from_polygon(
                polygon,
                custom_filter=self.SIDEWALK,
                truncate_by_edge=True,
                simplify=False,
                retain_all=True
            )
        except ValueError:
            return {
                'direct_trust_score': None,
                'time_trust_score': None,
                'indirect_values': None
            }

        direct_trust_score, time_trust_score = self._analyze_sidewalk_features(graph=graph)
        indirect_values = calculate_indirect_trust_components_from_polygon(
            polygon=polygon,
            proj=self.proj,
            date=self.date,
            osm_data_handler=self.osm_data_handler
        )

        return {
            'direct_trust_score': direct_trust_score,
            'time_trust_score': time_trust_score,
            'indirect_values': indirect_values
        }

    def _analyze_sidewalk_features(self, graph):
        gdf = gnx.graph_edges_to_gdf(graph)
        gdf = _initialize_gdf_columns(gdf=gdf)

        df_dask = _prepare_dask_dataframe(gdf=gdf)

        # Apply _compute_edge_statistics function to each row
        output = df_dask.apply(
            self._compute_edge_statistics,
            axis=1,
            meta=[
                ('u', 'int64'), ('v', 'int64'), ('osmid', 'int64'), ('geometry', 'geometry'),
                ('versions', 'object'), ('direct_confirmations', 'object'), ('changes_to_tags', 'object'),
                ('rollbacks', 'object'), ('tags', 'object'), ('user_count', 'object'),
                ('days_since_last_edit', 'object')
            ]
        ).compute(scheduler='multiprocessing')

        return _calculate_comprehensive_trust_scores(gdf=output)

    def _compute_edge_statistics(self, feature):
        """
        Update the feature with statistical information based on historical edge data.

        Args:
            feature (GeoDataFrame row): A row from a GeoDataFrame representing a geographic feature.

        Returns:
            GeoDataFrame row: The input feature row updated with statistical information.
        """
        osmid = feature['osmid']
        # Get historical information for the feature
        historical_info = self.osm_data_handler.get_way_history(osmid=osmid)

        # Filter historical data by date
        filtered_info = self._filter_historical_data_by_date(historical_info=historical_info)

        # Calculate edge statistics
        edge_statistics = self._calculate_statistics_for_edge(historical_info=filtered_info)

        # Update feature values
        feature.version = edge_statistics['versions']
        feature.direct_confirmations = edge_statistics['direct_confirmations']
        feature.changes_to_tags = edge_statistics['changes_to_tags']
        feature.rollbacks = edge_statistics['rollbacks']
        feature.user_count = edge_statistics['user_count']
        feature.days_since_last_edit = edge_statistics['days_since_last_edit']
        feature.tags = edge_statistics['tags']

        # Return the modified feature
        return feature

    def _calculate_statistics_for_edge(self, historical_info):
        """
        Calculate various statistics for an edge based on its historical information.

        Args:
            historical_info (dict): Historical information about an edge.

        Returns:
            dict: A dictionary containing calculated statistics for the edge.
        """

        user_count, days_since_last_edit = calculate_user_interaction_stats(
            historical_info=historical_info,
            date=self.date
        )

        return {
            'versions': len(historical_info),
            'direct_confirmations': calculate_direct_confirmations(historical_info=historical_info),
            'changes_to_tags': count_tag_changes(historical_info=historical_info),
            'rollbacks': check_for_rollbacks(historical_info=historical_info),
            'user_count': user_count,
            'days_since_last_edit': days_since_last_edit,
            'tags': count_tags(historical_info)
        }

    def _filter_historical_data_by_date(self, historical_info):
        """
        Filters the historical edge information by a given cutoff date.

        Args:
            historical_info (dict): A dictionary containing historical edge data.

        Returns:
            dict: Filtered historical information up to the cutoff date.
        """
        return {key: value for key, value in historical_info.items() if value['timestamp'] <= self.date}
