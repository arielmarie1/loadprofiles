from datetime import datetime, timedelta, timezone
import time
import requests
from dotenv import load_dotenv
import os
import pandas as pd
import json


load_dotenv()
api_token_elec = os.getenv("API_TOKEN_ELEC")

api_base = 'https://api.electricitymaps.com/'
url = api_base + 'v3/price-day-ahead/past-range'

s = requests.session()

s.headers = {
        "auth-token": api_token_elec
    }
zones = ['EE', 'FR', 'PL', 'SI']

sel_year = 2024
start = datetime(sel_year, 1, 1, 0, 0, tzinfo=timezone.utc)
end = datetime(sel_year+1, 1, 1, 0, 0, tzinfo=timezone.utc)
step = timedelta(days=10)

for zone in zones:
    prices = []
    current = start

    while current < end:
        nxt = min(current + step, end)
        args = {
            'zone': zone,
            'start': current.isoformat().replace("+00:00","Z"),
            'end': nxt.isoformat().replace("+00:00","Z"),
            'temporalGranularity': 'hourly'
        }

        r = s.get(url, params=args)
        r.raise_for_status()
        prices.extend(r.json()["data"])
        current = nxt
        time.sleep(0.3)

    df = pd.DataFrame(prices)
    df = df[["datetime","value", "unit"]].rename(columns={"datetime":"time"})

    out_dir = "electricity_prices"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{zone}_price_{sel_year}")
    df.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    print(df.head(10))

