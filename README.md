# TDEI-python-confidence-metric-lib

This package is used to calculate the confidence score of a geojson area.


## System requirements

| Software | Version |
|----------|---------|
| Python   | 3.10.x  |

## What this package does?

This package is used to calculate the confidence score of a geojson area.
- It takes username and password which can be generated [here](https://www.openstreetmap.org/)
- It also takes geojson file which confidence score needs to be generated


## Starting a new project with template

- Add `osw-confidence-metric` package as dependency in your `requirements.txt`
- or `pip install osw-confidence-metric`
- Start using the packages in your code.

## Initialize and Configuration

```python
from osw_confidence_metrics.osm_data_handler import OSMDataHandler
from osw_confidence_metrics.area_analyzer import AreaAnalyzer
username = ''
password = ''


if __name__ == '__main__':
    osm_data_handler = OSMDataHandler(username=username, password=password)
    area_analyzer = AreaAnalyzer(osm_data_handler=osm_data_handler)
    score = area_analyzer.calculate_area_confidence_score(file_path=<GEOJSON_FILE_PATH>)
    print(score)
```

### Testing

The project is configured with `python` to figure out the coverage of the unit tests. All the tests are in `tests`
folder.

- To execute the tests, please follow the commands:

  `pip install -r requirement.txt`

  `python -m unittest discover -v tests/unit_tests`

- To execute the code coverage, please follow the commands:

  `python -m coverage run --source=src/osw_confidence_metric -m unittest discover -s tests/unit_tests`

  `coverage html` // Can be run after 1st command

  `coverage report` // Can be run after 1st command

- After the commands are run, you can check the coverage report in `htmlcov/index.html`. Open the file in any browser,
  and it shows complete coverage details
- The terminal will show the output of coverage like this

```shell

>  python -m unittest discover -v tests/unit_tests
test_calculate_area_confidence_score (test_area_analyzer.TestAreaAnalyzer.test_calculate_area_confidence_score) ... ok
test_create_tiling_if_needed (test_area_analyzer.TestAreaAnalyzer.test_create_tiling_if_needed) ... ok
test_create_voronoi_diagram (test_area_analyzer.TestAreaAnalyzer.test_create_voronoi_diagram) ... ok
test_process_feature (test_area_analyzer.TestAreaAnalyzer.test_process_feature) ... ok
test_get_threshold_values (test_area_analyzer.TestGetThresholdValues.test_get_threshold_values) ... ok
test_initialize_columns (test_area_analyzer.TestInitializeColumns.test_initialize_columns) ... ok
test_get_item_history_invalid_item (test_osm_data_handler.TestOSMDataHandler.test_get_item_history_invalid_item) ... ok
test_get_item_history_invalid_type (test_osm_data_handler.TestOSMDataHandler.test_get_item_history_invalid_type) ... ok
test_get_item_history_node (test_osm_data_handler.TestOSMDataHandler.test_get_item_history_node) ... ok
test_get_item_history_relation (test_osm_data_handler.TestOSMDataHandler.test_get_item_history_relation) ... ok
test_get_item_history_way (test_osm_data_handler.TestOSMDataHandler.test_get_item_history_way) ... ok
test_get_map_data (test_osm_data_handler.TestOSMDataHandler.test_get_map_data) ... ok
test_get_way_history (test_osm_data_handler.TestOSMDataHandler.test_get_way_history) ... ok
test_get_way_history_valid_osmid (test_osm_data_handler.TestOSMDataHandler.test_get_way_history_valid_osmid) ... ok
test_initialization_with_credentials (test_osm_data_handler.TestOSMDataHandler.test_initialization_with_credentials) ... ok
test_all_data_after_cutoff (test_trust_score_calculator.TestTrustScoreAnalyzer.test_all_data_after_cutoff) ... ok
test_all_data_before_cutoff (test_trust_score_calculator.TestTrustScoreAnalyzer.test_all_data_before_cutoff) ... ok
test_analyze_sidewalk_features (test_trust_score_calculator.TestTrustScoreAnalyzer.test_analyze_sidewalk_features) ... ok
test_analyze_sidewalk_features_non_empty_graph (test_trust_score_calculator.TestTrustScoreAnalyzer.test_analyze_sidewalk_features_non_empty_graph) ... ok
test_calculate_statistics_for_edge (test_trust_score_calculator.TestTrustScoreAnalyzer.test_calculate_statistics_for_edge) ... ok
test_compute_edge_statistics (test_trust_score_calculator.TestTrustScoreAnalyzer.test_compute_edge_statistics) ... ok
test_data_before_and_after_cutoff (test_trust_score_calculator.TestTrustScoreAnalyzer.test_data_before_and_after_cutoff) ... ok
test_empty_historical_info (test_trust_score_calculator.TestTrustScoreAnalyzer.test_empty_historical_info) ... ok
test_get_measures_from_polygon_empty_graph (test_trust_score_calculator.TestTrustScoreAnalyzer.test_get_measures_from_polygon_empty_graph) ... ok
test_aggregate_feature_statistics (test_utils.TestUtils.test_aggregate_feature_statistics) ... ok
test_aggregate_feature_statistics_with_incomplete_dataset (test_utils.TestUtils.test_aggregate_feature_statistics_with_incomplete_dataset) ... ok
test_calculate_days_since_last_edit_current_date (test_utils.TestUtils.test_calculate_days_since_last_edit_current_date) ... ok
test_calculate_days_since_last_edit_for_empty_historical_info (test_utils.TestUtils.test_calculate_days_since_last_edit_for_empty_historical_info) ... ok
test_calculate_days_since_last_edit_multiple_dates (test_utils.TestUtils.test_calculate_days_since_last_edit_multiple_dates) ... ok
test_calculate_days_since_last_edit_single_date (test_utils.TestUtils.test_calculate_days_since_last_edit_single_date) ... ok
test_calculate_direct_confirmations (test_utils.TestUtils.test_calculate_direct_confirmations) ... ok
test_calculate_direct_confirmations_sith_single_entry (test_utils.TestUtils.test_calculate_direct_confirmations_sith_single_entry) ... ok
test_calculate_feature_trust_scores (test_utils.TestUtils.test_calculate_feature_trust_scores) ... ok
test_calculate_feature_trust_scores_where_no_thresholds_met (test_utils.TestUtils.test_calculate_feature_trust_scores_where_no_thresholds_met) ... ok
test_calculate_indirect_trust_components_from_polygon (test_utils.TestUtils.test_calculate_indirect_trust_components_from_polygon) ... ok
test_calculate_no_direct_confirmations (test_utils.TestUtils.test_calculate_no_direct_confirmations) ... ok
test_calculate_number_users_edited_for_duplicate_users (test_utils.TestUtils.test_calculate_number_users_edited_for_duplicate_users) ... ok
test_calculate_number_users_edited_for_empty_info (test_utils.TestUtils.test_calculate_number_users_edited_for_empty_info) ... ok
test_calculate_number_users_edited_for_unique_users (test_utils.TestUtils.test_calculate_number_users_edited_for_unique_users) ... ok
test_calculate_overall_trust_score_with_all_scores_missing (test_utils.TestUtils.test_calculate_overall_trust_score_with_all_scores_missing) ... ok
test_calculate_overall_trust_score_with_negative_scores (test_utils.TestUtils.test_calculate_overall_trust_score_with_negative_scores) ... ok
test_calculate_overall_trust_score_with_scores_present (test_utils.TestUtils.test_calculate_overall_trust_score_with_scores_present) ... ok
test_calculate_overall_trust_score_with_some_scores_missing (test_utils.TestUtils.test_calculate_overall_trust_score_with_some_scores_missing) ... ok
test_calculate_user_interaction_stats (test_utils.TestUtils.test_calculate_user_interaction_stats) ... ok
test_check_for_rollbacks (test_utils.TestUtils.test_check_for_rollbacks) ... ok
test_check_for_rollbacks_no_rollback (test_utils.TestUtils.test_check_for_rollbacks_no_rollback) ... ok
test_check_for_rollbacks_with_empty_historical_info (test_utils.TestUtils.test_check_for_rollbacks_with_empty_historical_info) ... ok
test_compute_feature_indirect_trust_with_above_thresholds (test_utils.TestUtils.test_compute_feature_indirect_trust_with_above_thresholds) ... ok
test_compute_feature_indirect_trust_with_below_thresholds (test_utils.TestUtils.test_compute_feature_indirect_trust_with_below_thresholds) ... ok
test_compute_feature_indirect_trust_with_missing (test_utils.TestUtils.test_compute_feature_indirect_trust_with_missing) ... ok
test_count_tag_changes (test_utils.TestUtils.test_count_tag_changes) ... ok
test_count_tag_changes_with_empty_historical_info (test_utils.TestUtils.test_count_tag_changes_with_empty_historical_info) ... ok
test_count_tag_changes_with_no_change (test_utils.TestUtils.test_count_tag_changes_with_no_change) ... ok
test_count_tags (test_utils.TestUtils.test_count_tags) ... ok
test_count_tags_with_no_tags (test_utils.TestUtils.test_count_tags_with_no_tags) ... ok
test_extract_features_from_polygon (test_utils.TestUtils.test_extract_features_from_polygon) ... ok
test_extract_features_from_polygon_failure (test_utils.TestUtils.test_extract_features_from_polygon_failure) ... ok
test_extract_road_features_from_polygon (test_utils.TestUtils.test_extract_road_features_from_polygon) ... ok
test_extract_road_features_from_polygon_failure (test_utils.TestUtils.test_extract_road_features_from_polygon_failure) ... ok
test_get_relevant_tags (test_utils.TestUtils.test_get_relevant_tags) ... ok
test_get_relevant_tags_with_empty_edge (test_utils.TestUtils.test_get_relevant_tags_with_empty_edge) ... ok
test_get_relevant_tags_with_no_relevant_tags (test_utils.TestUtils.test_get_relevant_tags_with_no_relevant_tags) ... ok
test_get_relevant_tags_with_some_tags_missing (test_utils.TestUtils.test_get_relevant_tags_with_some_tags_missing) ... ok

----------------------------------------------------------------------
Ran 63 tests in 1.906s

OK


```