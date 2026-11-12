"""Společné načítání map svazků a výpočet odhadu snímku."""
import json
import pathlib
import re

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
TYPES = {"N", "O", "Z", "iN", "iO", "iZ", "title", "blank"}
POINT_KEYS = {"scan", "type", "year", "year_to", "months", "page", "place", "letters", "note", "by"}
VOLUME_KEYS = {"schema", "archive", "portal", "portal_id", "url", "scan_url", "signature", "parish", "district",
               "places", "place_codes", "aliases", "records", "scans", "language", "order", "index", "points", "sections", "notes", "sources"}
WEB = "https://ondrnovy.github.io/mapa-matrik/v1"
RUIAN = pathlib.Path(__file__).resolve().parent.parent / "ciselniky" / "ruian_casti_obci.tsv"
_ruian = None


def load():
    for path in sorted(DATA.glob("*/*.json")):
        with open(path, encoding="utf-8") as f:
            yield path, json.load(f)


def years(text):
    """'1778–1817' -> (1778, 1817)."""
    nums = [int(n) for n in re.findall(r"\d{4}", text or "")]
    return (min(nums), max(nums)) if nums else None


def norm(text):
    table = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")
    return (text or "").lower().translate(table)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-")


def scan_link(vol, scan):
    if vol.get("scan_url"):
        return vol["scan_url"].replace("{scan}", str(scan))
    return f'{vol["url"]} (snímek {scan})'


def point_by(vol, point):
    if point.get("by"):
        return point["by"]
    sources = vol.get("sources") or [{}]
    return sources[0].get("by")


def mark_verified(vol):
    """Bod je ověřený, když stejný snímek, druh, rok a ves zapsali aspoň dva různí přispěvatelé."""
    groups = {}
    for p in vol.get("points") or []:
        key = (p.get("scan"), p.get("type"), p.get("year"), p.get("place"))
        groups.setdefault(key, set()).add(point_by(vol, p))
    for p in vol.get("points") or []:
        key = (p.get("scan"), p.get("type"), p.get("year"), p.get("place"))
        p["verified"] = len(groups[key]) >= 2
    return vol


def place_names(vol):
    """Obce knihy včetně jiných názvů (německé, historické) z pole aliases."""
    names = list(vol.get("places") or [])
    for alts in (vol.get("aliases") or {}).values():
        names += alts
    return names


def ruian():
    """Části obcí z RÚIAN: {kód: {kod, nazev, obec, obec_kod, okres}} (ciselniky/ruian_casti_obci.tsv)."""
    global _ruian
    if _ruian is None:
        _ruian = {}
        if RUIAN.exists():
            lines = RUIAN.read_text(encoding="utf-8").splitlines()
            head = lines[0].split("\t")
            for line in lines[1:]:
                row = dict(zip(head, line.split("\t")))
                row["kod"], row["obec_kod"] = int(row["kod"]), int(row["obec_kod"])
                _ruian[row["kod"]] = row
    return _ruian


def place_info(vol, name):
    """Obec knihy podle názvu nebo jiného názvu: {name, kod, obec, okres}; bez kódu okres knihy."""
    own = next((p for p in vol.get("places") or [] if norm(p) == norm(name)), None)
    if own is None:
        own = next((p for p, alts in (vol.get("aliases") or {}).items() if norm(name) in map(norm, alts)), name)
    info = {"name": own}
    code = (vol.get("place_codes") or {}).get(own)
    row = ruian().get(code)
    if row:
        info.update(kod=code, obec=row["obec"], okres=row["okres"])
    elif code:
        info["kod"] = code
    if "okres" not in info and vol.get("district"):
        info["okres"] = vol["district"]
    return info


def resolve_place(vol, place):
    """Kód RÚIAN (číslo) → název obce v knize; jinak název beze změny."""
    if str(place or "").isdigit():
        return next((p for p, c in (vol.get("place_codes") or {}).items() if c == int(place)), place)
    return place


def in_district(vol, place, okres):
    return not okres or norm(place_info(vol, resolve_place(vol, place)).get("okres")) == norm(okres)


