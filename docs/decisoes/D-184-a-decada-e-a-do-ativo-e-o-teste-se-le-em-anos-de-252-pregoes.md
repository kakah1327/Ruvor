# D-184 — A década é a do ativo, do primeiro pregão a dez anos de calendário depois, e o teste se lê em anos de 252 pregões, os trechos entre dois retreinos

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do
[M2.4](../specs/M2.4-regime-de-laboratorio.md) aprovada pelo dono (no portão: o veredito por ano só a 95%)

## Contexto

A Etapa 6 do TCC usa um período comum (2015–2024) que o banco não tem. Um período comum cortado nos dados
de hoje (2016-11 a 2026-09, que todos os seis ativos cobrem) mudaria o primeiro pregão da série,
invalidaria a identidade dos retratos (`first_price_date` e a impressão digital) e obrigaria cada
experimento a treinar do zero (~3 min por ativo), com números diferentes dos da produção para os mesmos
dias. E, com a coleta trazendo dez anos para trás da data da cobertura, um fim comum deixaria cada ativo
coberto depois com uma "década" menor.

## Decisão

1. **A década vai do primeiro pregão do ativo à mesma data dez anos depois** (29/02 vira 28/02); a série
   do experimento são os pregões com data menor ou igual ao fim; o experimento só existe com a década
   completa (o último pregão no fim ou depois) e suficiente (pelo menos 503 pregões). A coleta inicial
   traz exatamente isso, então todo ativo coberto completa a sua.
2. **O teste se corta em trechos de 252 retornos a partir do primeiro**, iguais para os nove modelos
   porque os nove reestimam nas mesmas posições; o último pode ser mais curto, e o trecho com menos de
   126 retornos não é julgado.
3. **O veredito por ano é só a 95%.** A 99%, num trecho de 252 esperam-se 2,5 violações, e o Kupiec
   rejeita até o trecho sem nenhuma violação a partir de **192** retornos (p ≈ 0,024 em 252): o veredito
   a 99% fica só na década. A 95%, cada trecho julgado de um modelo correto sai "não adequado" por acaso
   **perto de 7%** das vezes (o Kupiec ~6%, o Christoffersen ~1,6%) — cerca de um ano em catorze, entre as
   81 células julgadas —, e o texto avançado o diz.

## Consequências

- Os períodos diferem entre ativos, e cada um diz o seu. O ativo com IPO recente só ganha experimento
  quando completa dez anos de preço (o AALR3 completa em 2026-10-28).
- **A década depende de quando o ativo foi coberto**: um ativo coberto em 2028 tem a década 2018–2028, e
  as décadas de dois ativos não são o mesmo período nem comparáveis entre si.
- Anos de calendário ficaram de fora: o primeiro e o último seriam pedaços e não coincidiriam com o
  retreino.

## Correção registrada no fecho

O rascunho na spec (e o RF-03, o RF-16 e os Riscos dela) dizia "trechos de **~190** retornos ou mais" e
"perto de **10%**" de rejeição por acaso por trecho (1 − 0,95², supondo os dois testes independentes e
exatos). As contas da conferência técnica (`docs/mockups/M2.4/conferencia-laboratorio.md`, "O que não se
ancora") dão **192** (a fórmula do Kupiec com zero violações passa do crítico a partir de n = 192) e
**perto de 7%** (o Christoffersen rejeita bem menos que 5% em trechos com poucas violações). Esta decisão
nasce com os números corrigidos; as frases da tela já os usam.
