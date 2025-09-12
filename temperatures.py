import numpy as np
import pandas as pd


class Temperatures:
    def __init__(self, filename, coords: tuple[float, float]):
        self.lat = coords[0]
        self.lon = coords[1]
        self.cop_temps = np.array([-15, -10, -5, 0, 5, 10, 15, 20], dtype=float)
        self.cop_curves = {
            1.0: np.array([2.80, 3.00, 3.20, 3.35, 3.45, 3.55, 3.62, 3.70]),
            0.6: np.array([3.20, 3.35, 3.55, 3.70, 3.85, 4.00, 4.15, 4.30]),
            0.3: np.array([3.45, 3.60, 3.85, 4.05, 4.25, 4.40, 4.50, 4.60]),
        }
        self.filename = filename
        self.cop_avg = None

        self._load_temp()
        self._avg_temp()
        self._seasonal_avg()

    def cop_from_temp(self, temp_c_series, plr=0.6):
        cops = self.cop_curves[plr]
        x = np.asarray(temp_c_series, dtype=float)
        x_clipped = np.clip(x, self.cop_temps.min(), self.cop_temps.max())
        return np.interp(x_clipped, self.cop_temps, cops)

    def _load_temp(self):
        try:
            self.df_temp = pd.read_csv(self.filename, comment='#', sep=",", parse_dates=["time"])
            return self.df_temp['t2m']
        except Exception as e:
            print(f"Error loading temp/weather data: {e}")
            return None

    def _avg_temp(self):
        self.t_avg = self.df_temp["t2m"].mean()
        return self.t_avg

    def _seasonal_avg(self):
        # Summer - 3 hottest consecutive months
        summer = self.df_temp[self.df_temp["time"].dt.month.isin([6, 7, 8])]
        # Winter 3 coolest consecutive months
        winter = self.df_temp[self.df_temp["time"].dt.month.isin([12, 1, 2])]
        if self.lat >= 0:
            self.summer_avg = summer["t2m"].mean()
            self.winter_avg = winter["t2m"].mean()
        else:
            self.summer_avg = winter["t2m"].mean()
            self.winter_avg = summer["t2m"].mean()
        return self.summer_avg, self.winter_avg


LWS = Temperatures("re_ninja/ninja_weather_LWS.csv", coords=(65.44973126,27.18830351))
HS = Temperatures("re_ninja/ninja_weather_HS.csv", coords=(-12.82155901,45.13898189))
print(LWS.t_avg, LWS.winter_avg, LWS.summer_avg)
print(HS.t_avg, HS.winter_avg, HS.summer_avg)