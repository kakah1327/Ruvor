# D-144 — A classificação da B3 se corrige na saída da API, por tabela fechada; estende a D-47

**Status:** aceita · 2026-09-29 · estende a [D-47](D-47-fonte-do-catalogo-e-o-site-da-b3.md) ·
spec do [M1.7](../specs/M1.7-busca-e-catalogo.md)

## Contexto

A D-47 manda guardar a classificação setorial como a B3 a entrega, com ponto no lugar da vírgula, e a spec do
M1.1 deixou a vírgula "para a tela". A tela mostra "Petróleo. Gás e Biocombustíveis", e o M1.6b registrou
a dívida (`docs/ESTADO.md:1400`, "Dívida registrada"). O ponto não se corrige
por regra: no catálogo de 2026-09-29 há sete textos distintos com ponto, e em dois ("Máq. e Equip.") ele é
abreviação legítima. E o texto de `silver.asset` é a chave com que a `fundamentos` agrupa os pares
([D-132](D-132-pares-sao-o-segmento-da-b3-pela-tupla.md)): mudá-lo muda o grupo.

## Decisão

1. **O `silver` continua com o texto da B3** — a D-47 vale como está.
2. **A API corrige na saída**, por uma **tabela fechada** de texto inteiro para texto inteiro, em todo campo de
   classificação que publica: `sector`, `subsector`, `segment` do ativo e `group_*` dos pares. Texto fora da
   tabela sai como veio. Nunca se substitui trecho.
3. **Texto novo com ponto aparece no relatório** da coleta do catálogo, para a tabela ganhar a linha.

Decisão do dono da frente, 2026-09-29.

## Consequências

- Os contratos com a `fundamentos` não mudam: nenhum valor gravado muda.
- A tabela envelhece se a B3 mudar um texto; o relatório é o aviso, e a planilha oficial de classificação da B3
  continua sendo a saída maior, fora do M1.7.
- Quem consome a API pública vê a vírgula; quem lê o banco vê o ponto.
