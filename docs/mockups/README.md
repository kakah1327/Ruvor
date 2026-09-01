# Mockups

Um diretório por bloco. HTML estático, usando **os tokens reais** de
[`brand/ruvor/tokens.css`](../../brand/ruvor/tokens.css).

## Por que existem

Toda tarefa visual vira duas: primeiro o mockup, depois a implementação
([PROCESSO.md §7](../PROCESSO.md#7-portão-de-mockup)).

- **Revisar mockup é barato; revisar tela integrada é caro.** Mudar cor e reordenar bloco num
  HTML estático leva minutos; no componente já ligado a dados e estado, horas.
- **Usar os tokens reais** garante que o que se aprova é exatamente o que dá para construir —
  sem distância entre a arte e o que sai no navegador.
- **O mockup aprovado vira o critério da revisão** da implementação. Deixa de ser "ficou
  bonito?" e passa a ser "bate com o aprovado?", que é verificável.

## Regras

- Nada de valor de cor escrito à mão — só tokens
- Um arquivo por tela; nomes semânticos
- Iteração ganha sufixo de versão (`busca-v2.html`), nunca sobrescreve

*Nenhum mockup criado ainda.*
