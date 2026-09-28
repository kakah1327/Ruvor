/**
 * O módulo de textos (RF-21): todo texto visível das telas mora aqui, chave → texto ou
 * função dos valores. Os textos vêm dos mockups aprovados, literais.
 *
 * `casco.*` e `rodape.*`: do `busca.html` (T2), com os nomes de chave que o
 * `ativo-estados.html` (T4) registrou; `rodape.ultimoPregao` e `rodape.calculadoEm`, do
 * `ativo.html` (T3). `busca.*`: do `busca.html` (T2) — o HTML da página inicial e o objeto
 * `T` do script. A ressalva mora em `ressalva.ts`.
 */

import { formatInteger } from "../format/numbers";
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

  // A busca (RF-05): a página inicial e a lista suspensa da barra. O limpar e os estados
  // valem nos dois campos.
  "busca.eyebrow": "Busca",
  "busca.titulo": "Qual ativo você quer analisar?",
  "busca.sub":
    "Digite o código ou o nome de uma ação da B3, ou do Ibovespa. Na página do ativo, você vê como o preço se comportou e quanto nove métodos estimam que ele pode perder em um dia.",
  "busca.rotulo": "Buscar ativo por código ou nome",
  "busca.placeholder": "Código ou nome, como PETR4",
  "busca.limpar": "Limpar a busca",
  "busca.sugestaoTitulo": "ativos com risco calculado",
  "busca.sugestaoNota":
    "Os outros ativos do catálogo podem ter o risco calculado na página de cada um.",
  "busca.contagem": (n: number, q: string) =>
    `${n === 1 ? "1 ativo" : `${formatInteger(n)} ativos`} para “${q}”`,
  "busca.mostrando": (a: number, n: number) =>
    `Mostrando ${formatInteger(a)} de ${formatInteger(n)}.`,
  "busca.mostrarMais": "Mostrar mais",
  "busca.buscando": "Buscando…",
  "busca.semResultado": (q: string) => `Nenhum ativo com “${q}”.`,
  "busca.semResultadoDica": "Confira o código ou tente uma parte do nome.",
  "busca.erroTitulo": "A busca não respondeu.",
  "busca.erroTexto": "Pode ser uma falha passageira do servidor.",
  "busca.tentarDeNovo": "Tentar de novo",
  "busca.suspensaRodape": (a: number, n: number) =>
    `${formatInteger(a)} de ${formatInteger(n)} · continue digitando para filtrar`,
  "busca.tagIndice": "índice",
  "busca.tagInativo": "inativo",
  "busca.tagSemDados": "sem dados ainda",

  // O rodapé (RF-04).
  "rodape.ressalva": RESSALVA,
  "rodape.fonte": "Fontes: catálogo de ativos da B3 e preços do Yahoo Finance.",
  "rodape.ultimoPregao": (data: string) => `Último pregão usado: ${data}.`,
  "rodape.calculadoEm": (data: string, hora: string) =>
    `Risco calculado em ${data} às ${hora}.`,
} as const;

export type TextoKey = keyof typeof TEXTOS;
