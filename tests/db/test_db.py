import pickle
import tempfile
from pathlib import Path

from src.db import (
    Database,
    DatabaseGC,
    DiskStorage,
    DatabaseDriver,
    serialize_int,
    deserialize_int
)
def test_database_set_and_get():
    db = Database()
    db.set("name", "Myu")
    assert db.get("name") == "Myu"

def test_database_delete():
    db = Database()
    db.set("key", "value")
    db.delete("key")
    assert db.get("key") is None

def test_database_load_from_storage():
    class DummyStorage:
        data = {"a": 123, "b": "ok"}
    db = Database()
    db.load_from_storage(DummyStorage)
    assert db.get("a") == 123
    assert db.get("b") == "ok"

def test_database_gc_removes_none_entries():
    db = Database()
    db.set("alive", 1)
    db.set("dead", None)
    gc = DatabaseGC(db)
    removed = gc.collect()
    assert removed == ["dead"]
    assert "dead" not in db.data
    assert "alive" in db.data


def test_diskstorage_save_and_load(tmp_path):
    path = tmp_path / "data.pkl"
    storage = DiskStorage(path)
    data = {"x": 42, "y": "test"}
    storage.save(data)

    new_storage = DiskStorage(path)
    new_storage.load()
    assert new_storage.data == data


def test_diskstorage_load_invalid_file(tmp_path):
    path = tmp_path / "data.pkl"
    path.write_text("not a pickle file")

    storage = DiskStorage(path)
    storage.load()
    assert storage.data == {}


def test_diskstorage_load_empty_file(tmp_path):
    path = tmp_path / "empty.pkl"
    path.touch()
    storage = DiskStorage(path)
    storage.load()
    assert storage.data == {}


def test_database_driver_open_and_get_set(tmp_path):
    path = tmp_path / "driver.db"
    driver = DatabaseDriver(path)
    driver.open()

    driver.set("score", 99)
    assert path.exists()

    val = driver.get("score")
    assert val == 99
    driver.close()


def test_serialize_and_deserialize_int():
    value = 1337
    data = serialize_int(value)
    restored = deserialize_int(data)
    assert restored == value
    assert isinstance(data, bytes)
    assert len(data) == 4

def test_load_empty_file_triggers_empty_data():
    with tempfile.NamedTemporaryFile() as tmp:
        storage = DiskStorage(tmp.name)
        storage.load()
        assert storage.data == {}

def test_load_nonexistent_file_triggers_empty_data():
    storage = DiskStorage("/tmp/does_not_exist.db")
    storage.load()
    assert storage.data == {}

def test_load_corrupted_file_triggers_exception():
    with tempfile.NamedTemporaryFile("wb") as tmp:
        tmp.write(b"not a pickle")
        tmp.flush()
        storage = DiskStorage(tmp.name)
        storage.load()
        assert storage.data == {}

def test_load_non_dict_pickle_triggers_warning(capsys):
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        pickle.dump([1, 2, 3], tmp)
        tmp.flush()
        filepath = tmp.name

    storage = DiskStorage(filepath)
    storage.load()
    captured = capsys.readouterr()
    assert "contained invalid data" in captured.out
    assert storage.data == {}
