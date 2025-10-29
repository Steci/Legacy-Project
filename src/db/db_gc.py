class DatabaseGC:
    def __init__(self, database):
        self.db = database

    def collect(self):
        removed = []
        for key, val in list(self.db.data.items()):
            if val is None:
                del self.db.data[key]
                removed.append(key)
        return removed
