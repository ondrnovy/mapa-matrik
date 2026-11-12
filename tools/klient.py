"""Čtení mapy z webu (GitHub Pages) s mezipamětí, nebo z místní kopie repozitáře.

Adresa webu: proměnná MAPA_MATRIK_URL, jinak mapa.WEB. Mezipaměť ~/.cache/mapa-matrik/web (platí 1 den).
"""
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

from mapa import in_district, load, mark_verified, norm, place_names, slug, WEB

CACHE = pathlib.Path(os.environ.get("MAPA_MATRIK_CACHE", pathlib.Path.home() / ".cache" / "mapa-matrik" / "web"))
TTL = 24 * 3600


class Local:
    name = "místní data"

    def volumes(self, place, okres=None):
        """Knihy obce (název, jiný název, nebo kód části obce RÚIAN), volitelně jen v okrese."""
        vols = [mark_verified(v) for _, v in load()]
        if str(place or "").isdigit():
            vols = [v for v in vols if int(place) in (v.get("place_codes") or {}).values()]
        elif place:
            vols = [v for v in vols if slug(place) in [slug(p) for p in place_names(v)]]
        return [v for v in vols if in_district(v, place, okres)]

    def volume(self, archive, portal_id):
        for path, vol in load():
            if path.parent.name == archive and path.stem == portal_id:
                return mark_verified(vol)
        return None


class Web:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.name = self.base

    def get(self, path):
        cached = CACHE / path
        if cached.exists() and time.time() - cached.stat().st_mtime < TTL:
            return json.loads(cached.read_text(encoding="utf-8"))
        req = urllib.request.Request(f"{self.base}/{path}", headers={"User-Agent": "mapa-matrik-klient"})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    body = r.read().decode("utf-8")
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code != 429 or attempt:
                    raise
                time.sleep(int(e.headers.get("Retry-After") or 10))
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(body, encoding="utf-8")
        return json.loads(body)

    def volumes(self, place, okres=None):
        path = f"obce/kod/{place}.json" if str(place).isdigit() else f"obce/{slug(place)}.json"
        refs = self.get(path) or []
        if okres:
            refs = [r for r in refs if norm((r.get("place") or {}).get("okres") or r.get("district")) == norm(okres)]
        return [v for v in (self.get(r["path"]) for r in refs) if v]

    def volume(self, archive, portal_id):
        return self.get(f"svazky/{archive}/{portal_id}.json")


def source(mode):
    """mode: 'web', 'local' nebo 'auto' (web, při nedostupnosti místní data, jsou-li)."""
    if mode == "local":
        return Local()
    web = Web(os.environ.get("MAPA_MATRIK_URL", WEB))
    if mode == "web":
        return web
    try:
        web.get("index.json")
        return web
    except (urllib.error.URLError, OSError, ValueError):
        return Local()
