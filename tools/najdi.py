"""Kde hledat: python3 tools/najdi.py <obec | kód RÚIAN> <rok> [N|O|Z] [--okres=Rakovník] [--web]
            python3 tools/najdi.py <obec | kód RÚIAN> [rok] --cp=74 | --druh=census|chronicle|land_book

Matriky: knihy, které obec a rok pokrývají, nejbližší orientační body a odhad snímku.
Odhad je lineární interpolace mezi dvěma nejbližšími body téhož druhu (a téže vsi, je-li kniha po vsích).
S --cp nebo --druh další knihy obce (sčítání lidu, kroniky, pozemkové knihy): odhad snímku podle čísla domu nebo roku.
Bez --web čte místní data repozitáře, s --web zveřejněnou mapu (MAPA_MATRIK_URL).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from klient import source
from mapa import report, report_sources


def main(argv):
    web = "--web" in argv
    opts = dict(a[2:].split("=", 1) for a in argv[1:] if a.startswith("--") and "=" in a)
    args = [a for a in argv[1:] if not a.startswith("--")]
    sources = "cp" in opts or "druh" in opts
    if len(args) < (1 if sources else 2):
        print(__doc__)
        return 2
    place = args[0]
    year = int(args[1]) if len(args) > 1 else None
    volumes = source("web" if web else "local").volumes(place, opts.get("okres"))
    if sources:
        house = int(opts["cp"]) if "cp" in opts else None
        print(report_sources(volumes, place, year, house, opts.get("druh")))
    else:
        print(report(volumes, place, year, args[2] if len(args) > 2 else None))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
