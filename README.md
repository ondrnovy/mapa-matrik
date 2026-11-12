# Mapa matrik

Otevřená **mapa naskenovaných matričních knih** českých archivů: který snímek je který rok, ves a strana,
kde je rejstřík a jak je kniha uspořádaná. Vždy s odkazem na originál u archivu. Pro lidi i pro AI agenty,
kteří dělají rodokmeny nebo dějiny domů a obcí.

Vedle matrik mapuje i **další knihy** se stejným problémem: **sčítání lidu** a **pozemkové knihy** (který snímek je
které číslo domu) a **kroniky** obcí a škol (který snímek je který rok, kde je seznam domů nebo válka).

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

Mapa říká, **kde** co v knize najít, ne **co** tam stojí.

| je | není |
|---|---|
| signatura, fara, obce, roky, počet snímků, odkaz na portál | snímky (patří archivu) |
| orientační body: snímek → rok, měsíce, strana, ves, druh zápisu; u dalších knih číslo domu nebo téma | jména osob, přepisy zápisů a stran, strojový text (OCR) – to patří do [indexu matrik](https://github.com/pe-pan/matriky-index) |
| uspořádání knihy, kde je rejstřík, oddíly po vsích | údaje o žijících lidech |
| zvláštnosti (chyby rejstříku, zakrytá místa, přečíslování, vložené lístky) | výklady, kdo je kdo (patří do rodokmenu) |

Formát: [docs/FORMAT.md](docs/FORMAT.md). Celý návrh včetně dalších kroků: [docs/NAVRH.md](docs/NAVRH.md).

### Mapa matrik a index matrik

Obsah zápisů sdílí samostatný projekt **[pe-pan/matriky-index](https://github.com/pe-pan/matriky-index)**:
strojový text z PERO OCR, opravy čtení a zápisy přečtené očima (se jmény, jen zákonně veřejné). Oba projekty
označují knihu stejně – archiv, kniha, snímek (`soa-plzen/kozlany-22` zde = `portafontium/kozlany-22` tam,
eBadatelna má v obou stejné číslo knihy), takže se dají propojit.

Doporučený postup agenta: **zeptej se mapy** (který snímek) → otevři snímek → **bod do mapy** (snímek → rok, ves,
strana) → **zápis do indexu** (jména, data). Nikdo pak nečte stejný snímek dvakrát.

## Použití

### Pro agenty: HTTP (bez instalace)

Mapa je zveřejněná jako statické soubory JSON na `https://ondrnovy.github.io/mapa-matrik/v1/`:

| adresa | obsah |
|---|---|
| `v1/index.json` | přehled: počty, archivy, seznam obcí, obce s kódem RÚIAN (`codes`: kód → název, obec, okres) |
| `v1/obce/<obec>.json` | rozcestník: knihy, které obec pokrývají (obec malými písmeny bez diakritiky, mezery = `-`, např. `krakov`, `nova-ves`; funguje i německý název, např. `koschlan`). U každé knihy počet orientačních bodů (`points`) a obec, o kterou jde (`place`: název, kód RÚIAN, obec, okres) – stejnojmenné obce z různých okresů jsou v jednom souboru, rozliší je `place.okres` |
| `v1/obce/kod/<kód>.json` | totéž podle kódu části obce z RÚIAN (např. `72061` = Kožlany), jen ta jedna obec |
| `v1/svazky/<archiv>/<id>.json` | celá mapa knihy: uspořádání, rejstřík, oddíly, orientační body (`verified` = potvrdili dva různí přispěvatelé) |

Odhad snímku mezi dvěma body je lineární interpolace (viz `estimate` v [tools/mapa.py](tools/mapa.py)).

### Pro agenty: server MCP

```bash
git clone https://github.com/ondrnovy/mapa-matrik
claude mcp add mapa-matrik -- python3 "$PWD/mapa-matrik/tools/mcp_server.py"
```

Nástroje: `najdi_svazek(obec, rok, druh)`, `najdi_pramen(obec, cp, rok, druh)` (sčítání, kroniky, pozemkové
knihy), `svazek(archive, portal_id)`, `pridej_bod(…)`, `pridej_svazek(…)`,
`moje_body()`. Jen standardní knihovna Pythonu 3.9+, nic dalšího se neinstaluje. Body se ukládají lokálně;
do mapy je odešle uživatel (viz Jak přispět).

### Příkazová řádka

```bash
python3 tools/najdi.py Krakov 1787 N         # místní data
python3 tools/najdi.py Krakov 1787 N --web   # zveřejněná mapa
python3 tools/najdi.py Kožlany --cp=74       # sčítání a pozemkové knihy: dům čp. 74
python3 tools/najdi.py Kožlany 1866 --druh=chronicle   # kroniky: rok 1866
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
