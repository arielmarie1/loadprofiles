import pandas as pd
import hplib.hplib as hpl


class Temperatures:
    def __init__(self, filename, coords: tuple[float, float]):
        self.lat = coords[0]
        self.lon = coords[1]
        self.filename = filename

        self._hplib_temps()
        self._load_temp()
        self._avg_temp()
        self._seasonal_avg()

    def _hplib_temps(self, t_out=60.0):
        # Load database and parameters
        database = hpl.load_database()
        params = hpl.get_parameters(model="Generic", group_id=1, t_in=-7, t_out=52, p_th=10000)
        # Create Generic Air/Water Heat Pump
        hp = hpl.HeatPump(params)

        sim = hp.simulate(
            t_amb=self.df_temp['t2m'].values,
            t_in_primary=self.df_temp['t2m'].values,
            t_in_secondary=t_out,
            mode=1
        )
        self.cop_series = pd.Series(sim["COP"])
        self.cop_avg = pd.Series(sim["COP"]).mean()

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
