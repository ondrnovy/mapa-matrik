// Sběrná schránka: přijme orientační body a přepsané zápisy bez účtu GitHub a založí z nich pull requesty
// do Mapy matrik (ondrnovy/mapa-matrik) a indexu matrik (pe-pan/matriky-index). Sama nic neslučuje – kontrola
// a sloučení zůstávají v GitHub Actions obou repozitářů. Popis: schranka/README.md.

export const LIMIT_BAJTU = 256 * 1024;
export const MAX_BODU = 500;
export const MAX_ZAPISU = 200;
export const ZA_DEN_Z_IP = 10;
export const ZA_DEN_CELKEM = 300;
const ARCHIVY_MAPY = { "soa-plzen": "portafontium", "soa-praha": "ebadatelna" };
const ARCHIVY_INDEXU = ["portafontium", "soapraha", "ahmp"];
const DRUHY = new Set(["N", "O", "Z", "iN", "iO", "iZ", "title", "blank"]);
const LHUTA = { N: 100, O: 75, Z: 75 };
const ID = /^[a-z0-9][a-z0-9-]{0,80}$/;
const TEXT = /^[^\t\r\n]{0,600}$/;

export class Chyba extends Error {
  constructor(kod, zprava) { super(zprava); this.kod = kod; }
}

function text(v, pole, max = 600) {
  if (v === undefined || v === null || v === "") return undefined;
  if (typeof v !== "string" || v.length > max || !TEXT.test(v)) throw new Chyba(400, `pole ${pole}: text bez tabulátorů a nových řádků, nejvýš ${max} znaků`);
  return v.trim();
}

function cislo(v, pole, min, max) {
  if (v === undefined || v === null || v === "") return undefined;
  if (!Number.isInteger(v) || v < min || v > max) throw new Chyba(400, `pole ${pole}: celé číslo ${min}–${max}`);
  return v;
}

