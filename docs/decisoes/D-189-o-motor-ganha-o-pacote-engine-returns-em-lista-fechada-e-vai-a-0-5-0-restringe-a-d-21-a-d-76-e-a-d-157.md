# D-189 — O motor ganha o pacote `engine.returns`, em lista fechada de arquivos novos, e vai a `0.5.0`; restringe a D-21, a D-76 e a D-157

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do [M5.1](../specs/M5.1-retorno.md)
aprovada pelo dono

## Contexto

Mudança no motor só em lista fechada e autorizada ([D-21](D-21-motor-ml-congelado-ate-etapa-6.md),
[D-76](D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md),
[D-157](D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md)). A
[D-58](D-58-calculo-da-camada-2-mora-no-backend.md) diz que o motor é o ativo científico de VaR e
backtesting, e a [D-59](D-59-sem-dependencia-numerica-nova-no-backend.md) que o backend não ganha `numpy`.

## Decisão

1. **A lista fechada**: em `engine/src/`, só arquivos novos dentro de `engine/src/engine/returns/`
   (`__init__.py`, `base.py`, `registry.py`, `models.py`, `evaluation.py`, `runner.py`); **nenhuma linha de
   arquivo existente em `engine/src/` muda**; em `engine/pyproject.toml`, só a versão.
2. **Dois modelos**, `historical_mean` e `ar_1`, sem seleção de ordem, com registry próprio; só `numpy`,
   `pandas` e `scipy`.
3. **O motor vai a `0.5.0`.**
4. **O manifesto do retorno não tem semente**: nada é aleatório, e um teste prova a reprodução bit a bit —
   restrição à [D-15](D-15-manifesto-de-execucao.md) nesse ponto.
5. **Estende o que a D-58 diz do motor**: ele passa a ser também o ativo da previsão de retorno e da
   validação dela; função descritiva continua fora.

## Consequências

- A versão nova invalida todos os retratos ([D-77](D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md),
  [D-81](D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md)) e provoca, uma vez, o
  retreino completo dos quatro modelos caros em cada ativo coberto.
- O VaR do `0.5.0` é o do `0.4.0`: a linha de base numérica da
  [D-159](D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md) continua valendo, e a
  fase A do M5.1 confere os 108 pares (ativo, modelo, nível) iguais aos do `0.4.0`.
- Nunca rodar o código `0.4.0` com a imagem `0.5.0`, nem o contrário com o cálculo do retorno: a versão
  sairia errada em linhas imutáveis ([D-16](D-16-resultado-e-imutavel.md)).
