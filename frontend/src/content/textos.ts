/**
 * O módulo de textos (RF-21): todo texto visível das telas mora aqui, chave → texto ou
 * função dos valores. Os textos vêm dos mockups aprovados, literais.
 *
 * `casco.*` e `rodape.*`: do `busca.html` (T2), com os nomes de chave que o
 * `ativo-estados.html` (T4) registrou; `rodape.ultimoPregao` e `rodape.calculadoEm`, do
 * `ativo.html` (T3). A ressalva mora em `ressalva.ts`.
 */

import { RESSALVA } from "./ressalva";

export const TEXTOS = {
  // A barra superior.
  "casco.marca": "RUVOR",
  "casco.marca.rotulo": "Ruvor, ir para a busca",
  "casco.busca.placeholder": "Buscar ativo",
  "casco.busca.rotulo": "Buscar ativo",
  "casco.tema.rotulo": "Tema",
  "casco.tema.claro": "Claro",
  "casco.tema.escuro": "Escuro",
  "casco.tema.sistema": "Sistema",

  // A página não encontrada. O endereço digitado vai entre `antes` e `depois`, citado.
  "casco.naoEncontrada.eyebrow": "Endereço desconhecido",
  "casco.naoEncontrada.titulo": "Página não encontrada.",
  "casco.naoEncontrada.antes": "Nenhuma página do Ruvor fica em ",
  "casco.naoEncontrada.depois": ". O endereço pode ter sido digitado errado.",
  "casco.naoEncontrada.dica":
    "Para chegar a um ativo, busque pelo código ou pelo nome.",
  "casco.irParaBusca": "Ir para a busca",

  // O rodapé (RF-04).
  "rodape.ressalva": RESSALVA,
  "rodape.fonte": "Fontes: catálogo de ativos da B3 e preços do Yahoo Finance.",
  "rodape.ultimoPregao": (data: string) => `Último pregão usado: ${data}.`,
  "rodape.calculadoEm": (data: string, hora: string) =>
    `Risco calculado em ${data} às ${hora}.`,
} as const;

export type TextoKey = keyof typeof TEXTOS;
