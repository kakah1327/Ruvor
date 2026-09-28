# D-93 — Os ícones do produto vêm do Phosphor, num conjunto fechado dentro do kit

**Status:** aceita · 2026-09-28

## Contexto

No portão da vitrine do M1.6a, o dono da frente aprovou o kit, com uma ressalva: **está textual
demais e faltam ícones**. O kit não tinha conjunto de ícones — os quatro mockups de referência
somam uns doze, desenhados à mão, e a folha só tinha o `.ruvor-icon` dos sinais, com o SVG escrito
por quem usa.

O dono escolheu uma biblioteca aberta, com ícones nos componentes e na vitrine. Três foram
comparadas lado a lado, aplicadas ao kit nos dois temas
([`docs/mockups/M1.6a/icones-comparativo.html`](../mockups/M1.6a/icones-comparativo.html)):
Lucide (o traço exato dos mockups, um peso só), Phosphor (seis pesos do mesmo desenho) e Radix
(pequeno demais para o domínio: sem risco, gráfico de linha nem banco de dados). As skills de
direção visual do ambiente desaconselham o Lucide como genérico.

## Decisão

1. **Os ícones do produto vêm do [Phosphor](https://phosphoricons.com)** (licença MIT), pacote
   `@phosphor-icons/core`, numa versão fixa. **Peso `regular` na interface**; **`duotone` nos
   sinais** (`.ruvor-icon`) — é o que deixa o estado visual, não só escrito.
2. **Conjunto fechado, copiado para dentro do kit** — `brand/ruvor/icons/`, um `.svg` por ícone
   e peso, com o arquivo de licença e um `icons.json` que lista nome, peso, arquivo e versão de
   origem. **Sem dependência de runtime**: o frontend não instala o pacote. Ícone novo entra por
   acréscimo ao conjunto, com o mesmo teste.
3. **A cor do ícone é a do texto** (`fill: currentColor`; no duotone, a camada de fundo é a mesma
   cor com a opacidade do próprio desenho): o ícone nunca carrega cor própria. **Ícone nunca é o
   único sinal** — vem com rótulo, ou com `aria-label` quando o controle é só ícone —, como o
   `README` do kit já exige para a cor.
4. **A folha de componentes ganha o ícone ao lado do rótulo** — botão, tag, sinal, link da barra,
   cabeçalho de painel, `callout` —, com tamanho e espaçamento declarados na folha.

## Consequências

- O M1.6a ganha a tarefa T4b (plano), e a vitrine volta ao portão.
- O desenho do Phosphor é de forma cheia, não de traço: o `.ruvor-icon` deixa de desenhar por
  `stroke` e passa a `fill`. O traço de 2 px dos ícones desenhados à mão nos mockups de referência
  deixa de ser a régua — os mockups ficam como estão, como histórico da direção visual.
- O M1.6b usa os ícones do conjunto; o que faltar entra por acréscimo, do mesmo Phosphor.
