# D-80 — O retreino de produção é a cada 252 pregões, o do protocolo; restringe a D-18

**Status:** aceita · 2026-09-27

## Contexto

A [D-18](D-18-separacao-treino-previsao.md) separou treino de previsão em produção e disse
como: as redes "treinadas periodicamente (semanal ou mensal)" e a previsão diária "uma passada
só, em milissegundos". A ARQUITETURA repetia a mesma tabela de rotina.

O M1.5b implementou a separação, e nenhuma das duas frases sobreviveu ao contrato de igualdade
([D-78](D-78-incremental-igual-ao-do-zero-e-full-e-a-referencia.md)): o que a plataforma mostra
é o **backtest** de dez anos, e ele só sai igual ao do zero se os pontos de retreino forem os
do protocolo do motor.

## Decisão

**O retreino de produção é a cada 252 pregões**, nos mesmos pontos do backtest do motor e do
TCC (§3, "reestimação periódica a cada 252 dias úteis"). Qualquer outra cadência quebraria a
igualdade com o backtest.

**A rotina diária não é uma passada só**: ela reconstitui a série inteira do backtest por
previsão, trecho a trecho, cada um com o retrato do seu ponto — e treina só quando a série
cruza um ponto de retreino ou um retrato é invalidado. O custo é de **segundos por ativo**, não
de milissegundos. Um ativo novo, ou um retrato invalidado na posição 0, faz a busca de
configuração e treina tudo, como antes.

## Consequências

- A D-18 não é editada: continua valendo para o que ela protege — treino e previsão separados —
  e passa a valer restringida por esta na cadência e no custo.
- A tabela de rotina da ARQUITETURA foi corrigida no fecho do M1.5b.
- O custo medido no fecho do M1.5b está no ESTADO: o dia comum de um ativo sem invalidação,
  contra o cálculo completo.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
("Decisões novas que este bloco produz", 6; "O que fica falso").
