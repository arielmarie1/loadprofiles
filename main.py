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


load_dict = load_zone_definitions("Loads.csv")
profile_df = pd.read_excel('profili.xlsx')

# Create new column in dataframe for each functional zone defined by the file name
df = pd.DataFrame()
for name in load_dict:
    my_dict = {}
    load_list = []
    for i in range(int(NB_STEPS / STEPS_PER_DAY)):
        profile = profile_df[load_dict[name]['profile']]
        max_power = load_dict[name]['max_power']
        load = [item * random.uniform(0.8, 1.1) * max_power / 100 for item in profile]
        load_list.extend(load)
    new_df = pd.DataFrame.from_dict({f"{name}": load_list})
    df = pd.concat([df, new_df], axis=1)

# Create a time column measured in seconds
time = [(i+1) * int(SEC_INTERVAL) for i in range(NB_STEPS)]
time_df = pd.DataFrame.from_dict({"Time": time})

# Concatenate time column with the data
final_df = pd.concat([time_df, df], axis=1)

# Row 1: Column Names (Time, followed by each zone)
# Row 2: Description (example: start time for the start date for Time, and "load" for others)
# Row 3: Units ("s" for time, "MW" for loads)
# Row 4: TRUE/FALSE flags (all "true" in this example)
header1 = list(final_df.columns.values)
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
