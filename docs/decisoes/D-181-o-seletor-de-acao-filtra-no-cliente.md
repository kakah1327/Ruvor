# D-181 — O seletor de ação da carteira filtra no cliente

**Status:** aceita · 2026-10-03, com a spec do M2.2b · registrada no fecho do bloco, 2026-10-07 · frente `marco1`

## Contexto

A composição da carteira só aceita ação ativa: o M2.2a recusa índice, ação inativa e ação repetida com
`400 invalid_holdings`. O seletor da composição precisa de uma lista de ativos. A busca do catálogo
(`GET /api/v1/assets?q=`) já devolve `kind`, `status`, `has_prices` e `has_risk` em cada item. Uma rota nova, ou um
filtro novo na busca, mudaria o backend. O M2.2b só consome o backend como está.

## Decisão

1. **O seletor usa a busca do catálogo como está e filtra no cliente** (`pickReason`, em
   `frontend/src/components/AssetPicker.tsx`). Só a ação ativa (`kind` `stock`, `status` `active`) que ainda não está
   na composição pode ser escolhida.
2. **O resto da página da busca aparece desabilitado, com o motivo** no lugar do setor: índice, ação inativa ou ação
   já na composição. O item desabilitado tem `aria-disabled="true"`. As setas passam por ele, e o Enter e o clique
   não fazem nada.
3. **Se a página da busca vier só com itens que não servem**, a tela diz isso e pede um termo mais preciso.
4. **A ação sem preço pode ser escolhida.** A recusa dela é do cálculo do risco, com `insufficient_history` e o link
   à aba do risco dela. A composição não a recusa.

## Consequências

- O backend não muda. A aceitação final continua sendo do servidor: o `400 invalid_holdings` vira a mensagem na
  linha certa, pelo `index`.
- Uma busca com muitos índices ou inativas pode ocupar a página com itens desabilitados. O "termo mais preciso"
  resolve esse caso sem paginar no seletor.
