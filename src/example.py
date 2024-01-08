# example.py
import time

from python_confidence_metric.osm_data_handler import OSMDataHandler
from python_confidence_metric.area_analyzer import AreaAnalyzer
username = ''
password = ''


if __name__ == '__main__':
    start_time = time.time()
    osm_data_handler = OSMDataHandler(username=username, password=password)
    area_analyzer = AreaAnalyzer(osm_data_handler=osm_data_handler)
    score = area_analyzer.calculate_area_confidence_score(file_path='./src/assets/caphill_mini.geojson')
    print(score)
    print("--- %s seconds ---" % (time.time() - start_time))
# 0.5089541985791985
# 0.5626176462426462
# 0.5891414469671816
