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
 *     função, que cobre cada ramo. Chave de função sem exemplos reprova. O mesmo vale para as
 *     frases da leitura avançada, `TEXTOS_AVANCADOS` com `EXEMPLOS_AVANCADOS` (V-07 do M2.3).
 *     Os dois registros moram em `exemplos.ts`.
 *
 * A ressalva do rodapé é o único texto isento: pelo arquivo na forma (a), pela chave na (b).
 *
 * Vive fora de src/ de propósito: as próprias palavras abaixo reprovariam a forma (a).
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { MOTIVOS_CONHECIDOS, traduzirMotivo } from "../src/content/motivos";
import { RESSALVA } from "../src/content/ressalva";
import { TEXTOS } from "../src/content/textos";
import { EXEMPLOS, EXEMPLOS_AVANCADOS } from "./exemplos";

const CONTENT = fileURLToPath(new URL("../src/content", import.meta.url));

const PROIBIDAS =
  /(?<![\p{L}\p{N}_])(melhor|melhores|recomendado|recomendada|recomendados|recomendadas|recomendamos|confiável|confiáveis)(?![\p{L}\p{N}_])/iu;
const ISENTAS = new Set(["rodape.ressalva"]); // a entrada que re-exporta ressalva.ts

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
  it("varre textos.ts, motivos.ts e avancado.ts, e não varre ressalva.ts", () => {
    const nomes = arquivosDoConteudo().map((a) => a.slice(CONTENT.length + 1));
    expect(nomes).toContain("textos.ts");
    expect(nomes).toContain("motivos.ts");
    expect(nomes).toContain("avancado.ts");
    expect(nomes).not.toContain("ressalva.ts");
  });

  it("nenhum arquivo tem palavra proibida", () => {
    expect(varreFonte()).toEqual([]);
  });
});

type Exemplos = Readonly<Record<string, ReadonlyArray<readonly unknown[]>>>;

/** As chaves-função de um registro de textos. */
function chavesFuncao(registro: object): string[] {
  return (Object.entries(registro) as Array<[string, unknown]>)
    .filter(([, v]) => typeof v === "function")
    .map(([k]) => k);
}

/** As palavras proibidas que as entradas de um registro produzem, com os exemplos dados. */
function achadosEm(registro: object, exemplos: Exemplos, rotulo: string): string[] {
  const achados: string[] = [];
  for (const [chave, valor] of Object.entries(registro) as Array<[string, unknown]>) {
    if (ISENTAS.has(chave)) continue;
    const saidas =
      typeof valor === "string"
        ? [valor]
        : (exemplos[chave] ?? []).map((args) =>
            (valor as (...a: unknown[]) => string)(...args),
          );
    for (const saida of saidas) {
      const palavra = proibida(saida);
      if (palavra !== null) achados.push(`${rotulo} ${chave}: ${palavra}`);
    }
  }
  return achados;
}

