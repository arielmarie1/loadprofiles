# Creates a PERSEE readable file for sensitivity analysis based on the results of the legacy scenario
import pandas as pd
import os

location_names = ["HS", "HW", "HWS", "LWS", "MWS"]
duration = ["01Y", "10Y"]
TARGETS = ["CO2_Constraint", "FuelLogistics_Constraint", "LandFootprint_Constraint"]
PERC_LABELS = [
    ("PERC100", 1.0),
    ("PERC090", 0.9),
    ("PERC080", 0.8),
    ("PERC070", 0.7),
    ("PERC060", 0.6),
    ("PERC050", 0.5),
    ("PERC040", 0.4),
    ("PERC030", 0.3),
    ("PERC020", 0.2),
    ("PERC010", 0.1),
    ("PERC005", 0.05),
    ("PERC000", 0.0),
]


def load_plan(path, targets: list[str]):
    df = pd.read_csv(path, sep=";")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    found = {}
    for t in targets:
        series = df.loc[(df["Model"] == t) & (df["Indicator"] == "Subobjective"), "Value"]
        found[t] = float(series.iloc[0])
    return found


def write_sen_analysis(target: str, value: float):
    rows = []
    for label, percent in PERC_LABELS:
        scaled = round(value * percent, -1)
        min_val = 0 if percent == 0 or label == "PERC000" else (scaled - 10)
        row = [label, int(scaled), int(min_val)]
        rows.append(row)

    col1 = ""
    col2 = f"{target}__paramListJson__MaxConstraintBusValue"
    col3 = f"{target}__paramListJson__MinConstraintBusValue"

    df_out = pd.DataFrame(rows, columns=[col1, col2, col3])
    return df_out


legacy_folder = "legacy_files"
output_folder = "tab_ech"
os.makedirs(output_folder, exist_ok=True)

for year in duration:
    for location in location_names:
        file_name = f'0_{year}_{location}_W_NA_results_PLAN.csv'
        src_path = os.path.join(legacy_folder, file_name)
        values = load_plan(src_path, TARGETS)
        print(f"\n==={file_name}===")
        for target in TARGETS:
            v = values.get(target)
            print(f"{target}: {v:g}")

            df_out = write_sen_analysis(target, v)
            out_filename = f"{location}_{target}_tabech.csv"
            out_path = os.path.join(output_folder, out_filename)
            df_out.to_csv(out_path, sep=";", index=False)
            print(f"[OK] Wrote {out_filename}")
