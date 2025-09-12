import pandas as pd
import os
from persee_format import PerseeFormat
from ninja import RenewableNinja
from location_selection import LocationSelection

START_DATE = '2025-01-01 00:00'
SEC_INTERVAL = 3600  # Measured in seconds
STEPS_PER_DAY = 24  # Number of time steps in a day (typically measured in hours)
NB_STEPS = 8760  # Based on time steps but typically measured in hours

persee = PerseeFormat()
base_df = pd.DataFrame({"Time": [int((i + 1) * SEC_INTERVAL) for i in range(NB_STEPS)]})
base_load_dict = {}
# Download generic load profiles
profile_df = pd.read_excel('profili.xlsx')
# Add load profiles from excel file
base_df, base_load_dict = persee.generate_loads("Loads.csv", base_df, base_load_dict, NB_STEPS, STEPS_PER_DAY,
                                                profile_df, rand_range=(0.9, 1.1))
merge_map = {
    "Elec_Central": {
        "columns_idx": list(range(1, 10)),
        "load_type": "load",
        "units": "MW"
    }
}
# Run merge loads function  (optional)
base_df, base_load_dict = persee.merge_loads(base_df, base_load_dict, merge_map, drop_originals=False)

# Add location specific data
file_name = 'location_selection_global_atlas.csv'
out_dir = "locations"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, file_name)
loc_sel = LocationSelection(out_path)
for loc, lat, lon in loc_sel.locations:
    ninja = RenewableNinja(location_name=loc)
    pv_file = ninja.get_re_data((lat, lon), re_type="pv")
    wind_file = ninja.get_re_data((lat, lon), re_type="wind")
    demand_file = ninja.get_re_data((lat, lon), re_type="demand")
    temp_file = ninja.get_re_data((lat, lon), re_type="weather")
    # Add data from renewables ninja
    df, load_dict = persee.load_renewables(pv_file, ["PV"], [1],
                                           base_df, base_load_dict, 1000000, load_type="Generation")
    # Solar Thermal estimated at 707 W/m2 at 20C vs. 250 W/m2 for PV which is 2.8 times more
    df, load_dict = persee.load_renewables(pv_file, ["Solar_Thermal"], [1],
                                           df, load_dict, 353606, load_type="Generation")
    df, load_dict = persee.load_renewables(wind_file, ["Wind"], [1],
                                           df, load_dict, 1000, load_type="Generation")
    df, load_dict = persee.load_renewables(demand_file, ["Heating_Central", "Cooling_Central"], [2, 3],
                                           df, load_dict, 1000)
    df, load_dict = persee.load_renewables(temp_file, ["Temperature"], [1], df, load_dict,
                                           divider=1, load_type="Temperature", units="COP")

    # Add PERSEE required descriptive headers
    df = persee.add_headers(df, load_dict, START_DATE)

    # Save final DataFrame to CSV
    out_dir = "dataseries"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"INDY_{ninja.location_name}_dataseries.csv")
    df.to_csv(out_path, sep=";", index=False, header=False, float_format='%3g')
    print(f"Saved dataseries to {out_path}")
