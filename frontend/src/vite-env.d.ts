/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Vazio: mesma origem, via proxy do Vite. Preenchido: URL absoluta sem barra final. */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
