"""Offline tests: no network. Run with
uv run --with pytest --with mcp --with httpx pytest plugins/property-contacts/mcp/tests -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import property_data_server as s  # noqa: E402


def test_lot_number_is_not_street_number():
    p = s.parse_address("Lot 3673 Hookes Street, Riverlea Park SA 5120")
    assert p["lot"] == "3673" and p["street_number"] is None
    assert p["state"] == "SA" and p["postcode"] == "5120"
    assert "Lot" not in s._geocode_query(p)


def test_number_range_and_level():
    p = s.parse_address("Level 14, 96-100 King William St, Adelaide SA 5000")
    assert p["level"] == "14" and p["number_range"] == [96, 100]
    assert "Level" not in s._geocode_query(p)


def test_slash_unit():
    p = s.parse_address("W1509/2 Chippendale Way, Chippendale NSW 2008")
    assert p["unit"] == "W1509" and p["street_number"] == "2"
    assert s._geocode_query(p).startswith("2 Chippendale Way")


def test_plain_address():
    p = s.parse_address("100 King William St, Adelaide SA 5000")
    assert p["street_number"] == "100" and p["number_range"] is None


def _m(abn, name, score, pc="5000", st="SA", status="Active"):
    return {"Abn": abn, "Name": name, "Score": score, "Postcode": pc, "State": st, "AbnStatus": status, "IsCurrent": True}


def test_single_match_after_postcode_filter_is_assigned():
    ms = [_m("1", "DW Fox Tucker", 100), _m("2", "DW Fox", 90, pc="4207", st="QLD")]
    assert s.choose_abn_match(ms, "5000", None)["Abn"] == "1"


def test_many_similar_matches_are_ambiguous():
    ms = [_m(str(i), f"Walker {i}", 92 - i) for i in range(6)]
    assert s.choose_abn_match(ms, None, None) is None


def test_clear_winner_assigned():
    ms = [_m("1", "Exact Pty Ltd", 100), _m("2", "Exact-ish", 80)]
    assert s.choose_abn_match(ms, None, None)["Abn"] == "1"


def test_cancelled_ignored():
    ms = [_m("1", "Old Co", 100, status="Cancelled"), _m("2", "Old Co", 99)]
    assert s.choose_abn_match(ms, None, None)["Abn"] == "2"


def test_abr_without_guid_explains(monkeypatch):
    monkeypatch.delenv("ABR_GUID", raising=False)
    r = s.abn_search("Anything")
    assert r["assigned"] is None and "ABR_GUID" in r["error"]


def test_same_number_handles_ranges():
    assert s._same_number("100", "100")
    assert s._same_number("96-100", "100")
    assert not s._same_number("108-118", "100")
    assert not s._same_number("82", "100")
