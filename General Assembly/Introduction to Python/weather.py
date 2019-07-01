import requests
import pprint

URL = "http://api.openweathermap.org/data/2.5/forecast/daily?q=Boston&units=imperial&cnt=10&appid=f5f76fc80be1dfc220492acb706cb7e3"

weather = requests.get(URL).json()

# pprint.pprint(weather)

# This looks up the city name
city_name = weather['city']['name']

print(city_name)

day_list = weather['list']

# Prints first dictionary of the list in day_list
# pprint.pprint(day_list[0,1])

for single_day_forecast_dict in day_list:
    humidity = single_day_forecast_dict['humidity']
    wind_angle = single_day_forecast_dict['deg']
    # {} represents the variable referenced in order
    print('The humidity for this day is {} and the wind will be at {} degrees'.format(humidity, wind_angle))
