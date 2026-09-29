// A execução real do M1.6b (T13, V-18 e V-19): o roteiro que abre as telas num navegador de
// verdade, contra a stack de pé, e grava as capturas e as conferências.
//
// Roda na imagem oficial do Playwright, na rede do contêiner `frontend` — o comando está no
// plano (docs/planos/M1.6b-as-telas.md, "A execução real"). Não entra na CI nem no
// package.json da aplicação.
//
// Saída: frontend/e2e/capturas/*.png e frontend/e2e/capturas/resultado.json. Sai com código
// diferente de 0 se alguma conferência falhar — inclusive por erro de página (`pageerror`).
// A medida da taxa grava frontend/e2e/capturas/resultado-taxa.json e não apaga o resto.
//
// M1.6c (RF-17, docs/planos/M1.6c-fundamentos-e-contexto.md, "A execução real"): confere as
// seções Fundamentos e Comunicados no ITUB4, no IBOV e na companhia do mockup, e ganha três
// chaves, que entram por `-e` no `docker run`:
//   RUVOR_E2E_SOB_DEMANDA  padrão 1; com 0, o passo sob demanda não roda nem é conferido
//   RUVOR_E2E_MEDIR_TAXA   padrão 0; com 1, só a medida da taxa roda (nada mais)
//   RUVOR_E2E_EMPRESA      o ticker da companhia do mockup (a T0 do M1.6c escolheu PETR4)

import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { chromium } from "playwright";

const BASE = process.env.RUVOR_E2E_BASE ?? "http://localhost:5173";
const OUT = path.resolve("capturas");

const ON_DEMAND = (process.env.RUVOR_E2E_SOB_DEMANDA ?? "1") !== "0";
const MEASURE_RATE = (process.env.RUVOR_E2E_MEDIR_TAXA ?? "0") === "1";
const COMPANY = (process.env.RUVOR_E2E_EMPRESA ?? "").trim().toUpperCase() || null;

// A medida da taxa: a janela da taxa do anônimo é de um minuto; 65 s sem pedido a esvaziam.
const RATE_IDLE_MS = 65_000;
// Teto de cargas da medida: a 60/min e catorze pedidos por carga, o 429 chega na quinta.
const RATE_MAX_LOADS = 30;

// Cópia de SUGESTOES em frontend/src/content/sugestoes.ts: o roteiro só enxerga frontend/e2e.
const SUGESTOES = ["ITUB4", "PETR4", "VALE3", "BBDC4", "IBOV"];

// A chave do tema (frontend/src/theme.ts) e o fundo de cada tema (--ruvor-canvas em
// brand/ruvor/tokens.css), para conferir que a captura saiu no tema pedido.
const THEME_KEY = "ruvor-theme";
const CANVAS = { light: "#EEECE8", dark: "#1A1B1E" };

const FINAL_STATES = ["E1", "E3", "E6", "E7"];
const MAX_CANDIDATES = 3;
const RF24_LIMIT_MS = 2000;

// As cinco capturas por página: 1440×900 e 360×800, com a chave em claro e em escuro, e
// 1440×900 com a chave em sistema e o sistema escuro.
const VARIANTS = [
  { id: "1440-claro", width: 1440, height: 900, theme: "light", scheme: "light", expect: "light" },
  { id: "1440-escuro", width: 1440, height: 900, theme: "dark", scheme: "light", expect: "dark" },
  { id: "360-claro", width: 360, height: 800, theme: "light", scheme: "light", expect: "light" },
  { id: "360-escuro", width: 360, height: 800, theme: "dark", scheme: "light", expect: "dark" },
  { id: "1440-sistema-escuro", width: 1440, height: 900, theme: "system", scheme: "dark", expect: "dark" },
];

const result = {
  base: BASE,
  started_at: new Date().toISOString(),
  keys: { on_demand: ON_DEMAND, measure_rate: MEASURE_RATE, company: COMPANY },
  checks: [],
  sections: [],
  rate: null,
  captures: [],
  pages: {},
  on_demand: { attempts: [], computed: null },
  rf24: null,
  suggestions: null,
  page_errors: [],
};

