// A execução real do M2.2b (T11, RF-18, V-11): o caminho da carteira num navegador de verdade,
// contra a stack de pé — criar conta, entrar, criar uma carteira de duas ações com histórico, a
// composição inválida recusada, editar os pesos (versão 2), pedir o cálculo e acompanhar até
// pronto (uma vez), ler a perda em % e em reais, as capturas de leitura, pedir de novo (o 409),
// o `insufficient_history` com o link da ação sem preço, arquivar por último e a barra logada sem
// rolagem horizontal (docs/planos/M2.2b-telas-da-carteira.md, "A execução real").
//
// Roda na imagem oficial do Playwright, na rede do contêiner `frontend`. Não entra na CI nem no
// package.json da aplicação. Quem roda é o orquestrador: o checkout principal no ramo, a stack de
// pé com o `worker` (o cálculo da carteira roda nele) e o Beat parado (`docker compose stop
// beat`). Do diretório raiz do checkout principal, no Git Bash:
//
//   1. as ações: duas com 503 pregões ou mais e uma ativa sem preço — da busca (5273 é o
//      RUVOR_PORT_FRONTEND desta máquina):
//
//      curl -s "http://localhost:5273/api/v1/assets?has_risk=true&limit=100"
//      curl -s "http://localhost:5273/api/v1/assets?has_risk=false&limit=100"
//
//   2. o roteiro:
//
//      MSYS_NO_PATHCONV=1 docker run --rm \
//        --network "container:$(docker compose ps -q frontend)" \
//        -v "$(pwd)/frontend/e2e:/e2e" -w /e2e \
//        -e RUVOR_E2E_BASE=http://localhost:5173 \
//        -e RUVOR_E2E_ACOES=ITUB4,PETR4 -e RUVOR_E2E_SEM_PRECO=<ticker sem preço> \
//        mcr.microsoft.com/playwright:v1.63.0-noble \
//        sh -c "npm ci --no-audit --no-fund && node carteira.mjs"
//
// As chaves (por `-e` no `docker run`):
//   RUVOR_E2E_BASE        padrão http://localhost:5173 (o Vite, de dentro da rede do `frontend`)
//   RUVOR_E2E_ACOES       as duas ações com histórico, separadas por vírgula (padrão ITUB4,PETR4)
//   RUVOR_E2E_SEM_PRECO   a ação ativa sem preço (obrigatória); conferida pela API antes de começar
//
// A conta é nova a cada execução (`signup`, organização pessoal), com o instante no e-mail. O
// roteiro faz **um** `signup` e **um** login — o limite `auth` (10 por minuto por IP) não chega
// perto. O cálculo roda **uma vez** (~2,5 min no `worker`); as capturas não o refazem.
//
// Saída: frontend/e2e/capturas/carteira/*.png e frontend/e2e/capturas/carteira/resultado.json —
// numa pasta própria; o `capturas.mjs` de sempre apaga `capturas/` inteira ao começar: guarde
// `capturas/carteira/` antes de rodá-lo. Sai com código diferente de 0 se alguma conferência
// falhar — inclusive por erro de página (`pageerror`) e por qualquer resposta 429 da API.

import { randomBytes } from "node:crypto";
import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { chromium } from "playwright";

const BASE = (process.env.RUVOR_E2E_BASE ?? "http://localhost:5173").replace(/\/+$/, "");
const STOCKS = (process.env.RUVOR_E2E_ACOES ?? "ITUB4,PETR4")
  .split(",")
  .map((t) => t.trim().toUpperCase())
  .filter(Boolean);
const NO_PRICE = (process.env.RUVOR_E2E_SEM_PRECO ?? "").trim().toUpperCase();

const OUT = path.resolve("capturas", "carteira");

// O instante da execução, em AAAAMMDDhhmmss, no e-mail e nos nomes.
const TS = new Date().toISOString().replace(/\D/g, "").slice(0, 14);
const USER = { name: "Pessoa Carteira E2E", email: `e2e-c-${TS}@exemplo.com`, password: newPassword() };
const MAIN = { name: `Carteira E2E ${TS}`, notional: "100000" };
const SHORT = { name: `Sem preço E2E ${TS}` };

