# Přepisy zápisů (návrh, verze 2)

*Návrh, 10. 11. 2026. Zatím se podle něj nic nesbírá ani nezveřejňuje.*

Agent, který v knize hledá předka, přečte celou stranu. Mapa dnes z toho uloží jen orientační bod („sn. 62 = 1914“),
zbytek přečteného se zahodí a další hledající ho čte znovu. Přepisy ukládají **přečtené zápisy** – jména, role, data,
domy – vždy s odkazem na snímek u archivu. Přepis je ukazatel na originál, ne jeho náhrada: kdo chce jistotu,
otevře snímek.

## Soubor

`zapisy/<archiv>/<portal_id>.json` – jeden soubor na knihu, vedle mapy knihy `data/<archiv>/<portal_id>.json`
(kniha musí v mapě být).

```json
{
 "schema": 1,
 "archive": "soa-plzen",
 "portal_id": "kozlany-22",
 "scans": [
  {"scan": 62, "complete": true, "by": "ondrnovy"}
 ],
 "records": [
  {
   "scan": 62, "n": 3, "page": "fol. 60", "type": "Z",
   "date": "1914-03-12", "date2": "1914-03-14",
   "place": "Kožlany", "house": "209",
   "persons": [
    {"role": "deceased", "given": "Matouš", "surname": "Nový", "sex": "m", "age": "74", "occupation": "švec"},
    {"role": "spouse", "given": "Anna", "surname": "Nová"}
   ],
   "note": "okrajová poznámka, jak je v knize",
   "text": "doslovný přepis zápisu (volitelný)",
   "by": "ondrnovy",
   "read": "agent"
  }
 ]
}
```

(Jména a data v ukázce jsou jen pro formát.)

## Pole zápisu (`records[]`)

| pole | povinné | význam |
|---|---|---|
| `scan` | ano | snímek na portálu (stejné číslování jako body mapy) |
| `n` | ne | pořadí zápisu na snímku shora (1, 2, …), když jich je víc |
| `page` | ne | strana / folio, jak je v knize |
| `type` | ano | `N` křest/narození, `O` sňatek, `Z` úmrtí/pohřeb |
| `date` | ano | datum události (narození, sňatku, úmrtí) `RRRR-MM-DD`; neúplné `RRRR-MM` nebo `RRRR` |
| `date2` | ne | druhé datum (křest, pohřeb) |
| `place`, `house` | ne | obec a číslo popisné, jak jsou v zápisu |
| `persons` | ano | osoby v zápisu (níže) |
| `note` | ne | okrajové a pozdější poznámky (legitimace, sňatek, úmrtí) |
| `text` | ne | doslovný přepis celého zápisu |
| `by` | ano | účet GitHubu (doplní `body.py`, kontrola PR ho ověří) |
| `read` | ano | `agent` (přečetl model) nebo `human` |

### Osoba (`persons[]`)

| pole | význam |
|---|---|
| `role` | `child`, `father`, `mother`, `father_father`, `father_mother`, `mother_father`, `mother_mother`, `godparent`, `midwife`, `groom`, `bride`, `groom_father`, `groom_mother`, `bride_father`, `bride_mother`, `witness`, `deceased`, `spouse`, `priest`, `other` |
| `given`, `surname` | jméno a příjmení **tak, jak jsou v knize** (`Joannes`, `Nowy`) |
| `maiden` | rodné příjmení ženy |
| `sex` | `m` / `f` |
| `age`, `occupation`, `residence`, `religion` | jak je v zápisu |
| `note` | např. „nemanželské“, „vdova po …“ |

Nejisté čtení se značí „(?)“, nečitelné „[…]“ – stejně jako v přepisech rodokmenu. Nic se nedomýšlí ani nepřekládá
do moderních tvarů; srovnání jmen (Joannes = Jan, Nowy = Nový, bez diakritiky) dělá až vyhledávání.

## Úplnost snímku (`scans[]`)

`{"scan": 62, "complete": true}` = na snímku jsou přepsané **všechny** zápisy. Jen pak smí vyhledávání říct
„na sn. 62 tento člověk není“. Bez `complete` jde o vybrané zápisy (typicky jen hledaná rodina).

## Ověření

Zápis je ve zveřejněných datech `verified: true`, když dva různí přispěvatelé přečetli shodně snímek, druh, datum
a jména hlavních osob (dítě / snoubenci / zemřelý). Rozpor se neopravuje, přidá se druhé čtení (pravidlo 4 mapy).

Orientační body se z přepisů odvodí samy (snímek → druh, rok, ves) – nepíšou se dvakrát.

## Ochrana žijících a práva

- **Jen zápisy starší 100 let** (rok události ≤ letošní rok − 100), u narození 110 let. Mladší zápisy zůstávají
  v mapě jen jako orientační body bez jmen. Kontrola PR mladší zápis odmítne.
- **Žádné snímky** – jen text a odkaz na snímek u archivu.
- **Jen zápisy přečtené při práci**, ne systematické přepisování celých knih (databáze snímků je chráněná zvláštním
  právem pořizovatele, § 88–94 autorského zákona). Celé knihy jen se souhlasem archivu.
- **Zdroj** (archiv, signatura, odkaz) nese mapa knihy, na kterou přepis odkazuje.
- **Licence přepisů: CC BY-NC 4.0** (uvést zdroj, nevýdělečně) – v souladu s podmínkami portálů archivů
  (např. [Porta fontium](https://www.portafontium.eu/terms-of-use)). Mapa knih (body) zůstává CC0.

## Hledání

- MCP `najdi_osobu(prijmeni, jmeno, obec, rok_od, rok_do, druh)` – zápisy s odkazem na snímek, u úplných snímků
  i „prošlé snímky bez shody“.
- Statický rejstřík `v1/jmena/<příjmení>.json` (příjmení bez diakritiky), odkazuje na `v1/zapisy/<archiv>/<id>.json`.

## Sběr

- MCP `pridej_zapis(…)` uloží zápis lokálně (stejně jako `pridej_bod`), `body.py odeslat` ho pošle v pull requestu.
- Kontrola PR: známá pole a role, data a lhůty, `by` = autor PR, zápis míří na knihu v mapě, text do rozumné délky.
  Přidání nových zápisů se slučuje samo, změna cizího zápisu jde ke kontrole.
- První data: přepisy zemřelých předků z rodokmenu (bez rodinných poznámek), pak průběžně ze všeho, co agenti čtou.

## Otevřené otázky

- Hranice 100 / 110 let, nebo přísněji (sňatky s nevěstou mladší 18 let → narození před 110 lety)?
- Normalizovaná podoba jmen (`given_cs`) v datech, nebo jen ve vyhledávání?
- Souhlas archivů – oslovit před prvním zveřejněním přepisů?
