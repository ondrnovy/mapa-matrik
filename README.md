# Mapa matrik

Otevřená **mapa naskenovaných matričních knih** českých archivů: který snímek je který rok, ves a strana,
kde je rejstřík a jak je kniha uspořádaná. Vždy s odkazem na originál u archivu. Pro lidi i pro AI agenty,
kteří dělají rodokmeny.

**Hlavní přínos: rychlejší hledání, méně tokenů a menší zátěž archivů.** Agent (nebo člověk) neotvírá desítky snímků, aby našel
správný rok nebo ves – zeptá se mapy a otevře rovnou ten správný. Každý snímek je pro AI drahý obrázek ve vysokém
rozlišení a archivy kvůli opakovanému stahování blokují přístup; mapa tu orientaci zaplatí jednou pro všechny.

> Stav: **návrh a pilot** (listopad 2026) – první mapy z fary Čistá a Petrovice (SOA Praha) a Chříč,
> Kožlany, Kozojedy, Liblín (SOA Plzeň).

## Proč

Matriky jsou naskenované, ale **knihy bez rejstříku jsou slepé**: kdo hledá křest z roku 1787, musí nejdřív
otevřít desítky snímků, jen aby zjistil, kde ten rok začíná. U knih řazených po vsích je to ještě horší.
Každý badatel (a každý AI agent) tu práci dělá znovu – stojí to čas, peníze za výpočet a **zatěžuje to servery
archivů**, které pak blokují přístup.

Mapa tu orientaci zapisuje jednou a sdílí: „Čistá 06: snímek 49 = leden–květen 1791“, „Čistá 29 je po vsích podle
nevěsty, Krakov = snímky 105–110“. Další hledání jde rovnou na správný snímek.

## Co v ní je a co ne

| je | není |
|---|---|
| signatura, fara, obce, roky, počet snímků, odkaz na portál | snímky (patří archivu) |
| orientační body: snímek → rok, měsíce, strana, ves, druh zápisu | přepisy celých stran |
| uspořádání knihy, kde je rejstřík, oddíly po vsích | údaje o žijících lidech |
| zvláštnosti (chyby rejstříku, zakrytá místa, přečíslování) | |

Formát: [docs/FORMAT.md](docs/FORMAT.md). Celý návrh včetně dalších kroků: [docs/NAVRH.md](docs/NAVRH.md).

## Použití

### Pro agenty: HTTP (bez instalace)

Mapa je zveřejněná jako statické soubory JSON na `https://ondrnovy.github.io/mapa-matrik/v1/`:

| adresa | obsah |
|---|---|
| `v1/index.json` | přehled: počty, archivy, seznam obcí |
| `v1/obce/<obec>.json` | rozcestník: knihy, které obec pokrývají (obec malými písmeny bez diakritiky, mezery = `-`, např. `krakov`, `nova-ves`; funguje i německý název, např. `koschlan`). U každé knihy počet orientačních bodů (`points`) |
| `v1/svazky/<archiv>/<id>.json` | celá mapa knihy: uspořádání, rejstřík, oddíly, orientační body (`verified` = potvrdili dva různí přispěvatelé) |

Odhad snímku mezi dvěma body je lineární interpolace (viz `estimate` v [tools/mapa.py](tools/mapa.py)).

### Pro agenty: server MCP

```bash
git clone https://github.com/ondrnovy/mapa-matrik
claude mcp add mapa-matrik -- python3 "$PWD/mapa-matrik/tools/mcp_server.py"
```

Nástroje: `najdi_svazek(obec, rok, druh)`, `svazek(archive, portal_id)`, `pridej_bod(…)`, `pridej_svazek(…)`,
`moje_body()`. Jen standardní knihovna Pythonu 3.9+, nic dalšího se neinstaluje. Body se ukládají lokálně;
do mapy je odešle uživatel (viz Jak přispět).

### Příkazová řádka

```bash
python3 tools/najdi.py Krakov 1787 N         # místní data
python3 tools/najdi.py Krakov 1787 N --web   # zveřejněná mapa
python3 tools/kontrola.py                    # kontrola dat
```

Výstup: knihy, které obec a rok pokrývají, nejbližší orientační body a **odhad snímku** s odkazem.
Odhad je jen nápověda – vždy je potřeba se na snímek podívat.

## Jak přispět

Body se sbírají při práci (`pridej_bod` v MCP) a odešlou se jedním příkazem jako pull request:

```bash
gh repo fork ondrnovy/mapa-matrik --clone     # jednou
python3 mapa-matrik/tools/body.py prehled     # co čeká
python3 mapa-matrik/tools/body.py odeslat mapa-matrik
```

Pull request zkontroluje automat ([tools/kontrola_pr.py](tools/kontrola_pr.py)): formát dat a zkušební sestavení
mapy. Když projde, **sloučí se sám** – přidání i opravy. Správce ho projde jen tehdy, když sahá mimo `data/`, maže
knihu, ubírá body nebo přidává body za cizí účet (štítek `ke-kontrole`). Pravidla: [docs/PRISPIVANI.md](docs/PRISPIVANI.md).

## Licence

Data: CC0 1.0 (volné dílo). Kód: MIT.
