// A execução real do M2.1b (T16, RF-20, V-14): as telas de acesso num navegador de verdade,
// contra a stack de pé — criar conta, entrar, sair, o convite a calcular, a troca obrigatória,
// a gestão de usuários, o diálogo e o menu pelo teclado, o `logout` pelo proxy (RF-19), as
// capturas e a comparação com os mockups aprovados (docs/planos/M2.1b-telas-de-acesso.md,
// Tarefa 16, "A execução real" e "As marcas para o navegador").
//
// Roda na imagem oficial do Playwright, na rede do contêiner `frontend`. Não entra na CI nem no
// package.json da aplicação. Quem roda é o orquestrador: o checkout principal no ramo, a stack de
// pé e o Beat parado (`docker compose stop beat`). Do diretório raiz do checkout principal, no
// Git Bash:
//
//   1. a organização da execução — <ts> é o instante em AAAAMMDDhhmmss; a senha provisória sai
//      da segunda linha da saída ("admin <email> senha provisoria: <senha>"):
//
//      TS=$(date +%Y%m%d%H%M%S)
//      docker compose exec -T web python manage.py create_organization \
//        --name "E2E $TS" --slug "e2e-$TS" \
//        --admin-email "e2e-$TS@exemplo.com" --admin-name "Admin E2E"
//
//   2. o ticker sem risco: `active`, `stock`, sem `risk_run` fechada e sem preço — da busca, por
//      `has_risk=false` e `has_prices: false` (5273 é o RUVOR_PORT_FRONTEND desta máquina):
//
//      curl -s "http://localhost:5273/api/v1/assets?has_risk=false&limit=100" \
//        | .venv/Scripts/python.exe -c "import json,sys; print(next(a['ticker'] for a in json.load(sys.stdin)['results'] if a['status']=='active' and a['kind']=='stock' and a['has_prices'] is False))"
//
//   3. o roteiro:
//
//      MSYS_NO_PATHCONV=1 docker run --rm \
//        --network "container:$(docker compose ps -q frontend)" \
//        -v "$(pwd)/frontend/e2e:/e2e" -w /e2e \
//        -e RUVOR_E2E_BASE=http://localhost:5173 \
//        -e RUVOR_E2E_ADMIN_EMAIL="e2e-$TS@exemplo.com" -e RUVOR_E2E_ADMIN_SENHA='<senha>' \
//        -e RUVOR_E2E_SEM_RISCO=<ticker sem risco> \
//        mcr.microsoft.com/playwright:v1.63.0-noble \
//        sh -c "npm ci --no-audit --no-fund && node acesso.mjs"
//
// A senha provisória vale uma vez: o passo 4 a troca. **Cada execução pede uma organização
// nova** (o passo 1 de novo, com outro <ts>).
//
// As chaves (por `-e` no `docker run`):
//   RUVOR_E2E_BASE         padrão http://localhost:5173 (o Vite, de dentro da rede do `frontend`)
//   RUVOR_E2E_ADMIN_EMAIL  a administradora do `create_organization` (obrigatória)
//   RUVOR_E2E_ADMIN_SENHA  a senha provisória dela (obrigatória)
//   RUVOR_E2E_SEM_RISCO    o ticker sem risco (obrigatória); conferido pela API antes de começar
//
// Saída: frontend/e2e/capturas/acesso/*.png e frontend/e2e/capturas/acesso/resultado.json —
// numa pasta própria, que o `capturas.mjs` não sobrescreve com o resultado dele; mas o
// `capturas.mjs` de sempre apaga `capturas/` inteira ao começar: guarde `capturas/acesso/` antes
// de rodá-lo. Sai com código diferente de 0 se alguma conferência falhar — inclusive por erro de
// página (`pageerror`) e por qualquer resposta 429 da API.
//
// O limite `auth` (10 por minuto por IP, sem variável): o roteiro conta os pedidos de `signup`,
// `login` e `password` que faz e espera 65 s antes do 9.º de cada janela; o `resultado.json`
// diz quantas esperas houve. O `logout` não conta. O roteiro faz sete desses pedidos.
//
// A comparação com os mockups (passo 7): cada mockup aberto pelo Vite, em
// ${RUVOR_E2E_BASE}/@fs/repo/docs/mockups/M2.1b/<arquivo>.html?moldura=0&<estado de base>, com o
// tema fixado por `setAttribute("data-theme", t)`; a tela, no estado da tabela de "As marcas", com
// o tema pela chave de tema do casco (fora do casco, a mesma chave `ruvor-theme` gravada e a
// página recarregada — a entrada, o cadastro e a troca obrigatória não têm a chave na tela). Cada
// `data-part` existe uma vez nos dois, e `color`, `background-color`, `font-size` e `font-weight`
// calculados são iguais, e a largura difere em no máximo 2 px, em 1440 e 360 px, claro e escuro.

import { randomBytes } from "node:crypto";
import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { chromium } from "playwright";

