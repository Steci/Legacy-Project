from .disk_storage import DiskStorage
from .database import Database

class DatabaseDriver:
    def __init__(self, db_path: str):
        self.path = db_path
        self.storage = DiskStorage(db_path)
        self.db = Database()

    def open(self):
        self.storage.load()
        self.db.load_from_storage(self.storage)

    def get(self, key):
        return self.db.get(key)

    def set(self, key, value):
        self.db.set(key, value)
        self.storage.save(self.db)

    def close(self):
        self.storage.close()
