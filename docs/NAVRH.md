# Návrh: Mapa matrik (otevřená orientační mapa matričních knih)

*Pracovní návrh, 10. 11. 2026.*

## 1. Problém

Agent nebo badatel, který hledá zápis v naskenované matrice, tráví většinu času **orientací**, ne čtením:

- knihy před ~1850 často nemají rejstřík, jsou psané chronologicky a jeden rok zabírá 1–10 snímků;
- jiné jsou řazené po vsích (u sňatků někdy podle bydliště nevěsty), oddíly nejsou nikde popsané;
- stránkování rejstříku často nesedí s číslováním snímků na portálu.

Příklad z praxe (fara Čistá, 2026): najít oddíl Krakov v knize oddaných 1849–1942 stálo 10 otevřených snímků;
najít rok 1787 v knize narozených bez rejstříku 4 snímky. Každý další hledající to platí znovu.
Pro AI agenty je každý snímek drahý (obrázek ve vysokém rozlišení) a archivy kvůli opakovanému stahování
blokují IP adresy.

### Co už existuje (zjištěno 10. 11. 2026)

| úroveň | existuje | mezera |
|---|---|---|
| rozcestník obec → fara → archiv → knihy | [matriky.online](https://matriky.online) (~108 tis. knih, 9 archivů vč. eBadatelny, mapa, filtr roků a druhu, odkaz do prohlížeče archivu); [FamilySearch Parish Finder](https://www.familysearch.org/en/wiki/Czech_Republic_Parish_Finder); gazetteer GenTeam | API ani licence dat na matriky.online uvedené nejsou |
| orientace uvnitř knihy (snímek → rok / ves) | nic nenalezeno | **tady je tento projekt** |
| rejstřík jmen | dílčí: indexy FamilySearch, GenTeam (Morava 1585–1940, s registrací), místní indexy jednotlivců | pro Čechy souvislý není |

Rozcestník tedy nestavět znovu. Odkazy na knihy na matriky.online ale trvalé nejsou: vedou přes
`go.php?m=<id>&k=local|web&e=<čas>&t=<podpis>` a platnost vyprší za ~10 minut; web má i past na roboty (`trap.php`).
Proto v mapě odkazujeme přímo na portál archivu (trvalé ID svazku) a s matriky.online se párujeme přes archiv + signaturu;
jejich interní `m` jen se souhlasem provozovatele (spolupráce, případně export dat).

## 2. Cíl

Sdílená, otevřená, strojově čitelná **mapa svazků**: pro každou knihu orientační body „snímek → rok / měsíce /
strana / ves / druh zápisu“, uspořádání knihy a polohu rejstříku. Nástroj nad ní odpoví na otázku
„kterou knihu a který snímek mám otevřít pro obec X, rok Y, druh Z?“.

**Primárně pro agenty (boty):** strojově čitelná data v gitu, příkazová řádka a server MCP, otevřená licence,
agenti body i zapisují. Lidé až přes web nad stejnými daty. (Rozdíl proti matriky.online, který je pro lidi:
HTML bez API, odkazy s omezenou platností, past na roboty.)

Mimo rozsah: snímky, přepisy zápisů a rejstřík jmen. Obsah zápisů (OCR, přepisy, jména) sdílí samostatný projekt
[pe-pan/matriky-index](https://github.com/pe-pan/matriky-index); Mapa matrik ho doplňuje navigací v knize.

## 3. Oblast

- **Česká republika**, všechny státní oblastní archivy a městské archivy s online matrikami.
- **Pilot:** SOA Praha (eBadatelna – nejpracnější orientace, portál bez API) a SOA Plzeň (Porta fontium).
- Později: Slovensko, rakouský portál Matricula (stejné typy knih).

## 4. Data

Formát v [FORMAT.md](FORMAT.md). Jeden JSON na knihu, git jako databáze (historie, kontrola změn přes pull request).
Licence dat **CC0** (fakta o uspořádání knih; nejvolnější pro opakované použití), kód MIT.

### Kvalita

- Bod se zapisuje jen z toho, co čtenář viděl na snímku. Každý bod má zdroj (pseudonym/nástroj a datum).
- Odhady (interpolace) nejsou v datech, počítá je až vyhledávání.
- Rozpor se neřeší přepsáním: přidá se druhý bod a poznámka; vyhledávání ukáže oba.
- Ověřování: bod potvrzený dvěma nezávislými zdroji je „ověřený“ (příznak spočítá nástroj).

### Práva a soukromí

- Snímky ani přepisy se nesdílejí – jen metadata o uspořádání knihy a odkaz na snímek u archivu.
  Před zveřejněním projít podmínky užití jednotlivých portálů a případně archivy oslovit (projekt jim šetří servery).
- Mapa neobsahuje žádná jména osob, a proto ani osobní údaje. Jména a přepisy (jen zákonně veřejné zápisy)
  patří do [indexu matrik](https://github.com/pe-pan/matriky-index).
- Z katalogů archivů (databáze chráněné zvláštním právem pořizovatele) se přebírá jen popis knih, se kterými se
  skutečně pracuje; celý katalog jen se souhlasem archivu.

## 5. Úrovně a nástroje

Tři úrovně ve stejných datech, plněné postupně tím, co agenti stejně otevřou:

| úroveň | otázka | kde v datech | stav |
|---|---|---|---|
| 1. rozcestník | které knihy pokrývají obec a rok? | pole svazku (`parish`, `places`, `aliases`, `records`) → `v1/obce/<obec>.json` | roste s každou otevřenou knihou (`pridej_svazek`, u Porta fontium `katalog_pf.py`); celý katalog archivu jen s jeho souhlasem |
| 2. mapa svazku | který snímek otevřít? | `points`, `sections`, `index` | jádro, verze 1 |
| 3. obsah zápisů, jména | kde je konkrétní člověk? co v zápisu stojí? | mimo mapu: [matriky-index](https://github.com/pe-pan/matriky-index) (OCR, přepisy), propojení přes archiv + kniha + snímek | jiný projekt |

Architektura (bez vlastního serveru):

- **git (GitHub) = zdroj pravdy**, jeden JSON na knihu;
- **čtení = statické JSON na GitHub Pages** (`tools/build.py`, akce `web`) – pevné adresy, které boti volají jako API;
- **server MCP** (`tools/mcp_server.py`, jen standardní knihovna) nad týmiž daty pro agenty;
- **zápis = pull request** (`tools/body.py odeslat`) s automatickou kontrolou a sloučením (`tools/kontrola_pr.py`,
  akce `kontrola PR`), viz [PRISPIVANI.md](PRISPIVANI.md).

Server s dynamickým API (např. zápis bez účtu GitHubu) jde později postavit
**před** stejná data – nic z výše uvedeného se tím nemění.

## 6. Napojení na skill „rodokmen“

Skill už má místa, kudy každý snímek prochází (`tools/cache.py uloz`, `ebadatelna.py`, `portafontium.py`):

- **čtení** – před otevřením knihy se zeptat mapy (`najdi.py` / MCP) a začít odhadnutým snímkem;
- **zápis** – po přečtení snímku uložit orientační bod lokálně (`~/.cache/mapa-matrik/`), bez práce navíc;
- **sdílení** – na požádání uživatele vytvořit z lokálních bodů pull request do tohoto repozitáře
  (zveřejnění jen s výslovným souhlasem).

Mapa je samostatný projekt; skill ji používá volitelně. Funguje i bez skillu a pro jiné nástroje.

## 7. Plán

| krok | co | stav |
|---|---|---|
| 1 | formát + první mapy z jednoho projektu (26 knih) | hotovo |
| 2 | `najdi.py`, `kontrola.py` | hotovo |
| 3 | statické API (Pages), server MCP, sběr a odeslání bodů, automatická kontrola PR | hotovo lokálně |
| 4 | zveřejnění na GitHubu, napojení skillu rodokmen, návrh správci skillu | čeká |
| 5 | web, oslovení archivů (SOA Praha, SOA Plzeň) | |
| 6 | propojení s [matriky-index](https://github.com/pe-pan/matriky-index): odkazy mezi knihami, body z jejich OCR celých knih | návrh správci |

## 8. Otevřené otázky

- Jméno a umístění repozitáře (osobní účet / organizace).
- Licence dat CC0, nebo CC-BY (požadavek uvádět zdroj)?
- Jak ověřovat příspěvky od agentů ve velkém (dvojí čtení, namátkové kontroly)?
