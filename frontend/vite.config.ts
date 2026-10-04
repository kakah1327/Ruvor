import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const brandDir = fileURLToPath(new URL("../brand/ruvor", import.meta.url));

// Lida de process.env, e nao de import.meta.env: este arquivo roda antes de o Vite
// carregar os .env e nao recebe as VITE_* automaticamente. O padrao mantem a
// execucao nativa funcionando sem configuracao; o compose fixa web:8000.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@brand": brandDir } },
  server: {
    host: true,
    fs: { allow: [repoRoot] },
    // A forma curta liga o changeOrigin, e a checagem de origem do CSRF do Django (D-100)
    // passa a comparar Origin: localhost:<porta> com Host: web:8000 e recusa (RF-19).
    proxy: {
      "/health": { target: proxyTarget, changeOrigin: false },
      "/api": { target: proxyTarget, changeOrigin: false },
    },
    // Sondagem: o aviso de alteracao de arquivo nao atravessa a montagem
    // Windows -> conteiner. Medido na T6 do F3 -- o conteiner enxerga o arquivo novo,
    // mas o Vite nao emite evento algum, e a tela so muda com recarga manual.
    // Custa CPU continua, e por isso so foi ligada depois de a falta ser observada.
    watch: { usePolling: true },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
