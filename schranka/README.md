# Sběrná schránka

Cloudflare Worker, přes který můžou přispívat i lidé bez účtu GitHub (skill rodokmen, `tools/sdileni.py`).
Přijme orientační body a přepsané zápisy, ověří je a založí z nich pull requesty:

- **body** → [ondrnovy/mapa-matrik](https://github.com/ondrnovy/mapa-matrik) (sloučí je automatická kontrola PR jako ostatní datové PR),
- **zápisy** → [pe-pan/matriky-index](https://github.com/pe-pan/matriky-index) přes fork `ondrnovy/matriky-index` (slučuje správce indexu).

Schránka **nic neslučuje** – jen zakládá větve a PR. Kontrola dat a sloučení zůstávají v GitHub Actions obou repozitářů,
takže nesmysl nebo spam skončí jako zamítnutý PR.

## Co hlídá

- velikost (256 kB), nejvýš 500 bodů a 200 zápisů najednou, 10 odeslání z jedné IP za den, 300 celkem za den (KV `LIMITY`);
- body: jen podporované archivy (SOA Plzeň, SOA Praha), známá pole, bez tabulátorů a nových řádků, odkaz knihy jen na portál archivu;
- zápisy: formát řádku indexu, lhůty (narození 100 let, sňatky a úmrtí 75 let), `cetl` s modelem/effortem, jistota;
- duplicity: bod, který v knize už je, a řádek indexu se stejným snímkem, datem a druhem se nepřidá.

## API

`POST /v1/prispevek`, JSON:

```json
{"body": [{"archive": "soa-plzen", "portal_id": "kozlany-22", "signature": "Kožlany 22", "url": "https://www.portafontium.eu/register/soap-pn/kozlany-22",
           "scan": 40, "type": "Z", "year": 1914}],
 "zapisy": [{"archiv": "portafontium", "kniha": "kozlany-22", "nazev": "Kožlany 22", "url": "…", "snimek": "74", "datum": "1918-01-17", "typ": "Z",
             "obec": "Kožlany 303", "osoby": "zemřelý: …", "ostatni": "…", "jistota": "vysoká", "cetl": "claude-opus-5-5/high 2026-11-11 (z rodokmenu)"}]}
```

Odpověď `{"mapa": "<odkaz na PR>|null", "index": "<odkaz na PR>|null"}`, chyba `{"chyba": "…"}` s kódem 400/413/429.

## Nasazení (jednou)

Potřeba: účet Cloudflare (zdarma) a token GitHub účtu, pod kterým schránka zakládá PR.

1. Cloudflare: v dashboardu **My Profile → API Tokens → Create Token → „Edit Cloudflare Workers“** (přidej i
   *Workers KV Storage: Edit*). Token a Account ID ulož mimo git, např. `~/.config/mapa-matrik/cloudflare.env`:
   `CLOUDFLARE_API_TOKEN=…` a `CLOUDFLARE_ACCOUNT_ID=…` (`chmod 600`).
2. GitHub: **Settings → Developer settings → Personal access tokens (classic)**, jen scope `public_repo`
   (zakládá větve a PR ve veřejných repozitářích; nic víc). Fork `ondrnovy/matriky-index` musí existovat.
3. Ze složky `schranka/`:
   ```bash
   set -a; . ~/.config/mapa-matrik/cloudflare.env; set +a
   npx -y wrangler@4 kv namespace create LIMITY      # id dej do wrangler.toml
   npx -y wrangler@4 secret put GITHUB_TOKEN         # vlož token z kroku 2
   npx -y wrangler@4 deploy
   ```
4. Adresu (`https://mapa-matrik-schranka.<účet>.workers.dev`) dej do `SCHRANKA` v `tools/sdileni.py` skillu rodokmen.

Test bez sítě: `cd schranka && node --test test/schranka.test.js`.
