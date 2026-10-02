import pandas as pd

from py_sascensusapi import sas_backend as mod


class FakeSD:
    def __init__(self, owner):
        self.owner = owner

    def to_df(self):
        self.owner.pulls += 1
        return pd.DataFrame({"a": [1, 2]})


class FakeSAS:
    def __init__(self):
        self.pulls = 0
        self.mod = "100"

    def submit(self, code):
        return {"LOG": "", "LST": ""}

    def symget(self, name):
        return self.mod if "mod" in name else "2"

    def sasdata(self, *a, **k):
        return FakeSD(self)


def make(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DF_CACHE_DIR", tmp_path)
    b = mod.SASBackend()
    b._sas = FakeSAS()
    return b


def test_second_fetch_hits_cache_and_modify_time_invalidates(tmp_path, monkeypatch):
    b = make(tmp_path, monkeypatch)
    b.fetch_dataframe("t", "APILIB")
    b.fetch_dataframe("t", "APILIB")
    assert b._sas.pulls == 1
    b._sas.mod = "200"
    b.fetch_dataframe("t", "APILIB")
    assert b._sas.pulls == 2


def test_disk_cache_survives_new_backend_and_force_refresh_bypasses(tmp_path, monkeypatch):
    b = make(tmp_path, monkeypatch)
    b.fetch_dataframe("t", "APILIB")
    b2 = make(tmp_path, monkeypatch)
    b2.fetch_dataframe("t", "APILIB")
    assert b2._sas.pulls == 0
    b2.fetch_dataframe("t", "APILIB", force_refresh=True)
    assert b2._sas.pulls == 1