function check(name, ok, detail = {}) {
  result.checks.push({ name, ok: Boolean(ok), ...detail });
  console.log(`${ok ? "ok  " : "FALHOU"}  ${name}${Object.keys(detail).length ? ` ${JSON.stringify(detail)}` : ""}`);
  return Boolean(ok);
}

// Registra o tempo em que `data-ready="true"` apareceu pela primeira vez, a partir do início
// da navegação (`performance.now()` conta do `timeOrigin`), e alarga o buffer do
// PerformanceResourceTiming — o Vite de desenvolvimento serve cada módulo num pedido.
function initScript({ key, theme }) {
  if (theme !== null) {
    try {
      window.localStorage.setItem(key, theme);
    } catch {
      // sem armazenamento, a tela segue no padrão
    }
  }
  try {
    performance.setResourceTimingBufferSize(5000);
  } catch {
    // sem ajuste do buffer
  }
  const mark = () => {
    if (window.__readyAt === undefined && document.querySelector('[data-ready="true"]')) {
      window.__readyAt = performance.now();
    }
  };
  new MutationObserver(mark).observe(document, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["data-ready"],
  });
}

async function newContext(browser, variant) {
  const context = await browser.newContext({
    viewport: { width: variant.width, height: variant.height },
    colorScheme: variant.scheme,
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
  });
  await context.addInitScript(initScript, { key: THEME_KEY, theme: variant.theme });
  return context;
}

function watchErrors(page, where) {
  page.on("pageerror", (error) => {
    result.page_errors.push({ where, message: String(error?.message ?? error) });
  });
}

/** Espera a tela assentar: sem esqueleto, sem `aria-busy`, a rede parada. */
async function settle(page) {
  await page
    .waitForFunction(
      () =>
        document.querySelector(".ruvor-skeleton") === null &&
        document.querySelector('[aria-busy="true"]') === null,
      null,
      { timeout: 30_000, polling: 200 },
    )
    .catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
  await page.waitForTimeout(500);
}

/** A captura e as conferências dela: sem rolagem horizontal, no tema pedido. */
async function capture(page, name, variant) {
  const facts = await page.evaluate(() => {
    const root = document.documentElement;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      dataTheme: root.getAttribute("data-theme"),
      canvas: getComputedStyle(root).getPropertyValue("--ruvor-canvas").trim(),
      pressed: [...document.querySelectorAll('.ruvor-segmented__btn[aria-pressed="true"]')].map(
        (b) => b.textContent,
      ),
      sectionErrors: document.querySelectorAll('[role="alert"]').length,
      riskState: document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state") ?? null,
    };
  });
  const file = `${name}-${variant.id}.png`;
  await page.screenshot({ path: path.join(OUT, file), fullPage: true });
  result.captures.push({ file, ...facts });
  check(`${file}: sem rolagem horizontal`, facts.scrollWidth <= facts.clientWidth, {
    scrollWidth: facts.scrollWidth,
    clientWidth: facts.clientWidth,
  });
  check(`${file}: no tema ${variant.expect}`, facts.canvas.toUpperCase() === CANVAS[variant.expect], {
    canvas: facts.canvas,
    dataTheme: facts.dataTheme,
  });
  check(`${file}: a chave em ${variant.theme}`, facts.dataTheme === (variant.theme === "system" ? null : variant.theme), {
    dataTheme: facts.dataTheme,
    pressed: facts.pressed,
  });
  return facts;
}

/** Passo 1: a busca, com `itub` digitado e o ITUB4 na lista. */
async function searchPage(browser, variant) {
  const context = await newContext(browser, variant);
  const page = await context.newPage();
  watchErrors(page, `busca ${variant.id}`);
  await page.goto(`${BASE}/`);
  const box = page.getByRole("combobox");
  await box.fill("itub");
  const option = page.locator('[role="option"] a[href="/ativos/ITUB4"]');
  const found = await option
    .waitFor({ state: "visible", timeout: 15_000 })
    .then(() => true)
    .catch(() => false);
  check(`busca ${variant.id}: "itub" lista o ITUB4`, found, {
    options: await page.locator('[role="option"]').count(),
  });
  await settle(page);
  await capture(page, "busca", variant);
  await context.close();
}