// O cálculo da carteira: nove modelos no `worker` (~2,5 min); o teto da espera.
const COMPUTE_TIMEOUT_MS = 12 * 60_000;

// Os textos aprovados que o roteiro confere, copiados de frontend/src/content/textos.ts: o roteiro
// só enxerga frontend/e2e.
const TEXT = {
  nav: "Carteiras", // carteiras.nav
  name: "Nome", // carteiras.campo.nome
  notional: "Valor (opcional)", // carteiras.campo.valor
  picker: "Acrescentar ação", // carteiras.seletor.rotulo
  weight: (ticker) => `Peso de ${ticker}, em %`, // carteiras.peso.rotulo
  themeGroup: "Tema", // casco.tema.rotulo
  theme: { light: "Claro", dark: "Escuro" }, // casco.tema.claro, casco.tema.escuro
};

// A chave do tema (THEME_KEY em frontend/src/theme.ts) e o fundo de cada tema (--ruvor-canvas
// em brand/ruvor/tokens.css; o escuro em carvão quente desde a D-195).
const THEME_KEY = "ruvor-theme";
const CANVAS = { light: "#EEECE8", dark: "#110F0D" };

const VARIANTS = [
  { id: "1440-claro", width: 1440, height: 900, theme: "light" },
  { id: "1440-escuro", width: 1440, height: 900, theme: "dark" },
  { id: "360-claro", width: 360, height: 800, theme: "light" },
  { id: "360-escuro", width: 360, height: 800, theme: "dark" },
];

// As larguras da barra logada (as da T2 e da T11, com a barra estreita até 920 px).
const BAR_WIDTHS = [1440, 1024, 921, 920, 768, 720, 360];

const result = {
  base: BASE,
  started_at: new Date().toISOString(),
  ts: TS,
  stocks: STOCKS,
  no_price_ticker: NO_PRICE,
  email: USER.email,
  portfolio: null,
  short_portfolio: null,
  compute: null,
  checks: [],
  captures: [],
  requests: [],
  responses_429: [],
  page_errors: [],
};

function newPassword() {
  return `Rv-${randomBytes(12).toString("base64url")}`;
}

function check(name, ok, detail = {}) {
  result.checks.push({ name, ok: Boolean(ok), ...detail });
  console.log(`${ok ? "ok  " : "FALHOU"}  ${name}${Object.keys(detail).length ? ` ${JSON.stringify(detail)}` : ""}`);
  return Boolean(ok);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function initScript({ key, theme }) {
  try {
    if (window.localStorage.getItem(key) === null) window.localStorage.setItem(key, theme);
  } catch {
    // sem armazenamento, a tela segue no padrão
  }
}

async function newPage(context, where) {
  const page = await context.newPage();
  page.on("pageerror", (error) => {
    result.page_errors.push({ where, message: String(error?.message ?? error) });
  });
  page.on("response", (response) => {
    const url = new URL(response.url());
    if (!url.pathname.startsWith("/api/v1/")) return;
    const method = response.request().method();
    if (url.pathname.startsWith("/api/v1/portfolios")) {
      result.requests.push({ method, path: url.pathname + url.search, status: response.status() });
    }
    if (response.status() === 429) {
      result.responses_429.push({ where, url: response.url(), retry_after: response.headers()["retry-after"] ?? null });
    }
  });
  return page;
}

async function visible(locator, timeout = 30_000) {
  return locator
    .first()
    .waitFor({ state: "visible", timeout })
    .then(() => true)
    .catch(() => false);
}

/** Espera a tela assentar: sem esqueleto, sem `aria-busy`, a rede parada, as fontes prontas. */
async function settle(page) {
  await page
    .waitForFunction(
      () => document.querySelector(".ruvor-skeleton") === null && document.querySelector('[aria-busy="true"]') === null,
      null,
      { timeout: 30_000, polling: 200 },
    )
    .catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready.then(() => true)).catch(() => {});
  await page.waitForTimeout(300);
}