// Bod do mapy: kniha (archiv + id + popis pro novou knihu) a jeden orientační bod. Jména osob v bodech nejsou (zásada mapy).
export function overBod(b, letos) {
  if (!b || typeof b !== "object") throw new Chyba(400, "bod musí být objekt");
  if (!(b.archive in ARCHIVY_MAPY)) throw new Chyba(400, `archiv ${b.archive} schránka nezná (zná ${Object.keys(ARCHIVY_MAPY).join(", ")})`);
  if (!ID.test(String(b.portal_id || ""))) throw new Chyba(400, "portal_id: malá písmena, číslice, pomlčky");
  const p = { scan: cislo(b.scan, "scan", 1, 100000) };
  if (p.scan === undefined) throw new Chyba(400, "bod potřebuje scan");
  if (b.type !== undefined && !DRUHY.has(b.type)) throw new Chyba(400, `type ${b.type} neznámý`);
  p.type = b.type;
  p.year = cislo(b.year, "year", 1500, letos);
  p.year_to = cislo(b.year_to, "year_to", 1500, letos);
  for (const k of ["months", "page", "place", "letters"]) p[k] = text(b[k], k, 60);
  p.note = text(b.note, "note", 300);
  for (const k of Object.keys(p)) if (p[k] === undefined) delete p[k];
  const kniha = {
    signature: text(b.signature, "signature", 120),
    url: text(b.url, "url", 300),
    scans: cislo(b.scans, "scans", 1, 100000),
  };
  if (kniha.url && !/^https:\/\/(www\.portafontium\.eu|ebadatelna\.soapraha\.cz)\//.test(kniha.url)) throw new Chyba(400, "url knihy musí vést na portál archivu");
  return { archive: b.archive, portal_id: String(b.portal_id), bod: p, kniha };
}

// Zápis do indexu: řádek precteno.tsv (formát indexu) + kniha. Jen zápisy starší lhůt indexu.
export function overZapis(z, letos) {
  if (!z || typeof z !== "object") throw new Chyba(400, "zápis musí být objekt");
  const archiv = ARCHIVY_INDEXU.includes(z.archiv) ? z.archiv : undefined;
  if (!archiv) throw new Chyba(400, `archiv zápisu ${z.archiv} schránka nezná (zná ${ARCHIVY_INDEXU.join(", ")})`);
  const kniha = String(z.kniha || "");
  if (!ID.test(kniha)) throw new Chyba(400, "kniha: malá písmena, číslice, pomlčky");
  if (!["N", "O", "Z"].includes(z.typ)) throw new Chyba(400, "typ zápisu N, O nebo Z");
  const datum = text(z.datum, "datum", 20);
  const rok = Number((datum || "").match(/\d{4}/)?.[0]);
  if (!rok || rok < 1500) throw new Chyba(400, "datum zápisu s rokem (1817-03-12, 1817-03, ~1817)");
  if (rok > letos - LHUTA[z.typ]) throw new Chyba(400, `zápis ${z.typ} z roku ${rok} je mladší než ${LHUTA[z.typ]} let – do veřejného indexu nepatří`);
  const radek = {
    snimek: text(String(z.snimek ?? ""), "snimek", 20), datum, typ: z.typ,
    obec: text(z.obec, "obec", 120) || "", osoby: text(z.osoby, "osoby"), ostatni: text(z.ostatni, "ostatni") || "",
    jistota: text(z.jistota, "jistota", 20), cetl: text(z.cetl, "cetl", 200),
  };
  if (!radek.snimek) throw new Chyba(400, "zápis potřebuje snímek");
  if (!radek.osoby) throw new Chyba(400, "zápis potřebuje osoby");
  if (!/^(vysoká|střední|nízká)/.test(radek.jistota || "")) throw new Chyba(400, "jistota: vysoká, střední nebo nízká");
  if (!/[a-z][a-z0-9.-]*\/[a-z0-9]+/i.test(radek.cetl || "")) throw new Chyba(400, "cetl musí obsahovat model/effort (např. claude-opus-5-5/high)");
  const nazev = text(z.nazev, "nazev", 200);
  const url = text(z.url, "url", 300);
  return { archiv, kniha, radek, nazev, url };
}

export function overPrispevek(data, letos = new Date().getUTCFullYear()) {
  if (!data || typeof data !== "object") throw new Chyba(400, "očekávám JSON objekt");
  const body = Array.isArray(data.body) ? data.body : [];
  const zapisy = Array.isArray(data.zapisy) ? data.zapisy : [];
  if (!body.length && !zapisy.length) throw new Chyba(400, "prázdný příspěvek");
  if (body.length > MAX_BODU || zapisy.length > MAX_ZAPISU) throw new Chyba(413, `nejvýš ${MAX_BODU} bodů a ${MAX_ZAPISU} zápisů najednou`);
  return { body: body.map(b => overBod(b, letos)), zapisy: zapisy.map(z => overZapis(z, letos)) };
}

// ---------- úprava dat (stejně jako tools/sdileni.py ve skillu rodokmen) ----------

export function pridejBody(vol, body, dnes) {
  let pridano = 0;
  for (const p of body) {
    p.by = "schranka";
    const stejny = q => ["scan", "type", "year", "place", "letters"].every(k => (q[k] ?? null) === (p[k] ?? null));
    if (vol.points.some(stejny)) continue;
    vol.points.push(p);
    pridano++;
    if (["N", "O", "Z"].includes(p.type) && p.year) {
      const roky = [...String(vol.records[p.type] || "").matchAll(/\d{4}/g)].map(m => Number(m[0])).concat(p.year);
      const a = Math.min(...roky), b = Math.max(...roky);
      vol.records[p.type] = a === b ? String(a) : `${a}–${b}`;
    }
  }
  vol.points.sort((a, b) => a.scan - b.scan);
  if (pridano && !vol.sources.some(s => s.by === "schranka" && s.date === dnes)) vol.sources.push({ by: "schranka", date: dnes });
  return pridano;
}

export function novaKniha(archive, portal_id, kniha, dnes) {
  const podpis = kniha.signature || portal_id;
  const vol = {
    schema: 1, archive, portal: ARCHIVY_MAPY[archive], portal_id,
    url: kniha.url || (archive === "soa-plzen" ? `https://www.portafontium.eu/register/soap-pn/${portal_id}` : `https://ebadatelna.soapraha.cz/d/${portal_id}/`),
    signature: podpis, parish: podpis.replace(/\s+\d+\w*$/, "") || podpis, records: {}, points: [], sources: [],
  };
  if (kniha.scans) vol.scans = kniha.scans;
  return vol;
}

export const HLAVICKA = ["snimek", "datum", "typ", "obec", "osoby", "ostatni", "jistota", "cetl", "odkaz"];

export function pridejRadky(tsv, radky) {
  const lines = tsv ? tsv.replace(/\n+$/, "").split("\n") : [HLAVICKA.join("\t")];
  let pridano = 0;
  for (const r of radky) {
    const klic = [r.snimek, r.datum, r.typ].join("\t");
    if (lines.some(l => l.startsWith(klic + "\t"))) continue;
    lines.push(HLAVICKA.map(k => r[k] || "").join("\t"));
    pridano++;
  }
  return { tsv: lines.join("\n") + "\n", pridano };
}

export function knihaYaml(archiv, kniha, nazev, url) {
  const q = s => JSON.stringify(s);
  return [`archiv: ${q(archiv)}`, `kniha: ${q(kniha)}`, `nazev: ${q(nazev || kniha)}`, `url: ${q(url || "")}`,
    `obsah: ${q("snímek = číslo snímku na portálu; zatím jen jednotlivé zápisy")}`,
    `poznamka: ${q("zápisy přečtené při práci na rodokmenu, přišly sběrnou schránkou Mapy matrik; jen vybrané zápisy")}`, ""].join("\n");
}

// ---------- GitHub ----------

export function github(token, fetchFn = fetch) {
  return async function gh(metoda, cesta, telo) {
    const r = await fetchFn(`https://api.github.com${cesta}`, {
      method: metoda,
      headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "User-Agent": "mapa-matrik-schranka",
                 "X-GitHub-Api-Version": "2022-11-28", ...(telo ? { "Content-Type": "application/json" } : {}) },
      body: telo ? JSON.stringify(telo) : undefined,
    });
    if (r.status === 404 && metoda === "GET") return null;
    if (!r.ok) throw new Chyba(502, `GitHub ${metoda} ${cesta}: ${r.status} ${(await r.text()).slice(0, 200)}`);
    return r.status === 204 ? {} : r.json();
  };
}

