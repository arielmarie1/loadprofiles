import pandas as pd
import random

START_DATE = '2025-01-01 00;00'
SEC_INTERVAL = 3600  # Measured in seconds
STEPS_PER_DAY = 24  # Number of time steps in a day (typically measured in hours)
NB_STEPS = 8760  # Based on time steps but typically measured in hours


def load_zone_definitions(filename):
    """
    The Excel file should have a header row with the following columns:
      - 'Name' for the zone name (e.g., "Command")
      - 'Max Power' for the maximum power value (e.g., 0.3117)
      - 'Profile' for the profile number (e.g., 1, 2, etc.)
      - 'Load Type' for the load type (e.g "load" "Generation", "Massflow")
      - 'Units' for the units used (e.g "MW", "kg/hr")
    Returns a dictionary where each key is a zone name and its value is a dictionary containing the pre-stated columns.
    """
    try:
        dataframe = pd.read_csv(filename, sep=",")
        load_dictionary = {row['Name']: {'max_power': row['Max Power'], 'profile': row['Profile'],
                                         'load_type': row['Load Type'], 'units': row['Units']}
                           for idx, row in dataframe.iterrows()}
        return load_dictionary
    except Exception as e:
        print(f"Error reading zone definitions from {filename}: {e}")
        return None


def load_renewable_pv(filename, sep=","):
    """
    Load PV data from a CSV file.
    Assumes the file has 4 header rows to skip and that column C (index 2)
    contains the "electricity" data in Watts, which must be converted to MW.
    """
    try:
        df = pd.read_csv(filename, sep=sep, skiprows=4)
        # Convert column C from Watts to kW (divide by 1000)
        df["PV"] = df.iloc[:, 2] / 1000000
        return df[["PV"]]
    except Exception as e:
        print(f"Error loading PV data: {e}")
        return None


def load_renewable_wind(filename, sep=";"):
    """
    Load Wind data from a CSV file.
    Assumes the file has 4 header rows to skip and that column C (index 2)
    contains the "electricity" data in kW.
    """
    try:
        df = pd.read_csv(filename, sep=sep, skiprows=4)
        df["Wind"] = df.iloc[:, 2]
        return df[["Wind"]]
    except Exception as e:
        print(f"Error loading Wind data: {e}")
        return None


def load_renewable_heating_cooling(filename, sep=";"):
    """
    Load Heating and Cooling data from a CSV file.
    Assumes the file has 4 header rows to skip.
    Column D (index 3) contains Heating data and column E (index 4) contains Cooling data, both in kW.
    """
    try:
        df = pd.read_csv(filename, sep=sep, skiprows=4)
        df["Heating"] = df.iloc[:, 3]
        df["Cooling"] = df.iloc[:, 4]
        return df[["Heating", "Cooling"]]
    except Exception as e:
        print(f"Error loading Heating/Cooling data: {e}")
        return None


def merge_loads(dataframe, load_dictionary, merge_mapping):
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
        # Remove the original columns from the DataFrame
        dataframe.drop(columns=cols_to_merge, inplace=True)
        # Remove the merged columns from load_dict (if they exist)
        for col in cols_to_merge:
            if col in load_dictionary:
                del load_dictionary[col]
        # Add the new merged column to load_dict with the provided header info
        load_dictionary[new_col] = {
            "max_power": None,    # Not used in header creation
            "profile": None,      # Not used in header creation
            "load_type": merge_info.get("load_type", "load"),
            "units": merge_info.get("units", "MW")
        }
    return dataframe, load_dictionary


load_dict = load_zone_definitions("Loads.csv")
profile_df = pd.read_excel('profili.xlsx')

# Create new column in dataframe for each functional zone defined by the file name
df = pd.DataFrame()
for name in load_dict:
    load_list = []
    for i in range(int(NB_STEPS / STEPS_PER_DAY)):
        profile = profile_df[load_dict[name]['profile']]
        max_power = load_dict[name]['max_power']
        load = [item * random.uniform(0.8, 1.1) * max_power / 100 for item in profile]
        load_list.extend(load)
    new_df = pd.DataFrame.from_dict({f"{name}": load_list})
    df = pd.concat([df, new_df], axis=1)

# Testing new merging loads capability
merge_map = {
    "Merged_Load": {
        "columns_idx": [0, 2],
        "load_type": "load",
        "units": "MW"
        }
}

# Run merge loads function - optional
# df, load_dict = merge_loads(df,load_dict,merge_map)

# Create a time column measured in seconds
time = [(i+1) * int(SEC_INTERVAL) for i in range(NB_STEPS)]
time_df = pd.DataFrame.from_dict({"Time": time})

# Concatenate time column with the data
final_df = pd.concat([time_df, df], axis=1)

# Row 1: Column Names (Time, followed by each zone)
# Row 2: Description (example: start time for the start date for Time, and "load" for others)
# Row 3: Units ("s" for time, "MW" for loads)
# Row 4: TRUE/FALSE flags (all "true" in this example)
header1 = final_df.columns.to_list()
header2 = [START_DATE] + [load_dict[col]['load_type'] for col in final_df.columns[1:]]
header3 = ["s"] + [load_dict[col]['units'] for col in final_df.columns[1:]]
header4 = ["true"] * len(final_df.columns)
final = pd.DataFrame([header1, header2, header3, header4])

for i in range(len(final_df.index)):
    final.loc[len(final)] = (final_df.iloc[i].tolist())

# Convert the time column in the data portion (after the header rows) to integer
final.iloc[4:, 0] = final.iloc[4:, 0].astype(int)

# Save final DataFrame
final.to_csv("Test_dataseries.csv", sep=";", index=False, header=False)
