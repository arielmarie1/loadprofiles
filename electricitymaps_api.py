from datetime import datetime, timedelta, timezone
import time
import requests
from dotenv import load_dotenv
import os
import pandas as pd


load_dotenv()
api_token_elec = os.getenv("API_TOKEN_ELEC")


class ElectricityMaps:
    def __init__(self,
                 location_name: str,
                 token: str = os.getenv("API_TOKEN_ELEC"),
                 api_base: str = 'https://api.electricitymaps.com/',
                 sleep_s: float = 0.3
                 ):
        self.api_base = api_base
        self.location_name = location_name
        self.sleep_s = sleep_s
        self.s = requests.session()
        self.s.headers = {"auth-token": token}

    def fetch_electricity_prices(self, zone, sel_year: int = 2019):
        url = self.api_base + 'v3/price-day-ahead/past-range'

        start = datetime(sel_year, 1, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(sel_year+1, 1, 1, 0, 0, tzinfo=timezone.utc)
        step = timedelta(days=10)

        prices = []
        current = start

        while current < end:
            nxt = min(current + step, end)
            args = {
                'zone': zone,
                'start': current.isoformat().replace("+00:00", "Z"),
                'end': nxt.isoformat().replace("+00:00", "Z"),
                'temporalGranularity': 'hourly'
            }

            r = self.s.get(url, params=args)
            r.raise_for_status()
            prices.extend(r.json()["data"])
            current = nxt
            time.sleep(self.sleep_s)

        df = pd.DataFrame(prices)
        df = df[["datetime", "value", "unit"]].rename(columns={"datetime": "time"})

        out_dir = "electricity_prices"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"elec_price_{sel_year}_{self.location_name}.csv")
        df.to_csv(out_path, index=False)
        return out_path
