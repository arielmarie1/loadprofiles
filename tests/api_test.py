import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('API_TOKEN')
api_base = 'https://www.renewables.ninja/api/'

s = requests.session()
# Send token header with each request
s.headers = {'Authorization': 'Token ' + token}

# PV example

url = api_base + 'data/pv'

args = {
    'lat': 34.125,
    'lon': 39.814,
    'date_from': '2015-01-01',
    'date_to': '2015-12-31',
    'dataset': 'merra2',
    'capacity': 1.0,
    'system_loss': 0.1,
    'tracking': 0,
    'tilt': 35,
    'azim': 180,
    'format': 'json'
}

r = s.get(url, params=args)
r.raise_for_status()

# Parse JSON to get a pandas.DataFrame of data and dict of metadata
parsed_response = r.json()
data = pd.DataFrame.from_dict(parsed_response['data'], orient='index')
metadata = parsed_response['metadata']
print(data)