def covers(vol, place, year, kind):
    if place and norm(place) not in [norm(p) for p in place_names(vol)]:
        return False
    for k, span in (vol.get("records") or {}).items():
        if kind and k.lstrip("i") != kind:
            continue
        y = years(span)
        if y and y[0] <= year <= y[1]:
            return True
    return False


def relevant_points(vol, place, kind):
    pts = [p for p in vol.get("points") or [] if p.get("year") and (not kind or p.get("type") == kind)]
    if vol.get("order", "").startswith("by_village") and place:
        local = [p for p in pts if norm(p.get("place")) == norm(place)]
        if local:
            return local, True
    return pts, False


def estimate(pts, year):
    before = [p for p in pts if p["year"] <= year]
    after = [p for p in pts if p.get("year_to", p["year"]) >= year]
    exact = [p for p in pts if p["year"] <= year <= p.get("year_to", p["year"])]
    if exact:
        return min(p["scan"] for p in exact), max(p["scan"] for p in exact), "přímo z bodu"
    if before and after:
        a = max(before, key=lambda p: (p["year"], p["scan"]))
        b = min(after, key=lambda p: (p["year"], p["scan"]))
        if b["year"] != a["year"]:
            s = a["scan"] + (year - a["year"]) * (b["scan"] - a["scan"]) / (b["year"] - a["year"])
            return round(s), round(s), f"odhad mezi sn. {a['scan']} ({a['year']}) a {b['scan']} ({b['year']})"
    return None


def report(volumes, place, year, kind):
    """Text odpovědi na „kde hledat obec, rok, druh“ nad seznamem svazků."""
    out = []
    asked = place
    districts = sorted({place_info(v, resolve_place(v, place)).get("okres") or "?" for v in volumes})
    if place and len(districts) > 1:
        out.append(f"⚠ {place} je v mapě ve více okresech ({', '.join(districts)}) – u každé knihy je okres; "
                   f"upřesni okres nebo hledej podle kódu RÚIAN")
    for vol in volumes:
        place = resolve_place(vol, asked)
        if not covers(vol, place, year, kind):
            continue
        info = place_info(vol, place) if place else {}
        rec = ", ".join(f"{k} {v}" for k, v in vol["records"].items())
        where = f"; {info['name']}, okres {info['okres']}" if info.get("okres") else ""
        out.append(f"\n{vol['signature']} ({vol['archive']}, {vol['portal']} {vol['portal_id']}{where}) – {rec}")
        out.append(f"  uspořádání: {vol.get('order', '?')}; snímků: {vol.get('scans', '?')}")
        if vol.get("index"):
            out.append(f"  rejstřík: {vol['index']}")
        pts, local = relevant_points(vol, place, kind)
        if not vol.get("points"):
            out.append("  orientační body zatím nejsou (kniha je jen z katalogu archivu) – po přečtení snímku zapiš bod")
        if vol.get("order", "").startswith("by_village") and not local:
            out.append(f"  ⚠ kniha je po vsích a oddíl {place} v mapě zatím není – odhad podle jiných vsí nemá smysl")
            pts = []
        for s in vol.get("sections") or []:
            if not place or norm(s.get("place")) == norm(place):
                out.append(f"  oddíl: {s}")
        near = sorted(pts, key=lambda p: abs(p["year"] - year))[:4]
        for p in sorted(near, key=lambda p: p["scan"]):
            extra = " ".join(f"{k}={v}" for k, v in p.items() if k not in ("scan", "type", "year", "verified", "by"))
            mark = " ✓ověřený" if p.get("verified") else ""
            out.append(f"  bod: sn. {p['scan']} = {p.get('type')} {p['year']} {extra}{mark}")
        est = estimate(pts, year)
        if est:
            lo, hi, how = est
            label = f"sn. {lo}" if lo == hi else f"sn. {lo}–{hi}"
            out.append(f"  → začni na {label} ({how}): {scan_link(vol, lo)}")
        else:
            out.append(f"  kniha: {vol['url']}")
        for n in vol.get("notes") or []:
            out.append(f"  pozn.: {n}")
    if not any(line.startswith("\n") for line in out):
        return f"Žádná kniha v mapě nepokrývá {asked} {year} {kind or ''}. (Mapa je zatím malá – přidej ji.)"
    return "\n".join(out).lstrip("\n")
