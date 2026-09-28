# D-130 — A notícia do Ruvor é o que a companhia divulga na CVM (IPE), não a imprensa

**Status:** aceita · 2026-09-27

## Contexto

A camada 5 do produto pede "notícias" ([PRODUTO §3](../PRODUTO.md#3-as-cinco-camadas)), e
nenhuma fonte estava escolhida. Portais de imprensa têm termos de uso e licença do conteúdo que o
produto não controla, e ligam a notícia ao ticker por texto, sem chave. A CVM publica nos dados
abertos o **IPE**, os documentos que a própria companhia entrega, com `Codigo_CVM`, categoria,
data de entrega e link. É o mesmo portal e o mesmo cliente HTTP do M3.1
([D-120](D-120-fundamento-vem-dos-dados-abertos-da-cvm.md)).

## Decisão

**As notícias do Ruvor são os comunicados da companhia à CVM**, do IPE, em três categorias:
**fato relevante**, **comunicado ao mercado** e **aviso aos acionistas**. Guardam-se o título, a
data, a categoria e o link para o documento na CVM. O documento em si (o PDF) não é baixado,
lido nem resumido. As outras categorias do IPE ficam só na `bronze`, que guarda o zip inteiro
([D-121](D-121-a-bronze-guarda-o-zip-inteiro-e-so-quando-o-conteudo-muda.md)).

## Consequências

- A ligação com o ticker é por `code_cvm`, valor, como a da companhia
  ([D-126](D-126-companhia-e-entidade-ligada-ao-ticker-por-valor.md)); não há casamento por texto.
- Comunicado não é notícia: o que a imprensa publica antes da companhia não aparece até a
  companhia entregar o documento. A tela, de outro bloco, precisa chamá-los de "comunicados da
  companhia à CVM".
- Imprensa, se um dia entrar, é outra fonte e outra decisão.

Origem: [spec M3.2 — Contexto](../specs/M3.2-contexto.md) (RF-02, RF-03, RF-05).
