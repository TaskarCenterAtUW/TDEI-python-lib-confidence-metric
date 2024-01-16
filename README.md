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

- Add `python-osw-validation` package as dependency in your `requirements.txt`
- or `pip install python-osw-validation`
- Start using the packages in your code.

## Initialize and Configuration

```python
from python_confidence_metric.osm_data_handler import OSMDataHandler
from python_confidence_metric.area_analyzer import AreaAnalyzer
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

  `pip install -r requirements.txt`

  `python -m unittest discover -v tests/unit_tests`

- To execute the code coverage, please follow the commands:

  `python -m coverage run --source=src -m unittest discover -s tests/unit_tests`

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

----------------------------------------------------------------------
Ran 15 tests in 0.318s

OK

```