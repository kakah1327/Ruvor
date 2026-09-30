# D-151 — O texto das duas leituras mora no frontend; restringe a D-97 e a PRODUTO §2

**Status:** aceita · 2026-09-29 · com a aprovação da [spec do M2.3](../specs/M2.3-camada-explicativa.md)

## Contexto

A [PRODUTO §2](../PRODUTO.md#2-público-e-postura) quer o texto explicativo "versionado com a métrica que
explica". A [D-97](D-97-no-marco-1-cada-numero-tem-uma-frase-fixa.md) pôs a frase de cada número num módulo do
frontend no Marco 1 e deixou ao M2.3 decidir onde o texto mora quando houver duas leituras. Levá-lo ao banco ou à
API exigiria tabela, rota e mudança de contrato da API pública do M4.2, sem leitor que precise dele fora da tela.

## Decisão

1. **As duas leituras moram em `frontend/src/content/`**, uma entrada por (chave, nível), versionadas no
   repositório. A avançada tem a mesma chave e a mesma assinatura da iniciante.
2. **Restringe o item 3 da D-97**, que previa o M2.3 substituindo o módulo de textos: o módulo `textos.ts` **não é
   substituído** — continua com a leitura iniciante — e **ganha um irmão**, `avancado.ts` (`TEXTOS_AVANCADOS`).
3. **"Versionado com a métrica" é cumprido pelo repositório:** a frase e o cálculo mudam no mesmo commit e são
   revisados na mesma PR. Não há texto no banco nem na API; a chave de leitura do M4.2 não recebe texto.

## Consequências

- A API não muda com o M2.3.
- Nada automático impede o cálculo de mudar no backend e a frase ficar para trás; a proteção é de processo. **Dentro
  da `marco1`**, o bloco que muda um cálculo com frase atualiza as duas frases na mesma PR. **Entre frentes** — os
  fundamentos e os pares, calculados pela `fundamentos` — a mesma PR não existe: a proteção é o contrato de revisão de
  [FRENTES.md](../FRENTES.md#contratos-entre-frentes), pelo qual mudar o sentido de uma coluna lida exige a revisão da
  `marco1`, que atualiza as frases.
- Se um consumidor da API precisar do texto (relatório do M4.1, por exemplo), uma decisão nova o leva adiante.

Origem: [spec M2.3 — Camada explicativa](../specs/M2.3-camada-explicativa.md).
