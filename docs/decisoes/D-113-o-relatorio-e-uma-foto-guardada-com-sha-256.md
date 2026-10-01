# D-113 — O relatório é uma foto guardada: o JSON entregue, byte a byte, com o SHA-256 dele, em `core.report`

**Status:** aceita · 2026-09-29 · frente `identidade`

## Contexto

O Marco 4 pede relatórios exportáveis e auditáveis. O risco de um ativo só saía pelo
`GET /api/v1/assets/{ticker}/risk`, um corpo de API que muda quando o risco é recalculado e não tem
identidade própria. O manifesto (D-15) e a imutabilidade do resultado
([D-16](D-16-resultado-e-imutavel.md)) dizem de onde cada número veio, mas nada registrava **o que
foi entregue, a quem e quando**: um CSV editado à mão era indistinguível do original.

## Decisão

Cada relatório gerado é uma linha de `core.report`, com os **bytes exatos** do JSON entregue
(`content`) e o SHA-256 deles (`sha256`). O JSON é o **original**: é ele que se guarda, que recebe
o hash e que o `GET reports/{id}/json` devolve sem nenhuma transformação. O **CSV** é uma visão da
tabela de resultados, derivada de forma determinística do JSON guardado — nunca do banco de risco —
e sem hash próprio; um PDF, se vier, também deriva do JSON guardado, sem recalcular.

O conteúdo tem `format` e `format_version`. O formato 1 (o risco do ativo: o manifesto da execução,
os 18 resultados e, por nível, a faixa entre os modelos e os não rejeitados) e a serialização dele
— `json.dumps` com `sort_keys`, sem espaço, UTF-8, decimal em texto de ponto fixo, instante em UTC
— **são contrato para sempre**. Mudança no conteúdo é um `format_version` novo; os relatórios
antigos continuam no formato em que nasceram. Gera-se sempre da última execução fechada do ativo,
e gerar duas vezes dá dois relatórios.

## Consequências

- Estende a D-16 da execução para a entrega: recalcular o risco não muda relatório já gerado.
- Dentro do conteúdo imutável vai só o **nome** de quem pediu, no instante; o e-mail fica na coluna
  `requested_by`, lida pela API. Apagar o nome por pedido de titular exige decisão nova e
  intervenção no banco.
- A zona de Basileia fica fora do formato 1: um número suspeito gravado num relatório imutável
  ficaria para sempre.
- O SHA-256 prova integridade contra o registro do Ruvor, não autoria para terceiro sem acesso a
  ele; isso seria assinatura digital, fora deste bloco.
- `core.report` tem `PROTECT` para a execução, o ativo, a organização e a pessoa que cita: nada que
  um relatório cita se apaga.
- Medido na execução real (2026-09-30), o relatório do `ITUB4` tem 10 077 bytes.

Origem: [spec M4.1 — Relatórios](../specs/M4.1-relatorios.md).