describe("V-09 — (b) o resultado de cada entrada", () => {
  const funcoes = chavesFuncao(TEXTOS);
  const funcoesAvancadas = chavesFuncao(TEXTOS_AVANCADOS);

  it("toda chave de função tem exemplos, e todo exemplo é de uma chave de função", () => {
    const semExemplo = funcoes.filter((k) => (EXEMPLOS[k]?.length ?? 0) === 0);
    expect(semExemplo).toEqual([]);
    expect(Object.keys(EXEMPLOS).filter((k) => !funcoes.includes(k))).toEqual([]);
  });

  it("V-07: toda chave-função avançada tem exemplos, e todo exemplo avançado é de uma chave-função avançada", () => {
    const semExemplo = funcoesAvancadas.filter(
      (k) => (EXEMPLOS_AVANCADOS[k]?.length ?? 0) === 0,
    );
    expect(semExemplo).toEqual([]);
    expect(
      Object.keys(EXEMPLOS_AVANCADOS).filter((k) => !funcoesAvancadas.includes(k)),
    ).toEqual([]);
  });

  it("nenhuma entrada, fora a ressalva, produz palavra proibida — nas duas leituras", () => {
    expect([
      ...achadosEm(TEXTOS, EXEMPLOS, "iniciante"),
      ...achadosEm(TEXTOS_AVANCADOS, EXEMPLOS_AVANCADOS, "avançada"),
    ]).toEqual([]);
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

/**
 * RF-17 do M2.4: a seção do laboratório não elege modelo. Além da varredura de sempre, as
 * entradas `laboratorio.*` — nas duas leituras, avaliadas pelos exemplos — não usam as palavras
 * do "ranking" da Etapa 6 do TCC; palavra inteira, sem caixa.
 */
const PROIBIDAS_LABORATORIO =
  /(?<![\p{L}\p{N}_])(pior|piores|vencedor|vencedores|venceu|ranking|campeão)(?![\p{L}\p{N}_])/iu;

describe("RF-17 do M2.4 — o vocabulário do laboratório nas entradas laboratorio.*", () => {
  it.each(["o pior", "Vencedor", "RANKING", "campeão", "os piores", "venceu"])(
    "pega %j",
    (texto) => {
      expect(PROIBIDAS_LABORATORIO.test(texto)).toBe(true);
    },
  );

  it.each(["superior", "convenceu", "rankings2"])("não pega %j", (texto) => {
    expect(PROIBIDAS_LABORATORIO.test(texto)).toBe(false);
  });

  const registros: Array<[string, object, Exemplos]> = [
    ["iniciante", TEXTOS, EXEMPLOS],
    ["avançada", TEXTOS_AVANCADOS, EXEMPLOS_AVANCADOS],
  ];

  it.each(registros)("as entradas laboratorio.* da %s existem", (_rotulo, registro) => {
    const chaves = Object.keys(registro).filter((k) => k.startsWith("laboratorio."));
    expect(chaves.length).toBeGreaterThan(0);
  });

  it.each(registros)(
    "nenhuma entrada laboratorio.* da %s usa o vocabulário do ranking",
    (_rotulo, registro, exemplos) => {
      const achados: string[] = [];
      for (const [chave, valor] of Object.entries(registro) as Array<
        [string, unknown]
      >) {
        if (!chave.startsWith("laboratorio.")) continue;
        const saidas =
          typeof valor === "string"
            ? [valor]
            : (exemplos[chave] ?? []).map((args) =>
                (valor as (...a: unknown[]) => string)(...args),
              );
        expect(saidas.length, chave).toBeGreaterThan(0);
        for (const saida of saidas) {
          const m = PROIBIDAS_LABORATORIO.exec(saida);
          if (m !== null) achados.push(`${chave}: ${m[1]}`);
        }
      }
      expect(achados).toEqual([]);
    },
  );
});

/**
 * V-16 do M5.1 (RF-21): a lista ampliada do vocabulário, fechada no portão do `retorno.html` —
 * palavra inteira, sem caixa, por raiz —, sobre as entradas `retorno.*` nas duas leituras,
 * avaliadas pelos exemplos (a forma (b)). `retorno.aviso` é a única isenta: diz "comprar, vender
 * ou manter" e "vai fazer" de propósito, para negar. A lista não cabe na forma (a): os textos dos
 * fundamentos dizem "lucro" e "venda".
 */
const AMPLIADA =
  /(?<![\p{L}\p{N}_])(compr\p{L}*|vend\p{L}*|mant(er|enha|enham|ém)|lucr\p{L}*|ganh\p{L}*|rentab\p{L}*|oportunidades?|garant\p{L}*|alvos?|apost\p{L}*|promissor(a|as|es)?)(?![\p{L}\p{N}_])|vai (subir|cair|valorizar|desvalorizar|render)|vai se (valorizar|desvalorizar)|vão (subir|cair)|deve (subir|cair|render)|tende a (subir|cair)/iu;
const ISENTAS_RETORNO = ["retorno.aviso"];

describe("V-16 do M5.1 — a lista ampliada do RF-21 nas entradas retorno.*", () => {
  it.each([
    "vendeu",
    "comprado",
    "mantenha",
    "a ação vai subir",
    "deve cair",
    "tende a subir",
    "oportunidade",
    "garante",
    "lucro",
    "ganho",
    "rentabilidade",
    "vai se valorizar",
  ])("pega %j", (texto) => {
    expect(AMPLIADA.test(texto)).toBe(true);
  });

  it.each(["reestimação", "manteiga_", "_lucro", "alvorada", "comprimento"])(
    "não pega %j",
    (texto) => {
      // "comprimento" é raiz "compr": a lista o pega de propósito (por raiz); os outros, não.
      expect(AMPLIADA.test(texto)).toBe(texto === "comprimento");
    },
  );

  it("a isenção é exatamente retorno.aviso", () => {
    expect(ISENTAS_RETORNO).toEqual(["retorno.aviso"]);
    expect(AMPLIADA.test(TEXTOS["retorno.aviso"])).toBe(true);
  });

  const registros: Array<[string, object, Exemplos]> = [
    ["iniciante", TEXTOS, EXEMPLOS],
    ["avançada", TEXTOS_AVANCADOS, EXEMPLOS_AVANCADOS],
  ];

  it.each(registros)("as entradas retorno.* da %s existem", (_rotulo, registro) => {
    const chaves = Object.keys(registro).filter((k) => k.startsWith("retorno."));
    expect(chaves.length).toBeGreaterThan(0);
  });

  it.each(registros)(
    "nenhuma entrada retorno.* da %s usa a lista ampliada",
    (_rotulo, registro, exemplos) => {
      const achados: string[] = [];
      for (const [chave, valor] of Object.entries(registro) as Array<
        [string, unknown]
      >) {
        if (!chave.startsWith("retorno.") || ISENTAS_RETORNO.includes(chave)) continue;
        const saidas =
          typeof valor === "string"
            ? [valor]
            : (exemplos[chave] ?? []).map((args) =>
                (valor as (...a: unknown[]) => string)(...args),
              );
        expect(saidas.length, chave).toBeGreaterThan(0);
        for (const saida of saidas) {
          const m = AMPLIADA.exec(saida);
          if (m !== null) achados.push(`${chave}: ${m[0]}`);
        }
      }
      expect(achados).toEqual([]);
    },
  );
});
