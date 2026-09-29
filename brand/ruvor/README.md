# Ruvor — identidade visual

Especificação da marca. Este diretório **manda** em qualquer questão visual.

---

## Hierarquia — qual arquivo vence

Em caso de divergência, vale de cima para baixo:

| Ordem | Onde | O que é |
|---|---|---|
| 1 | [`mockups/`](mockups/) | **as quatro telas de referência do produto.** Estabelecem shell, componentes, hierarquia, densidade e estados. Nada acima disso |
| 2 | `tokens.css` / `tokens.json` e `components.css` | os tokens e a folha de componentes do produto, **derivados dos mockups**. Onde divergem deles, é de propósito, e está dito abaixo |
| 3 | [`examples/`](examples/) | estudos anteriores. **Perdem para os mockups** |
| 4 | [`estudos/`](estudos/) | histórico de como se chegou à marca. Não é especificação |

**Onde os tokens não copiam os mockups, de propósito** (M1.6a): o texto da tag `review`, que
nos mockups fica abaixo de 4,5:1, é escurecido o mínimo (`--ruvor-review-text`); e o que os
mockups não têm — o tema escuro, os estados de interação, a tag e o sinal de `decision` —
nasce no plano do M1.6a e é aprovado na vitrine do kit.

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
| `--ruvor-paper` | `#F8F7F4` | fundo principal e marca reversa |
| `--ruvor-surface` | `#FFFEFA` | cards e painéis |
| `--ruvor-surface-2` | `#E9E7E2` | superfícies secundárias |
| `--ruvor-border` | `#D5D2CC` | divisórias e campos |
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

## Ícones

Do [Phosphor](https://phosphoricons.com) (MIT), num conjunto fechado copiado para
[`icons/`](icons/) ([D-93](../../docs/decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md)):
um `.svg` por ícone e peso, a licença em `icons/LICENSE` e o `icons.json`, que lista nome, peso,
arquivo e a versão de origem do pacote `@phosphor-icons/core`. O frontend **não** instala o
pacote.

| Peso | Onde |
|---|---|
| `regular` | a interface: botão, tag, link da barra, cabeçalho de painel, `callout`, dica e erro de campo — `svg` inline com `.ruvor-glyph` (16 px; `--sm` 14, `--lg` 20) |
| `duotone` | só os sinais (`.ruvor-icon`): `decision` → `flag`, `review` → `warning`, `evidence` → `info`, `validated` → `check-circle`, `critical` → `x-circle` |

**A cor do ícone é a do texto** (`currentColor`); o arquivo não carrega cor. **Ícone nunca é o
único sinal**: vem com rótulo, ou com `aria-label` no botão só de ícone (`.ruvor-btn--icon`), e
o `svg` decorativo leva `aria-hidden="true"`. No botão só de ícone, "carregando" é trocar o
glyph pelo `spinner-gap`, além do `aria-busy="true"`.

**Com ícone, o conteúdo vai num só filho.** Botão, dica (`.ruvor-hint`), erro de campo
(`.ruvor-field__error`) e `callout` só viram flex quando o ícone é filho direto — `.ruvor-glyph`,
ou `.ruvor-icon` no `callout` —; sem ícone, o texto corre normal, como nos mockups. Com ícone, o
que vai ao lado dele fica num só elemento (`<span>` ou `<div>`): solto no contêiner flex, cada
pedaço de texto e cada `<b>` viraria um item, separado pelo `gap`.

Os desenhos não se alteram. Ícone novo entra por
acréscimo ao conjunto, do mesmo Phosphor, com entrada no `icons.json` — o teste
`frontend/tests/icones.test.ts` reprova arquivo sem entrada, cor fixa e ícone fora da
[vitrine](../../docs/mockups/M1.6a/kit.html).

---

## Como consumir no produto

```css
@import url('brand/ruvor/tokens.css');
@import url('brand/ruvor/components.css');
```

A paleta acima é a do tema claro. O escuro vem pelos mesmos tokens, com `data-theme="dark"`
no `html` ou, sem o atributo, pela preferência escura do sistema.

`components.css` só estiliza classes com o prefixo `ruvor-`: não mexe em `html`, `body` nem
títulos soltos. O estilo de base da página — fundo, cor e fonte do corpo — vem da classe
`ruvor-app`, que a página aplica.

`tokens.json` espelha cores e escalas para ferramentas e implementações não-CSS.

**As telas do M1.6b** (busca, casco e tela do ativo) usam só classes da folha: os componentes e
o arranjo que os mockups aprovados de `docs/mockups/M1.6b/` desenharam foram levados a
`components.css` — o campo de busca e a lista (`.ruvor-search*`), a chave de tema
(`.ruvor-segmented`), o rodapé (`.ruvor-footer`), o cabeçalho do ativo, os números com a frase
(`.ruvor-stat`, `.ruvor-note`), os gráficos (`.ruvor-chart*`), a tabela dos modelos com a linha
que abre (`.ruvor-table--models`, `.ruvor-table__row--expandable`), os estados de uma seção
(`.ruvor-state`, `.ruvor-progress`), a trilha (`.ruvor-rail--stack`, `.ruvor-trail`) e a quebra
abaixo de 720 px. A vitrine mostra cada um, nos dois temas. O token `--ruvor-topbar-control` é
o fundo e a borda da chave de tema sobre a barra (mesmo valor do avatar, nome próprio).

---

## Lacunas conhecidas

Os mockups resolveram a lacuna dos **campos de formulário e da densidade**
(`03-nova-analise.html`, e `.field` em `foundation.css`). O M1.6a fechou outras três:

| Fechada | Onde |
|---|---|
| **Estados de interação** — sobrevoo, foco, pressionado, desabilitado, carregando, erro | `components.css`, com token próprio quando o estado muda cor |
| **Modo escuro** | `tokens.css`, pelos mesmos tokens de cor |
| **Escala tipográfica** | `tokens.css`, os tokens `--ruvor-type-*` |

O que continua fora:

| Falta | Situação |
|---|---|
| **Fonte embutida** | a pilha dos mockups começa pela Avenir Next, do macOS; no Windows cai na Segoe UI. Embutir uma fonte é decisão de licença e de peso, e fica para quando houver hospedagem |
| **Guia de componentes escrito** | os mockups e a folha de componentes servem de referência, mas não há especificação textual por componente |

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