const BASE = (process.env.RUVOR_E2E_BASE ?? "http://localhost:5173").replace(/\/+$/, "");
const ADMIN_EMAIL = (process.env.RUVOR_E2E_ADMIN_EMAIL ?? "").trim();
const ADMIN_TEMP = process.env.RUVOR_E2E_ADMIN_SENHA ?? "";
const NO_RISK = (process.env.RUVOR_E2E_SEM_RISCO ?? "").trim().toUpperCase();

const OUT = path.resolve("capturas", "acesso");
const MOCKUPS = `${BASE}/@fs/repo/docs/mockups/M2.1b`;

// O instante da execução, em AAAAMMDDhhmmss, nos e-mails criados.
const TS = new Date().toISOString().replace(/\D/g, "").slice(0, 14);
const USER = { name: "Pessoa E2E", email: `e2e-u-${TS}@exemplo.com`, password: newPassword() };
const MEMBER = { name: "Membro E2E", email: `e2e-m-${TS}@exemplo.com`, temp: null, password: newPassword() };
const ADMIN_NEW = newPassword();

// O limite `auth` (DEFAULT_THROTTLE_RATES["auth"] = "10/min", backend/config/settings.py).
const AUTH_BEFORE_WAIT = 8;
const AUTH_WAIT_MS = 65_000;

// Os textos aprovados que o roteiro confere, copiados de frontend/src/content/textos.ts: o roteiro
// só enxerga frontend/e2e.
const TEXT = {
  credentials: "E-mail ou senha incorretos.", // acesso.erro.credenciais
  manageUsers: "Usuários da organização", // conta.menu.usuarios
  continue: "Continuar", // senha.sucesso.continuar
  themeGroup: "Tema", // casco.tema.rotulo
  theme: { light: "Claro", dark: "Escuro" }, // casco.tema.claro, casco.tema.escuro
};

// A chave do tema (THEME_KEY em frontend/src/theme.ts) e o fundo de cada tema (--ruvor-canvas
// em brand/ruvor/tokens.css), para conferir que a captura saiu no tema pedido.
const THEME_KEY = "ruvor-theme";
const CANVAS = { light: "#EEECE8", dark: "#1A1B1E" };

// As quatro variações das capturas (passo 6) e da comparação (passo 7).
const VARIANTS = [
  { id: "1440-claro", width: 1440, height: 900, theme: "light" },
  { id: "1440-escuro", width: 1440, height: 900, theme: "dark" },
  { id: "360-claro", width: 360, height: 800, theme: "light" },
  { id: "360-escuro", width: 360, height: 800, theme: "dark" },
];

// Os pares de "As marcas para o navegador" (a lista fechada do plano): o mockup, o estado de base
// dele pela URL e os `data-part` comparados.
const PAIRS = {
  entrada: {
    file: "entrada.html",
    query: "vista=tela&estado=vazio",
    parts: ["cena", "form", "titulo", "campo-email", "campo-senha", "nota-senha", "botao-entrar", "link-cadastro", "link-continuar"],
  },
  cadastro: {
    file: "cadastro.html",
    query: "vista=tela&estado=vazio",
    parts: ["cena", "form", "campo-nome", "campo-email", "campo-senha", "campo-confirmacao", "dica-senha", "botao-criar"],
  },
  senhaVoluntaria: {
    file: "senha.html",
    query: "modo=voluntaria&estado=vazio&vista=tela",
    parts: ["form", "campo-atual", "campo-nova", "campo-confirmacao", "dica-senha", "botao-trocar"],
  },
  senhaObrigatoria: {
    file: "senha.html",
    query: "modo=obrigatoria&estado=vazio&vista=tela",
    parts: ["cena", "form-obrigatoria", "botao-sair"],
  },
  contaAnonimo: {
    file: "conta.html",
    query: "vista=e8&sessao=anonimo",
    parts: ["barra", "entrar"],
  },
  contaLogado: {
    file: "conta.html",
    query: "vista=e8&sessao=logado&org=admin",
    parts: ["barra", "conta", "avatar"],
  },
  contaMenu: {
    file: "conta.html",
    query: "vista=e8&sessao=logado&org=admin&menu=aberto",
    parts: ["menu", "menu-nome", "menu-organizacao", "menu-sair"],
  },
  contaConvite: {
    file: "conta.html",
    query: "vista=e8&sessao=anonimo",
    parts: ["convite"],
  },
  usuarios: {
    file: "usuarios.html",
    query: "vista=lista",
    parts: ["lista", "linha", "linha-voce", "form-criar", "botao-criar"],
  },
};
const STYLE_KEYS = ["color", "backgroundColor", "fontSize", "fontWeight"];
const WIDTH_TOLERANCE_PX = 2;

const result = {
  base: BASE,
  started_at: new Date().toISOString(),
  ts: TS,
  admin_email: ADMIN_EMAIL,
  no_risk_ticker: NO_RISK,
  emails: { user: USER.email, member: MEMBER.email },
  auth: { requests: [], waits: 0, wait_ms: AUTH_WAIT_MS },
  checks: [],
  captures: [],
  comparisons: [],
  differences: [],
  responses_429: [],
  page_errors: [],
};

