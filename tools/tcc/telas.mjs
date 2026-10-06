// As telas da plataforma para o TCC (Figuras 3 a 5): PETR4, tema claro, leitura avançada, sem explicações,
// 1440 × 860, só a primeira dobra. Roda na imagem do Playwright (ver exportar.sh) e grava em /out.
import { chromium } from "playwright";
const B = "http://localhost:5173";
const pages = [
  ["01-inicio", "/"],
  ["02-visao-geral", "/ativos/PETR4"],
  ["03-risco", "/ativos/PETR4/risco"],
  ["04-laboratorio", "/ativos/PETR4/laboratorio"],
  ["05-retorno", "/ativos/PETR4/retorno"],
];
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 860 }, deviceScaleFactor: 1.5 });
await ctx.addInitScript(() => {
  localStorage.setItem("ruvor-theme", "light");
  localStorage.setItem("ruvor-reading", "advanced");
  localStorage.setItem("ruvor-explain", "off");
});
const page = await ctx.newPage();
for (const [name, path] of pages) {
  await page.goto(B + path, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `/out/${name}.png`, fullPage: false });
  console.log(name, await page.evaluate(() => document.body.scrollHeight));
}
await browser.close();