function b64(s) {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

function z64(s) {
  const bin = atob(s.replace(/\n/g, ""));
  return new TextDecoder().decode(Uint8Array.from(bin, c => c.charCodeAt(0)));
}

async function soubor(gh, repo, cesta, ref) {
  const r = await gh("GET", `/repos/${repo}/contents/${encodeURI(cesta)}?ref=${ref}`);
  return r ? z64(r.content) : null;
}

async function commit(gh, repo, zakladSha, soubory, zprava, vetev) {
  const base = await gh("GET", `/repos/${repo}/git/commits/${zakladSha}`);
  const tree = await gh("POST", `/repos/${repo}/git/trees`, {
    base_tree: base.tree.sha,
    tree: Object.entries(soubory).map(([path, content]) => ({ path, mode: "100644", type: "blob", content })),
  });
  const c = await gh("POST", `/repos/${repo}/git/commits`, { message: zprava, tree: tree.sha, parents: [zakladSha] });
  await gh("POST", `/repos/${repo}/git/refs`, { ref: `refs/heads/${vetev}`, sha: c.sha });
}

export async function doMapy(gh, env, body, vetev, dnes) {
  const repo = env.REPO_MAPA;
  const main = await gh("GET", `/repos/${repo}/git/ref/heads/main`);
  const podleKnihy = new Map();
  for (const b of body) {
    const k = `${b.archive}/${b.portal_id}`;
    if (!podleKnihy.has(k)) podleKnihy.set(k, { ...b, body: [] });
    podleKnihy.get(k).body.push(b.bod);
  }
  const soubory = {};
  let pridano = 0;
  for (const [k, kn] of podleKnihy) {
    const cesta = `data/${k}.json`;
    const stary = await soubor(gh, repo, cesta, main.object.sha);
    const vol = stary ? JSON.parse(stary) : novaKniha(kn.archive, kn.portal_id, kn.kniha, dnes);
    vol.sources ||= [];
    vol.records ||= {};
    const n = pridejBody(vol, kn.body, dnes);
    if (n) { soubory[cesta] = JSON.stringify(vol, null, 1) + "\n"; pridano += n; }
  }
  if (!pridano) return null;
  await commit(gh, repo, main.object.sha, soubory, `Body ze schránky: ${pridano}`, vetev);
  const pr = await gh("POST", `/repos/${repo}/pulls`, {
    title: `Body ze schránky: ${pridano}`, head: vetev, base: "main",
    body: `Orientační body poslané sběrnou schránkou (bez účtu GitHub, skill rodokmen). Knih: ${Object.keys(soubory).length}.`,
  });
  return pr.html_url;
}

export async function doIndexu(gh, env, zapisy, vetev) {
  const fork = env.FORK_INDEXU, upstream = env.REPO_INDEXU;
  await gh("POST", `/repos/${fork}/merge-upstream`, { branch: "main" });
  const main = await gh("GET", `/repos/${fork}/git/ref/heads/main`);
  const podleKnihy = new Map();
  for (const z of zapisy) {
    const k = `knihy/${z.archiv}/${z.kniha}`;
    if (!podleKnihy.has(k)) podleKnihy.set(k, { ...z, radky: [] });
    podleKnihy.get(k).radky.push(z.radek);
  }
  const soubory = {};
  let pridano = 0;
  for (const [k, kn] of podleKnihy) {
    if (!(await soubor(gh, fork, `${k}/kniha.yaml`, main.object.sha))) soubory[`${k}/kniha.yaml`] = knihaYaml(kn.archiv, kn.kniha, kn.nazev, kn.url);
    const { tsv, pridano: n } = pridejRadky(await soubor(gh, fork, `${k}/precteno.tsv`, main.object.sha), kn.radky);
    if (n) { soubory[`${k}/precteno.tsv`] = tsv; pridano += n; }
  }
  if (!pridano) return null;
  await commit(gh, fork, main.object.sha, soubory, `Zápisy ze schránky Mapy matrik: ${pridano}`, vetev);
  const pr = await gh("POST", `/repos/${upstream}/pulls`, {
    title: `Zápisy z rodokmenu (schránka Mapy matrik): ${pridano} zápisů z ${podleKnihy.size} knih`,
    head: `${fork.split("/")[0]}:${vetev}`, base: "main",
    body: `Zápisy přečtené při práci na rodokmenu (skill rodokmen) od uživatele bez účtu GitHub, poslané sběrnou schránkou ` +
      `Mapy matrik (https://github.com/ondrnovy/mapa-matrik/tree/main/schranka). Kdo a čím četl, je u řádků ve sloupci \`cetl\`. ` +
      `Schránka hlídá formát a lhůty; kontrola indexu běží v tomto PR.\n\n- [x] přidávám jen nové řádky, cizí jsem neměnil(a)\n` +
      `- [x] žádné zápisy mladší než 100 let (narození) / 75 let (sňatky, úmrtí)\n- [x] data pod CC BY 4.0 (souhlas dal přispěvatel ve skillu)`,
  });
  return pr.html_url;
}

// ---------- limity a obsluha požadavku ----------

async function limit(env, ip, den) {
  if (!env.LIMITY) return;
  const klice = [`ip:${den}:${ip}`, `vse:${den}`];
  const [zIp, celkem] = await Promise.all(klice.map(k => env.LIMITY.get(k).then(v => Number(v || 0))));
  if (zIp >= ZA_DEN_Z_IP || celkem >= ZA_DEN_CELKEM) throw new Chyba(429, "denní limit schránky je vyčerpaný, zkus to zítra");
  await Promise.all([env.LIMITY.put(klice[0], String(zIp + 1), { expirationTtl: 2 * 86400 }),
                     env.LIMITY.put(klice[1], String(celkem + 1), { expirationTtl: 2 * 86400 })]);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 1), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}

