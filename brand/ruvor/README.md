# Ruvor — identidade visual

Especificação da marca. Este diretório **manda** em qualquer questão visual.

---

## Hierarquia — qual arquivo vence

Em caso de divergência, vale de cima para baixo:

| Ordem | Onde | O que é |
|---|---|---|
| 1 | `tokens.css` / `tokens.json` | os valores oficiais. Nada acima disso |
| 2 | [`mockups/`](mockups/) | **as quatro telas de referência do produto.** Estabelecem shell, componentes, hierarquia, densidade e estados |
| 3 | `implementation.css` | referência de componentes para o produto |
| 4 | `examples/` | estudos anteriores. **Perdem para os mockups** |
| 5 | [`estudos/`](estudos/) | histórico de como se chegou à marca. Não é especificação |

Os SVGs são ativos oficiais e não se redesenham.

---

## As quatro telas de referência

Em [`mockups/`](mockups/), com `foundation.css` reunindo os padrões compartilhados:

| Tela | Padrão que estabelece |
|---|---|
| `01-login.html` | acesso institucional, confiança, tratamento de erro |
| `02-visao-geral.html` | home operacional, sinais prioritários, evidência, ranking de modelos |
| `03-nova-analise.html` | formulário analítico denso, seleção de parâmetros, resumo antes de executar |
| `04-resultado-analitico.html` | resultado completo, gráfico de VaR, backtests, comparação de modelos, trilha da execução |

Não formam protótipo navegável nem representam o escopo da plataforma. São referência de
implementação: ao derivar tela nova, formulários partem de `03`, leitura e auditoria de `04`,
telas operacionais de `02`.

> **Os dados são ilustrativos.** Valores, nomes de ativo, quantidades, notas e prazos que
> aparecem nas telas existem para dar densidade realista à referência visual — **não são
> especificação de produto**. O que vale desses arquivos é a forma: shell, componentes,
> hierarquia, densidade e linguagem de sinais.

> **`foundation.css` é folha de mockup, não de produto.** Ela usa dezenas de cores literais
> para montar as telas de referência rapidamente. O código do produto consome **tokens**, e
> cor literal em `frontend/src/` é reprovada por verificação automatizada.

---

## Assinatura

| Arquivo | Uso |
|---|---|
| `ruvor-logo.svg` | padrão, sobre fundos claros (`#F7F6F2`) |
| `ruvor-logo-reverse.svg` | sobre grafite (`#292A2E`) |
| `ruvor-mark.svg` | ícone para app, favicon e áreas compactas |
| `ruvor-mark-reverse.svg` | o mesmo, sobre grafite |

O logo completo traz o símbolo mais a palavra "ruvor" **já vetorizada** — não depende de
fonte instalada.

O símbolo é uma matriz de sinais analíticos. **Sempre em uma cor só**, sem gradiente, sombra
ou semáforo aplicado aos pontos. A cor vive no produto; o símbolo permanece técnico.

**Espaço livre:** ao menos a largura de um ponto grande do símbolo, em todos os lados.
**Tamanho mínimo:** 24 px para o símbolo, 120 px para a assinatura completa.

---

## Paleta

| Token | Cor | Significado |
|---|---|---|
| `--ruvor-ink` | `#292A2E` | marca, tipografia e estrutura |
| `--ruvor-paper` | `#F7F6F2` | fundo principal e marca reversa |
| `--ruvor-surface` | `#E9E7E2` | cards e superfícies secundárias |
| `--ruvor-border` | `#C8C4BC` | divisórias e campos |
| `--ruvor-decision` | `#8F3B4B` | decisão, limite, foco de ação |
| `--ruvor-review` | `#B79754` | revisão e atenção |
| `--ruvor-evidence` | `#54727B` | evidência, séries, comparação |
| `--ruvor-validated` | `#587060` | validação e condição preservada |
| `--ruvor-critical` | `#B4524C` | exceção crítica |

**A cor carrega significado, não decoração.** Grafite, papel e superfície ocupam a maior parte
da tela; as semânticas entram para indicar condição.

**Vinho e vermelho-óxido são distintos de propósito:** `decision` é "precisa de ação";
`critical` é "algo falhou". Trocar um pelo outro faz "agir" se confundir com "quebrou".

---

## Regras de interface

**Cor nunca é o único sinal.** Todo estado precisa de texto e/ou ícone junto — vale para
acessibilidade e para quem imprime em preto e branco.

**Raios:** cards usam `--ruvor-radius-md`; botões e campos, `--ruvor-radius-sm`.

**Tipografia:** dados quantitativos em mono (`--ruvor-font-mono`); navegação e texto corrido
em sans (`--ruvor-font-sans`). Número que se lê e se compara pede monoespaçada.

**Nunca escreva um valor de cor no produto.** Se um tom necessário não existe como token, ele
não foi aprovado — o caminho é acrescentar o token aqui, não improvisar na tela.

---

## Como consumir no produto

```css
@import url('brand/ruvor/tokens.css');
```

`tokens.json` espelha cores e escalas para ferramentas e implementações não-CSS.

---

## Lacunas conhecidas

Os mockups resolveram a maior lacuna anterior — **campos de formulário e densidade agora têm
referência** (`03-nova-analise.html`, e `.field` em `foundation.css`). O que ainda falta:

| Falta | Situação |
|---|---|
| **Estados de interação** — foco, sobrevoo, desabilitado, erro | `foundation.css` define apenas `:active` |
| **Modo escuro** | o kit é só claro; o protótipo antigo era escuro-primeiro. Decisão de produto pendente |
| **Guia de componentes escrito** | os mockups servem de referência visual, mas não há especificação textual por componente |

Registrado em [`docs/ESTADO.md`](../../docs/ESTADO.md) e
[`docs/PRODUTO.md`](../../docs/PRODUTO.md#8-pendências-de-produto).

---

## Relação com os mockups do processo

Estes mockups são a **linguagem visual do produto**, produzidos no trabalho de marca.

Os mockups do [portão do processo](../../docs/PROCESSO.md#7-portão-de-mockup), em
`docs/mockups/<bloco>/`, são **derivados destes** para uma tela específica de um bloco, e
passam por aprovação humana antes de virar código. São coisas diferentes: aqui é o
vocabulário; lá é a frase.

---

## Histórico e pendência

Como se chegou a esta identidade está em [`estudos/`](estudos/) — registro de decisão, não
especificação.

A verificação de disponibilidade de marca e domínio, pedida ao fim das rodadas de naming,
**nunca foi feita**. O nome está decidido
([D-01](../../docs/decisoes/D-01-nome-do-produto-e-ruvor.md)); a verificação segue valendo em
paralelo.
