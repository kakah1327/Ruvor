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
| M1.6b | [`M1.6b/graficos-comparativo.html`](M1.6b/graficos-comparativo.html) | Recharts, uPlot e lightweight-charts desenhando preço, distribuição de retornos e VaR por modelo, com dado real da API pelo proxy do Vite, nos dois temas, para a escolha da biblioteca de gráfico | ✅ usado na escolha; o uPlot foi escolhido ([D-94](../decisoes/D-94-os-graficos-sao-do-uplot.md)) |
| M1.6b | [`M1.6b/busca.html`](M1.6b/busca.html) | o casco e a busca: barra, chave de tema, rodapé com a ressalva, a página inicial em todos os estados e a lista suspensa; dado real pelo proxy | ✅ aprovado pelo dono em 2026-09-28 |
| M1.6b | [`M1.6b/ativo.html`](M1.6b/ativo.html) | a tela do ativo com dado real do ITUB4: cabeçalho, preço, proventos, comportamento, risco com discordância, não rejeitados e a tabela dos nove, trilha; com os textos de cada número | ✅ aprovado pelo dono em 2026-09-28, com cinco ajustes aplicados |
| M1.6b | [`M1.6b/ativo-estados.html`](M1.6b/ativo-estados.html) | os estados da seção de risco (E2 a E9, E6b, carregando e erro), as respostas do pedido, cada motivo, e os estados fora do risco (comportamento não calculado, sem preço, índice, ativo não encontrado, erro de seção) | ✅ aprovado pelo dono em 2026-09-28 |
| M1.6c | [`M1.6c/ativo-fundamentos.html`](M1.6c/ativo-fundamentos.html) | as seções Fundamentos e Comunicados da companhia à CVM depois do risco, com dado real da PETR4 e do ITUB4 pelo proxy (os pares, o filtro e o "mostrar mais"); os estados montados à mão num seletor — sem indicador (AZEV11 e IBOV reais), pares `subsector`/`none`/nulos, P/L negativo, cada motivo de `per_share_missing` e `market_cap_missing`, o plano de contas, a genérica, sem comunicados, filtro sem resultado, os dois `company: null`, carregando e erro —; e a tabela de todos os textos novos | ✅ aprovado pelo dono em 2026-09-29 |

A vitrine não é tela de produto: consome só `tokens.css` e `components.css`, e as classes de
estado forçado (`.is-hover`, `.is-focus`) existem só nela. O serviço `frontend` monta este
diretório só para leitura, e `frontend/tests/icones.test.ts` confere que todo ícone do conjunto
aparece na vitrine.
