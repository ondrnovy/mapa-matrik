# Formát mapy svazku

Jeden svazek (matriční kniha) = jeden soubor `data/<archiv>/<portal_id>.json`, kódování UTF-8.
Klíče jsou anglicky (aby je snadno četly nástroje odkudkoli), hodnoty česky tak, jak je píše archiv.

```json
{
  "schema": 1,
  "archive": "soa-praha",
  "portal": "ebadatelna",
  "portal_id": "4889",
  "url": "https://ebadatelna.soapraha.cz/pages/MatrikaPage/matrikaId/4889",
  "scan_url": "https://ebadatelna.soapraha.cz/d/4889/{scan}",
  "signature": "Čistá 06",
  "parish": "Čistá",
  "district": "Rakovník",
  "places": ["Čistá", "Krakov", "Břežany"],
  "records": {"N": "1778–1817"},
  "scans": 200,
  "language": "latina",
  "order": "chronological",
  "index": null,
  "points": [
    {"scan": 2, "note": "titulní list"},
    {"scan": 49, "type": "N", "year": 1791, "months": "I–V", "page": null}
  ],
  "sections": [],
  "notes": ["Dodatečný zápis křtu z r. 1824 na konci roku 1791 (sn. 51)."],
  "sources": [{"by": "rodokmen", "date": "2026-11-10"}]
}
```

## Pole

