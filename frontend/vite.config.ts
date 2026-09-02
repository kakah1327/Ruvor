import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const brandDir = fileURLToPath(new URL("../brand/ruvor", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@brand": brandDir } },
  server: {
    fs: { allow: [repoRoot] },
    proxy: { "/health": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
