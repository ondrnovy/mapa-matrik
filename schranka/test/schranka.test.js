// node --test schranka/test – bez sítě: GitHub API je nahrazené pamětí.
import { test } from "node:test";
import assert from "node:assert/strict";
import worker, { overPrispevek, pridejBody, pridejRadky, Chyba } from "../src/index.js";

const BOD = { archive: "soa-plzen", portal_id: "kozlany-22", signature: "Kožlany 22", scan: 40, type: "Z", year: 1914 };
const ZAPIS = { archiv: "portafontium", kniha: "kozlany-22", nazev: "Kožlany 22", url: "https://www.portafontium.eu/register/soap-pn/kozlany-22",
  snimek: "74", datum: "1918-01-17", typ: "Z", obec: "Kožlany 303", osoby: "zemřelý: Oldřich Nový", ostatni: "záškrt",
  jistota: "vysoká", cetl: "claude-opus-5-5/high 2026-11-11 (z rodokmenu)" };

test("ověření: lhůty, formát, neznámé archivy", () => {
  assert.equal(overPrispevek({ body: [BOD], zapisy: [ZAPIS] }, 2026).zapisy[0].radek.obec, "Kožlany 303");
  const chyba = (d, re) => assert.throws(() => overPrispevek(d, 2026), e => e instanceof Chyba && re.test(e.message));
  chyba({ zapisy: [{ ...ZAPIS, datum: "1960-02-03" }] }, /mladší než 75/);
  chyba({ zapisy: [{ ...ZAPIS, typ: "N", datum: "1930-01-01" }] }, /mladší než 100/);
  chyba({ zapisy: [{ ...ZAPIS, osoby: "a\tb" }] }, /tabulátorů/);
  chyba({ zapisy: [{ ...ZAPIS, cetl: "Claude" }] }, /model\/effort/);
  chyba({ body: [{ ...BOD, archive: "mza" }] }, /nezná/);
  chyba({ body: [{ ...BOD, portal_id: "../x" }] }, /portal_id/);
  chyba({ body: [{ ...BOD, url: "https://zlo.example/x" }] }, /portál archivu/);
  chyba({}, /prázdný/);
});

test("body: bez duplicit, rozsah knihy, zdroj", () => {
  const vol = { points: [{ scan: 40, type: "Z", year: 1914 }], records: { Z: "1900–1949" }, sources: [] };
  assert.equal(pridejBody(vol, [{ scan: 40, type: "Z", year: 1914 }, { scan: 90, type: "Z", year: 1951 }], "2026-11-11"), 1);
  assert.equal(vol.records.Z, "1900–1951");
  assert.equal(vol.points[1].by, "schranka");
  assert.deepEqual(vol.sources, [{ by: "schranka", date: "2026-11-11" }]);
});

test("řádky indexu: hlavička, bez duplicit", () => {
  const { tsv, pridano } = pridejRadky(null, [{ snimek: "74", datum: "1918-01-17", typ: "Z", osoby: "x" }]);
  assert.equal(pridano, 1);
  assert.match(tsv, /^snimek\tdatum\ttyp\tobec\tosoby\tostatni\tjistota\tcetl\todkaz\n74\t1918-01-17\tZ\t\tx\t/);
  assert.equal(pridejRadky(tsv, [{ snimek: "74", datum: "1918-01-17", typ: "Z", osoby: "y" }]).pridano, 0);
});

function falesnyGitHub() {
  const volani = [];
  const soubory = { "ondrnovy/mapa-matrik:data/soa-plzen/kozlany-22.json": JSON.stringify({ schema: 1, archive: "soa-plzen", points: [], records: {}, sources: [] }) };
  const fetchFn = async (url, opt) => {
    const cesta = url.replace("https://api.github.com", "");
    volani.push(`${opt.method} ${cesta.split("?")[0]}`);
    const ok = d => new Response(JSON.stringify(d), { status: 200 });
    let m;
    if ((m = cesta.match(/^\/repos\/([^/]+\/[^/]+)\/contents\/([^?]+)/))) {
      const obsah = soubory[`${m[1]}:${decodeURI(m[2])}`];
      return obsah ? ok({ content: Buffer.from(obsah).toString("base64") }) : new Response("", { status: 404 });
    }
    if (cesta.includes("/git/ref/heads/main")) return ok({ object: { sha: "abc" } });
    if (cesta.includes("/git/commits/abc")) return ok({ tree: { sha: "t0" } });
    if (cesta.endsWith("/git/trees")) return ok({ sha: "t1" });
    if (cesta.endsWith("/git/commits")) return ok({ sha: "c1" });
    if (cesta.endsWith("/git/refs") || cesta.endsWith("/merge-upstream")) return ok({});
    if (cesta.endsWith("/pulls")) return ok({ html_url: `https://github.com${cesta.replace("/repos", "").replace("/pulls", "/pull/1")}` });
    return new Response("?", { status: 500 });
  };
  return { fetchFn, volani };
}

const ENV = { GITHUB_TOKEN: "x", REPO_MAPA: "ondrnovy/mapa-matrik", REPO_INDEXU: "pe-pan/matriky-index", FORK_INDEXU: "ondrnovy/matriky-index" };

test("celý požadavek: dva PR", async () => {
  const { fetchFn, volani } = falesnyGitHub();
  const req = new Request("https://s.example/v1/prispevek", { method: "POST", body: JSON.stringify({ body: [BOD], zapisy: [ZAPIS] }) });
  const r = await worker.fetch(req, ENV, {}, fetchFn);
  const data = await r.json();
  assert.equal(r.status, 200, JSON.stringify(data));
  assert.match(data.mapa, /mapa-matrik\/pull/);
  assert.match(data.index, /pe-pan\/matriky-index\/pull/);
  assert.ok(volani.includes("POST /repos/ondrnovy/matriky-index/merge-upstream"));
  assert.ok(!volani.some(v => /merge$|\/merges/.test(v) && !v.includes("merge-upstream")), "schránka nic neslučuje");
});

test("špatný požadavek: 400, bez volání GitHubu", async () => {
  const { fetchFn, volani } = falesnyGitHub();
  const r = await worker.fetch(new Request("https://s.example/v1/prispevek", { method: "POST", body: "{" }), ENV, {}, fetchFn);
  assert.equal(r.status, 400);
  assert.equal(volani.length, 0);
});
