# D-18 — Separacao entre treino e previsao em producao

**Status:** aceita · 2026-08-29

## Contexto

Os 20 a 60 minutos de um experimento fizeram surgir a pergunta: o usuario vai esperar uma hora? Treinar e prever tem custos separados por ordens de grandeza.

## Decisão

Em producao, **treino e previsao sao atividades distintas**: as redes sao treinadas periodicamente (semanal ou mensal) e a previsao diaria e uma passada so, em milissegundos.

## Consequências

- Esta e a decisao de arquitetura que faz a conta fechar. Sem ela, o produto seria inviavel.
- Rotina diaria: busca precos, roda previsoes com modelos ja treinados, reajusta os modelos estatisticos (segundos).
- Os pesos de uma rede nao mudam de forma relevante de um dia para o outro; o que muda e o dado que entra nela.
- Quando o usuario pesquisa um ativo coberto, a resposta ja esta no banco.
