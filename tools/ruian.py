"""Kódy obcí z RÚIAN: python3 tools/ruian.py nacti|hledej|dopln

  nacti <složka>        z číselníků ČÚZK (UI_CAST_OBCE.csv, UI_OBEC.csv, UI_OKRES.csv, kódování cp1250) sestaví
                        ciselniky/ruian_casti_obci.tsv; číselníky: https://services.cuzk.cz/sestavy/cis/<název>.zip
  hledej <název>        části obcí toho jména s obcí a okresem
  dopln [--zapsat]      navrhne place_codes knihám, které je nemají: jen část obce v okrese knihy, fary nebo
                        ostatních vsí (víc takových → ta z obce ostatních vsí); s --zapsat je zapíše,
                        ostatní vypíše s kandidáty k ručnímu doplnění

Kód je kód části obce (ves, osada), ne obce: farní knihy počítají po vsích a obec jich má často několik.
"""
import csv
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mapa import RUIAN, load, norm, ruian


def nacti(folder):
    folder = pathlib.Path(folder)

    def rows(name):
        with open(folder / name, encoding="cp1250", newline="") as f:
            return [r for r in csv.DictReader(f, delimiter=";") if not r["PLATI_DO"]]

    okresy = {r["KOD"]: r["NAZEV"] for r in rows("UI_OKRES.csv")}
    obce = {r["KOD"]: r for r in rows("UI_OBEC.csv")}
    out = []
    for r in rows("UI_CAST_OBCE.csv"):
        obec = obce[r["OBEC_KOD"]]
        out.append((int(r["KOD"]), r["NAZEV"], obec["NAZEV"], int(obec["KOD"]), okresy[obec["OKRES_KOD"]]))
    RUIAN.parent.mkdir(exist_ok=True)
    with open(RUIAN, "w", encoding="utf-8", newline="") as f:
        f.write("kod\tnazev\tobec\tobec_kod\tokres\n")
        for row in sorted(out):
            f.write("\t".join(map(str, row)) + "\n")
    print(f"{RUIAN}: {len(out)} částí obcí")


def candidates(name):
    return [c for c in ruian().values() if norm(c["nazev"]) == norm(name)]


def hledej(name):
    for c in candidates(name):
        print(f"{c['kod']}\t{c['nazev']}\tobec {c['obec']}\tokres {c['okres']}")


def choose(name, districts, obce):
    """Kandidát v okrese knihy (fary, ostatních vsí); víc v okrese → ten z obce ostatních vsí knihy."""
    cands = candidates(name)
    for district in districts:
        local = [c for c in cands if c["okres"] == district]
        if len(local) > 1:
            local = [c for c in local if c["obec"] in obce]
        if len(local) == 1:
            return local[0], None
    if not districts and len(cands) == 1:
        return cands[0], None
    return None, cands


def with_codes(vol, codes):
    """Kniha s place_codes hned za places, v pořadí places."""
    out = {}
    for k, v in vol.items():
        if k != "place_codes":
            out[k] = v
        if k == "places":
            out["place_codes"] = {p: codes[p] for p in vol["places"] if p in codes}
    return out


def write_codes(path, vol, codes):
    path.write_text(json.dumps(with_codes(vol, codes), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def suggest(vol):
    """Kódy pro obce knihy bez kódu: {obec: kód} (jen jednoznačné) a seznam nedořešených obcí."""
    codes = dict(vol.get("place_codes") or {})
    missing = [p for p in vol.get("places") or [] if p not in codes]
    known = Counter(ruian()[k]["okres"] for k in codes.values() if k in ruian())
    obce = {ruian()[k]["obec"] for k in codes.values() if k in ruian()}
    parish = [c["okres"] for c in candidates(vol.get("parish") or "")]
    changed = True
    while changed:
        changed = False
        districts = [vol.get("district")] + [d for d, _ in known.most_common()]
        if len(parish) == 1 or vol.get("district") in parish:
            districts.append(vol.get("district") if vol.get("district") in parish else parish[0])
        districts = list(dict.fromkeys(d for d in districts if d))
        for place in [p for p in missing if p not in codes]:
            hit, _ = choose(place, districts, obce)
            if hit:
                codes[place] = hit["kod"]
                known[hit["okres"]] += 1
                obce.add(hit["obec"])
                changed = True
    return codes, [p for p in missing if p not in codes]


def dopln(write):
    unresolved = 0
    for path, vol in load():
        old = vol.get("place_codes") or {}
        codes, left = suggest(vol)
        for place in vol.get("places") or []:
            if place in codes and place not in old:
                c = ruian()[codes[place]]
                print(f"{path.parent.name}/{path.stem}: {place} → {c['kod']} ({c['obec']}, {c['okres']})")
        for place in left:
            unresolved += 1
            opts = "; ".join(f"{c['kod']} {c['obec']}, {c['okres']}" for c in candidates(place)) or "v RÚIAN není"
            print(f"{path.parent.name}/{path.stem}: {place} ?? {opts}")
        if write and codes != old:
            write_codes(path, vol, codes)
    print(f"nejednoznačných nebo nenalezených: {unresolved}")


def main(argv):
    if len(argv) >= 3 and argv[1] == "nacti":
        nacti(argv[2])
    elif len(argv) >= 3 and argv[1] == "hledej":
        hledej(" ".join(argv[2:]))
    elif len(argv) >= 2 and argv[1] == "dopln":
        dopln("--zapsat" in argv)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
