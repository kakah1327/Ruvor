# D-64 — O veredito de adequação é Kupiec **e** Christoffersen; DQ e Basileia ficam de fora

**Status:** aceita · 2026-09-24

## Contexto

O motor roda quatro testes de backtesting por (modelo, nível): Kupiec, Christoffersen, DQ e
Basileia. A plataforma precisa responder **"este modelo é adequado para este ativo?"**, e
quatro resultados soltos não respondem — quem lê precisaria do critério de combinação, que é
justamente o que a plataforma existe para ter.

## Decisão

```python
adequate = None if error else (kupiec_passed and christoffersen_passed)
```

Os dois testam coisas diferentes e complementares — **cobertura incondicional** e
**independência das violações** —, e é o par clássico de cobertura condicional.

**DQ e Basileia são gravados e não entram no veredito.** O DQ é o mais rigoroso dos quatro e
reprovaria quase tudo; a Basileia só reprova na zona **vermelha**, e é critério regulatório
bancário, não teste estatístico de adequação. Incluir qualquer um dos dois daria aparência de
rigor sem acrescentar poder de decisão.

## Consequências

- Os quatro continuam gravados, com `passed`, `p_value` e — no caso da Basileia — a zona.
  Quem quiser outro critério tem o dado; o que a plataforma fixa é o veredito que ela
  publica.
- **`adequate` é nulo quando há `error`**, e isso é o terceiro valor de propósito: "não deu
  para julgar" não é "reprovado". Gravar `False` apagaria a distinção.
- O veredito é **por (modelo, nível)**: um modelo pode ser adequado a 95% e não a 99% no
  mesmo ativo.
- **O veredito fala da série de VaR no período de teste, não do `var_latest`.** Os quatro
  testes avaliam a série; o número que o usuário vê é o do último pregão, e ele não tem
  backtest próprio. O veredito diz "este modelo tem se comportado bem neste ativo", não
  "este número está certo" — distinção que a camada explicativa do M2.3 vai precisar fazer e
  que a tela do M1.6 não deve apagar.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-13, RF-14).
