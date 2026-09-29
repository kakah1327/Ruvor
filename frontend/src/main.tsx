import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Os tokens da marca entram antes da folha de componentes e do estilo da tela, que so os
// consomem. A folha so estiliza classe ruvor-: nao muda a tela que nao a usa. A folha do
// uPlot entra antes do app.css, que a sobrepoe so com token (RF-22).
import "@brand/tokens.css";
import "@brand/components.css";
import "uplot/dist/uPlot.min.css";
import "./app.css";

import { App } from "./App";
import { initTheme } from "./theme";

// O tema lembrado, antes do primeiro desenho (RF-03).
initTheme();

const root = document.getElementById("root");
if (root === null) {
  throw new Error("elemento #root ausente em index.html");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