export default {
  async fetch(request, env, ctx, fetchFn = fetch) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/") {
      return json({ schranka: "Mapa matrik", popis: "https://github.com/ondrnovy/mapa-matrik/tree/main/schranka", prijimam: "POST /v1/prispevek" });
    }
    if (request.method !== "POST" || url.pathname !== "/v1/prispevek") return json({ chyba: "POST /v1/prispevek" }, 404);
    try {
      const delka = Number(request.headers.get("Content-Length") || 0);
      if (delka > LIMIT_BAJTU) throw new Chyba(413, `nejvýš ${LIMIT_BAJTU / 1024} kB`);
      const surove = await request.text();
      if (surove.length > LIMIT_BAJTU) throw new Chyba(413, `nejvýš ${LIMIT_BAJTU / 1024} kB`);
      let data;
      try { data = JSON.parse(surove); } catch { throw new Chyba(400, "neplatný JSON"); }
      const prispevek = overPrispevek(data);
      const ted = new Date();
      const den = ted.toISOString().slice(0, 10);
      await limit(env, request.headers.get("CF-Connecting-IP") || "?", den);
      const gh = github(env.GITHUB_TOKEN, fetchFn);
      const vetev = `schranka-${ted.toISOString().replace(/[-:T]/g, "").slice(0, 14)}-${crypto.randomUUID().slice(0, 6)}`;
      const vysledek = {
        mapa: prispevek.body.length ? await doMapy(gh, env, prispevek.body, vetev, den) : null,
        index: prispevek.zapisy.length ? await doIndexu(gh, env, prispevek.zapisy, vetev) : null,
      };
      return json(vysledek);
    } catch (e) {
      const kod = e instanceof Chyba ? e.kod : 500;
      return json({ chyba: e instanceof Chyba ? e.message : "chyba schránky" }, kod);
    }
  },
};
