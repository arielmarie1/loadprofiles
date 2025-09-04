import pandas as pd
from persee_format import PerseeFormat
from ninja import RenewableNinja

START_DATE = '2025-01-01 00:00'
SEC_INTERVAL = 3600  # Measured in seconds
STEPS_PER_DAY = 24  # Number of time steps in a day (typically measured in hours)
NB_STEPS = 8760  # Based on time steps but typically measured in hours

persee = PerseeFormat()
ninja = RenewableNinja(location_name='Ede')

df = pd.DataFrame({"Time": [int((i+1) * SEC_INTERVAL) for i in range(NB_STEPS)]})
load_dict = {}

# Download generic load profiles
profile_df = pd.read_excel('profili.xlsx')

# Add load profiles from excel file
df, load_dict = persee.generate_loads("Loads_LJ.csv", df, load_dict, NB_STEPS, STEPS_PER_DAY, profile_df,
                                      rand_range=(0.9, 1.1))

# Optional merge loads capability
merge_map = {
    "Elec_Central": {
        "columns_idx": list(range(1, 10)),
        "load_type": "load",
        "units": "MW"
        }
}
# Run merge loads function  (optional)
df, load_dict = persee.merge_loads(df, load_dict, merge_map, drop_originals=False)

# Add data from renewables ninja
df, load_dict = persee.load_renewables("ninja_pv.csv", ["PV"], [2],
                                       df, load_dict, 1000000, load_type="Generation")
# Solar Thermal estimated at 707 W/m2 at 20C vs. 250 W/m2 for PV which is 2.8 times more
df, load_dict = persee.load_renewables("ninja_pv.csv", ["Solar_Thermal"], [2],
                                       df, load_dict, 353606, load_type="Generation")
df, load_dict = persee.load_renewables("ninja_wind.csv", ["Wind"], [2],
                                       df, load_dict, 1000, load_type="Generation")
df, load_dict = persee.load_renewables("ninja_demand.csv", ["Heating_Central", "Cooling_Central"], [3, 4],
                                       df, load_dict, 1000)

# Add PERSEE required descriptive headers
df = persee.add_headers(df, load_dict, START_DATE)

# Save final DataFrame
df.to_csv("INDY_dataseries_Testing.csv", sep=";", index=False, header=False, float_format='%3g')
