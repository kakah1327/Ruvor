# M2.3 — Conferência técnica: casco e preço (T2)

Só leitura. Para cada uma das duas chaves da seção, o que a frase avançada vai afirmar e o
`caminho:linha` em que cada afirmação foi conferida, no código que calcula (spec, RF-05). Os
caminhos são relativos à raiz do repositório. **Afirmação sem `caminho:linha` não vai ao
mockup.** Conferido no ramo `marco1/M2.3-camada-explicativa`, em 2026-10-01.

As duas chaves e a aridade que têm hoje (a avançada repete a assinatura, RF-05):

- `ativo.ultimoFechamento` — função de um argumento, a data já formatada
  (`frontend/src/content/textos.ts:87`), chamada com `formatDate(last.date)` em
  `frontend/src/components/AssetHeader.tsx:90`;
- `ativo.precoAjustado` — texto (`frontend/src/content/textos.ts:91`), usado em
  `frontend/src/components/PriceSection.tsx:39`.

## A tabela

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em | Parâmetros lidos (janela, anualização, nível, casas) |
|---|---|---|---|---|
| `ativo.ultimoFechamento` | — (com preço; sem preço a tela mostra `ativo.semPreco`, que não é desta lista) | O valor é o `close` do pregão mais recente guardado em `silver.price` para o ativo, na data mostrada: o fechamento do `chart` v8 do Yahoo como a fonte o devolve, sem o ajuste por proventos que vai para o ajustado. A data do pregão é a do fuso da bolsa, não UTC. | `backend/apps/api/serializers.py:115` (o último por data); `backend/apps/api/serializers.py:86` (`date`, `close`, `adj_close`); `frontend/src/components/AssetHeader.tsx:87` (a tela mostra `last.close`, não o `adj_close`); `backend/apps/assets/conform_prices.py:93` e `backend/apps/assets/conform_prices.py:104` (o `close` vem de `indicators.quote[0].close`, só quantizado); `backend/apps/assets/conform_prices.py:71` (data no fuso `exchangeTimezoneName`); `backend/apps/assets/yahoo.py:30` (o `chart` v8) | Guardado a 6 casas (`backend/apps/assets/conform_prices.py:23`, `backend/apps/assets/models.py:193`); exibido em reais com 2 casas (`frontend/src/format/numbers.ts:29`, `frontend/src/format/numbers.ts:37`); data `dd/mm/aaaa` (`frontend/src/format/numbers.ts:91`). Sem janela nem anualização: é um pregão só. |
| `ativo.precoAjustado` | — (texto; sem preço a seção mostra `ativo.preco.vazio`, que não é desta lista) | A linha é o `adj_close`, o fechamento ajustado que o Yahoo devolve em `indicators.adjclose` — o Ruvor não o recalcula a partir do `close` e dos eventos. A coleta pede os eventos de dividendos e desdobramentos junto com a série, e quando chega um evento ainda não guardado a série inteira é pedida de novo, porque o ajustado de todo o passado muda. | `frontend/src/components/PriceChart.tsx:51` (a linha é o `adj_close`); `backend/apps/assets/conform_prices.py:88` e `backend/apps/assets/conform_prices.py:105` (o `adj_close` vem de `indicators.adjclose[0].adjclose`, só quantizado); `backend/apps/assets/yahoo.py:60` (`events=div,splits`); `backend/apps/assets/prices.py:218` e `backend/apps/assets/prices.py:219` (evento novo → coleta completa); `backend/apps/assets/prices.py:283` (o teste do evento novo) | Guardado a 6 casas (`backend/apps/assets/conform_prices.py:23`, `backend/apps/assets/models.py:194`). Janela: a série inteira guardada (`backend/apps/api/views.py:283`, ordenada por data); a primeira coleta pede dez anos (`backend/apps/assets/prices.py:132`). |
| `ativo.precoAjustado` | a série que vai aos modelos | O retorno diário é o logaritmo da razão entre dois ajustados consecutivos, `ln(adj_close_t / adj_close_{t-1})`, sobre a série guardada. É o ajustado — não o `close` — que vai aos modelos de risco: o motor recebe o `adj_close` na coluna que ele lê como preço e tira dela o log-retorno. | `backend/apps/assets/prices.py:293` e `backend/apps/assets/prices.py:319` (o `log_return` sobre o `adj_close`); `backend/apps/risk/provider.py:51` e `backend/apps/risk/provider.py:54` (o `adj_close` vira a coluna `close` do motor); `backend/apps/risk/compute.py:411` (o cálculo usa o `SilverPriceProvider`); `engine/src/engine/experiments/runner.py:81` e `engine/src/engine/data/preprocessing.py:15` (o motor tira o log-retorno dessa coluna) | `log_return` guardado a 10 casas (`backend/apps/assets/prices.py:293`, `backend/apps/assets/models.py:196`); no motor, `float` (`backend/apps/risk/provider.py:54`). Janela do cálculo: a série inteira, da primeira à última data (`backend/apps/risk/compute.py:411`). |

## O que não se ancora no código

- **O que o ajustado inclui.** O código só copia o `adjclose` do Yahoo
  (`backend/apps/assets/conform_prices.py:105`); que ele corrige por proventos **e**
  desdobramentos é afirmação sobre a fonte, não sobre o Ruvor. O apoio está em documento, não em
  código: a [D-53](../../decisoes/D-53-evento-novo-rebusca-a-serie-inteira.md)
  ("a cada evento corporativo o Yahoo recalcula o `adjclose` de toda a série anterior") e o
  "`adj_close` da fonte, não recalculado" da [spec do M1.2](../../specs/M1.2-ingestao-de-precos.md).
  A frase avançada deve dizer "o ajustado que o Yahoo devolve", sem prometer a fórmula do ajuste.
- **O `close` "como foi negociado".** A frase iniciante de hoje (`frontend/src/content/textos.ts:88`)
  diz "como foi negociado na bolsa — sem ajuste por proventos". O código só guarda o `close` do
  `quote` do Yahoo como veio (`backend/apps/assets/conform_prices.py:104`); se esse `close` vem ou
  não corrigido por desdobramento é comportamento da fonte, que nenhum arquivo do repositório
  fixa. Por isso a afirmação da tabela diz "o fechamento do Yahoo como a fonte o devolve, sem o
  ajuste por proventos que vai para o ajustado" e **não** "o preço negociado". O portão decide se
  quer mais que isso; afirmar mais pede conferir a fonte.