/** As duas seções do M1.6c fora do carregando (ou o teto de 30 s). */
async function sectionsSettled(page) {
  return page
    .waitForFunction(
      () =>
        ["fundamentals", "disclosures"].every((name) => {
          const el = document.querySelector(`[data-section="${name}"]`);
          return el !== null && el.getAttribute("data-state") !== "loading";
        }),
      null,
      { timeout: 30_000, polling: 200 },
    )
    .then(() => true)
    .catch(() => false);
}

/** O que as marcas das duas seções dizem (docs/planos/M1.6c, "As marcas para a execução real"). */
function sectionFacts(page) {
  return page.evaluate(() => {
    const of = (name) => {
      const el = document.querySelector(`[data-section="${name}"]`);
      if (el === null) return null;
      return {
        state: el.getAttribute("data-state"),
        company: el.getAttribute("data-company"),
        alerts: el.querySelectorAll('[role="alert"]').length,
        nullReasons: [...el.querySelectorAll("[data-null-reason]")].map((n) => n.getAttribute("data-null-reason")),
        peers: [...el.querySelectorAll("[data-peer-k]")].map((n) => ({
          k: n.getAttribute("data-peer-k"),
          n: n.getAttribute("data-peer-n"),
        })),
        links: el.querySelectorAll("[data-disclosure-link]").length,
      };
    };
    return { fundamentals: of("fundamentals"), disclosures: of("disclosures") };
  });
}

/**
 * As conferências das seções (RF-17): presentes, fora do carregando, sem `[role="alert"]`; e o
 * que cada página deve mostrar — `bank` (ITUB4), `index` (IBOV), `company` (a do mockup).
 */
function checkSections(label, facts, expect) {
  result.sections.push({ page: label, expect, ...facts });
  for (const name of ["fundamentals", "disclosures"]) {
    const s = facts[name];
    check(`${label}: a seção ${name} presente`, s !== null);
    if (s === null) continue;
    check(`${label}: a seção ${name} fora do carregando`, s.state !== null && s.state !== "loading", {
      state: s.state,
    });
    check(`${label}: a seção ${name} sem [role="alert"]`, s.alerts === 0, { alerts: s.alerts });
  }
  const f = facts.fundamentals;
  const d = facts.disclosures;
  if (f === null || d === null) return;
  if (expect === "bank") {
    check(`${label}: Fundamentos com a frase do plano bank`, f.nullReasons.includes("plan:bank"), {
      nullReasons: [...new Set(f.nullReasons)],
    });
    check(`${label}: ao menos um comunicado com link`, d.links > 0, { links: d.links, company: d.company });
  } else if (expect === "index") {
    check(`${label}: Fundamentos vazia (índice)`, f.state === "empty", { state: f.state });
    check(`${label}: Comunicados vazia (índice)`, d.state === "empty", { state: d.state });
    check(`${label}: Comunicados com data-company none-index`, d.company === "none-index", {
      company: d.company,
    });
  } else if (expect === "company") {
    check(`${label}: ao menos um indicador com a posição entre os pares`, f.peers.length > 0, {
      peers: f.peers,
    });
    check(`${label}: ao menos um comunicado com link`, d.links > 0, { links: d.links, company: d.company });
  }
}

/** Passos 2 e 3: a tela do ativo pelo carregamento direto, em cada variação. */
async function assetPage(browser, ticker, variant, expectState, expectSections = null) {
  const context = await newContext(browser, variant);
  const page = await context.newPage();
  watchErrors(page, `${ticker} ${variant.id}`);
  const response = await page.goto(`${BASE}/ativos/${ticker}`);
  const ready = await page
    .locator('[data-ready="true"]')
    .first()
    .waitFor({ timeout: 60_000 })
    .then(() => true)
    .catch(() => false);
  check(`${ticker} ${variant.id}: carregamento direto chega a data-ready`, ready && response?.ok(), {
    status: response?.status(),
  });
  if (expectSections !== null) await sectionsSettled(page);
  await settle(page);
  if (expectSections !== null) {
    checkSections(`${ticker} ${variant.id}`, await sectionFacts(page), expectSections);
  }
  const facts = await capture(page, ticker, variant);
  if (expectState !== null) {
    check(`${ticker} ${variant.id}: data-risk-state ${expectState}`, facts.riskState === expectState, {
      riskState: facts.riskState,
    });
  }
  check(`${ticker} ${variant.id}: nenhuma seção em erro`, facts.sectionErrors === 0, {
    sectionErrors: facts.sectionErrors,
  });
  await context.close();
  return facts;
}