| pole | povinné | význam |
|---|---|---|
| `schema` | ano | verze formátu (teď 1) |
| `kind` | ne | druh knihy: `register` matrika (výchozí, pole se vynechává), `census` sčítání lidu, `chronicle` kronika obce nebo školy, `land_book` pozemková (gruntovní) kniha – viz [Další knihy](#další-knihy-sčítání-kroniky-pozemkové-knihy) |
| `archive` | ano | zkratka archivu: `soa-praha`, `soa-plzen`, `soa-litomerice`, `soa-trebon`, `soa-zamrsk`, `za-opava`, `mza-brno`, `ahmp`, … |
| `portal` | ano | `ebadatelna`, `portafontium`, `aron`, `actapublica`, `vademecum`, `matricula`, … |
| `portal_id` | ano | identifikátor knihy na portálu (eBadatelna `matrikaId`, Porta fontium část adresy, např. `chric-12`) |
| `url` | ano | stránka knihy na portálu |
| `scan_url` | ne | šablona adresy snímku, `{scan}` = pořadové číslo snímku |
| `signature` | ano | signatura, jak ji uvádí archiv |
| `parish`, `district` | ano / ne | fara (původce) a okres |
| `places` | ne | obce, které kniha pokrývá (dnešní český název) |
| `place_codes` | ne | kód části obce z [RÚIAN](https://cuzk.gov.cz/ruian/) ke každé obci: `{"Kožlany": 72061}`; klíč musí být v `places`. Rozliší stejnojmenné obce (Petrovic je v ČR 25). Kandidáty s obcí a okresem vypíše `python3 tools/ruian.py hledej Petrovice`; jednoznačné kódy doplní `body.py odeslat` sám. Zaniklé vsi, mlýny a samoty kód nemají – vynech je |
| `aliases` | ne | jiné názvy obcí (německé, historické, jak je píše kniha): `{"Kožlany": ["Koschlan", "Kozlany"]}`; klíč musí být v `places`. Rozcestník najde knihu i podle nich |
| `records` | ano (matriky) | druhy zápisů a roky: `N` narození, `O` oddaní, `Z` zemřelí, `iN` `iO` `iZ` rejstříky |
| `years` | ano (jiné knihy) | roky knihy mimo matriky: `"1921"`, `"1877–1970"` |
| `scans` | ne | počet snímků |
| `language` | ne | jazyk zápisů |
| `order` | ne | `chronological` (po letech), `by_village` (oddíly po vsích), `by_village_bride` (oddaní podle vsi nevěsty), `mixed` |
| `index` | ne | kde je rejstřík: `{"scans": "125–128", "by": "groom", "refers_to": "page"}` nebo odkaz na jiný svazek `{"volume": "soa-praha/5866"}` |
| `points` | ano | orientační body (viz níže) – jádro mapy |
| `sections` | ne | oddíly knihy: `{"scans": "105–110", "type": "O", "place": "Krakov", "years": "1849–1864"}` |
| `notes` | ne | zvláštnosti: zakrytá místa, chyby rejstříku, přečíslování domů, prázdné listy |
| `sources` | ano | kdo body přidal a kdy (jen pseudonym nebo název nástroje, žádné osobní údaje) |

### Orientační bod (`points[]`)

Co čtenář na snímku skutečně viděl:

| pole | význam |
|---|---|
| `scan` | pořadové číslo snímku na portálu (povinné) |
| `type` | `N`, `O`, `Z`, `iN`, `iO`, `iZ` (rejstřík), `title`, `blank` |
| `year` | rok zápisů na snímku (u přelomu roku první z nich) |
| `year_to` | poslední rok na snímku, když se liší |
| `months` | měsíce, např. `"I–IV"` |
| `page` | strana / folio, jak je v knize napsané (text, např. `"116–117"` nebo `"fol. 176"`) |
| `place` | ves, když je kniha po vsích |
| `letters` | u rejstříku písmena, např. `"L–M"` |
| `house` | číslo popisné (sčítání, pozemková kniha), text: `"74"`, `"70–79"` |
| `topic` | u kroniky krátké téma: `"seznam domů"`, `"válka 1914–1918"`, `"požár"` (nejvýš 80 znaků) |
| `note` | cokoli dalšího |
| `by` | kdo bod zapsal (účet GitHubu; doplní `body.py`, kontrola PR ho ověří proti autorovi PR) |

Ve zveřejněných souborech (`v1/svazky/…`) má každý bod navíc `verified`: `true`, když stejný snímek, druh, rok, ves
a číslo domu zapsali aspoň dva různí přispěvatelé. U starších bodů bez `by` se počítá první zdroj ze `sources`.

## Další knihy (sčítání, kroniky, pozemkové knihy)

Stejný problém jako u matrik: kniha má stovky snímků a hledá se jeden dům nebo rok. Formát je stejný, jen:

- svazek má `kind` a místo `records` pole `years`;
- bod u **sčítání lidu** a **pozemkové knihy** nese `house` (čp. na snímku), u sčítání s více ročníky v jedné
  knize i `year`; arch domácnosti = jeden bod na první snímek domu;
- bod u **kroniky** nese `year` (o kterém roce se píše – i zpětné kapitoly o starší historii obce) a/nebo `topic`;
- `type` u nich jen `title` nebo `blank` (druhy zápisů N/O/Z jsou jen matriční).

```json
{"schema": 1, "kind": "census", "archive": "soa-plzen", "portal": "portafontium", "portal_id": "…",
 "url": "…", "signature": "Sčítání lidu 1921, Kožlany", "parish": "Kožlany", "places": ["Kožlany"],
 "years": "1921", "points": [{"scan": 12, "house": "1"}, {"scan": 140, "house": "74"}], "sources": […]}
```

Kde to archiv už řeší sám, body nepiš: **Porta fontium (SOA Plzeň) má sčítání lidu rozdělené po domech** –
každé číslo popisné má vlastní stránku a seznam domů („Nr. 303“, `census/soap-ps/<rok>/okres-<okres>`), mapa by
nic nepřidala. Mapa se hodí tam, kde je sčítání jedna dlouhá kniha za obec.

`parish` je u nich původce knihy (obec, škola, úřad). **Žádná jména ani zde**: archy sčítání a pozemkové knihy
jsou plné jmen, do mapy jde jen číslo domu. Přepisy patří do indexu, ne do mapy.

Hledání: `najdi_pramen(obec, cp)` odhadne snímek podle čísla domu (archy i listy gruntů bývají seřazené podle čp.),
`najdi_pramen(obec, rok, druh="chronicle")` podle roku; `najdi_svazek` u obce upozorní, že další knihy v mapě jsou.

## Svazky z katalogu archivu

Rozcestník (obec → knihy) se plní i z katalogů portálů, bez otevírání snímků: `tools/katalog_pf.py` převede uložený
výpis matrik Porta fontium na svazky se zdrojem `{"by": "katalog-portafontium"}` a prázdným `points`. Roky v `records`
jsou u nich za celý svazek, jak je uvádí katalog (u knihy N + O + Z z let 1655–1684 mají všechny tři druhy stejný
rozsah). Orientační body do nich přibývají běžně (`pridej_bod`).

Katalog je databáze chráněná zvláštním právem pořizovatele (§ 88–94 autorského zákona) a podle
[podmínek Porta fontium](https://www.portafontium.eu/terms-of-use) se popisy smí užívat jen nevýdělečně s uvedením zdroje.
Bez souhlasu archivu se proto převádějí jen knihy, se kterými se skutečně pracuje, ne celý katalog.

## Pravidla

1. **Jen to, co je vidět na snímku.** Žádné odhady. Odhad (interpolaci) počítá až vyhledávací nástroj.
2. **Žádné snímky ani přepisy celých stran** – jen orientace (rok, strana, ves). Snímky patří archivu.
3. **Žádná jména osob.** Mapa jmen neobsahuje vůbec, ani v poznámkách (hlídá to kontrola PR). Přepis zápisu
   se jmény patří do [indexu matrik](https://github.com/pe-pan/matriky-index) – stejný archiv, kniha a snímek.
4. **Rozpor = poznámka, ne přepis.** Když nový čtenář vidí na snímku něco jiného, přidá bod se svým zdrojem
   a poznámku; neopravuje cizí bod potichu.
5. **Jen známá pole.** Pole mimo tabulky výše kontrola odmítne (ochrana proti úniku osobních údajů).
