import os
import pickle

class DiskStorage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}

    def load(self):
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            self.data = {}
            return
        with open(self.filepath, 'rb') as f:
            loaded = pickle.load(f)
            # Make sure it’s a dict
            if isinstance(loaded, dict):
                self.data = loaded
            else:
                print(f"Warning: storage file {self.filepath} contained invalid data, resetting.")
                self.data = {}


    def save(self, data):
        with open(self.filepath, 'wb') as f:
            pickle.dump(data, f)

    def close(self):
        pass
