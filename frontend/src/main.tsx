import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Os tokens da marca entram antes do estilo da tela, que so os consome.
import "@brand/tokens.css";
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
