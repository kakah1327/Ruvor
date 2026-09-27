# D-129 — Lucro só na mãe: vale a mãe; e o LPA não cai para a `3.99`

**Status:** aceita · 2026-09-27

## Contexto

No consolidado, o lucro da controladora é a filha "Atribuído a/aos Sócios da Empresa
Controladora" da conta de lucro consolidado
([D-122](D-122-conta-se-localiza-pela-descricao-sob-mae-fixa.md)). A revisão final da
implementação achou companhias que informam o lucro **só na mãe** e deixam as duas filhas — a
da controladora e a dos não controladores — zeradas. A Sabesp (`14443`) informa, no DFP 2024,
`3.11` = 9.579.563 mil e `3.11.01` = `3.11.02` = 0.

Pela regra como estava, essas companhias saíam com lucro **0**, e com ROE e margem 0: número
errado com cara de certo. Na `gold` da carga real havia 37 linhas com `roe`, `net_margin` ou
`net_income_ttm` exatamente 0. Medido na `bronze`: 49 documentos do catálogo no DFP 2024 e 112
no ITR 2026 nesse caso.

## Decisão

**Vale a mãe** (decisão do dono da frente, 2026-09-27). No consolidado, por período
(`DT_INI_EXERC`), se a filha da controladora e a dos não controladores **somam 0** e a mãe de
nível 1 é **diferente de 0**, `net_income_parent` é o valor da mãe: a companhia não separou a
parte dos não controladores, e o lucro consolidado vai inteiro como da controladora.

A filha dos não controladores se reconhece pela descrição **igual** a uma das duas grafias
medidas nos 22 zips — "Atribuído a Sócios Não Controladores" e "Atribuído aos Sócios não
Controladores" (esta nos bancos forma A). **Ausente**, conta como 0; **repetida** (mais de uma linha), a
regra não se aplica e vale a regra geral de localização (RF-08).

**O LPA não cai para a conta `3.99`** quando falta nas filhas de "Lucro Básico por Ação": no
Itaú ela traz a soma das classes (16,72 contra 4,20 por ação), e alargar a regra dependeria da
sorte da fonte. A escala das ações dessas companhias fica nula
([D-124](D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md)).

## Consequências

- Pode superestimar o lucro da controladora onde há minoritários não informados.
- O 4º trimestre pode subtrair um DFP que valeu a mãe de um ITR que valeu a filha: 29 casos
  companhia-ano de 2016 a 2025, todos de magnitude pequena.
- Aplicada por `--reconform` sobre a `bronze` já baixada: SBSP3 passou a sair com
  `net_income_ttm` de R$ 8.040 mi e `roe` 0,178, e **nenhuma** linha da `gold` ficou com `roe`,
  `net_margin` ou `net_income_ttm` exatamente 0 (antes, 37). PETR4, VALE3 e ITUB4 não mudaram:
  as três têm a filha da controladora diferente de 0.
- Dos 51 documentos do DFP 2024 consolidado com o lucro zerado, 49 se resolvem; 2 têm os não
  controladores diferentes de 0 e seguem em 0.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-08b; "A escala das ações é
inferida, não lida"); plano, tarefa 11c.
