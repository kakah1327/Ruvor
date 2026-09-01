# Ruvor — identidade visual

Especificação da marca. Este diretório **manda** em qualquer questão visual: se um estudo em
[`estudos/`](estudos/) divergir daqui, o que vale é isto.

---

## Ordem de leitura

1. Este documento
2. `tokens.css` — os valores; importe **antes** de qualquer estilo do produto
3. `implementation.css` — referência de componentes e layout, consumindo só tokens aprovados
4. `examples/` — três telas funcionais que demonstram o uso. Abra no navegador

Os exemplos não são arte solta: são a prova de que os tokens sustentam telas reais.

---

## Assinatura

| Arquivo | Uso |
|---|---|
| `ruvor-logo.svg` | Padrão, sobre fundos claros (`#F7F6F2`) |
| `ruvor-logo-reverse.svg` | Sobre grafite (`#292A2E`) |
| `ruvor-mark.svg` | Ícone para app, favicon e áreas compactas |
| `ruvor-mark-reverse.svg` | O mesmo, sobre grafite |

O logo completo traz o símbolo mais a palavra "ruvor" **já vetorizada** — não depende de
fonte instalada.

O símbolo é uma matriz de sinais analíticos. **Sempre em uma cor só**, sem gradiente, sombra
ou semáforo aplicado aos pontos. A cor vive no produto; o símbolo permanece técnico.

### Regras de aplicação

- **Espaço livre:** ao menos a largura de um ponto grande do símbolo, em todos os lados
- **Tamanho mínimo:** 24 px para o símbolo; 120 px para a assinatura completa
- **Nunca** redesenhar, recolorir ou aplicar efeito

---

## Paleta

| Token | Cor | Significado |
|---|---|---|
| `--ruvor-ink` | `#292A2E` | Marca, tipografia e estrutura |
| `--ruvor-paper` | `#F7F6F2` | Fundo principal e marca reversa |
| `--ruvor-surface` | `#E9E7E2` | Cards e superfícies secundárias |
| `--ruvor-border` | `#C8C4BC` | Divisórias e campos |
| `--ruvor-decision` | `#8F3B4B` | Decisão, limite, foco de ação |
| `--ruvor-review` | `#B79754` | Revisão e atenção |
| `--ruvor-evidence` | `#54727B` | Evidência, séries, comparação |
| `--ruvor-validated` | `#587060` | Validação e condição preservada |
| `--ruvor-critical` | `#B4524C` | Exceção crítica |

**A cor carrega significado, não decoração.** Grafite, papel e superfície ocupam a maior
parte da tela; as cores semânticas entram para indicar condição.

**Vinho e vermelho-óxido são distintos de propósito:** `decision` é "precisa de ação";
`critical` é "algo falhou". Nunca substituir um pelo outro — senão "agir" se confunde com
"quebrou".

---

## Regras de interface

**Cor nunca é o único sinal.** Todo estado precisa de texto e/ou ícone junto. Vale para
acessibilidade e para quem imprime em preto e branco.

**Raios:** cards usam `--ruvor-radius-md`; botões e campos usam `--ruvor-radius-sm`.

**Tipografia:** dados quantitativos em fonte mono (`--ruvor-font-mono`); navegação e texto
corrido em sans (`--ruvor-font-sans`). Um número que se lê e se compara pede monoespaçada.

---

## Como consumir no produto

```css
@import url('brand/ruvor/tokens.css');
```

`tokens.json` espelha as cores e escalas para ferramentas e implementações não-CSS.

**Nunca escreva um valor de cor direto no produto.** Se um tom necessário não existe como
token, ele não foi aprovado — o caminho é acrescentar o token aqui, não improvisar na tela.

---

## Lacunas conhecidas

O kit está incompleto. Estas faltas **bloqueiam o Marco 1**, porque toda tela passa por
mockup aprovado antes de virar código, e os mockups usam estes tokens:

| Falta | Por que bloqueia |
|---|---|
| **Componentes de formulário** — campo, seleção, caixa de marcação | A tela de configuração de análise é essencialmente um formulário grande |
| **Estados de interação** — foco, sobrevoo, desabilitado, erro | Nenhuma tela interativa fica completa sem eles |
| **Modo escuro** | O kit é só claro; o protótipo atual é escuro-primeiro. Decisão pendente |
| **Guia de componentes** | Previsto no plano original do kit, nunca escrito |

Registrado em [`docs/ESTADO.md`](../../docs/ESTADO.md) e
[`docs/PRODUTO.md`](../../docs/PRODUTO.md#8-pendências-de-produto).

---

## Histórico

Como se chegou a esta identidade — direções exploradas, rodadas de naming, estudos de
assinatura e cor — está em [`estudos/`](estudos/). É registro de decisão, **não
especificação**.

**Pendência:** a verificação de disponibilidade de marca e domínio, pedida ao fim das
rodadas de naming, nunca foi feita. O nome está decidido
([D-01](../../docs/decisoes/D-01-nome-do-produto-e-ruvor.md)), mas a verificação segue
valendo em paralelo.
