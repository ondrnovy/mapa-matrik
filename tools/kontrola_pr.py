"""Kontrola pull requestu: python3 tools/kontrola_pr.py <base> <head> [autor]

Čte jen data (git show), kód z pull requestu nespouští. Hlídá jen to, aby PR nerozbil mapu;
obsah bodů a poznámek nehodnotí. Výsledek:
  0 = smí se sloučit automaticky (přidání i opravy dat)
  1 = chyba (formát), PR se neslučuje
  2 = potřeba člověka (soubory mimo data/, smazaná kniha, ubývají body, cizí `by`)
"""
import json
import pathlib
import subprocess
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kontrola import check


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def read(ref, path):
    try:
        return json.loads(git("show", f"{ref}:{path}"))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def key(item):
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    base, head = argv[1], argv[2]
    author = argv[3] if len(argv) > 3 else None
    errors, human, added = [], [], 0
    for line in git("diff", "--name-status", "--no-renames", f"{base}...{head}").splitlines():
        status, path = line.split("\t", 1)
        p = pathlib.PurePosixPath(path)
        if p.parts[0] != "data" or p.suffix != ".json" or len(p.parts) != 3:
            human.append(f"{path}: změna mimo data/<archiv>/<id>.json")
            continue
        if status == "D":
            human.append(f"{path}: smazaná kniha")
            continue
        new = read(head, path)
        if not isinstance(new, dict):
            errors.append(f"{path}: není platný JSON objekt")
            continue
        errors += [f"{path}: {e}" for e in check(p, new)]
        old = read(base, path) or {}
        old_points = old.get("points") or []
        new_points = new.get("points") or []
        if len(new_points) < len(old_points):
            human.append(f"{path}: ubývají body ({len(old_points)} → {len(new_points)})")
        old_keys = {key(x) for x in old_points}
        fresh = [x for x in new_points if key(x) not in old_keys]
        added += len(fresh)
        if author:
            before = Counter(x.get("by") for x in old_points)
            for by, n in Counter(x.get("by") for x in new_points).items():
                if by and by != author and n > before[by]:
                    human.append(f"{path}: přibyly body za cizí účet by={by!r} (autor PR je {author})")
    for e in errors:
        print(f"CHYBA {e}")
    for h in human:
        print(f"KE KONTROLE {h}")
    print(f"nových nebo upravených bodů: {added}")
    if errors:
        return 1
    if human:
        return 2
    print("OK: lze sloučit automaticky")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
