# Přispívání

Mapu plní hlavně AI agenti při práci s matrikami; lidé jsou vítaní stejně.

## Co zapisovat

- **Jen to, co je na snímku vidět**: rok, měsíce, strana, ves, druh zápisu, začátek rejstříku, titulní list.
  Žádné odhady – ty počítá až vyhledávání.
- Pokud možno **bez jmen osob**, přepisů a snímků – mapa je o tom, kde co v knize je. Poznámky krátce a věcně
  („rok 1785 chybí“, „strany přečíslované od 120“). Automat obsah nehodnotí; co se nepovede, opraví další PR.
- Nesouhlasí-li existující bod s tím, co vidíš, **přidej raději vlastní bod** – vyhledávání ukáže oba a shoda
  dvou účtů dává `verified`. Zjevnou chybu (překlep v roce, špatné číslo snímku) klidně oprav přímo.

## Jak se příspěvek dostane do mapy

1. `pridej_bod` / `pridej_svazek` (MCP) uloží bod lokálně.
2. `python3 tools/body.py odeslat <klon>` vytvoří větev, doplní `by` = tvůj účet GitHubu a pošle pull request.
3. Akce `kontrola PR` (kód z `main`, z PR čte jen data):
   - **chyba formátu** (neznámé pole, snímek mimo rozsah knihy, špatný druh) → PR neprojde, oprav a pošli znovu;
   - **data v pořádku** (přidání i úpravy bodů a knih) a mapa se z nich sestaví (`tools/build.py`) →
     **sloučí se automaticky** a mapa na webu se do pár minut obnoví;
   - **správce** rozhoduje jen tam, kde by PR mohl mapě uškodit: soubory mimo `data/`, smazaná kniha, ubývající
     body, nebo nové body za cizí účet (`by`) – štítek `ke-kontrole`.

## Ověřené body

Bod, který nezávisle zapíší dva různí přispěvatelé, je ve zveřejněných datech `verified: true`.
Stejný bod od druhého účtu tedy není zbytečný – potvrzuje ho.

## Správce

Sloučení PR se štítkem `ke-kontrole` a změny kódu (`tools/`, `.github/`) jsou jen na správci.
Každou změnu lze vrátit (`git revert`).
