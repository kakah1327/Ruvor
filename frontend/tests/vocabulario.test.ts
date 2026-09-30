/**
 * @vitest-environment node
 *
 * V-09, a varredura do vocabulário proibido (RF-14): nenhum texto do módulo de textos diz
 * que um modelo é melhor, recomendado ou confiável — palavra inteira, sem distinção de caixa.
 *
 * Duas formas, porque uma função de texto pode ter ramos que um único conjunto de valores não
 * exercita:
 *
 * (a) sobre o **texto-fonte** de todo arquivo de `frontend/src/content/`, menos `ressalva.ts`
 *     — pega o ramo que nenhum exemplo alcança;
 * (b) sobre o **resultado** de cada entrada de `TEXTOS` e de cada tradução de `motivos.ts`, com
 *     as funções chamadas pelos valores de `EXEMPLOS` — uma lista de argumentos por chave de
 *     função, que cobre cada ramo. Chave de função sem exemplos reprova.
 *
 * A ressalva do rodapé é o único texto isento: pelo arquivo na forma (a), pela chave na (b).
 *
 * Vive fora de src/ de propósito: as próprias palavras abaixo reprovariam a forma (a).
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { MOTIVOS_CONHECIDOS, traduzirMotivo } from "../src/content/motivos";
import { RESSALVA } from "../src/content/ressalva";
import { TEXTOS } from "../src/content/textos";

const CONTENT = fileURLToPath(new URL("../src/content", import.meta.url));

const PROIBIDAS =
  /(?<![\p{L}\p{N}_])(melhor|melhores|recomendado|recomendada|recomendados|recomendadas|recomendamos|confiável|confiáveis)(?![\p{L}\p{N}_])/iu;
const ISENTAS = new Set(["rodape.ressalva"]); // a entrada que re-exporta ressalva.ts

// Um conjunto de argumentos por ramo de cada função de texto.
const EXEMPLOS: Readonly<Record<string, ReadonlyArray<readonly unknown[]>>> = {
  "busca.contagem": [
    [1, "itub"],
    [1234, "itub"],
  ],
  "busca.mostrando": [[20, 1234]],
  "busca.semResultado": [["xpto"]],
  "busca.suspensaRodape": [[8, 1234]],
  "rodape.ultimoPregao": [["26/09/2026"]],
  "rodape.calculadoEm": [["26/09/2026", "18:40"]],
  "ativo.listagem": [["N1"]],
  "ativo.ultimoFechamento": [["26/09/2026"]],
  "ativo.eventos.periodo": [["26/09/2026"]],
  "ativo.eventos.valor": [["R$ 0,50"]],
  "ativo.eventos.proporcao": [["2", "1"]],
  "ativo.eventos.verTodos": [["42"]],
  "ativo.naoEncontrado": [["XPTO3"]],
  "grafico.dicaPreco": [["26/09/2026", "R$ 30,00"]],
  "grafico.resumoPreco": [
    [
      "26/09/2016",
      "26/09/2026",
      "R$ 9,00",
      "20/01/2016",
      "R$ 40,00",
      "01/08/2025",
      "R$ 38,00",
    ],
  ],
  "grafico.faixa": [["−0,5%", "0,0%"]],
  "grafico.dicaBarra": [
    ["de −0,5% a 0,0%", 1],
    ["de −0,5% a 0,0%", 5],
  ],
  "grafico.resumoHistograma": [
    ["de 0,0% a 0,5%", "300", 1, 1],
    ["de 0,0% a 0,5%", "300", 3, 2],
  ],
  "comportamento.ate": [["26/09/2026"]],
  "comportamento.nota.ibov": [["1.230"]],
  "comportamento.nota.distribuicao": [["1.230"]],
  "comportamento.nulo.janela": [[60]],
  "comportamento.nulo.pregoes": [[252]],
  "comportamento.return_1m": [["R$ 102,00"]],
  "comportamento.return_3m": [["R$ 102,00"]],
  "comportamento.return_6m": [["R$ 102,00"]],
  "comportamento.return_12m": [["R$ 102,00"]],
  "comportamento.return_36m": [["R$ 102,00"]],
  "comportamento.return_60m": [["R$ 102,00"]],
  "comportamento.return_120m": [["R$ 102,00"]],
  "comportamento.return_ytd": [["R$ 102,00"]],
  "comportamento.volatility_12m": [["25,0%"]],
  "comportamento.volatility_60m": [["25,0%"]],
  "comportamento.max_drawdown": [
    ["31,2%", "05/01/2022", "12/10/2022", "22/09/2016", "03/03/2024"],
    ["31,2%", "05/01/2022", "12/10/2022", "22/09/2016", null],
  ],
  "comportamento.max_drawdown_recovery_sessions": [["1,4"]],
  "comportamento.beta_60m": [
    ["0,85%", false],
    ["0,15%", true],
  ],
  "comportamento.correlation_60m": [["0,62"]],
  "comportamento.skewness": [
    ["−0,35", -1],
    ["0,35", 1],
    ["0,00", 0],
  ],
  "comportamento.excess_kurtosis": [
    ["5,10", 1],
    ["−0,20", -1],
  ],
  "comportamento.dividend_yield_12m": [["26/09/2026", "R$ 6,10"]],
  "comportamento.unidade.volume": [["25,3"]],
  "risco.faixa": [["2,1%", "2,7%"]],
  "risco.discordancia": [
    [null, null, 0, 9, 20, null],
    [null, null, 1, 9, 100, "3,9%"],
    ["2,1%", "2,7%", 9, 9, 20, null],
    ["2,1%", "2,7%", 8, 9, 20, null],
    ["2,1%", "2,7%", 7, 9, 100, null],
  ],
  "risco.naoRejeitados": [
    [0, 0, 9],
    [0, 9, 9],
    [0, 8, 9],
    [0, 7, 9],
    [1, 9, 9],
    [3, 8, 9],
    [3, 7, 9],
  ],
  "risco.tabela.abrir": [["Histórico"]],
  "risco.violacoes": [
    ["25", "25,1", 20, true],
    ["40", "25,1", 20, false],
  ],
  "risco.kupiec": [
    ["0,919", true],
    ["0,021", false],
  ],
  "risco.christoffersen": [
    ["0,919", true],
    ["0,021", false],
  ],
  "risco.dq": [
    ["0,082", true],
    ["< 0,001", false],
  ],
  "risco.erroModelo": [["texto do erro do motor"]],
  "risco.trilha.pregoes": [["1.980"]],
  "risco.trilha.coleta": [["Yahoo Finance", "26/09/2026 às 18:40"]],
  "risco.trilha.instante": [["26/09/2026", "18:40"]],
  "risco.trilha.status.partial": [[2]],
  "risco.estado.recalculando": [[12, 18]],
  "risco.estado.E4": [[3, 18]],
  "risco.pedido.erro": [["Erro interno. Tente de novo mais tarde."]],
  // fundamentos.*: os do registro EXEMPLOS do ativo-fundamentos.html (M1.6c), um por ramo.
  "fundamentos.proveniencia": [["30/06/2026", "ITR", "28/09/2026 às 08:02"]],
  "fundamentos.vezes": [["4,65"]],
  "fundamentos.ebit_ttm": [[false], [true]],
  "fundamentos.net_income_ttm": [[false], [true]],
  "fundamentos.net_margin": [
    ["R$ 24,32", false],
    ["R$ 4,21", true],
  ],
  "fundamentos.ebit_margin": [
    ["R$ 33,86", false],
    ["R$ 2,10", true],
  ],
  "fundamentos.roe": [
    ["R$ 27,73", false],
    ["R$ 6,12", true],
  ],
  "fundamentos.net_debt": [[false], [true]],
  "fundamentos.net_debt_to_equity": [
    ["R$ 65,03", false],
    [null, true],
  ],
  "fundamentos.close": [["25/09/2026"]],
  "fundamentos.closeOutraData": [["25/09/2026", "28/09/2026"]],
  "fundamentos.eps": [
    ["12.888.732.761", false],
    ["4.980.000.000", true],
  ],
  "fundamentos.bvps": [["12.888.732.761"]],
  "fundamentos.pe": [
    ["25/09/2026", "R$ 48,07", "4,6", false],
    ["25/09/2026", "R$ 12,15", "−28,7", true],
  ],
  "fundamentos.pb": [["25/09/2026", "R$ 48,07", "1,29"]],
  "fundamentos.equity_parent": [[false], [true]],
  "fundamentos.pares.segmento": [["Exploração. Refino e Distribuição"]],
  "fundamentos.pares.subsetor": [["Petróleo. Gás e Biocombustíveis"]],
  "fundamentos.pares.posicao": [
    ["6", "6"],
    ["2", "3"],
  ],
  "fundamentos.pares.abaixoDeTodas": [["7"]],
  "fundamentos.pares.mediana": [["11,3%"], ["7,20 vezes"]],
  // comunicados.*: os do registro EXEMPLOS do ativo-fundamentos.html (M1.6c).
  "comunicados.companhia": [["PETROLEO BRASILEIRO S.A. PETROBRAS", "9512"]],
  "comunicados.companhiaSemNome": [["9512"]],
  "comunicados.referencia": [["11/09/2026"]],
  "comunicados.mostrando": [["10", "2.765"]],
  "comunicados.filtroVazio": [
    ["fato relevante"],
    ["comunicado ao mercado"],
    ["aviso aos acionistas"],
  ],
  "motivos.serieCurta": [["312", "503"]],
  "motivos.expirado": [["30"]],
  "motivos.desconhecido": [["qualquer outro texto"]],
};

// Um motivo concreto por forma da lista, e um desconhecido.
const MOTIVOS_EXEMPLO = [
  ...MOTIVOS_CONHECIDOS.map((m) => m.replace("N", "312")),
  "qualquer outro texto",
];

function proibida(texto: string): string | null {
  const match = PROIBIDAS.exec(texto);
  return match === null ? null : match[0];
}

function arquivosDoConteudo(): string[] {
  return readdirSync(CONTENT)
    .filter((nome) => nome !== "ressalva.ts")
    .map((nome) => join(CONTENT, nome));
}

function varreFonte(): string[] {
  const achados: string[] = [];
  for (const arquivo of arquivosDoConteudo()) {
    readFileSync(arquivo, "utf8")
      .split(/\r?\n/)
      .forEach((linha, i) => {
        const palavra = proibida(linha);
        if (palavra !== null) achados.push(`${arquivo}:${i + 1} ${palavra}`);
      });
  }
  return achados;
}

describe("V-09 — a regra das palavras", () => {
  it.each([
    "o melhor modelo",
    "MELHORES",
    "Recomendado",
    "recomendada",
    "recomendados",
    "recomendadas",
    "recomendamos",
    "confiável",
    "CONFIÁVEIS",
    "é o melhor.",
  ])("pega %j", (texto) => {
    expect(proibida(texto)).not.toBeNull();
  });

  it.each([
    "melhora",
    "melhoria",
    "recomendação",
    "confiabilidade",
    "desconfiável",
    "imelhor",
    "melhor_",
  ])("não pega %j", (texto) => {
    expect(proibida(texto)).toBeNull();
  });
});

describe("V-09 — (a) o texto-fonte de src/content/", () => {
  it("varre textos.ts e motivos.ts, e não varre ressalva.ts", () => {
    const nomes = arquivosDoConteudo().map((a) => a.slice(CONTENT.length + 1));
    expect(nomes).toContain("textos.ts");
    expect(nomes).toContain("motivos.ts");
    expect(nomes).not.toContain("ressalva.ts");
  });

  it("nenhum arquivo tem palavra proibida", () => {
    expect(varreFonte()).toEqual([]);
  });
});

describe("V-09 — (b) o resultado de cada entrada", () => {
  const entradas = Object.entries(TEXTOS) as Array<[string, unknown]>;
  const funcoes = entradas.filter(([, v]) => typeof v === "function").map(([k]) => k);

  it("toda chave de função tem exemplos, e todo exemplo é de uma chave de função", () => {
    const semExemplo = funcoes.filter((k) => (EXEMPLOS[k]?.length ?? 0) === 0);
    expect(semExemplo).toEqual([]);
    expect(Object.keys(EXEMPLOS).filter((k) => !funcoes.includes(k))).toEqual([]);
  });

  it("nenhuma entrada, fora a ressalva, produz palavra proibida", () => {
    const achados: string[] = [];
    for (const [chave, valor] of entradas) {
      if (ISENTAS.has(chave)) continue;
      const saidas =
        typeof valor === "string"
          ? [valor]
          : (EXEMPLOS[chave] ?? []).map((args) =>
              (valor as (...a: unknown[]) => string)(...args),
            );
      for (const saida of saidas) {
        const palavra = proibida(saida);
        if (palavra !== null) achados.push(`${chave}: ${palavra}`);
      }
    }
    expect(achados).toEqual([]);
  });

  it("nenhuma tradução de motivo produz palavra proibida", () => {
    const achados = MOTIVOS_EXEMPLO.map(traduzirMotivo).filter(
      (f) => proibida(f) !== null,
    );
    expect(achados).toEqual([]);
  });

  it("a isenção pela chave é só a da ressalva", () => {
    expect([...ISENTAS]).toEqual(["rodape.ressalva"]);
    expect(TEXTOS["rodape.ressalva"]).toBe(RESSALVA);
  });
});

/**
 * V-09 do M1.6c (RF-11, D-130): a seção Comunicados nunca chama o que a companhia entrega à CVM
 * pela palavra da imprensa. O radical sem borda no fim pega a palavra no singular, no plural e
 * sem acento; sem caixa.
 */
