import pandas as pd
import os


class LocationSelection:
    def __init__(self, filename, sep=","):
        self.filename = filename
        self.sep = sep
        self._locations_list()
        pass

    def _locations_list(self):
        try:
            location_list = pd.read_csv(self.filename, sep=self.sep)
            print(location_list)
        except Exception as e:
            print(f"Error loading RE data: {e}")
            return None


file_name = 'location_selection_ranking.csv'
out_dir = "locations"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, file_name)
locations = LocationSelection(out_path)
