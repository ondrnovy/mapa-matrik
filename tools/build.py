"""Sestaví statické „API“ pro GitHub Pages: python3 tools/build.py <výstupní složka>

<výstup>/v1/index.json            přehled (počty, archivy, seznam obcí)
<výstup>/v1/obce/<obec>.json      svazky, které obec pokrývají (odkazy na svazky)
<výstup>/v1/svazky/<archiv>/<id>.json   celý svazek s příznakem verified u bodů
"""
import datetime
import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mapa import kind_of, load, mark_verified, place_info, place_names, slug

PAGE = """<!doctype html>
<html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa matrik</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 16px;background:#fff;color:#222}
code{background:#f2f2f2;padding:0 .2em}@media (prefers-color-scheme: dark){body{background:#151515;color:#ddd}code{background:#2a2a2a}}</style>
</head><body>
<h1>Mapa matrik</h1>
<p>Otevřená mapa naskenovaných matričních knih: který snímek je který rok, ves a strana. Nově i další knihy
(sčítání lidu, kroniky, pozemkové knihy): který snímek je které číslo domu nebo rok. Data pro AI agenty i lidi.</p>
<ul>
<li><code>v1/index.json</code> – přehled a seznam obcí</li>
<li><code>v1/obce/&lt;obec&gt;.json</code> – knihy pro obec (malá písmena bez diakritiky, mezery jako pomlčky, např. <code>v1/obce/krakov.json</code>)</li>
<li><code>v1/svazky/&lt;archiv&gt;/&lt;id&gt;.json</code> – orientační body knihy</li>
</ul>
<p>Svazků: VOLUMES, orientačních bodů: POINTS. Sestaveno BUILT. Licence dat CC0.</p>
</body></html>
"""


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = pathlib.Path(argv[1])
    if out.exists():
        shutil.rmtree(out)
    v1 = out / "v1"
    places = {}
    codes = {}
    archives = {}
    kinds = {}
    volumes = points = 0
    for path, vol in load():
        mark_verified(vol)
        rel = f"svazky/{vol['archive']}/{vol['portal_id']}.json"
        target = v1 / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(vol, ensure_ascii=False, indent=1), encoding="utf-8")
        volumes += 1
        points += len(vol.get("points") or [])
        archives[vol["archive"]] = archives.get(vol["archive"], 0) + 1
        ref = {k: vol[k] for k in ("kind", "archive", "portal_id", "signature", "parish", "district", "records",
                                   "years", "order", "scans") if vol.get(k) is not None}
        kinds[kind_of(vol)] = kinds.get(kind_of(vol), 0) + 1
        ref["points"] = len(vol.get("points") or [])
        ref["path"] = rel
        for key in dict.fromkeys(slug(p) for p in place_names(vol)):
            name = next(p for p in place_names(vol) if slug(p) == key)
            info = place_info(vol, name)
            entry = places.setdefault(key, {"name": name, "volumes": []})
            entry["volumes"].append({**ref, "place": info})
            if info.get("kod"):
                codes.setdefault(info["kod"], {**info, "volumes": []})
                if ref not in codes[info["kod"]]["volumes"]:
                    codes[info["kod"]]["volumes"].append(ref)
    for key, entry in places.items():
        target = v1 / "obce" / f"{key}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(entry["volumes"], ensure_ascii=False, indent=1), encoding="utf-8")
    for code, entry in codes.items():
        target = v1 / "obce" / "kod" / f"{code}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(entry["volumes"], ensure_ascii=False, indent=1), encoding="utf-8")
    built = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    index = {"schema": 1, "built": built, "volumes": volumes, "points": points, "archives": archives, "kinds": kinds,
             "places": {k: e["name"] for k, e in sorted(places.items())},
             "codes": {str(k): {f: e[f] for f in ("name", "obec", "okres") if f in e} for k, e in sorted(codes.items())}}
    (v1 / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "index.html").write_text(PAGE.replace("VOLUMES", str(volumes)).replace("POINTS", str(points)).replace("BUILT", built), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"{out}: {volumes} svazků, {points} bodů, {len(places)} obcí, {len(codes)} s kódem RÚIAN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
