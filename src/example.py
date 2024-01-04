# example.py

from python_confidence_metric.osm_data_handler import OSMDataHandler
from python_confidence_metric.area_analyzer import AreaAnalyzer

if __name__ == '__main__':
    osm_data_handler = OSMDataHandler(username='sujatam@gaussiansolutions.com', password='R@lling#1')
    area_analyzer = AreaAnalyzer(osm_data_handler=osm_data_handler)
    score = area_analyzer.calculate_area_confidence_score(file_path='/Users/anujkumar/Work/Gaussian/TDEI-python-lib-confidence-metric/src/assets/caphill_mini.geojson')
    print(score)
# 0.5089541985791985
# 0.5626176462426462
# 0.5891414469671816
