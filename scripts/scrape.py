import requests
import json
import re
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

my_location = 'highwood pass alberta'

locator = Nominatim(user_agent='myGeocoder')
location = locator.geocode(my_location, country_codes='ca')

url = "https://api.avalanche.ca/forecasts/:lang/products/point?lat={}&long={}".format(location.latitude, location.longitude)

resp = requests.get(url)

json_data = json.loads(resp.text)

print(json_data['report']['dangerRatings'])

rating_date = json_data['report']['dangerRatings'][0]['date']['display']
rating_alpine = json_data['report']['dangerRatings'][0]['ratings']['alp']['rating']['display']
rating_treeline = json_data['report']['dangerRatings'][0]['ratings']['tln']['rating']['display']
rating_belowtreeline = json_data['report']['dangerRatings'][0]['ratings']['btl']['rating']['display']

ratings_summary = 'The danger rating for today, {}, is the following. Alpine is {}, treeline is {}, and below treeline is {}.'.format(rating_date, rating_alpine, rating_treeline, rating_belowtreeline)

avy_main = json_data['report']['highlights']
avy_summary = json_data['report']['summaries'][0]['content']
avy_snowpack = json_data['report']['summaries'][1]['content']
avy_weather = json_data['report']['summaries'][2]['content']

l = [
    avy_main, 
    ratings_summary, 
    'Here is the detailed avalanche summary.',
    avy_summary, 
    'Here is the detailed snowpack summary.',
    avy_snowpack, 
    'Here is the detailed weather summary.',
    avy_weather
]

clean_string = []
for txt in l:
    soup = BeautifulSoup(txt, 'html.parser')
    clean_string.append(soup.get_text(' ', strip=True))

clean_string = ' '.join(clean_string)

print(clean_string)