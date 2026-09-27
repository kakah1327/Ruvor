# D-121 — A `bronze` guarda o zip inteiro, e o conteúdo só de novo quando mudou

**Status:** aceita · 2026-09-27

## Contexto

A [D-13](D-13-camadas-bronze-prata-ouro.md) quer a `bronze` para provar e **reprocessar**. No
M1.1 e no M1.2 a resposta da fonte é pequena e cabe inteira na linha. Os zips da CVM têm de
0,2 a 33 MB cada, e a conformação lê só uma fração deles.

Medido na spec: a CVM **regera os zips dos anos recentes toda semana**, com `Last-Modified`
novo, mesmo quando nada mudou dentro. Comparar o hash do arquivo baixado gravaria o mesmo
conteúdo toda semana.

## Decisão

**Todo `GET` deixa uma linha em `bronze.cvm_file`**, com ou sem `payload`. O **zip inteiro** vai
em `payload` **só quando o conteúdo é novo** — o `content_sha256` difere do da última linha com
`payload` daquele (tipo, ano). O hash é **do conteúdo, não do zip**: nome e bytes de cada
membro, em ordem de nome, de modo que o zip regerado com os mesmos CSVs dá o mesmo hash.

A coleta é incremental: `HEAD` antes, e `GET` só se o `Last-Modified` difere do último visto.
`--full` baixa todos.

A `silver` se refaz a partir da `bronze` por `import_fundamentals --reconform [ANO ...]`, **sem
sair para a rede**.

## Consequências

- Guardar só as linhas do catálogo seria menor, e perderia a companhia que entra no catálogo
  depois: com o zip inteiro, ela recebe o histórico todo sem baixar nada.
- A primeira carga real ocupou ~404 MiB. Depois, cada semana em que o conteúdo de um ano recente
  muda grava o zip de novo — no pior caso, ~1,5 GB por ano. Retenção da `bronze` é pergunta de
  hospedagem, que está aberta.
- Medido em 2026-09-27: a segunda execução, logo depois da carga, saiu com os 22 arquivos
  `nao modificado` (V-09); `--reconform 2025` saiu com 0 criados e 0 atualizados, sem chamada à
  CVM (V-10).
- Regra corrigida volta a valer para o passado por `--reconform`: foi o caminho do RF-08b,
  nascido na revisão final, aplicado sobre a `bronze` já baixada.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-04 a RF-06, RF-17, RF-18).
