"""Kontrola formátu map svazků: python3 tools/kontrola.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mapa import KINDS, POINT_KEYS, TYPES, VOLUME_KEYS, kind_of, load, norm, ruian, years

REQUIRED = ["schema", "archive", "portal", "portal_id", "url", "signature", "parish", "points", "sources"]
ORDERS = {"chronological", "by_village", "by_village_bride", "mixed"}


def check(path, vol):
    errors = []
    for key in REQUIRED:
        if key not in vol:
            errors.append(f"chybí pole {key}")
    for key in set(vol) - VOLUME_KEYS:
        errors.append(f"neznámé pole {key}")
    if vol.get("schema") != 1:
        errors.append("schema musí být 1")
    if path.stem != str(vol.get("portal_id")):
        errors.append(f"název souboru {path.stem} ≠ portal_id {vol.get('portal_id')}")
    if path.parent.name != vol.get("archive"):
        errors.append(f"složka {path.parent.name} ≠ archive {vol.get('archive')}")
    vkind = kind_of(vol)
    if vkind not in KINDS:
        errors.append(f"neznámé kind {vkind} (jen {', '.join(sorted(KINDS))})")
    if vkind == "register" and "records" not in vol:
        errors.append("chybí pole records")
    if vkind != "register" and vol.get("records"):
        errors.append("records patří jen matrikám; u jiných knih roky do years")
    if vkind != "register" and not years(vol.get("years")):
        errors.append("chybí nebo je špatně years (např. \"1921\" nebo \"1877–1970\")")
    if vol.get("order") and vol["order"] not in ORDERS:
        errors.append(f"neznámé order {vol['order']}")
    aliases = vol.get("aliases") or {}
    if not isinstance(aliases, dict):
        errors.append("aliases musí být objekt {obec: [jiné názvy]}")
        aliases = {}
    for place, alts in aliases.items():
        if place not in (vol.get("places") or []):
            errors.append(f"aliases: obec {place} není v places")
        if not isinstance(alts, list) or not all(isinstance(a, str) and a for a in alts):
            errors.append(f"aliases: {place} musí mít seznam názvů")
    codes = vol.get("place_codes") or {}
    if not isinstance(codes, dict):
        errors.append("place_codes musí být objekt {obec: kód části obce RÚIAN}")
        codes = {}
    for place, code in codes.items():
        if place not in (vol.get("places") or []):
            errors.append(f"place_codes: obec {place} není v places")
        if not isinstance(code, int) or isinstance(code, bool):
            errors.append(f"place_codes: {place} musí mít číselný kód")
        elif ruian() and code not in ruian():
            errors.append(f"place_codes: {place} – kód {code} v RÚIAN není (tools/ruian.py hledej {place})")
        elif ruian() and norm(ruian()[code]["nazev"]) != norm(place):
            errors.append(f"place_codes: {place} – kód {code} patří k {ruian()[code]['nazev']}")
    for kind, span in (vol.get("records") or {}).items():
        if kind not in TYPES or not years(span):
            errors.append(f"records: špatně {kind}: {span}")
    scans = vol.get("scans")
    seen = set()
    for p in vol.get("points") or []:
        s = p.get("scan")
        if not isinstance(s, int) or s < 1 or (scans and s > scans):
            errors.append(f"bod se špatným snímkem: {p}")
        for key in set(p) - POINT_KEYS:
            errors.append(f"bod s neznámým polem {key}: {p}")
        if p.get("type") and p["type"] not in TYPES:
            errors.append(f"bod s neznámým typem: {p}")
        if vkind != "register" and p.get("type") not in (None, "title", "blank"):
            errors.append(f"bod mimo matriku smí mít type jen title nebo blank: {p}")
        for key, size in (("house", 20), ("topic", 80)):
            if key in p and (not isinstance(p[key], str) or not p[key].strip() or len(p[key]) > size):
                errors.append(f"{key} musí být krátký text (nejvýš {size} znaků): {p}")
        if p.get("year_to") and p.get("year") and p["year_to"] < p["year"]:
            errors.append(f"year_to < year: {p}")
        key = (s, p.get("type"), p.get("year"), p.get("place"), p.get("house"), p.get("topic"), p.get("by"))
        if key in seen:
            errors.append(f"bod je dvakrát: {p}")
        seen.add(key)
    return errors


def main():
    total = bad = points = 0
    for path, vol in load():
        total += 1
        points += len(vol.get("points") or [])
        for e in check(path, vol):
            bad += 1
            print(f"{path.relative_to(path.parent.parent.parent)}: {e}")
    print(f"{total} svazků, {points} orientačních bodů, {bad} chyb")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
