from src.osw_confidence_metric.osm_data_handler import OSMDataHandler
from src.osw_confidence_metric.area_analyzer import AreaAnalyzer
import threading
import time
# nerope1097@wentcity.com
# $$WentCityErwin
username = 'nerope1097@wentcity.com'
password = '$$WentCityErwin'


osm_data_handler = OSMDataHandler(username=username, password=password)
area_analyzer = AreaAnalyzer(osm_data_handler=osm_data_handler)

def analyse_score(file_path:str) :
    score = area_analyzer.calculate_area_confidence_score(file_path=file_path)
    print(score)


if __name__ == '__main__':
    start = time.time()
    # your code here    

    score = area_analyzer.calculate_area_confidence_score(file_path="./src/assets/caphill_mini.geojson")
    print(score)
   
    # Have three threads
    # process_thread = threading.Thread(target=analyse_score, args=["./src/assets/caphill_mini.geojson"])
    # process_thread.start()
    
    print(time.time() - start)
    # pthread2 = threading.Thread(target=analyse_score,args=["./src/assets/seattle_downtown.geojson"])
    # pthread2.start()
    
    # pthread3 = threading.Thread(target=analyse_score,args=["./src/assets/redmond_town_center.geojson"])
    # pthread3.start()
    # process_thread.join()
    # pthread2.join()
    # pthread3.join()
    

