"""Server MCP pro Mapu matrik (stdio, jen standardní knihovna Pythonu).

Přidání do Claude Code:  claude mcp add mapa-matrik -- python3 /cesta/k/mapa-matrik/tools/mcp_server.py
Přepínač --lokalne čte jen místní data repozitáře; jinak zveřejněnou mapu (při nedostupnosti místní data).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import body
from klient import source
from mapa import report

STR = {"type": "string"}
INT = {"type": "integer"}

TOOLS = [
    {
        "name": "najdi_svazek",
        "description": "Kterou matriční knihu a který snímek otevřít pro obec, rok a druh zápisu. Vrací knihy, "
                       "nejbližší orientační body a odhad snímku s odkazem. Volej před otevřením knihy v archivu.",
        "inputSchema": {"type": "object", "required": ["obec", "rok"], "properties": {
            "obec": {**STR, "description": "obec, např. Krakov, nebo kód části obce RÚIAN"},
            "okres": {**STR, "description": "okres, např. Rakovník – u obcí, kterých je v ČR víc se stejným názvem"},
            "rok": INT,
            "druh": {**STR, "enum": ["N", "O", "Z"], "description": "N narození, O oddaní, Z zemřelí"}}},
    },
    {
        "name": "svazek",
        "description": "Celá mapa jedné knihy (JSON): uspořádání, rejstřík, oddíly, všechny orientační body.",
        "inputSchema": {"type": "object", "required": ["archive", "portal_id"], "properties": {
            "archive": {**STR, "description": "např. soa-praha, soa-plzen"},
            "portal_id": {**STR, "description": "ID knihy na portálu, např. 4889 nebo chric-12"}}},
    },
    {
        "name": "pridej_bod",
        "description": "Zapíše orientační bod, který jsi právě viděl na snímku (jen lokálně; do mapy ho odešle "
                       "uživatel příkazem body.py odeslat). Jen to, co je na snímku vidět, žádné odhady ani jména. "
                       "Přepis přečteného zápisu (jména, data) patří do indexu https://github.com/pe-pan/matriky-index.",
        "inputSchema": {"type": "object", "required": ["archive", "portal_id", "scan", "type"], "properties": {
            "archive": STR, "portal_id": STR,
            "scan": {**INT, "description": "pořadové číslo snímku na portálu"},
            "type": {**STR, "enum": ["N", "O", "Z", "iN", "iO", "iZ", "title", "blank"]},
            "year": INT, "year_to": INT,
            "months": {**STR, "description": "např. I–IV"},
            "page": {**STR, "description": "strana nebo folio, jak je v knize"},
            "place": {**STR, "description": "ves, je-li kniha po vsích"},
            "letters": {**STR, "description": "u rejstříku písmena, např. L–M"},
            "note": {**STR, "description": "krátce, bez jmen osob"}}},
    },
    {
        "name": "pridej_svazek",
        "description": "Údaje o knize, která v mapě ještě není (aby k ní šlo přidat body). Jen lokálně.",
        "inputSchema": {"type": "object",
                        "required": ["archive", "portal", "portal_id", "url", "signature", "parish", "records"],
                        "properties": {
                            "archive": STR, "portal": {**STR, "description": "ebadatelna, portafontium, aron, …"},
                            "portal_id": STR, "url": STR,
                            "scan_url": {**STR, "description": "šablona adresy snímku s {scan}"},
                            "signature": STR, "parish": STR, "district": STR,
                            "places": {"type": "array", "items": STR},
                            "place_codes": {"type": "object", "description": "kódy částí obcí RÚIAN {obec: kód}, "
                                            "např. {\"Kožlany\": 72061}; najde je tools/ruian.py hledej"},
                            "records": {"type": "object", "description": "např. {\"N\": \"1778–1817\"}"},
                            "scans": INT, "language": STR,
                            "order": {**STR, "enum": ["chronological", "by_village", "by_village_bride", "mixed"]}}},
    },
    {
        "name": "moje_body",
        "description": "Body a svazky zapsané lokálně, které ještě nebyly odeslány do mapy.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def call(name, args, src):
    if name == "najdi_svazek":
        return report(src.volumes(args["obec"], args.get("okres")), args["obec"], int(args["rok"]), args.get("druh"))
    if name == "svazek":
        vol = src.volume(args["archive"], str(args["portal_id"]))
        return json.dumps(vol, ensure_ascii=False, indent=1) if vol else "Kniha v mapě není."
    if name == "pridej_bod":
        point = {k: args.get(k) for k in ("scan", "type", "year", "year_to", "months", "page", "place", "letters", "note")}
        return "Uloženo lokálně: " + json.dumps(body.add_point(args["archive"], args["portal_id"], point), ensure_ascii=False)
    if name == "pridej_svazek":
        return "Uloženo lokálně: " + json.dumps(body.add_volume(args), ensure_ascii=False)
    if name == "moje_body":
        entries = body.pending()
        return "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) or "Nic nečeká na odeslání."
    raise KeyError(name)


def handle(msg, state):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "mapa-matrik", "version": "0.1.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        try:
            if "src" not in state:
                state["src"] = source(state["mode"])
            text, error = call(params["name"], params.get("arguments") or {}, state["src"]), False
        except Exception as e:
            text, error = f"Chyba: {e}", True
        result = {"content": [{"type": "text", "text": text}], "isError": error}
    elif mid is None:
        return None
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"neznámá metoda {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main(argv):
    state = {"mode": "local" if "--lokalne" in argv else "auto"}
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        reply = handle(msg, state)
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
