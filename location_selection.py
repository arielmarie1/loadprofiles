import pandas as pd


class LocationSelection:
    def __init__(self, filename, sep=","):
        self.filename = filename
        self.sep = sep
        self.locations = self._locations_list()
        pass

    def _locations_list(self):
        try:
            df = pd.read_csv(self.filename, sep=self.sep)
            locations = list(df.itertuples(index=False, name=None))
            return locations
        except Exception as e:
            print(f"Error loading location csv: {e}")
            return None