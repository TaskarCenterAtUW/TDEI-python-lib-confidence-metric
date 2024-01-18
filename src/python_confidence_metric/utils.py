# utils.py file

import osmnx as ox
import geopandas as gpd
import geonetworkx as gnx
from statistics import mean


def compute_feature_indirect_trust(feature, thresholds):
    """
    Calculate the indirect trust score for a feature based on various threshold comparisons.

    Args:
        feature (dict): A dictionary representing a feature with indirect values.
        thresholds (dict): A dictionary of threshold values for different feature items.

    Returns:
        int: 1 if the indirect trust score is above the threshold, 0 otherwise.
    """
    indirect_trust_score = 0
    item_name_array = ['road_users', 'road_time', 'poi_count', 'poi_users', 'poi_time', 'bldg_count', 'bldg_users',
                       'bldg_time']
    for item_name in item_name_array:
        if feature.indirect_values is not None and feature.indirect_values[item_name] is not None and \
          feature.indirect_values[item_name] >= thresholds[item_name]:
            indirect_trust_score += 1

    return int(indirect_trust_score > 2)


def calculate_overall_trust_score(feature):
    """
    Calculate the overall trust score for a feature.

    Args:
        feature (object): An object (or dict) representing a feature with trust scores.

    Returns:
        float: The overall trust score calculated from direct, indirect, and time trust scores.
    """
    direct_trust_score = getattr(feature, 'direct_trust_score', 0) or 0
    indirect_trust_score = getattr(feature, 'indirect_trust_score', 0) or 0
    time_trust_score = getattr(feature, 'time_trust_score', 0) or 0

    return (direct_trust_score * 0.5) + (indirect_trust_score * 0.25) + (time_trust_score * 0.25)


def calculate_indirect_trust_components_from_polygon(polygon, proj, date, osm_data_handler):
    """
    Calculate indirect trust score components from a given polygon.

    Args:
        polygon (Polygon): The polygon to analyze.
        proj (string): to_crs.
        date (string): date
        osm_data_handler (object): OSM Handler
    Returns:
        dict: A dictionary containing calculated components for indirect trust score.
    """

    gdf_pois = extract_features_from_polygon(polygon=polygon, tags={'amenity': True}, proj=proj)
    gdf_bldgs = extract_features_from_polygon(polygon=polygon, tags={'building': True}, proj=proj)
    gdf_roads = extract_road_features_from_polygon(polygon=polygon, proj=proj)

    # Initialize values dict with counts
    values_dict = {
        'poi_count': len(gdf_pois),
        'bldg_count': len(gdf_bldgs),
        'road_count': len(gdf_roads),
        'poi_users': None,
        'road_users': None,
        'bldg_users': None,
        'poi_time': None,
        'road_time': None,
        'bldg_time': None,
    }

    # Calculate stats for each feature type
    values_dict['poi_users'], values_dict['poi_time'] = aggregate_feature_statistics(gdf=gdf_pois, date=date,
                                                                                     osm_data_handler=osm_data_handler)
    values_dict['road_users'], values_dict['road_time'] = aggregate_feature_statistics(gdf=gdf_roads, date=date,
                                                                                       osm_data_handler=osm_data_handler)
    values_dict['bldg_users'], values_dict['bldg_time'] = aggregate_feature_statistics(gdf=gdf_bldgs, date=date,
                                                                                       osm_data_handler=osm_data_handler)

    return values_dict


def extract_features_from_polygon(polygon, tags, proj):
    """
    Extract features from a polygon based on specified tags.

    Args:
        polygon (Polygon): The polygon to analyze.
        tags (dict): Tags to filter features.
        proj (string): to_crs.

    Returns:
        GeoDataFrame: A GeoDataFrame of extracted features.
    """
    try:
        gdf_features = ox.features.features_from_polygon(polygon, tags=tags).to_crs(proj)
    except ValueError:
        gdf_features = gpd.GeoDataFrame(columns=list(tags.keys()) + ['geometry'], geometry='geometry')
    return gdf_features


def extract_road_features_from_polygon(polygon, proj):
    """
    Extract road features from a polygon.

    Args:
        polygon (Polygon): The polygon to analyze.
        proj (string): to_crs.
    Returns:
        GeoDataFrame: A GeoDataFrame of road features.
    """
    try:
        G_roads = ox.graph.graph_from_polygon(polygon, network_type='drive', simplify=False, retain_all=True)
        gdf_roads = gnx.graph_edges_to_gdf(G_roads).to_crs(proj)
    except ValueError:
        gdf_roads = gpd.GeoDataFrame(columns=['u', 'v', 'osmid', 'highway', 'geometry'], geometry='geometry')
    return gdf_roads


def aggregate_feature_statistics(gdf, date, osm_data_handler):
    """
    Aggregate user count and days since last edit statistics from a GeoDataFrame.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame to analyze.
        date (string): date
        osm_data_handler (OSMDataHandler): OSMDataHandler class object
    Returns:
        tuple: Mean user count and mean days since last edit.
    """
    user_counts = []
    days_since_last_edits = []

    for row in gdf.itertuples(index=False):
        historical_information = osm_data_handler.get_item_history(item=row)
        if historical_information:
            user_count, days_since_last_edit = calculate_user_interaction_stats(
                historical_info=historical_information,
                date=date
            )
            user_counts.append(user_count)
            days_since_last_edits.append(days_since_last_edit)

    mean_user_count = mean(user_counts) if user_counts else 0
    mean_days_since_last_edit = mean(filter(None, days_since_last_edits)) if days_since_last_edits else None
    return mean_user_count, mean_days_since_last_edit


