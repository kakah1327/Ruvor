import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Os tokens da marca entram antes da folha de componentes e do estilo da tela, que so os
// consomem. A folha so estiliza classe ruvor-: nao muda a tela que nao a usa.
import "@brand/tokens.css";
import "@brand/components.css";
import "./app.css";

import { App } from "./App";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("elemento #root ausente em index.html");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
