import hplib.hplib as hpl
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Load input temperatures dataseries
df_temp = pd.read_csv("re_ninja/ninja_weather_HS.csv", comment='#', sep=",", parse_dates=["time"])
t_amb = df_temp['t2m']
T_in = df_temp['t2m']
T_out = 60.0

print(t_amb.min(), t_amb.max())
# Load database and parameters
database = hpl.load_database()
params = hpl.get_parameters(model="Generic", group_id=1, t_in=-7, t_out=52, p_th=10000)
# Create Generic Air/Water Heat Pump
hp = hpl.HeatPump(params)

sim = hp.simulate(
    t_amb=t_amb.values,
    t_in_primary=T_in.values,
    t_in_secondary=T_out,
    mode=1
)
print(pd.Series(sim["COP"]).mean())

