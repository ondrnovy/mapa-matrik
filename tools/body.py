"""Body nasbírané při práci (lokálně) a jejich odeslání do mapy.

python3 tools/body.py prehled                 co čeká na odeslání
python3 tools/body.py zapis <klon repozitáře>  zapíše body do data/ v klonu (nic neodesílá)
python3 tools/body.py odeslat <klon repozitáře>  zapíše, vytvoří větev, commit, push a pull request (gh)

Body se ukládají do MAPA_MATRIK_BODY, jinak ~/.local/share/mapa-matrik/body.jsonl.
Pole `by` u bodů doplní `odeslat` / `zapis` podle přihlášeného účtu GitHubu (gh api user).
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ruian
from mapa import POINT_KEYS, TYPES

STORE = pathlib.Path(os.environ.get("MAPA_MATRIK_BODY",
                                    pathlib.Path.home() / ".local" / "share" / "mapa-matrik" / "body.jsonl"))
UPSTREAM = "ondrnovy/mapa-matrik"
VOLUME_REQUIRED = ("archive", "portal", "portal_id", "url", "signature", "parish", "records")


def today():
    return datetime.date.today().isoformat()


def append(entry):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def add_point(archive, portal_id, point):
    point = {k: v for k, v in point.items() if v not in (None, "")}
    unknown = set(point) - POINT_KEYS - {"by"}
    if unknown:
        raise ValueError(f"neznámá pole bodu: {sorted(unknown)}")
    if not isinstance(point.get("scan"), int) or point["scan"] < 1:
        raise ValueError("scan musí být kladné celé číslo")
    if point.get("type") and point["type"] not in TYPES:
        raise ValueError(f"type musí být jedno z {sorted(TYPES)}")
    point.pop("by", None)
    append({"archive": archive, "portal_id": str(portal_id), "point": point, "date": today()})
    return point


def add_volume(meta):
    missing = [k for k in VOLUME_REQUIRED if not meta.get(k)]
    if missing:
        raise ValueError(f"chybí pole svazku: {missing}")
    meta = {k: v for k, v in meta.items() if v not in (None, "", [])}
    meta["portal_id"] = str(meta["portal_id"])
    append({"volume": meta, "date": today()})
    return meta


def pending():
    if not STORE.exists():
        return []
    return [json.loads(line) for line in STORE.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def login():
    return run("gh", "api", "user", "--jq", ".login", cwd=None)


def apply(repo, by):
    """Zapíše čekající body do data/ v klonu. Vrátí (počet bodů, seznam varování)."""
    entries = pending()
    volumes = {(e["volume"]["archive"], e["volume"]["portal_id"]): e["volume"] for e in entries if "volume" in e}
    added, warnings, touched = 0, [], {}
    for e in entries:
        if "point" not in e:
            continue
        path = pathlib.Path(repo) / "data" / e["archive"] / f"{e['portal_id']}.json"
        if path not in touched:
            if path.exists():
                touched[path] = json.loads(path.read_text(encoding="utf-8"))
            elif (e["archive"], e["portal_id"]) in volumes:
                touched[path] = {"schema": 1, **volumes[(e["archive"], e["portal_id"])], "points": [], "sources": []}
            else:
                warnings.append(f"{e['archive']}/{e['portal_id']}: svazek v mapě není a chybí jeho údaje (pridej_svazek)")
                continue
        vol = touched[path]
        for k, v in volumes.get((e["archive"], e["portal_id"]), {}).items():
            vol.setdefault(k, v)
        point = {**e["point"], "by": by}
        if point in vol["points"]:
            continue
        vol["points"].append(point)
        added += 1
        source = {"by": by, "date": e["date"]}
        if source not in vol["sources"]:
            vol["sources"].append(source)
    for path, vol in touched.items():
        codes, _ = ruian.suggest(vol)
        if codes != (vol.get("place_codes") or {}):
            vol = touched[path] = ruian.with_codes(vol, codes)
        vol["points"].sort(key=lambda p: (p["scan"], p.get("place") or ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(vol, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return added, warnings


def send(repo):
    by = login()
    remotes = run("git", "remote", cwd=repo).split()
    upstream = "upstream" if "upstream" in remotes else "origin"
    branch = f"body-{by}-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"
    if run("git", "status", "--porcelain", cwd=repo):
        raise RuntimeError(f"{repo} má neuložené změny, nic se neodeslalo")
    previous = run("git", "branch", "--show-current", cwd=repo)
    run("git", "fetch", upstream, cwd=repo)
    run("git", "switch", "-c", branch, f"{upstream}/main", cwd=repo)
    try:
        added, warnings = apply(repo, by)
        if not added:
            return 0, warnings, None
        check = subprocess.run([sys.executable, "tools/kontrola.py"], cwd=repo, capture_output=True, text=True)
        if check.returncode:
            raise RuntimeError(f"kontrola neprošla, nic se neodeslalo:\n{check.stdout}")
        run("git", "add", "data", cwd=repo)
        run("git", "commit", "-m", f"Body od {by}: {added}", cwd=repo)
        run("git", "push", "-u", "origin", branch, cwd=repo)
        url = run("gh", "pr", "create", "--repo", UPSTREAM, "--head", f"{by}:{branch}", "--base", "main",
                  "--title", f"Body od {by}: {added}", "--body", "Orientační body z práce agenta (tools/body.py).",
                  cwd=repo)
    finally:
        run("git", "checkout", "--", ".", cwd=repo)
        run("git", "switch", previous or "main", cwd=repo)
    STORE.rename(STORE.with_name(f"body.odeslane-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"))
    return added, warnings, url


def main(argv):
    if len(argv) < 2 or argv[1] not in ("prehled", "zapis", "odeslat") or (argv[1] != "prehled" and len(argv) < 3):
        print(__doc__)
        return 2
    if argv[1] == "prehled":
        entries = pending()
        for e in entries:
            print(json.dumps(e, ensure_ascii=False))
        print(f"{sum('point' in e for e in entries)} bodů, {sum('volume' in e for e in entries)} svazků čeká ({STORE})")
        return 0
    if argv[1] == "zapis":
        added, warnings = apply(argv[2], login())
        url = None
    else:
        added, warnings, url = send(argv[2])
    for w in warnings:
        print(f"varování: {w}")
    print(f"zapsáno bodů: {added}" + (f", pull request: {url}" if url else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
