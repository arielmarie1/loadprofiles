import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
api_token = os.getenv("API_TOKEN")


class RenewableNinja:
    def __init__(self,
                 location_name: str,
                 token: str = os.getenv("API_TOKEN"),
                 api_base: str = 'https://www.renewables.ninja/api/',
                 format_type: str = 'csv'
                 ):
        self.api_base = api_base
        self.location_name = location_name
        self.format_type = format_type
        self.s = requests.Session()
        self.s.headers = {'Authorization': 'Token ' + token}

    def _calc_date_range(self, start_date: str, duration: int):
        pass

    def get_re_data(self, coords: tuple[float, float], re_type: str, use_cache: bool = True):
        lat = coords[0]
        lon = coords[1]
        # Helpful link to renewables.ninja api models: https://www.renewables.ninja/api/models
        if re_type == "pv":
            ext = 'data/pv'
            args = {
                'lat': lat,
                'lon': lon,
                'date_from': '2019-01-01',
                'date_to': '2019-12-31',
                'dataset': 'merra2',
                'capacity': 250,
                'system_loss': 0.1,
                'tracking': 0,
                'tilt': 35,
                'azim': 180,
                'format': self.format_type
            }
        elif re_type == "wind":
            ext = 'data/wind'
            args = {
                'lat': lat,
                'lon': lon,
                'date_from': '2019-01-01',
                'date_to': '2019-12-31',
                'capacity': 150,
                'height': 30,
                'turbine': 'Nordex N27 150',
                'format': self.format_type
            }
        elif re_type == "weather":
            ext = 'data/weather'
            args = {
                'lat': lat,
                'lon': lon,
                'date_from': '2019-01-01',
                'date_to': '2019-12-31',
                'var_t2m': True,  # Temperature
                'format': self.format_type
            }
        else:
            ext = 'data/demand'
            args = {
                'lat': lat,
                'lon': lon,
                'date_from': '2019-01-01',
                'date_to': '2019-12-31',
                'dataset': 'merra2',
                'heating_threshold': 14,
                'cooling_threshold': 20,
                'base_power': 0,
                'heating_power': 90,
                'cooling_power': 100,
                'smoothing': 0.5,
                'solar_gains': 0.012,
                'wind_chill': -0.2,
                'humidity_discomfort': 0.05,
                'use_diurnal_profile': True,
                'format': self.format_type
            }

        url = self.api_base + ext

        if self.format_type == 'csv':
            fname = f"ninja_{re_type}_{self.location_name}.{self.format_type}"
            out_dir = "re_ninja"
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, fname)

            if use_cache and os.path.exists(out_path):
                print(f"[Renewables Ninja] Using cached file: {out_path}")
                return out_path

            response = self.s.get(url, params=args)
            response.raise_for_status()
            time.sleep(1.0)

            with open(out_path, 'w') as f:
                f.write(response.text)
            print(f"[Renewables Ninja] Saved: {out_path}")
            return out_path

        elif self.format_type == 'json':
            response = self.s.get(url, params=args)
            response.raise_for_status()
            time.sleep(1.0)
            data = response.json()
            print(data)