/** O tema pela chave de tema do casco (todas as telas da carteira estão no casco). */
async function setTheme(page, theme) {
  await page.emulateMedia({ colorScheme: theme });
  const group = page.locator(".ruvor-topbar").getByRole("group", { name: TEXT.themeGroup, exact: true });
  await group.getByRole("button", { name: TEXT.theme[theme], exact: true }).click();
  await page
    .waitForFunction((t) => document.documentElement.getAttribute("data-theme") === t, theme, { timeout: 15_000 })
    .catch(() => {});
}

async function noHorizontalScroll(page) {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
}

/** A captura, sem rolagem horizontal, no tema pedido; `element` recorta (o resultado). */
async function capture(page, name, variant, element = null) {
  const facts = await page.evaluate(() => {
    const root = document.documentElement;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      dataTheme: root.getAttribute("data-theme"),
      canvas: getComputedStyle(root).getPropertyValue("--ruvor-canvas").trim(),
    };
  });
  const file = `${name}-${variant.id}.png`;
  if (element === null) {
    await page.screenshot({ path: path.join(OUT, file), fullPage: true });
  } else {
    await element.screenshot({ path: path.join(OUT, file) });
  }
  result.captures.push({ file, ...facts });
  check(`${file}: sem rolagem horizontal`, facts.scrollWidth <= facts.clientWidth, {
    scrollWidth: facts.scrollWidth,
    clientWidth: facts.clientWidth,
  });
  check(`${file}: no tema ${variant.theme}`, facts.canvas.toUpperCase() === CANVAS[variant.theme], {
    canvas: facts.canvas,
    dataTheme: facts.dataTheme,
  });
}

async function step(name, fn) {
  console.log(`\n== ${name}`);
  try {
    await fn();
  } catch (error) {
    check(`${name}: correu até o fim`, false, { error: String(error?.stack ?? error) });
  }
}

/** Escolhe uma ação pelo seletor: digita o código e clica na opção dele, se escolhível. */
async function pick(page, ticker) {
  const input = page.getByRole("combobox", { name: TEXT.picker, exact: true });
  await input.fill(ticker);
  const option = page.locator('[role="option"]').filter({ hasText: ticker }).first();
  const shown = await visible(option, 15_000);
  const disabled = shown ? await option.getAttribute("aria-disabled") : null;
  if (shown && disabled !== "true") await option.click();
  return check(`o seletor oferece ${ticker} como escolhível`, shown && disabled !== "true", { disabled });
}

async function weight(page, ticker, text) {
  const field = page.getByRole("textbox", { name: TEXT.weight(ticker), exact: true });
  await field.fill(text);
  await field.blur();
}

/** Cria uma carteira pela tela e devolve o id, pela URL da página dela. */
async function createPortfolio(page, name, notional, holdings) {
  await page.goto(`${BASE}/carteiras`);
  await visible(page.locator('[data-screen="carteiras"]'));
  await settle(page);
  // Com a lista vazia, o botão é o "criar a primeira" do estado vazio; senão, o "Nova carteira".
  await page.locator('[data-part="nova"], [data-part="criar-primeira"]').first().click();
  const form = page.locator('[data-part="criacao"]');
  await visible(form, 10_000);
  await form.getByLabel(TEXT.name, { exact: true }).fill(name);
  if (notional !== null) await form.getByLabel(TEXT.notional, { exact: true }).fill(notional);
  for (const [ticker] of holdings) await pick(page, ticker);
  for (const [ticker, text] of holdings) await weight(page, ticker, text);
  // O peso digitado fica como foi digitado (RF-06): o editor nunca o reescreve.
  for (const [ticker, text] of holdings) {
    const value = await page.getByRole("textbox", { name: TEXT.weight(ticker), exact: true }).inputValue();
    check(`criação: o peso de ${ticker} fica "${text}" no campo`, value === text, { value });
  }
  await form.locator('[data-part="criar"]').click();
  await page.waitForURL(/\/carteiras\/[^/]+$/, { timeout: 30_000 });
  await visible(page.locator('[data-screen="carteira"]'));
  const id = decodeURIComponent(new URL(page.url()).pathname.split("/").pop());
  return id;
}

