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

## Mockups

| Bloco | Arquivo | O que é | Situação |
|---|---|---|---|
| M1.6a | [`M1.6a/kit.html`](M1.6a/kit.html) | a vitrine do kit: cada token e cada componente, em todos os estados, nos dois temas, com a chave de tema e os ícones do conjunto | ✅ aprovada pelo dono da frente em 2026-09-28 |
| M1.6a | [`M1.6a/icones-comparativo.html`](M1.6a/icones-comparativo.html) | Lucide, Phosphor e Radix aplicados ao kit, lado a lado, para a escolha da biblioteca de ícones | ✅ usado no portão; o Phosphor foi escolhido ([D-93](../decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md)) |

A vitrine não é tela de produto: consome só `tokens.css` e `components.css`, e as classes de
estado forçado (`.is-hover`, `.is-focus`) existem só nela. O serviço `frontend` monta este
diretório só para leitura, e `frontend/tests/icones.test.ts` confere que todo ícone do conjunto
aparece na vitrine.