async function allAssets(request) {
  const all = [];
  let offset = 0;
  for (;;) {
    const response = await request.get(`${BASE}/api/v1/assets?limit=100&offset=${offset}`);
    if (!response.ok()) throw new Error(`/api/v1/assets offset=${offset}: ${response.status()}`);
    const page = await response.json();
    all.push(...page.results);
    offset += page.limit;
    if (offset >= page.count || page.results.length === 0) break;
  }
  return all;
}

/** Passo 5: a medida do RF-24 — a segunda carga do ITUB4, sem cache HTTP. */
async function measure(browser) {
  const variant = VARIANTS[0];
  const context = await newContext(browser, variant);
  const page = await context.newPage();
  watchErrors(page, "medida ITUB4");
  // No Playwright, interceptar as rotas desliga o cache HTTP do navegador.
  await page.route("**/*", (r) => r.continue());

  const loads = [];
  for (let i = 0; i < 2; i += 1) {
    const sizes = {};
    const onResponse = async (resp) => {
      if (resp.url().includes("/api/v1/")) {
        try {
          sizes[new URL(resp.url()).pathname] = (await resp.body()).length;
        } catch {
          // corpo indisponível
        }
      }
    };
    page.on("response", onResponse);
    await page.goto(`${BASE}/ativos/ITUB4`);
    await page.waitForFunction(() => window.__readyAt !== undefined, null, {
      timeout: 60_000,
      polling: 50,
    });
    await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
    page.off("response", onResponse);
    const timing = await page.evaluate(() => {
      const nav = performance.getEntriesByType("navigation")[0];
      return {
        ready_ms: window.__readyAt,
        dom_content_loaded_ms: nav?.domContentLoadedEventEnd ?? null,
        load_ms: nav?.loadEventEnd ?? null,
        resources_total: performance.getEntriesByType("resource").length,
        api: performance
          .getEntriesByType("resource")
          .filter((e) => e.name.includes("/api/v1/"))
          .map((e) => ({
            path: new URL(e.name).pathname,
            start_ms: Math.round(e.startTime),
            response_end_ms: Math.round(e.responseEnd),
            duration_ms: Math.round(e.duration),
            ttfb_ms: Math.round(e.responseStart - e.requestStart),
            transfer_size: e.transferSize,
            encoded_body_size: e.encodedBodySize,
            decoded_body_size: e.decodedBodySize,
          })),
      };
    });
    loads.push({ ...timing, body_bytes: sizes });
  }
  await context.close();

  const second = loads[1];
  const prices = second.api.find((e) => e.path.endsWith("/prices"));
  result.rf24 = {
    first_load: loads[0],
    second_load: second,
    second_ready_ms: Math.round(second.ready_ms),
    prices_bytes: second.body_bytes["/api/v1/assets/ITUB4/prices"] ?? prices?.decoded_body_size ?? null,
    limit_ms: RF24_LIMIT_MS,
  };
  console.log(`medida: segunda carga do ITUB4 em ${Math.round(second.ready_ms)} ms`);
  for (const e of second.api) {
    console.log(`  ${e.path}: ${e.duration_ms} ms (início ${e.start_ms} ms, fim ${e.response_end_ms} ms, ${e.decoded_body_size} B)`);
  }
  check("RF-24: a segunda carga do ITUB4 até data-ready em até 2 s", second.ready_ms <= RF24_LIMIT_MS, {
    ready_ms: Math.round(second.ready_ms),
  });
  check("RF-24: as cinco rotas do ativo medidas", second.api.length >= 5, {
    paths: second.api.map((e) => e.path),
  });
}