async function riskState(page) {
  return page.locator('[data-part="risco"]').getAttribute("data-risk-state").catch(() => null);
}

// --------------------------------------------------------------------------------- os passos

/** Antes de começar: as ações pela API — as duas com risco e preço, a sem preço ativa e sem preço. */
async function preflight(request) {
  for (const ticker of STOCKS) {
    const r = await request.get(`${BASE}/api/v1/assets?q=${ticker}&limit=5`);
    const item = (await r.json()).results?.find((a) => a.ticker === ticker) ?? null;
    check(`preflight: ${ticker} é ação ativa com preço`, item?.kind === "stock" && item?.status === "active" && item?.has_prices === true, { item });
  }
  const r = await request.get(`${BASE}/api/v1/assets?q=${NO_PRICE}&limit=5`);
  const item = (await r.json()).results?.find((a) => a.ticker === NO_PRICE) ?? null;
  check(`preflight: ${NO_PRICE} é ação ativa sem preço`, item?.kind === "stock" && item?.status === "active" && item?.has_prices === false, { item });
}

/** Um signup e um login; antes de entrar, /carteiras mostra o aviso de quem não entrou, sem pedido. */
async function signIn(page) {
  await page.goto(`${BASE}/carteiras`);
  await visible(page.locator('[data-screen="carteiras"]'));
  await settle(page);
  const navAnon = await page.locator(".ruvor-nav--account").count();
  check('anônimo: sem o item "Carteiras" na barra', navAnon === 0, { count: navAnon });
  const before = result.requests.length;
  check("anônimo: /carteiras não pede nada à API das carteiras", before === 0, { requests: result.requests });
  const notice = page.locator(".ruvor-page-notice, .ruvor-state--signin").first();
  check("anônimo: /carteiras mostra o aviso de entrar", await visible(notice, 10_000));

  await page.goto(`${BASE}/cadastro`);
  await visible(page.locator('[data-screen="cadastro"]'));
  const form = page.locator('[data-screen="cadastro"] form');
  await form.locator('input[name="name"]').fill(USER.name);
  await form.locator('input[name="email"]').fill(USER.email);
  await form.locator('input[name="password"]').fill(USER.password);
  await form.locator('input[name="password_confirmation"]').fill(USER.password);
  await form.locator('button[type="submit"]').click();
  check("signup: logado", await visible(page.locator('[data-account="authenticated"]')), { url: page.url() });

  await page.locator('[data-part="conta"]').click();
  await page.locator('[data-part="menu-sair"]').click();
  await visible(page.locator('[data-account="anonymous"]'));

  await page.goto(`${BASE}/entrar?next=%2Fcarteiras`);
  const login = page.locator('[data-screen="entrada"] form');
  await visible(login);
  await login.locator('input[name="email"]').fill(USER.email);
  await login.locator('input[name="password"]').fill(USER.password);
  await login.locator('button[type="submit"]').click();
  const arrived = await page
    .waitForURL((url) => url.pathname === "/carteiras", { timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
  check("login: o next leva a /carteiras", arrived, { url: page.url() });
  const nav = page.locator(".ruvor-nav--account").getByRole("link", { name: TEXT.nav, exact: true });
  check('logado: o item "Carteiras" na barra', await visible(nav, 10_000));
  await settle(page);
}

/** Criar a carteira de duas ações (versão 1), com valor. */
async function create(page) {
  const [a, b] = STOCKS;
  const id = await createPortfolio(page, MAIN.name, MAIN.notional, [[a, "50"], [b, "50"]]);
  result.portfolio = id;
  check("criação: a página da carteira abre", id !== null && (await visible(page.locator('[data-screen="carteira"]'))), { url: page.url() });
  const post = result.requests.find((r) => r.method === "POST" && r.path === "/api/v1/portfolios");
  check("criação: o POST voltou 201", post?.status === 201, { post });
  await settle(page);
  const version = ((await page.locator('[data-part="versao"]').textContent()) ?? "").trim();
  check("criação: versão 1", version === "1", { version });
}

/** A composição inválida, recusada pela conferência do cliente sem PUT; depois os pesos válidos (versão 2). */
async function edit(page) {
  const [a, b] = STOCKS;
  await page.locator('[data-part="editar-composicao"]').first().click();
  await visible(page.getByRole("textbox", { name: TEXT.weight(a), exact: true }), 10_000);

  const putsBefore = result.requests.filter((r) => r.method === "PUT").length;
  await weight(page, a, "60");
  await weight(page, b, "30");
  await page.locator('[data-part="salvar-composicao"]').click();
  const refused = await visible(page.locator('[data-part="soma-erros"]'), 10_000);
  await sleep(1000);
  const putsAfter = result.requests.filter((r) => r.method === "PUT").length;
  check("composição inválida (60 + 30): recusada com a soma, sem PUT", refused && putsAfter === putsBefore, { putsBefore, putsAfter });

  // 60,5 + 39,5 — a vírgula aceita, a soma exata em 100,00.
  await weight(page, a, "60,5");
  await weight(page, b, "39,5");
  await page.locator('[data-part="salvar-composicao"]').click();
  const replied = await visible(page.locator('[data-part="resposta"]'), 30_000);
  const put = result.requests.filter((r) => r.method === "PUT").at(-1);
  check("edição: o PUT voltou 200", put?.status === 200, { put });
  await page
    .waitForFunction(() => document.querySelector('[data-part="versao"]')?.textContent?.trim() === "2", null, { timeout: 15_000 })
    .catch(() => {});
  const version = ((await page.locator('[data-part="versao"]').textContent()) ?? "").trim();
  check("edição: versão 2, com a resposta", replied && version === "2", { version });
  await settle(page);
}

/** Pedir o cálculo e acompanhar até pronto, uma vez. */
async function compute(page) {
  const state0 = await riskState(page);
  check("risco: antes do pedido, nunca calculado", state0 === "never", { state: state0 });
  const started = Date.now();
  await page.locator('[data-part="risco"] [data-part="pedido"]').click();
  const seen = new Set();
  let state = null;
  while (Date.now() - started < COMPUTE_TIMEOUT_MS) {
    state = await riskState(page);
    if (state !== null) seen.add(state);
    if (state === "ready" || state === "failed") break;
    await sleep(2000);
  }
  const elapsed = Math.round((Date.now() - started) / 1000);
  result.compute = { seconds: elapsed, states: [...seen], final: state };
  const post = result.requests.find((r) => r.method === "POST" && r.path.endsWith("/risk"));
  check("risco: o pedido voltou 202", post?.status === 202, { post });
  check("risco: passou por calculando", seen.has("calculating"), { states: [...seen] });
  check("risco: acompanhou até pronto", state === "ready", { state, seconds: elapsed });
  const polls = result.requests.filter((r) => r.method === "GET" && r.path.endsWith("/risk")).length;
  check("risco: a consulta repetida leu o GET .../risk mais de uma vez", polls > 2, { polls });
  await settle(page);
}

/** Ler o resultado: a perda em % e em reais, a data dos preços, os nove modelos, a trilha. */
async function readResult(page) {
  const section = page.locator('[data-part="risco"]');
  const pct = await section.locator('[data-phrase="perda"]').count();
  check("resultado: a frase da perda nos dois níveis", pct === 2, { count: pct });
  const brl = await section.locator('[data-part="perda-reais"]').count();
  const brlText = brl > 0 ? ((await section.locator('[data-part="perda-reais"]').first().textContent()) ?? "") : "";
  check("resultado: a perda em reais (com valor)", brl === 2 && brlText.includes("R$"), { count: brl, text: brlText.trim() });
  const asOf = ((await section.locator('[data-phrase="asOf"]').textContent()) ?? "").trim();
  check("resultado: a data dos preços", /\d{2}\/\d{2}\/\d{4}/.test(asOf), { asOf });
  const value = await section.locator('[data-phrase="valorAgora"]').count();
  check("resultado: a frase do valor de agora", value === 1, { count: value });

  // A tabela dos nove modelos, atrás do recolhível na leitura iniciante.
  const opener = section.locator("summary, button[aria-expanded]").filter({ hasText: /modelo/i }).first();
  if ((await opener.count()) > 0 && (await opener.getAttribute("aria-expanded")) === "false") await opener.click();
  await sleep(500);
  const rows = await section.locator("table tbody tr").count();
  check("resultado: os nove modelos nos dois níveis (18 linhas, ou 9 por nível)", rows === 18 || rows === 9, { rows });
  const trail = page.locator('[data-phrase="serie"]');
  if ((await trail.count()) === 0) {
    const t = page.locator(".ruvor-rail__inner summary, .ruvor-rail__inner button[aria-expanded]").first();
    if ((await t.count()) > 0) await t.click();
  }
  check("resultado: a trilha da carteira", await visible(page.locator('[data-phrase="serie"]'), 5_000));
}

/** As capturas de leitura: a lista, a carteira e o resultado, nos dois temas e nas duas larguras. */
async function captures(page) {
  const carteiraUrl = `${BASE}/carteiras/${encodeURIComponent(result.portfolio)}`;
  for (const variant of VARIANTS) {
    await page.setViewportSize({ width: variant.width, height: variant.height });
    await page.goto(`${BASE}/carteiras`);
    await visible(page.locator('[data-screen="carteiras"] [data-part="lista"]'));
    await setTheme(page, variant.theme);
    await settle(page);
    await capture(page, "lista", variant);

    await page.goto(carteiraUrl);
    await visible(page.locator('[data-part="risco"][data-risk-state="ready"]'));
    await setTheme(page, variant.theme);
    await settle(page);
    await capture(page, "carteira", variant);
    await capture(page, "resultado", variant, page.locator('[data-part="risco"]'));
  }
  const posts = result.requests.filter((r) => r.method === "POST" && r.path.endsWith("/risk")).length;
  check("capturas: sem pedido de cálculo novo", posts === 1, { posts });
}

/** Pedir de novo: o 409 portfolio_risk_up_to_date relê e diz a data. */
async function askAgain(page) {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${BASE}/carteiras/${encodeURIComponent(result.portfolio)}`);
  await visible(page.locator('[data-part="risco"][data-risk-state="ready"]'));
  await settle(page);
  await page.locator('[data-part="risco"] [data-part="pedido"]').click();
  const shown = await visible(page.locator('[data-part="atualizado"]'), 15_000);
  const text = shown ? ((await page.locator('[data-part="atualizado"]').textContent()) ?? "").trim() : "";
  const post = result.requests.filter((r) => r.method === "POST" && r.path.endsWith("/risk")).at(-1);
  check("pedir de novo: 409", post?.status === 409, { post });
  check("pedir de novo: a resposta com a data", shown && /\d{2}\/\d{2}\/\d{4}/.test(text), { text });
}

/** A carteira com a ação sem preço: o insufficient_history com o link à aba do risco dela. */
async function insufficient(page) {
  const [a] = STOCKS;
  const id = await createPortfolio(page, SHORT.name, null, [[a, "50"], [NO_PRICE, "50"]]);
  result.short_portfolio = id;
  await settle(page);
  await page.locator('[data-part="risco"] [data-part="pedido"]').click();
  const panel = page.locator('[data-part="historico-curto"]');
  check("sem preço: o painel do histórico curto", await visible(panel, 15_000));
  const post = result.requests.filter((r) => r.method === "POST" && r.path.endsWith("/risk")).at(-1);
  check("sem preço: o POST voltou 409 insufficient_history", post?.status === 409, { post });
  const group = panel.locator('[data-group="sem-preco"]');
  const link = group.getByRole("link");
  const href = (await link.count()) === 1 ? await link.getAttribute("href") : null;
  check(`sem preço: o link vai a /ativos/${NO_PRICE}/risco`, href === `/ativos/${NO_PRICE}/risco`, { href, links: await link.count() });
  const others = await panel.locator('[data-group="curtas"] a').count();
  check("sem preço: nenhum link fora das sem preço", others === 0, { others });
}

/** A barra logada sem rolagem horizontal, em cada largura. */
async function bar(page) {
  await page.goto(`${BASE}/carteiras`);
  await visible(page.locator('[data-screen="carteiras"]'));
  for (const width of BAR_WIDTHS) {
    await page.setViewportSize({ width, height: 900 });
    await page.waitForTimeout(300);
    const facts = await noHorizontalScroll(page);
    const navShown = await page.locator(".ruvor-nav--account").isVisible();
    check(`barra logada em ${width} px: sem rolagem horizontal, com "Carteiras"`, facts.scrollWidth <= facts.clientWidth && navShown, { ...facts, navShown });
  }
  await page.setViewportSize({ width: 1440, height: 900 });
}

/** Arquivar, por último: o diálogo, o DELETE e a volta à lista com o aviso. */
async function archive(page, id, name) {
  await page.goto(`${BASE}/carteiras/${encodeURIComponent(id)}`);
  await visible(page.locator('[data-screen="carteira"]'));
  await settle(page);
  const deletesBefore = result.requests.filter((r) => r.method === "DELETE").length;
  await page.locator('[data-part="arquivar"]').click();
  const dialog = await visible(page.locator('[data-part="confirmar-arquivar"]'), 10_000);
  check(`arquivar "${name}": o diálogo pede confirmação`, dialog);
  await sleep(500);
  const deletesOpen = result.requests.filter((r) => r.method === "DELETE").length;
  check(`arquivar "${name}": nada enviado antes de confirmar`, deletesOpen === deletesBefore, { deletesBefore, deletesOpen });
  await page.locator('[data-part="confirmar-arquivar"]').click();
  const back = await page
    .waitForURL((url) => url.pathname === "/carteiras", { timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
  const del = result.requests.filter((r) => r.method === "DELETE").at(-1);
  check(`arquivar "${name}": DELETE 204 e a volta à lista`, back && del?.status === 204, { del, url: page.url() });
  check(`arquivar "${name}": o aviso de arquivada`, await visible(page.locator('[data-part="arquivada"]'), 10_000));
}

// ------------------------------------------------------------------------------------ a ordem

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

if (NO_PRICE === "" || STOCKS.length !== 2) {
  console.error("RUVOR_E2E_SEM_PRECO é obrigatória, e RUVOR_E2E_ACOES precisa de duas ações");
  process.exit(2);
}

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  colorScheme: "light",
  locale: "pt-BR",
  timezoneId: "America/Sao_Paulo",
});
await context.addInitScript(initScript, { key: THEME_KEY, theme: "light" });
const page = await newPage(context, "carteira");

await step("preflight: as ações", () => preflight(context.request));
await step("entrar: um signup e um login", () => signIn(page));
await step("criar a carteira (versão 1)", () => create(page));
await step("a composição inválida e os pesos editados (versão 2)", () => edit(page));
await step("pedir o cálculo e acompanhar até pronto", () => compute(page));
await step("ler o resultado", () => readResult(page));
await step("as capturas de leitura", () => captures(page));
await step("pedir de novo (409)", () => askAgain(page));
await step("a ação sem preço (insufficient_history)", () => insufficient(page));
await step("a barra logada nas larguras", () => bar(page));
await step("arquivar, por último", async () => {
  await archive(page, result.short_portfolio, SHORT.name);
  await archive(page, result.portfolio, MAIN.name);
});

await browser.close();

check("nenhuma resposta 429 da API", result.responses_429.length === 0, { responses_429: result.responses_429 });
check("nenhum erro de página", result.page_errors.length === 0, { page_errors: result.page_errors });

result.finished_at = new Date().toISOString();
const failed = result.checks.filter((c) => !c.ok);
result.summary = { checks: result.checks.length, failed: failed.length };
await writeFile(path.join(OUT, "resultado.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(`\n${result.checks.length} conferências, ${failed.length} falhas`);
process.exit(failed.length === 0 ? 0 : 1);
