# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2.3,<3", "httpx>=0.27"]
# ///
"""Property data MCP server: structured lookups for the property-contact-lookup skill.

Tools
- normalise_address: parse lot/unit/level/number ranges locally, then geocode with
  OpenStreetMap Nominatim (free; 1 request/second policy enforced here).
- businesses_at: OpenStreetMap Overpass query for named businesses tagged at or
  near a point (free).
- abn_search / abn_details: official Australian Business Register web services
  (free; needs a registered GUID in the ABR_GUID environment variable).

All tools are read-only, return JSON-serialisable dicts with a "source" and
"retrieved" field, and never guess: missing data comes back as null with a note.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import date
from functools import lru_cache
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

USER_AGENT = os.environ.get(
    "PROPERTY_DATA_USER_AGENT",
    "property-contacts-claude/1.0 (+https://github.com/sara-hamza/property-contacts-claude)",
)
CONTACT_EMAIL = os.environ.get("NOMINATIM_EMAIL", "")  # optional, per Nominatim policy
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URLS = [u.strip() for u in os.environ.get(
    "OVERPASS_URLS",
    "https://overpass.private.coffee/api/interpreter,"
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter,"
    "https://overpass-api.de/api/interpreter,"
    "https://overpass.kumi.systems/api/interpreter",
).split(",") if u.strip()]
PHOTON_URL = os.environ.get("PHOTON_URL", "https://photon.komoot.io/reverse")
ABR_BASE = "https://abr.business.gov.au/json"
ABR_REGISTER_URL = "https://abr.business.gov.au/Tools/WebServices"

mcp = MCPServer(
    "property-data",
    version="1.1.0",
    instructions="Read-only Australian property lookups for the property-contact-lookup skill: "
    "normalise_address -> businesses_at; abn_search / abn_details for every business and managing company.",
)
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
_client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=25.0)
_nominatim_lock = threading.Lock()
_nominatim_last = 0.0


def _today() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------- address parsing

STATES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"}
_LOT = re.compile(r"\blot\s+(\d+[a-z]?)\b", re.I)
_UNIT = re.compile(r"\b(?:unit|apt|apartment|suite|shop)\s*([a-z]?\d+[a-z]?)\b", re.I)
_SLASH_UNIT = re.compile(r"\b([a-z]?\d+[a-z]?)\s*/\s*(\d+[a-z]?)\b", re.I)
_LEVEL = re.compile(r"\b(?:level|lvl|l)\s*(\d+|g|ground)\b", re.I)
_RANGE = re.compile(r"\b(\d+)\s*[-–]\s*(\d+)\b")
_STATE_PC = re.compile(r"\b(NSW|VIC|QLD|SA|WA|TAS|ACT|NT)\s*(\d{4})?\b", re.I)


def parse_address(address: str) -> dict[str, Any]:
    """Pull the parts a geocoder tends to get wrong out of a free-text AU address."""
    text = " ".join(address.split())
    out: dict[str, Any] = {
        "input": text,
        "lot": None,
        "unit": None,
        "level": None,
        "street_number": None,
        "number_range": None,
        "state": None,
        "postcode": None,
        "notes": [],
    }
    if m := _LOT.search(text):
        out["lot"] = m.group(1)
        out["notes"].append(
            "Lot number, not a street number: geocoders match the street only. "
            "Street numbers are assigned by council at titling."
        )
    if m := _LEVEL.search(text):
        out["level"] = m.group(1).upper()
    if m := _UNIT.search(text):
        out["unit"] = m.group(1).upper()
    elif m := _SLASH_UNIT.search(text):
        out["unit"], out["street_number"] = m.group(1).upper(), m.group(2)
    if m := _RANGE.search(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo < hi:
            out["number_range"] = [lo, hi]
            out["street_number"] = out["street_number"] or str(hi)
            out["notes"].append(
                f"Number range {lo}-{hi}: tenants may list either end; search both."
            )
    if out["street_number"] is None and not out["lot"]:
        if m := re.search(r"(?:^|,\s*)(\d+[a-z]?)\s+[A-Za-z]", text):
            out["street_number"] = m.group(1)
    if m := _STATE_PC.search(text):
        out["state"] = m.group(1).upper()
        out["postcode"] = m.group(2)
    return out


def _geocode_query(parsed: dict[str, Any]) -> str:
    """Strip unit/level/lot noise so Nominatim matches the building, not nothing."""
    q = parsed["input"]
    q = _LOT.sub("", q)
    q = _LEVEL.sub("", q)
    q = _UNIT.sub("", q)
    q = _SLASH_UNIT.sub(lambda m: m.group(2), q)
    if parsed["number_range"]:
        q = _RANGE.sub(str(parsed["number_range"][0]), q, count=1)
    q = re.sub(r"^[\s,]+|[\s,]+$", "", re.sub(r"\s*,\s*,", ",", q))
    if "australia" not in q.lower():
        q += ", Australia"
    return q


@lru_cache(maxsize=256)
def _nominatim(query: str) -> list[dict[str, Any]]:
    global _nominatim_last
    with _nominatim_lock:  # Nominatim usage policy: max 1 request per second
        wait = 1.05 - (time.monotonic() - _nominatim_last)
        if wait > 0:
            time.sleep(wait)
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "extratags": 1,
            "namedetails": 1,
            "countrycodes": "au",
            "limit": 3,
        }
        if CONTACT_EMAIL:
            params["email"] = CONTACT_EMAIL
        r = _client.get(NOMINATIM_URL, params=params)
        _nominatim_last = time.monotonic()
    r.raise_for_status()
    return r.json()


@mcp.tool(annotations=READ_ONLY)
def normalise_address(address: str) -> dict[str, Any]:
    """Normalise an Australian address and geocode it.

    Returns the parsed parts (lot, unit, level, number range, state, postcode),
    up to 3 geocoder candidates with coordinates, suburb, building name and OSM
    type, plus notes on traps (lot numbers, number ranges). Use the coordinates
    with businesses_at. Confirm the right candidate before relying on it.
    """
    parsed = parse_address(address)
    query = _geocode_query(parsed)
    try:
        hits = _nominatim(query)
    except httpx.HTTPError as e:
        return {"parsed": parsed, "query": query, "candidates": [], "error": str(e),
                "source": "OpenStreetMap Nominatim", "retrieved": _today()}
    approximate = False
    if not hits and (parsed["lot"] or parsed["postcode"]):
        # New estates / unaddressed lots: fall back to the suburb so callers still get a location.
        parts = [x.strip() for x in query.split(",") if x.strip()]
        suburb_q = ", ".join(parts[1:]) if len(parts) > 2 else query  # drop the street segment
        try:
            hits, approximate = _nominatim(suburb_q), True
        except httpx.HTTPError:
            hits = []
    candidates = []
    for h in hits:
        a = h.get("address", {})
        candidates.append({
            "display_name": h.get("display_name"),
            "building_name": (h.get("namedetails") or {}).get("name") or a.get("building"),
            "house_number": a.get("house_number"),
            "road": a.get("road"),
            "suburb": a.get("suburb") or a.get("locality") or a.get("village") or a.get("town") or ((h.get("namedetails") or {}).get("name") if h.get("category") == "boundary" else None) or a.get("city_district") or a.get("city"),
            "state": a.get("state"),
            "postcode": a.get("postcode"),
            "lat": float(h["lat"]),
            "lon": float(h["lon"]),
            "osm_type": f'{h.get("category")}/{h.get("type")}',
            "osm_url": f'https://www.openstreetmap.org/{h.get("osm_type")}/{h.get("osm_id")}',
        })
    notes = list(parsed["notes"])
    if approximate and candidates:
        notes.append("Exact street not in OpenStreetMap (common in new estates); coordinates are the suburb, not the lot.")
    if not candidates:
        notes.append("No geocoder match. New estates are often missing from OSM; try the street and suburb only.")
    elif parsed["street_number"] and not any(c["house_number"] for c in candidates):
        notes.append("Geocoder matched the street, not the exact number. Treat coordinates as approximate.")
    return {"parsed": parsed, "query": query, "approximate": approximate, "candidates": candidates, "notes": notes,
            "source": "OpenStreetMap Nominatim (ODbL)", "retrieved": _today()}


# ---------------------------------------------------------------- businesses (OSM)

_BUSINESS_KEYS = ("shop", "amenity", "office", "craft", "tourism", "leisure", "healthcare")
_SKIP_AMENITY = {"bench", "waste_basket", "bicycle_parking", "parking", "telephone",
                 "post_box", "drinking_water", "toilets", "vending_machine", "atm",
                 "parking_entrance", "motorcycle_parking", "shelter", "clock", "fountain"}


@lru_cache(maxsize=256)
def _overpass(lat: float, lon: float, radius_m: int) -> tuple[str, list[dict[str, Any]]]:
    """Query public Overpass servers in turn; they are often busy or blocking."""
    filters = "".join(f'nwr(around:{radius_m},{lat},{lon})["name"]["{k}"];' for k in _BUSINESS_KEYS)
    query = f"[out:json][timeout:20];({filters});out center tags 200;"
    errors = []
    for url in OVERPASS_URLS:
        try:
            r = _client.post(url, data={"data": query}, timeout=15.0)
            r.raise_for_status()
            return url, r.json().get("elements", [])
        except (httpx.HTTPError, ValueError) as e:
            errors.append(f"{url}: {e.__class__.__name__} {getattr(getattr(e, 'response', None), 'status_code', '')}".strip())
    raise httpx.HTTPError("; ".join(errors))


@lru_cache(maxsize=256)
def _photon(lat: float, lon: float, radius_m: int) -> list[dict[str, Any]]:
    """Fallback: Photon reverse search returns nearby OSM objects (names and categories, no contacts)."""
    r = _client.get(PHOTON_URL, params={"lat": lat, "lon": lon, "radius": radius_m / 1000, "limit": 40, "lang": "en"},
                    timeout=15.0)
    r.raise_for_status()
    return r.json().get("features", [])


def _addr_line(t: dict[str, str]) -> str | None:
    parts = [t.get("addr:unit") and f'Unit {t["addr:unit"]}', t.get("level") and f'Level {t["level"]}',
             " ".join(filter(None, [t.get("addr:housenumber"), t.get("addr:street")])) or None,
             t.get("addr:suburb") or t.get("addr:city"), t.get("addr:postcode")]
    line = ", ".join(p for p in parts if p)
    return line or None


@mcp.tool(annotations=READ_ONLY)
def businesses_at(lat: float, lon: float, radius_m: int = 35, house_number: str | None = None) -> dict[str, Any]:
    """List named businesses mapped in OpenStreetMap at or near a point.

    Use the lat/lon from normalise_address. radius_m 25-50 suits one building;
    larger picks up neighbours. If house_number is given, results whose OSM
    address has a different house number are flagged "likely_neighbour".
    OSM coverage is volunteer-made: treat each result as a lead to confirm on
    the business's own site (Medium confidence at most on its own).
    """
    radius_m = max(5, min(int(radius_m), 200))
    lat, lon = round(lat, 6), round(lon, 6)
    notes = ["Volunteer-mapped data; confirm each business on its own website or ABN Lookup."]
    try:
        backend, elements = _overpass(lat, lon, radius_m)
        rows = [(el.get("tags", {}), f'https://www.openstreetmap.org/{el["type"]}/{el["id"]}') for el in elements]
        source = f"OpenStreetMap via Overpass ({backend}) (ODbL)"
    except httpx.HTTPError as overpass_err:
        try:
            feats = _photon(lat, lon, radius_m)
        except httpx.HTTPError as e:
            return {"count": 0, "businesses": [], "error": f"Overpass: {overpass_err}; Photon: {e}",
                    "source": "OpenStreetMap", "retrieved": _today()}
        rows = []
        for f in feats:
            pr = f.get("properties", {})
            if pr.get("osm_key") not in _BUSINESS_KEYS or not pr.get("name"):
                continue
            tags = {pr["osm_key"]: pr.get("osm_value"), "name": pr["name"],
                    "addr:housenumber": pr.get("housenumber"), "addr:street": pr.get("street"),
                    "addr:suburb": pr.get("district") or pr.get("city"), "addr:postcode": pr.get("postcode")}
            osm_t = {"N": "node", "W": "way", "R": "relation"}.get(pr.get("osm_type"), "node")
            rows.append(({k: v for k, v in tags.items() if v}, f'https://www.openstreetmap.org/{osm_t}/{pr.get("osm_id")}'))
        source = "OpenStreetMap via Photon (ODbL)"
        notes.append("Overpass servers unavailable, so Photon was used: names and categories only, no phone/website. "
                     "Look those up on each business's own site.")
    seen, out = set(), []
    for t_, url in rows:
        if t_.get("amenity") in _SKIP_AMENITY:
            continue
        key = (t_.get("name", "").lower(), t_.get("addr:housenumber"))
        if key in seen:
            continue
        seen.add(key)
        hn = t_.get("addr:housenumber")
        out.append({
            "name": t_.get("name"),
            "brand": t_.get("brand"),
            "category": next((f"{k}={t_[k]}" for k in _BUSINESS_KEYS if k in t_), None),
            "address": _addr_line(t_),
            "phone": t_.get("phone") or t_.get("contact:phone"),
            "website": t_.get("website") or t_.get("contact:website"),
            "email": t_.get("email") or t_.get("contact:email"),
            "opening_hours": t_.get("opening_hours"),
            "likely_neighbour": bool(house_number and hn and not _same_number(hn, house_number)),
            "osm_url": url,
        })
    out.sort(key=lambda b: (b["likely_neighbour"], b["name"] or ""))
    return {"count": len(out), "radius_m": radius_m, "businesses": out, "notes": notes,
            "source": source, "retrieved": _today()}


def _same_number(osm_number: str, wanted: str) -> bool:
    """'108-118' contains '110'; '100' equals '100'."""
    wanted = str(wanted).strip()
    if m := re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", osm_number.strip()):
        return wanted.isdigit() and int(m.group(1)) <= int(wanted) <= int(m.group(2))
    return osm_number.strip().lower() == wanted.lower()


# ---------------------------------------------------------------- ABN Lookup (ABR)

class AbrError(RuntimeError):
    pass


def _abr(endpoint: str, **params: Any) -> dict[str, Any]:
    guid = os.environ.get("ABR_GUID", "").strip()
    if not guid:
        raise AbrError(
            f"ABR_GUID is not set. Register free at {ABR_REGISTER_URL}, then set ABR_GUID "
            "in your environment and restart Claude. Until then, use ABN Lookup on the web."
        )
    r = _client.get(f"{ABR_BASE}/{endpoint}", params={**params, "guid": guid, "callback": "c"})
    r.raise_for_status()
    body = r.text.strip()
    m = re.fullmatch(r"c\((.*)\)\s*;?", body, re.S)  # ABR returns JSONP
    data = json.loads(m.group(1) if m else body)
    if data.get("Message"):
        raise AbrError(f'ABR: {data["Message"]}')
    return data


def choose_abn_match(matches: list[dict[str, Any]], postcode: str | None, state: str | None) -> dict[str, Any] | None:
    """Decide whether one ABR match is safe to assign, or return None ("ambiguous").

    The skill's rule: never pick one of several similar entities. Default policy:
    keep active, current matches; narrow by postcode then state when given;
    assign only if exactly one remains, or if the top score is >= 95 and beats
    the runner-up by at least 10 points.
    """
    pool = [m for m in matches if m.get("AbnStatus") == "Active" and m.get("IsCurrent", True)]
    if postcode:
        pool = [m for m in pool if str(m.get("Postcode")) == str(postcode)] or pool
    if state:
        pool = [m for m in pool if (m.get("State") or "").upper() == state.upper()] or pool
    if len(pool) == 1:
        return pool[0]
    pool = sorted(pool, key=lambda m: m.get("Score", 0), reverse=True)
    if len(pool) >= 2 and pool[0].get("Score", 0) >= 95 and pool[0]["Score"] - pool[1].get("Score", 0) >= 10:
        return pool[0]
    return None


@mcp.tool(annotations=READ_ONLY)
def abn_search(name: str, postcode: str | None = None, state: str | None = None, max_results: int = 10) -> dict[str, Any]:
    """Search the Australian Business Register by business or entity name.

    Returns ranked matches (ABN, name, name type, status, state, postcode, score)
    and "assigned": the single safe match, or null with a reason when several
    similar entities match. Never assign an ABN the tool marked ambiguous.
    Needs ABR_GUID (free registration).
    """
    try:
        data = _abr("MatchingNames.aspx", name=name, maxResults=max(1, min(max_results, 50)))
    except (AbrError, httpx.HTTPError, ValueError) as e:
        return {"matches": [], "assigned": None, "error": str(e), "source": "ABN Lookup", "retrieved": _today()}
    matches = data.get("Names", [])
    chosen = choose_abn_match(matches, postcode, state)
    return {
        "query": {"name": name, "postcode": postcode, "state": state},
        "matches": [{k: m.get(k) for k in ("Abn", "Name", "NameType", "AbnStatus", "State", "Postcode", "Score")} for m in matches],
        "assigned": chosen and {"abn": chosen["Abn"], "name": chosen["Name"]},
        "assigned_reason": "single safe match" if chosen else (
            "no matches" if not matches else "ambiguous: several similar entities; confirm from the business's own documents"),
        "source": f'ABN Lookup https://abr.business.gov.au/Search/ResultsActive?SearchText={name.replace(" ", "+")}',
        "retrieved": _today(),
    }


@mcp.tool(annotations=READ_ONLY)
def abn_details(abn: str) -> dict[str, Any]:
    """Get ABR details for one ABN: entity name, status and date, entity type,
    GST registration, main business location (state/postcode) and business names.
    Needs ABR_GUID (free registration)."""
    digits = re.sub(r"\D", "", abn)
    if len(digits) != 11:
        return {"error": "An ABN has 11 digits.", "source": "ABN Lookup", "retrieved": _today()}
    try:
        d = _abr("AbnDetails.aspx", abn=digits)
    except (AbrError, httpx.HTTPError, ValueError) as e:
        return {"error": str(e), "source": "ABN Lookup", "retrieved": _today()}
    return {
        "abn": d.get("Abn"), "status": d.get("AbnStatus"), "status_from": d.get("AbnStatusEffectiveFrom"),
        "entity_name": d.get("EntityName"), "entity_type": d.get("EntityTypeName"), "acn": d.get("Acn") or None,
        "gst_registered_from": d.get("Gst"), "state": d.get("AddressState"), "postcode": d.get("AddressPostcode"),
        "business_names": d.get("BusinessName", []),
        "source": f"ABN Lookup https://abr.business.gov.au/ABN/View?abn={digits}", "retrieved": _today(),
    }


if __name__ == "__main__":
    mcp.run()