/** Passo 4: um ativo sem preço, pedido pela tela, até três candidatos. */
async function onDemand(browser, request) {
  const assets = await allAssets(request);
  const candidates = assets
    .filter((a) => a.status === "active" && a.kind === "stock" && a.has_prices === false)
    .map((a) => a.ticker);
  result.on_demand.candidates_total = candidates.length;
  result.on_demand.candidates_first = candidates.slice(0, MAX_CANDIDATES);

  for (const ticker of candidates.slice(0, MAX_CANDIDATES)) {
    const attempt = { ticker };
    result.on_demand.attempts.push(attempt);
    const variant = VARIANTS[0];
    const context = await newContext(browser, variant);
    const page = await context.newPage();
    watchErrors(page, `sob demanda ${ticker}`);
    await page.goto(`${BASE}/ativos/${ticker}`);
    await page.locator('[data-ready="true"]').first().waitFor({ timeout: 60_000 });
    const stateOf = () =>
      page.evaluate(
        () => document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state") ?? null,
      );
    attempt.initial_state = await stateOf();

    const button = page.getByRole("button", { name: "Calcular o risco" });
    if ((await button.count()) === 0) {
      attempt.outcome = "sem botão";
      console.log(`sob demanda ${ticker}: sem o botão "Calcular o risco" (estado ${attempt.initial_state})`);
      await context.close();
      continue;
    }

    const clickedAt = Date.now();
    await button.click();
    const started = await page
      .waitForFunction(
        () => ["E4", "E5"].includes(document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state")),
        null,
        { timeout: 30_000, polling: 100 },
      )
      .then(() => true)
      .catch(() => false);
    attempt.started_state = await stateOf();
    attempt.started_after_ms = Date.now() - clickedAt;
    if (!started) {
      attempt.outcome = "não entrou em E4/E5 em 30 s";
      console.log(`sob demanda ${ticker}: não entrou em E4/E5 (estado ${attempt.started_state})`);
      await context.close();
      continue;
    }

    const finished = await page
      .waitForFunction(
        (finals) => finals.includes(document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state")),
        FINAL_STATES,
        { timeout: 600_000, polling: 500 },
      )
      .then(() => true)
      .catch(() => false);
    attempt.final_state = await stateOf();
    attempt.elapsed_ms = Date.now() - clickedAt;
    const risk = await (await request.get(`${BASE}/api/v1/assets/${ticker}/risk`)).json();
    attempt.request = risk.request;
    attempt.latest = risk.latest
      ? { status: risk.latest.status, as_of_date: risk.latest.as_of_date, calculated_at: risk.latest.calculated_at }
      : null;
    console.log(
      `sob demanda ${ticker}: ${attempt.final_state} em ${(attempt.elapsed_ms / 1000).toFixed(1)} s` +
        ` (pedido ${risk.request?.status ?? "-"}: ${risk.request?.reason ?? "-"})`,
    );

    if (finished && attempt.final_state === "E1") {
      attempt.outcome = "E1";
      await settle(page);
      await page.screenshot({ path: path.join(OUT, `sob-demanda-${ticker}-E1.png`), fullPage: true });
      result.captures.push({ file: `sob-demanda-${ticker}-E1.png`, riskState: "E1" });
      await context.close();
      result.on_demand.computed = { ticker, elapsed_ms: attempt.elapsed_ms };
      return ticker;
    }
    attempt.outcome = finished ? attempt.final_state : "sem estado final em 10 min";
    await context.close();
  }
  return null;
}

/** Passo 6: as sugestões conferidas contra a busca completa. */
async function suggestions(request) {
  const assets = await allAssets(request);
  const byTicker = new Map(assets.map((a) => [a.ticker, a]));
  const listed = SUGESTOES.map((t) => ({ ticker: t, has_prices: byTicker.get(t)?.has_prices ?? null }));
  const others = assets.filter((a) => a.has_prices && !SUGESTOES.includes(a.ticker)).map((a) => a.ticker);
  result.suggestions = { catalog: assets.length, listed, others_with_prices: others };
  check("sugestões: as cinco têm has_prices", listed.every((s) => s.has_prices === true), { listed });
  console.log(`sugestões: outros com preço fora da lista: ${others.length ? others.join(", ") : "nenhum"}`);
}

/**
 * A medida da taxa (RF-17), com a taxa padrão do anônimo: 65 s sem pedido; depois o ITUB4 em
 * sequência, uma carga por vez até o `data-ready` e as duas seções fora do carregando, sem pedido
 * `/api/v1/` em voo quando a próxima começa; conta os pedidos pela rede do Playwright até a
 * primeira resposta 429. Carga completa é a que terminou sem nenhum 429.
 */
async function measureRate(browser) {
  console.log(`medida da taxa: ${RATE_IDLE_MS / 1000} s sem pedido`);
  await new Promise((resolve) => setTimeout(resolve, RATE_IDLE_MS));

  const variant = VARIANTS[0];
  const context = await newContext(browser, variant);
  const page = await context.newPage();
  watchErrors(page, "medida da taxa");
  // Sem cache HTTP do navegador: todo pedido chega ao servidor.
  await page.route("**/*", (r) => r.continue());

  const isApi = (url) => new URL(url).pathname.startsWith("/api/v1/");
  let requests = 0;
  let inFlight = 0;
  let first429 = null;
  let loadRequests = 0;
  let load429 = false;
  // Por carga: as respostas por status e os pedidos que falharam sem resposta (o `StrictMode`
  // aborta o primeiro efeito de cada rota).
  let loadStatuses = {};
  let loadFailed = 0;
  page.on("request", (req) => {
    if (!isApi(req.url())) return;
    requests += 1;
    loadRequests += 1;
    inFlight += 1;
  });
  const done = (req) => {
    if (isApi(req.url())) inFlight -= 1;
  };
  page.on("requestfinished", done);
  page.on("response", (resp) => {
    if (isApi(resp.url())) loadStatuses[resp.status()] = (loadStatuses[resp.status()] ?? 0) + 1;
  });
  page.on("requestfailed", (req) => {
    done(req);
    if (isApi(req.url())) loadFailed += 1;
  });
  page.on("response", (resp) => {
    if (!isApi(resp.url()) || resp.status() !== 429) return;
    load429 = true;
    if (first429 === null) {
      // `requests` já contou este pedido: o número inclui o que recebeu o 429.
      first429 = { path: new URL(resp.url()).pathname, requests_so_far: requests, retry_after: resp.headers()["retry-after"] ?? null };
    }
  });

  const loads = [];
  let complete = 0;
  const started = Date.now();
  for (let i = 1; i <= RATE_MAX_LOADS && first429 === null; i += 1) {
    loadRequests = 0;
    load429 = false;
    loadStatuses = {};
    loadFailed = 0;
    const t0 = Date.now();
    await page.goto(`${BASE}/ativos/ITUB4`);
    const settled = await page
      .waitForFunction(
        () =>
          document.querySelector('[data-ready="true"]') !== null &&
          ["fundamentals", "disclosures"].every((name) => {
            const el = document.querySelector(`[data-section="${name}"]`);
            return el !== null && el.getAttribute("data-state") !== "loading";
          }),
        null,
        { timeout: 60_000, polling: 100 },
      )
      .then(() => true)
      .catch(() => false);
    // Nenhum pedido em voo antes da próxima carga.
    const deadline = Date.now() + 30_000;
    while (inFlight > 0 && Date.now() < deadline) await page.waitForTimeout(50);
    await page.waitForTimeout(200);
    while (inFlight > 0 && Date.now() < deadline) await page.waitForTimeout(50);
    const entry = {
      load: i,
      requests: loadRequests,
      got_429: load429,
      statuses: loadStatuses,
      failed: loadFailed,
      settled,
      in_flight_at_end: inFlight,
      elapsed_ms: Date.now() - t0,
      since_start_ms: Date.now() - started,
    };
    loads.push(entry);
    console.log(`  carga ${i}: ${loadRequests} pedidos ${JSON.stringify(loadStatuses)}, ${loadFailed} sem resposta${load429 ? ", com 429" : ""}${settled ? "" : ", sem assentar"} (${entry.elapsed_ms} ms)`);
    if (!load429) {
      if (!settled) break;
      complete += 1;
    }
  }
  await context.close();

  result.rate = {
    idle_ms: RATE_IDLE_MS,
    complete_loads: complete,
    requests_until_first_429: first429?.requests_so_far ?? null,
    first_429: first429,
    total_requests: requests,
    loads,
  };
  console.log(
    `medida da taxa: ${complete} cargas completas; ${first429?.requests_so_far ?? "-"} pedidos até o primeiro 429` +
      ` (${first429?.path ?? "sem 429"})`,
  );
  check("taxa: chegou a um 429", first429 !== null, { loads: loads.length });
  check("taxa: toda carga antes do 429 assentou", loads.every((l) => l.got_429 || l.settled), {
    unsettled: loads.filter((l) => !l.got_429 && !l.settled).map((l) => l.load),
  });
  check("taxa: nenhum pedido em voo entre cargas", loads.every((l) => l.in_flight_at_end === 0), {
    in_flight: loads.map((l) => l.in_flight_at_end),
  });
}

async function main() {
  // A medida da taxa não apaga as capturas das conferências: grava o próprio resultado ao lado.
  if (!MEASURE_RATE) await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  const browser = await chromium.launch();
  const request = (await browser.newContext()).request;
  try {
    if (MEASURE_RATE) {
      // Só a medida da taxa (RF-17): nada antes dela pede a API.
      await measureRate(browser);
    } else {
      // 1 e 3: a busca.
      for (const variant of VARIANTS) {
        await searchPage(browser, variant);
      }
      // 2 e 3: ITUB4, IBOV e a companhia do mockup pelo carregamento direto, com as seções.
      check("RUVOR_E2E_EMPRESA definida", COMPANY !== null, { company: COMPANY });
      const pages = [
        ["ITUB4", "bank"],
        ["IBOV", "index"],
      ];
      if (COMPANY !== null) pages.push([COMPANY, "company"]);
      for (const [ticker, expectSections] of pages) {
        for (const variant of VARIANTS) {
          await assetPage(browser, ticker, variant, "E1", expectSections);
        }
      }
      // 5: a medida, antes do cálculo sob demanda, para o worker ocupado não pesar na máquina.
      await measure(browser);
      // 4: um ativo sem preço, pedido pela tela — só com RUVOR_E2E_SOB_DEMANDA diferente de 0.
      if (ON_DEMAND) {
        const computed = await onDemand(browser, request);
        if (check("sob demanda: um ativo sem preço chega a E1 em até três candidatos", computed !== null, {
          attempts: result.on_demand.attempts.map((a) => ({ ticker: a.ticker, outcome: a.outcome })),
        })) {
          for (const variant of VARIANTS) {
            await assetPage(browser, computed, variant, "E1");
          }
        }
      } else {
        result.on_demand = { skipped: "RUVOR_E2E_SOB_DEMANDA=0" };
        console.log("sob demanda: não roda (RUVOR_E2E_SOB_DEMANDA=0)");
      }
      // 6: as sugestões.
      await suggestions(request);
    }
  } catch (error) {
    check("o roteiro correu até o fim", false, { error: String(error?.stack ?? error) });
  } finally {
    await browser.close();
  }

  // O erro de página reprova (RF-17; o M1.6b só juntava).
  check("nenhum erro de página", result.page_errors.length === 0, { page_errors: result.page_errors });

  result.finished_at = new Date().toISOString();
  result.ok = result.checks.every((c) => c.ok);
  await writeFile(path.join(OUT, MEASURE_RATE ? "resultado-taxa.json" : "resultado.json"), `${JSON.stringify(result, null, 2)}\n`);
  const failed = result.checks.filter((c) => !c.ok);
  console.log(`\n${result.checks.length} conferências, ${failed.length} falharam; ${result.captures.length} capturas em ${OUT}`);
  if (result.page_errors.length) console.log(`erros de página: ${JSON.stringify(result.page_errors)}`);
  process.exitCode = failed.length === 0 ? 0 : 1;
}

await main();