def calculate_user_interaction_stats(historical_info, date):
    user_count = calculate_number_users_edited(historical_info=historical_info)
    days_since_last_edit = calculate_days_since_last_edit(historical_info=historical_info, date=date)
    return user_count, days_since_last_edit


def calculate_number_users_edited(historical_info):
    """
    Calculate the number of unique users who have edited the edge.

    Args:
        historical_info (dict): Historical information about an edge.

    Returns:
        int: The count of unique users who have edited the edge.
    """
    users = set()
    for edge in historical_info.values():
        users.add(edge['user'])

    return len(users)


def calculate_days_since_last_edit(historical_info, date):
    """
    Calculate the number of days since the last edit was made to the feature.

    Args:
        historical_info (dict): Historical information about a feature.
        date (datetime): The current date to compare against the last edit date.

    Returns:
        int: The number of days since the last edit was made.
    """
    if not historical_info:
        return 0

        # Find the most recent edit based on the timestamp
    most_recent_edit = max(historical_info.values(), key=lambda edge: edge['timestamp'])

    # Calculate the difference in days
    last_edit_date = most_recent_edit['timestamp']
    diff = date - last_edit_date

    return diff.days


def calculate_direct_confirmations(historical_info):
    """
    Calculate the number of direct confirmations for an edge.

    Args:
        historical_info (dict): Historical information about an edge.

    Returns:
        int: 1 if there is a direct confirmation, 0 otherwise.
    """
    sorted_keys = sorted(historical_info, reverse=True)
    current_edge = historical_info[sorted_keys.pop(0)]
    current_edge_tags = get_relevant_tags(edge=current_edge)

    for key in sorted_keys:
        last_edge = historical_info[key]
        if last_edge['user'] != current_edge['user'] and get_relevant_tags(edge=last_edge) == current_edge_tags:
            return 1
    return 0


def get_relevant_tags(edge):
    # Define a list of tag keys to extract
    tag_keys = ['nd', 'footway', 'highway', 'surface', 'crossing', 'lit', 'width', 'tactile_paving', 'access',
                'step_count']

    # Initialize an output dictionary with all keys set to None
    output = {key: None for key in tag_keys}

    # Assign the 'nd' value directly from the edge
    output['nd'] = edge.get('nd')

    # Extract tags from the edge and assign values for each relevant key
    tags = edge.get('tag', {})
    for key in tag_keys[1:]:  # Skip 'nd' as it's already handled
        output[key] = tags.get(key)

    return output


def count_tag_changes(historical_info):
    """
    Calculate the number of changes to tags across historical edge information.

    Args:
        historical_info (dict): Historical information about an edge.

    Returns:
        int: The count of changes in tags across the historical information.
    """
    # Sort the keys of historical information
    sorted_keys = sorted(historical_info.keys())

    # Initialize the change count
    change_count = 0

    # Iterate over the sorted keys and count changes in tags
    for i in range(len(sorted_keys) - 1):
        current_tags = get_relevant_tags(edge=historical_info[sorted_keys[i]])
        next_tags = get_relevant_tags(edge=historical_info[sorted_keys[i + 1]])

        # Count how many tags have changed
        change_count += sum(current_tags[key] != next_tags[key] for key in current_tags)

    return change_count


def check_for_rollbacks(historical_info):
    """
    Check if there is a rollback in the historical edge information.

    Args:
        historical_info (dict): Historical information about an edge.

    Returns:
        int: 1 if a rollback is found, 0 otherwise.
    """
    return any(not edge.get('visible', True) for edge in historical_info.values())


def count_tags(historical_info):
    """
    Count the number of non-None tags in the most recent entry of the historical edge information.

    Args:
        historical_info (dict): A dictionary containing historical information of an edge.

    Returns:
        int: The count of non-None tags in the most recent historical entry.
    """
    tag_count = 0
    sorted_keys = sorted(historical_info, reverse=True)
    current_edge = historical_info[sorted_keys.pop(0)]
    tags = get_relevant_tags(current_edge)
    for key, value in tags.items():
        if value is not None:
            tag_count += 1
    return tag_count


def calculate_feature_trust_scores(feature, versions_threshold, direct_confirm_threshold, changes_to_tags_threshold,
                                   rollbacks_threshold, tags_threshold, user_count_threshold,
                                   days_since_last_edit_threshold):
    """
    Calculate trust scores for a given feature based on various thresholds.

    Args:
        feature (GeoDataFrame row): A row from a GeoDataFrame representing a feature.
        :param feature:
        :param days_since_last_edit_threshold:
        :param user_count_threshold:
        :param tags_threshold:
        :param rollbacks_threshold:
        :param changes_to_tags_threshold:
        :param direct_confirm_threshold:
        :param versions_threshold:

    Returns:
        DataFrame row: The input feature row with updated trust scores.
    """
    direct_trust_score = 0
    if feature['versions'] >= versions_threshold:
        direct_trust_score += .2
    if feature['direct_confirmations'] >= direct_confirm_threshold:
        direct_trust_score += .2
    if feature['user_count'] >= user_count_threshold:
        direct_trust_score += .2
    if feature['rollbacks'] >= rollbacks_threshold:
        direct_trust_score += .1
    if feature['changes_to_tags'] >= changes_to_tags_threshold:
        direct_trust_score += .1
    if feature['tags'] >= tags_threshold:
        direct_trust_score += .2
    feature.direct_trust_score = direct_trust_score

    feature.time_trust_score = int(feature['days_since_last_edit'] > days_since_last_edit_threshold)

    return feature