function newPassword() {
  // Sem o instante nem o nome: o `UserAttributeSimilarityValidator` recusaria a parecida com o
  // e-mail. Doze bytes aleatórios passam dos dez caracteres e não são só número nem comuns.
  return `Rv-${randomBytes(12).toString("base64url")}`;
}

function check(name, ok, detail = {}) {
  result.checks.push({ name, ok: Boolean(ok), ...detail });
  console.log(`${ok ? "ok  " : "FALHOU"}  ${name}${Object.keys(detail).length ? ` ${JSON.stringify(detail)}` : ""}`);
  return Boolean(ok);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Antes de cada `signup`, `login` ou `password`: espera 65 s antes do 9.º da janela. */
let authInWindow = 0;
async function authRequest(label) {
  if (authInWindow >= AUTH_BEFORE_WAIT) {
    result.auth.waits += 1;
    console.log(`limite auth: ${AUTH_WAIT_MS / 1000} s de espera antes de "${label}"`);
    await sleep(AUTH_WAIT_MS);
    authInWindow = 0;
  }
  authInWindow += 1;
  result.auth.requests.push({ label, at: new Date().toISOString(), in_window: authInWindow });
}

/** Grava o tema na chave antes da primeira carga, se ainda não houver escolha. */
function initScript({ key, theme }) {
  try {
    if (window.localStorage.getItem(key) === null) window.localStorage.setItem(key, theme);
  } catch {
    // sem armazenamento, a tela segue no padrão
  }
}

async function newContext(browser, variant = VARIANTS[0]) {
  const context = await browser.newContext({
    viewport: { width: variant.width, height: variant.height },
    colorScheme: variant.theme,
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
  });
  await context.addInitScript(initScript, { key: THEME_KEY, theme: variant.theme });
  return context;
}

async function newPage(context, where) {
  const page = await context.newPage();
  page.on("pageerror", (error) => {
    result.page_errors.push({ where, message: String(error?.message ?? error) });
  });
  page.on("response", (response) => {
    if (response.status() === 429 && new URL(response.url()).pathname.startsWith("/api/v1/")) {
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

async function gone(locator, timeout = 30_000) {
  return locator
    .first()
    .waitFor({ state: "detached", timeout })
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

/**
 * O tema da tela: no casco, pela chave de tema (o botão "Claro"/"Escuro"); fora dele, a mesma
 * chave `ruvor-theme` gravada e a página recarregada. Devolve `true` se recarregou — quem chama
 * espera a tela de novo.
 */
async function setScreenTheme(page, theme) {
  await page.emulateMedia({ colorScheme: theme });
  const group = page.locator(".ruvor-topbar").getByRole("group", { name: TEXT.themeGroup, exact: true });
  let reloaded = false;
  if ((await group.count()) > 0) {
    await group.getByRole("button", { name: TEXT.theme[theme], exact: true }).click();
  } else {
    await page.evaluate(([key, value]) => window.localStorage.setItem(key, value), [THEME_KEY, theme]);
    await page.reload();
    reloaded = true;
  }
  await page
    .waitForFunction((t) => document.documentElement.getAttribute("data-theme") === t, theme, { timeout: 15_000 })
    .catch(() => {});
  return reloaded;
}

/** A variação na tela: a largura, o tema e, se recarregou, a espera pelo seletor da tela. */
async function applyVariant(page, variant, readySelector) {
  await page.setViewportSize({ width: variant.width, height: variant.height });
  const reloaded = await setScreenTheme(page, variant.theme);
  if (reloaded) await visible(page.locator(readySelector), 30_000);
  await settle(page);
}

/** Passo 6: a captura, sem rolagem horizontal, no tema pedido. */
async function capture(page, name, variant) {
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
  await page.screenshot({ path: path.join(OUT, file), fullPage: true });
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

/** Os estilos calculados e a largura de cada `data-part`, como estão agora. */
function readParts(page, parts) {
  return page.evaluate((names) => {
    const out = {};
    for (const name of names) {
      const all = document.querySelectorAll(`[data-part="${name}"]`);
      if (all.length === 0) {
        out[name] = { count: 0 };
        continue;
      }
      const el = all[0];
      const cs = getComputedStyle(el);
      out[name] = {
        count: all.length,
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        fontSize: cs.fontSize,
        fontWeight: cs.fontWeight,
        width: el.getBoundingClientRect().width,
      };
    }
    return out;
  }, parts);
}

// O mockup, numa página própria; a leitura de cada (par, variação) uma vez só.
let mockPage = null;
let mockUrl = null;
const mockCache = new Map();

async function readMockup(pairId, variant) {
  const key = `${pairId}|${variant.id}`;
  if (mockCache.has(key)) return mockCache.get(key);
  const pair = PAIRS[pairId];
  const url = `${MOCKUPS}/${pair.file}?moldura=0&${pair.query}`;
  await mockPage.setViewportSize({ width: variant.width, height: variant.height });
  if (mockUrl !== url) {
    const response = await mockPage.goto(url);
    mockUrl = url;
    check(`mockup ${pair.file}?${pair.query}: abre pelo Vite`, response?.ok(), { status: response?.status(), url });
    await visible(mockPage.locator(`[data-part="${pair.parts[0]}"]`), 15_000);
  }
  await mockPage.emulateMedia({ colorScheme: variant.theme });
  await mockPage.evaluate((t) => document.documentElement.setAttribute("data-theme", t), variant.theme);
  await mockPage.evaluate(() => document.fonts.ready.then(() => true)).catch(() => {});
  await mockPage.waitForTimeout(200);
  const parts = await readParts(mockPage, pair.parts);
  mockCache.set(key, parts);
  return parts;
}

/**
 * Passo 7: um par, numa variação — a tela já no estado da tabela, na largura e no tema da
 * variação. Toda diferença vai ao `resultado.json`, e qualquer uma reprova.
 */
async function compare(page, pairId, variant) {
  const pair = PAIRS[pairId];
  const mock = await readMockup(pairId, variant);
  const app = await readParts(page, pair.parts);
  const differences = [];
  for (const name of pair.parts) {
    const m = mock[name];
    const a = app[name];
    if (m.count !== 1 || a.count !== 1) {
      differences.push({ part: name, what: "count", mockup: m.count, tela: a.count });
      if (m.count === 0 || a.count === 0) continue;
    }
    for (const prop of STYLE_KEYS) {
      if (m[prop] !== a[prop]) differences.push({ part: name, what: prop, mockup: m[prop], tela: a[prop] });
    }
    if (Math.abs(m.width - a.width) > WIDTH_TOLERANCE_PX) {
      differences.push({ part: name, what: "width", mockup: m.width, tela: a.width });
    }
  }
  const label = `${pair.file} [${pairId}] ${variant.id}`;
  result.comparisons.push({ pair: pairId, file: pair.file, query: pair.query, variant: variant.id, mockup: mock, tela: app, differences });
  for (const d of differences) result.differences.push({ pair: pairId, variant: variant.id, ...d });
  check(`comparação ${label}: sem diferença`, differences.length === 0, differences.length ? { differences } : {});
}

/** Abre o menu de conta e espera ele à vista. */
async function openMenu(page) {
  await page.locator('[data-part="conta"]').click();
  return visible(page.locator('[data-part="menu"]'), 10_000);
}

/** Um `step` que falha não derruba os seguintes: a falha vira conferência reprovada. */
async function step(name, fn) {
  console.log(`\n== ${name}`);
  try {
    await fn();
  } catch (error) {
    check(`${name}: correu até o fim`, false, { error: String(error?.stack ?? error) });
  }
}

// --------------------------------------------------------------------------------- os passos

/** Antes de tudo: o ticker sem risco é `active`, `stock`, sem `risk_run` fechada nem em curso. */
async function preconditions(request) {
  check("RUVOR_E2E_ADMIN_EMAIL definida", ADMIN_EMAIL !== "");
  check("RUVOR_E2E_ADMIN_SENHA definida", ADMIN_TEMP !== "");
  check("RUVOR_E2E_SEM_RISCO definida", NO_RISK !== "");
  if (ADMIN_EMAIL === "" || ADMIN_TEMP === "" || NO_RISK === "") return false;
  const asset = await request.get(`${BASE}/api/v1/assets/${encodeURIComponent(NO_RISK)}`);
  const body = asset.ok() ? await asset.json() : null;
  const risk = await request.get(`${BASE}/api/v1/assets/${encodeURIComponent(NO_RISK)}/risk`);
  const riskBody = risk.ok() ? await risk.json() : null;
  const facts = {
    http: asset.status(),
    status: body?.status ?? null,
    kind: body?.kind ?? null,
    risk_http: risk.status(),
    latest: riskBody?.latest ?? null,
    in_progress: riskBody?.in_progress ?? null,
    // Só registrado: um pedido aberto tira o convite (E4/E5), e o passo 3 reprova por ele.
    request: riskBody?.request ?? null,
  };
  result.no_risk_facts = facts;
  return check(
    `${NO_RISK}: active, stock, sem risk_run fechada nem em curso`,
    facts.http === 200 && facts.status === "active" && facts.kind === "stock" && facts.risk_http === 200 && facts.latest === null && facts.in_progress === null,
    facts,
  );
}

/** Passo 1: criar conta pela tela → logado com o nome; sair → anônimo. */
async function step1(page) {
  await page.goto(`${BASE}/cadastro`);
  check("passo 1: /cadastro abre a tela de cadastro", await visible(page.locator('[data-screen="cadastro"]')));
  const form = page.locator('[data-screen="cadastro"] form');
  await form.locator('input[name="name"]').fill(USER.name);
  await form.locator('input[name="email"]').fill(USER.email);
  await form.locator('input[name="password"]').fill(USER.password);
  await form.locator('input[name="password_confirmation"]').fill(USER.password);
  await authRequest("signup (passo 1)");
  await form.locator('button[type="submit"]').click();
  const signedIn = await visible(page.locator('[data-account="authenticated"]'));
  const name = signedIn ? ((await page.locator(".ruvor-account__name").first().textContent()) ?? "").trim() : null;
  check('passo 1: depois do cadastro, data-account="authenticated" com o nome', signedIn && name === USER.name, {
    name,
    expected: USER.name,
    url: page.url(),
  });

  await openMenu(page);
  await page.locator('[data-part="menu-sair"]').click();
  check('passo 1: sair → data-account="anonymous"', await visible(page.locator('[data-account="anonymous"]')), { url: page.url() });
}

/** Passo 2: a senha errada → o texto aprovado; a certa, com o `next` → `/ativos/ITUB4`. */
async function step2(page) {
  await page.goto(`${BASE}/entrar?next=%2Fativos%2FITUB4`);
  check("passo 2: /entrar abre a tela de entrada", await visible(page.locator('[data-screen="entrada"]')));
  const form = page.locator('[data-screen="entrada"] form');
  await form.locator('input[name="email"]').fill(USER.email);
  await form.locator('input[name="password"]').fill(`${USER.password}-errada`);
  await authRequest("login com a senha errada (passo 2)");
  await form.locator('button[type="submit"]').click();
  const alert = form.locator('[role="alert"]');
  const shown = await visible(alert, 15_000);
  const text = shown ? ((await alert.first().textContent()) ?? "").trim() : null;
  check(`passo 2: a senha errada mostra "${TEXT.credentials}"`, text === TEXT.credentials, { text });

  await form.locator('input[name="password"]').fill(USER.password);
  await authRequest("login (passo 2)");
  await form.locator('button[type="submit"]').click();
  const arrived = await page
    .waitForURL((url) => url.pathname === "/ativos/ITUB4", { timeout: 15_000 })
    .then(() => true)
    .catch(() => false);
  check("passo 2: a senha certa, a partir de /entrar?next=%2Fativos%2FITUB4, leva a /ativos/ITUB4", arrived, { url: page.url() });
  check('passo 2: logado, data-account="authenticated"', await visible(page.locator('[data-account="authenticated"]')));
}

/** Passo 3, anônimo, e a comparação do convite (passo 7) na mesma carga. */
async function step3Anonymous(page) {
  await page.goto(`${BASE}/ativos/${NO_RISK}`);
  await visible(page.locator('[data-ready="true"]'), 60_000);
  const invite = await visible(page.locator('[data-risk-invite="signin"]'));
  const compute = await page.locator('[data-risk-invite="compute"]').count();
  const buttons = await page.locator('[data-risk-invite] button').count();
  check(`passo 3: anônimo em /ativos/${NO_RISK} → data-risk-invite="signin", sem o botão`, invite && compute === 0 && buttons === 0, {
    compute,
    buttons,
    riskState: await page.evaluate(() => document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state") ?? null),
  });
  for (const variant of VARIANTS) {
    await applyVariant(page, variant, '[data-risk-invite="signin"]');
    await compare(page, "contaConvite", variant);
  }
}

/** Passo 3, logado: o botão de calcular à vista, sem clicar. */
async function step3SignedIn(page) {
  await page.goto(`${BASE}/ativos/${NO_RISK}`);
  await visible(page.locator('[data-ready="true"]'), 60_000);
  const invite = await visible(page.locator('[data-risk-invite="compute"]'));
  const buttons = await page.locator('[data-risk-invite="compute"] button').count();
  const signin = await page.locator('[data-risk-invite="signin"]').count();
  check(`passo 3: logado em /ativos/${NO_RISK} → data-risk-invite="compute" (sem clicar)`, invite && buttons === 1 && signin === 0, {
    buttons,
    signin,
  });
}

/** A troca obrigatória pela tela: a atual, a nova, a confirmação, "Continuar" → a mesma URL. */
async function changeRequired(page, current, next, label) {
  const form = page.locator('[data-part="form-obrigatoria"]');
  await form.locator('input[name="current_password"]').fill(current);
  await form.locator('input[name="new_password"]').fill(next);
  await form.locator('input[name="confirmation"]').fill(next);
  await authRequest(`password (${label})`);
  await form.locator('button[type="submit"]').click();
  const cont = page.locator('[data-screen="senha-obrigatoria"]').getByRole("button", { name: TEXT.continue, exact: true });
  const done = await visible(cont, 15_000);
  check(`passo 4: ${label} troca a senha e vê "${TEXT.continue}"`, done);
  if (!done) return false;
  await cont.click();
  const left = await gone(page.locator('[data-screen="senha-obrigatoria"]'), 15_000);
  const search = await visible(page.getByRole("combobox"), 15_000);
  const pathname = new URL(page.url()).pathname;
  return check(`passo 4: ${label} depois do "${TEXT.continue}" → a busca em /`, left && search && pathname === "/", { pathname });
}

/** Entra pela tela de entrada sem `next`. */
async function signIn(page, email, password, label) {
  await page.goto(`${BASE}/entrar`);
  await visible(page.locator('[data-screen="entrada"]'));
  const form = page.locator('[data-screen="entrada"] form');
  await form.locator('input[name="email"]').fill(email);
  await form.locator('input[name="password"]').fill(password);
  await authRequest(`login (${label})`);
  await form.locator('button[type="submit"]').click();
}

/** O foco agora: dentro do `<dialog>` aberto, no `body` ou fora. */
function focusFacts(page) {
  return page.evaluate(() => {
    const active = document.activeElement;
    const dialog = document.querySelector("dialog[open]");
    return {
      inside: dialog !== null && active !== null && dialog.contains(active),
      body: active === document.body || active === null,
      tag: active?.tagName ?? null,
      text: (active?.textContent ?? "").trim().slice(0, 60),
    };
  });
}

/** Passo 4 inteiro, mais as capturas e comparações que dependem da administradora. */
async function step4(browser, adminPage) {
  // A administradora entra: a troca obrigatória no lugar da busca, com a URL em `/`.
  await signIn(adminPage, ADMIN_EMAIL, ADMIN_TEMP, "administradora, a senha provisória");
  const required = await visible(adminPage.locator('[data-screen="senha-obrigatoria"]'));
  const pathname = new URL(adminPage.url()).pathname;
  if (!check('passo 4: a administradora entra → data-screen="senha-obrigatoria" com a URL /', required && pathname === "/", { pathname })) {
    return;
  }
  // Passos 6 e 7: a troca obrigatória (o tema pela chave e a recarga: a tela não tem a chave).
  for (const variant of VARIANTS) {
    await applyVariant(adminPage, variant, '[data-screen="senha-obrigatoria"]');
    await capture(adminPage, "troca-obrigatoria", variant);
    await compare(adminPage, "senhaObrigatoria", variant);
  }
  await applyVariant(adminPage, VARIANTS[0], '[data-screen="senha-obrigatoria"]');
  if (!(await changeRequired(adminPage, ADMIN_TEMP, ADMIN_NEW, "a administradora"))) return;

  // Passos 6 e 7 logados: a barra com o menu fechado e aberto, em `/`.
  await settle(adminPage);
  for (const variant of VARIANTS) {
    await applyVariant(adminPage, variant, '[data-account="authenticated"]');
    await compare(adminPage, "contaLogado", variant);
    check(`menu ${variant.id}: abre pelo botão de conta`, await openMenu(adminPage));
    await capture(adminPage, "menu-aberto", variant);
    await compare(adminPage, "contaMenu", variant);
    await adminPage.keyboard.press("Escape");
  }
  await applyVariant(adminPage, VARIANTS[0], '[data-account="authenticated"]');

  // Passo 7: a troca voluntária, logada, formulário vazio.
  await adminPage.goto(`${BASE}/conta/senha`);
  await visible(adminPage.locator('[data-screen="senha"] [data-part="form"]'));
  for (const variant of VARIANTS) {
    await applyVariant(adminPage, variant, '[data-screen="senha"] [data-part="form"]');
    await compare(adminPage, "senhaVoluntaria", variant);
  }
  await applyVariant(adminPage, VARIANTS[0], '[data-screen="senha"] [data-part="form"]');

  // A gestão pelo menu: a administradora de organização real tem "Usuários da organização".
  await adminPage.goto(`${BASE}/`);
  await visible(adminPage.locator('[data-account="authenticated"]'));
  await openMenu(adminPage);
  const manage = adminPage.locator('[data-part="menu"]').getByRole("link", { name: TEXT.manageUsers, exact: true });
  check(`passo 4: o menu da administradora tem "${TEXT.manageUsers}"`, (await manage.count()) === 1);
  await manage.click();
  const listed = await visible(adminPage.locator('[data-screen="usuarios"] tr[data-email]'));
  check("passo 4: /organizacao/usuarios com a lista carregada", listed && new URL(adminPage.url()).pathname === "/organizacao/usuarios", {
    url: adminPage.url(),
  });

  // Cria o membro e lê a senha provisória no diálogo.
  const create = adminPage.locator('[data-part="form-criar"]');
  await create.locator('input[name="name"]').fill(MEMBER.name);
  await create.locator('input[name="email"]').fill(MEMBER.email);
  await create.locator('button[type="submit"]').click();
  const dialog = adminPage.locator('dialog[data-dialog="senha-provisoria"][open]');
  const opened = await visible(dialog, 15_000);
  MEMBER.temp = opened ? await dialog.locator("input[readonly]").inputValue() : null;
  check('passo 4: criar o membro abre data-dialog="senha-provisoria" com a senha', opened && Boolean(MEMBER.temp), {
    email: MEMBER.email,
  });
  if (!opened) return;

  // O foco preso: a cada `Tab` (dez), o foco dentro do diálogo, ou o `body`, que se tolera.
  const tabs = [];
  for (let i = 0; i < 10; i += 1) {
    await adminPage.keyboard.press("Tab");
    tabs.push(await focusFacts(adminPage));
  }
  result.dialog_tabs = tabs;
  check("passo 4: no diálogo, dez Tab sem foco fora dele (o body se tolera)", tabs.every((f) => f.inside || f.body), {
    outside: tabs.filter((f) => !f.inside && !f.body),
  });
  // O `Esc` fecha, e o foco volta ao botão que o abriu ("Criar usuário").
  await adminPage.keyboard.press("Escape");
  const closed = await gone(adminPage.locator("dialog[open]"), 10_000);
  await adminPage.waitForTimeout(200);
  const back = await adminPage.evaluate(() => document.activeElement?.getAttribute("data-part") ?? document.activeElement?.tagName ?? null);
  check('passo 4: Esc fecha o diálogo e o foco volta a data-part="botao-criar"', closed && back === "botao-criar", { closed, focus: back });

  // Passos 6 e 7: a gestão, com a lista relida (a administradora e o membro).
  await visible(adminPage.locator(`tr[data-email="${MEMBER.email}"]`), 15_000);
  for (const variant of VARIANTS) {
    await applyVariant(adminPage, variant, `tr[data-email="${MEMBER.email}"]`);
    await capture(adminPage, "usuarios", variant);
    await compare(adminPage, "usuarios", variant);
  }
  await applyVariant(adminPage, VARIANTS[0], `tr[data-email="${MEMBER.email}"]`);

  // Em outro contexto, o membro entra, troca, e o menu não tem "Usuários da organização".
  if (MEMBER.temp) {
    const memberContext = await newContext(browser);
    try {
      const memberPage = await newPage(memberContext, "membro");
      await signIn(memberPage, MEMBER.email, MEMBER.temp, "o membro, a senha provisória");
      const memberRequired = await visible(memberPage.locator('[data-screen="senha-obrigatoria"]'));
      check('passo 4: o membro entra → data-screen="senha-obrigatoria"', memberRequired);
      if (memberRequired && (await changeRequired(memberPage, MEMBER.temp, MEMBER.password, "o membro"))) {
        check("passo 4: o menu do membro abre", await openMenu(memberPage));
        const links = await memberPage.locator('[data-part="menu"]').getByRole("link", { name: TEXT.manageUsers, exact: true }).count();
        check(`passo 4: o menu do membro não tem "${TEXT.manageUsers}"`, links === 0, { links });
        await memberPage.keyboard.press("Escape");
      }
    } finally {
      await memberContext.close();
    }
  }

  // A administradora desativa o membro.
  const row = adminPage.locator(`tr[data-email="${MEMBER.email}"]`);
  await row.locator('[data-act="desativar"]').click();
  const confirm = adminPage.locator('dialog[data-dialog="confirmar-desativar"][open]');
  check('passo 4: "Desativar" abre data-dialog="confirmar-desativar"', await visible(confirm, 10_000));
  await confirm.locator(".ruvor-dialog__actions .ruvor-btn--primary").click();
  await gone(adminPage.locator("dialog[open]"), 15_000);
  check("passo 4: a administradora desativa o membro (a linha passa a Reativar)", await visible(row.locator('[data-act="reativar"]'), 15_000));

  // No menu, `Esc` o fecha e devolve o foco ao botão de conta.
  check("passo 4: o menu da administradora abre", await openMenu(adminPage));
  await adminPage.keyboard.press("Escape");
  const menuHidden = await adminPage.locator('[data-part="menu"]').isHidden();
  const focus = await adminPage.evaluate(() => document.activeElement?.getAttribute("data-part") ?? null);
  const expanded = await adminPage.locator('[data-part="conta"]').getAttribute("aria-expanded");
  check('passo 4: Esc fecha o menu e devolve o foco a data-part="conta"', menuHidden && focus === "conta" && expanded === "false", {
    menuHidden,
    focus,
    expanded,
  });

  // O `focusout` do menu (T13: sem prova direta no jsdom, conferido aqui): o `Tab` que sai do
  // último item fecha o menu; o Sair que falha deixa o menu aberto, com a linha de alerta.
  await openMenu(adminPage);
  await adminPage.locator('[data-part="menu-sair"]').focus();
  await adminPage.keyboard.press("Tab");
  await adminPage.waitForTimeout(200);
  check("focusout: o Tab que sai do último item do menu o fecha", await adminPage.locator('[data-part="menu"]').isHidden());

  await adminPage.route("**/api/v1/auth/logout", (route) => route.abort());
  try {
    await openMenu(adminPage);
    await adminPage.locator('[data-part="menu-sair"]').click();
    const alertShown = await visible(adminPage.locator('[data-part="menu"] [role="alert"]'), 10_000);
    await adminPage.waitForTimeout(500);
    const stillOpen = await adminPage.locator('[data-part="menu"]').isVisible();
    const stillIn = (await adminPage.locator('[data-account="authenticated"]').count()) === 1;
    check("focusout: o Sair que falha deixa o menu aberto, com a linha de alerta, e a sessão", alertShown && stillOpen && stillIn, {
      alertShown,
      stillOpen,
      stillIn,
    });
    await adminPage.keyboard.press("Escape");
  } finally {
    await adminPage.unroute("**/api/v1/auth/logout");
  }
}

/** Passo 5: logado, a página faz `POST /api/v1/auth/logout` pelo proxy — não 403 (RF-19). */
async function step5(page) {
  await page.goto(`${BASE}/`);
  check("passo 5: logado em /", await visible(page.locator('[data-account="authenticated"]')));
  await openMenu(page);
  const [response] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/v1/auth/logout" && r.request().method() === "POST", { timeout: 15_000 }),
    page.locator('[data-part="menu-sair"]').click(),
  ]);
  const status = response.status();
  result.logout_status = status;
  check("passo 5: POST /api/v1/auth/logout pelo proxy não é 403", status !== 403, { status });
  check("passo 5: POST /api/v1/auth/logout responde 204", status === 204, { status });
  check('passo 5: depois do logout, data-account="anonymous"', await visible(page.locator('[data-account="anonymous"]')));
}

/** Passos 6 e 7, anônimos: a entrada, o cadastro e a barra em `/`. */
async function anonymousScreens(page) {
  await page.goto(`${BASE}/entrar`);
  await visible(page.locator('[data-screen="entrada"]'));
  for (const variant of VARIANTS) {
    await applyVariant(page, variant, '[data-screen="entrada"]');
    await capture(page, "entrada", variant);
    await compare(page, "entrada", variant);
  }

  await page.goto(`${BASE}/cadastro`);
  await visible(page.locator('[data-screen="cadastro"]'));
  for (const variant of VARIANTS) {
    await applyVariant(page, variant, '[data-screen="cadastro"]');
    await capture(page, "cadastro", variant);
    await compare(page, "cadastro", variant);
  }

  await page.goto(`${BASE}/`);
  await visible(page.locator('[data-account="anonymous"]'));
  for (const variant of VARIANTS) {
    await applyVariant(page, variant, '[data-account="anonymous"]');
    await compare(page, "contaAnonimo", variant);
  }
}

async function main() {
  await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });

  const browser = await chromium.launch();
  try {
    const probe = await browser.newContext();
    const ready = await preconditions(probe.request);
    await probe.close();
    if (!ready) {
      result.aborted = "preconditions";
      console.log("abortado: as chaves obrigatórias e o ticker sem risco");
      return;
    }

    const mockContext = await browser.newContext({ locale: "pt-BR" });
    mockPage = await newPage(mockContext, "mockup");

    // A conta do passo 1, que segue logada pelos passos 2, 3 e 5.
    const userContext = await newContext(browser);
    const userPage = await newPage(userContext, "conta nova");
    // O anônimo dos passos 3, 6 e 7.
    const anonContext = await newContext(browser);
    const anonPage = await newPage(anonContext, "anônimo");
    // A administradora do passo 4.
    const adminContext = await newContext(browser);
    const adminPage = await newPage(adminContext, "administradora");

    await step("passo 1: criar conta e sair", () => step1(userPage));
    await step("passo 2: entrar", () => step2(userPage));
    await step("passo 3: o convite, anônimo", () => step3Anonymous(anonPage));
    await step("passo 3: o convite, logado", () => step3SignedIn(userPage));
    await step("passo 4: a administradora, o membro, o diálogo e o menu", () => step4(browser, adminPage));
    await step("passo 5: o logout pelo proxy", () => step5(userPage));
    await step("passos 6 e 7: a entrada, o cadastro e a barra, anônimos", () => anonymousScreens(anonPage));

    await Promise.all([userContext.close(), anonContext.close(), adminContext.close(), mockContext.close()]);
  } catch (error) {
    check("o roteiro correu até o fim", false, { error: String(error?.stack ?? error) });
  } finally {
    await browser.close();
    await finish();
  }
}

async function finish() {
  check("nenhum erro de página", result.page_errors.length === 0, { page_errors: result.page_errors });
  check("nenhuma resposta 429 da API", result.responses_429.length === 0, { responses_429: result.responses_429 });

  result.finished_at = new Date().toISOString();
  result.ok = result.checks.every((c) => c.ok);
  await writeFile(path.join(OUT, "resultado.json"), `${JSON.stringify(result, null, 2)}\n`);
  const failed = result.checks.filter((c) => !c.ok);
  console.log(
    `\n${result.checks.length} conferências, ${failed.length} falharam; ${result.captures.length} capturas e` +
      ` ${result.comparisons.length} comparações (${result.differences.length} diferenças) em ${OUT}`,
  );
  console.log(`limite auth: ${result.auth.requests.length} pedidos, ${result.auth.waits} esperas de ${AUTH_WAIT_MS / 1000} s`);
  console.log(`e-mails: ${USER.email}, ${MEMBER.email}; administradora ${ADMIN_EMAIL}; ticker sem risco ${NO_RISK}`);
  process.exitCode = failed.length === 0 ? 0 : 1;
}

await main();