const RADICAL_IMPRENSA = /not[ií]cia/iu;

describe("V-09 do M1.6c — o radical da imprensa nas entradas comunicados.*", () => {
  it.each(["notícia", "Notícias da companhia", "NOTÍCIAS", "noticia", "noticias"])(
    "pega %j",
    (texto) => {
      expect(RADICAL_IMPRENSA.test(texto)).toBe(true);
    },
  );

  it.each(["comunicado", "notificação", "Notas"])("não pega %j", (texto) => {
    expect(RADICAL_IMPRENSA.test(texto)).toBe(false);
  });

  const entradas = (Object.entries(TEXTOS) as Array<[string, unknown]>).filter(([k]) =>
    k.startsWith("comunicados."),
  );

  it("as entradas comunicados.* existem", () => {
    expect(entradas.length).toBeGreaterThan(0);
    expect(entradas.map(([k]) => k)).toContain("comunicados.titulo");
  });

  it("nenhuma entrada comunicados.* contém o radical", () => {
    const achados: string[] = [];
    for (const [chave, valor] of entradas) {
      const saidas =
        typeof valor === "string"
          ? [valor]
          : (EXEMPLOS[chave] ?? []).map((args) =>
              (valor as (...a: unknown[]) => string)(...args),
            );
      expect(saidas.length).toBeGreaterThan(0);
      for (const saida of saidas) {
        if (RADICAL_IMPRENSA.test(saida)) achados.push(`${chave}: ${saida}`);
      }
    }
    expect(achados).toEqual([]);
  });
});
