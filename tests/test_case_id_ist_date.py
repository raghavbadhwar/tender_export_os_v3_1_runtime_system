import datetime as real_dt

import scripts.create_cases_from_deep_source_results as create_cases


class FakeDateTime(real_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 1, 0, 30, tzinfo=tz)


def test_case_id_date_uses_asia_kolkata(monkeypatch) -> None:
    monkeypatch.setattr(create_cases.dt, "datetime", FakeDateTime)
    assert create_cases.today_compact() == "20260701"
    assert create_cases.today_iso() == "2026-07-01"
