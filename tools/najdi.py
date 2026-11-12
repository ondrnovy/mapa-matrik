"""Kde hledat zápis: python3 tools/najdi.py <obec | kód RÚIAN> <rok> [N|O|Z] [--okres=Rakovník] [--web]

Vypíše knihy, které obec a rok pokrývají, nejbližší orientační body a odhad snímku.
Odhad je lineární interpolace mezi dvěma nejbližšími body téhož druhu (a téže vsi, je-li kniha po vsích).
Bez --web čte místní data repozitáře, s --web zveřejněnou mapu (MAPA_MATRIK_URL).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from klient import source
from mapa import report


def main(argv):
    web = "--web" in argv
    okres = next((a.split("=", 1)[1] for a in argv if a.startswith("--okres=")), None)
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    place, year = args[0], int(args[1])
    kind = args[2] if len(args) > 2 else None
    print(report(source("web" if web else "local").volumes(place, okres), place, year, kind))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
