# D-131 — Um documento do IPE se identifica pelo link, e a `silver` guarda só a versão corrente

**Status:** aceita · 2026-09-27

## Contexto

O IPE traz `Protocolo_Entrega`, `Versao` e `Link_Download`. Medido em 2026-09-27, o par
(protocolo, versão) **não** é único: 58 pares se repetem nas três categorias das companhias do
catálogo, sempre com links diferentes — uma entrega com mais de um documento. O link é único por
documento, e a versão faz parte dele (`numVersao`).

A companhia reapresenta documentos (espontaneamente ou por exigência), e o zip de cada ano traz,
em regra, só a versão vigente. Guardar tudo na `silver` misturaria a versão superada com a atual.

## Decisão

**A identidade de uma linha de `silver.disclosure` é o `Link_Download`.** Conformar (companhia,
ano) grava os links do zip corrente que passam nas três categorias e **remove** as linhas da
companhia naquele ano cujo link não está no conjunto conformado do ano — a versão superada, o
documento retirado, o que mudou para categoria de fora e o que passou a outra companhia. Link
que já existe sob outra companhia é **atualizado**, não é falha. O histórico fica na `bronze`.

**Exceção de reversão:** a volta da migration `0002_disclosures_and_peers` apaga as linhas
`kind = 'ipe'` de `bronze.cvm_file`, a única escrita que apaga numa tabela só-acréscimo. Sem ela,
a volta deixaria na `bronze` um tipo que a coluna, de volta à `0001`, não aceita.

## Consequências

- A `silver` é o estado corrente do IPE, não o histórico: a contagem é por link. Na carga real de
  2026-09-27, 80.900 linhas; os 80.842 medidos na spec eram pares (protocolo, versão) distintos,
  e a diferença são os 58 pares repetidos.
- A remoção roda sobre o conjunto do ano inteiro, calculado antes do laço das companhias: a
  ordem em que as companhias são visitadas não muda o resultado.

Origem: [spec M3.2 — Contexto](../specs/M3.2-contexto.md) (RF-04, RF-04a, RF-04b).
