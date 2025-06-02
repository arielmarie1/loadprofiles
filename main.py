import pandas as pd
import random
# from datetime import datetime, timedelta

START_DATE = '2025-01-01 00:00'
SEC_INTERVAL = 3600  # Measured in seconds
STEPS_PER_DAY = 24  # Number of time steps in a day (typically measured in hours)
NB_STEPS = 8760  # Based on time steps but typically measured in hours


def load_renewables(filename, names, indices, dataframe, load_dictionary, divider,
                    sep=",", skiprows=3, load_type="load", units="MW"):
    """
    Load data from a CSV file downloaded from Renewables Ninja.
    Assumes the file has header rows to skip and that column C (index 2, 3 or 4)
    contains the "electricity" data in Watts or kW, which must be converted to MW using divider value.
    """
    try:
        df_re = pd.read_csv(filename, sep=sep, skiprows=skiprows)
        for name, idx in zip(names, indices):
            dataframe[name] = df_re.iloc[:, idx] / float(divider)
            load_dictionary[name] = {
                "max_power": None,  # Not used in header creation
                "profile": None,  # Not used in header creation
                "load_type": load_type,
                "units": units
            }
        return dataframe, load_dictionary
    except Exception as e:
        print(f"Error loading RE data: {e}")
        return None


def merge_loads(dataframe, load_dictionary, merge_mapping, drop_originals=True):
    """
    Merge specified columns in the DataFrame and update the load_dictionary accordingly.
    Parameters:
        dataframe (pd.DataFrame): DataFrame containing the load data.
        load_dictionary (dict): Dictionary with load definitions for header creation.
        merge_mapping (dict): Mapping where each key is the new column name, and its value is a dict:
            - "columns": list of existing columns to merge.
            - "load_type": description for the new column header.
            - "units": units for the new column header.
    Returns:
        Tuple (updated DataFrame, updated load_dict)
    """
    for new_col, merge_info in merge_mapping.items():
        # Map provided gives column indices
        cols_to_merge = [dataframe.columns[j] for j in merge_info["columns_idx"]]
        # Sum the specified columns row-wise to create the new merged column
        dataframe[new_col] = dataframe[cols_to_merge].sum(axis=1)
        # Add the new merged column to load_dict with the provided header info
        load_dictionary[new_col] = {
            "max_power": None,    # Not used in header creation
            "profile": None,      # Not used in header creation
            "load_type": merge_info.get("load_type", "load"),
            "units": merge_info.get("units", "MW")
        }
        if drop_originals:
            # Remove the original columns from the DataFrame
            dataframe.drop(columns=cols_to_merge, inplace=True)

            # Remove the original columns from load_dict (if they exist)
            for col in cols_to_merge:
                if col in load_dictionary:
                    del load_dictionary[col]

    return dataframe, load_dictionary


def generate_loads(filename, dataframe, load_dictionary,
                   nb_steps, steps_per_day, profile_dataframe,
                   rand_range=(1.0, 1.0)):
    """
        The Excel file should have a header row with the following columns:
          - 'Name' for the zone name (e.g., "Command")
          - 'Max Power' for the maximum power value (e.g., 0.05 MW)
          - 'Profile' for the profile number
            (e.g., 1. Work, 2. Nonstop, 3. Recreation, 4. Utility, 5. Food, 6. Accommodation, 7. Ward, 8. Test)
          - 'Load Type' for the load type (e.g "load" "Generation", "Massflow")
          - 'Units' for the units used (e.g "MW", "kg/hr")
        Returns a dictionary where each key is "Name" and its value is a dictionary of the above-mentioned columns.
        Returns a dataframe with the generated loads.
        """
    try:
        df_orig = pd.read_csv(filename, sep=",")
        for idx, row in df_orig.iterrows():
            load_dictionary[row['Name']] = {
                'max_power': row['Max Power'],
                'profile': row['Profile'],
                'load_type': row['Load Type'],
                'units': row['Units']
            }
        for name, params in load_dictionary.items():
            # Check for a valid profile before processing.
            if params['profile'] is None:
                continue
            load_list = []
            num_days = int(nb_steps / steps_per_day)
            profile_series = profile_dataframe.iloc[:, int(params['profile'])]
            max_power = params['max_power']
            for day in range(num_days):
                # profile = profile_df[load_dictionary[name]['profile']]
                # max_power = load_dictionary[name]['max_power']
                load = [item * random.uniform(*rand_range) * max_power / 100 for item in profile_series]
                load_list.extend(load)
            new_df = pd.DataFrame.from_dict({f"{name}": load_list})
            dataframe = pd.concat([dataframe, new_df], axis=1)
        return dataframe, load_dictionary
    except Exception as e:
        print(f"Error reading zone definitions from {filename}: {e}")
        return None


def add_headers(dataframe, load_dictionary, start_date):
    # Row 1: Column Names (Time, followed by each zone)
    # Row 2: Description (example: start time for the start date for Time, and "load" for others)
    # Row 3: Units ("s" for time, "MW" for loads)
    # Row 4: TRUE/FALSE flags (all "true" in this example)
    header1 = dataframe.columns.to_list()
    header2 = [start_date] + [load_dictionary[col]['load_type'] for col in dataframe.columns[1:]]
    header3 = ["s"] + [load_dictionary[col]['units'] for col in dataframe.columns[1:]]
    header4 = ["true"] * len(dataframe.columns)
    final = pd.DataFrame([header1, header2, header3, header4])
    for i in range(len(dataframe.index)):
        final.loc[len(final)] = (dataframe.iloc[i].tolist())
    # Convert the time column in the data portion (after the header rows) to integer
    final.iloc[4:, 0] = final.iloc[4:, 0].astype(int)
    return final


df = pd.DataFrame({"Time": [int((i+1) * SEC_INTERVAL) for i in range(NB_STEPS)]})
load_dict = {}

# Download generic load profiles
profile_df = pd.read_excel('profili.xlsx')

# Add load profiles from excel file
df, load_dict = generate_loads("Loads_LJ.csv", df, load_dict, NB_STEPS, STEPS_PER_DAY, profile_df,
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
df, load_dict = merge_loads(df, load_dict, merge_map, drop_originals=False)

# Add data from renewables ninja
df, load_dict = load_renewables("ninja_pv.csv", ["PV"], [2],
                                df, load_dict, 1000000, load_type="Generation")
# Solar Thermal estimated at 707 W/m2 at 20C vs. 250 W/m2 for PV which is 2.8 times more
df, load_dict = load_renewables("ninja_pv.csv", ["Solar_Thermal"], [2],
                                df, load_dict, 353606, load_type="Generation")
df, load_dict = load_renewables("ninja_wind.csv", ["Wind"], [2],
                                df, load_dict, 1000, load_type="Generation")
df, load_dict = load_renewables("ninja_demand.csv", ["Heating_Central", "Cooling_Central"], [3, 4],
                                df, load_dict, 1000)

# Add PERSEE required descriptive headers
df = add_headers(df, load_dict, START_DATE)

# Save final DataFrame
df.to_csv("INDY_dataseries_Ede.csv", sep=";", index=False, header=False, float_format='%3g')
