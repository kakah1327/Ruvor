# D-71 — A `risk_run` nasce no `worker`, não em quem enfileira

**Status:** aceita · 2026-09-25

## Contexto

No caminho assíncrono, alguém enfileira — hoje o `compute_risk --async` e o Beat; no M1.6, a
`web` — e alguém calcula, o `worker`. A linha da `risk_run` carrega o manifesto
([D-15](D-15-manifesto-de-execucao.md)), e montá-lo exige
`importlib.metadata.version("ruvor-engine")` e a série já passada pelo `clean_prices`, que é
código do motor.

O motor **só existe no `worker`**: `infra/backend.Dockerfile` o instala só nesse alvo, e o
`compose.yaml` monta `./engine` só nele (e no `beat`, que importa mas não calcula). `import
engine` na `web` dá `ModuleNotFoundError`. Levar o motor para a `web` custaria os +328 MB que
o M1.4 mediu e recusou, mais o TensorFlow, que a ARQUITETURA registra como 1–2 GB de RAM.

## Decisão

**A `risk_run` é criada dentro do `worker`**, por uma tarefa de abertura,
`apps.risk.tasks.abrir_execucao`. Ela carrega o registry, lê a série, confere o piso de
`MIN_SESSIONS`, cria a linha `running` e, com o `run_id` em mãos, enfileira o `chord` das
nove tarefas com o fecho de corpo. As nove recebem o **identificador**, não o manifesto: a
linha é a fonte de verdade.

**Quem enfileira não cria linha**: resolve e valida os candidatos (`InvalidTickers` e
`ModelsMissing` com código 1, antes de enfileirar qualquer coisa), produz o `calculated_at`
**uma vez** — que viaja em ISO a todas as aberturas do mesmo pedido — e devolve.

## Consequências

- **Há uma janela entre "o pedido foi aceito" e "existe linha no banco".** Quem consultar
  nesse intervalo não encontra execução nenhuma, e é o M1.6 que vai desenhar esse instante.
  Na execução real do M1.5 as quatro linhas existiam ~1,2 s depois de o comando devolver.
- Se a abertura falhar, não há linha: é a única tarefa que pode levantar, e o modo de falha
  dela é o log. O comando já respondeu "enfileirei".
- Série curta é pulo silencioso, como no síncrono: a abertura devolve `None`, não cria linha,
  e o relato fica no log do `worker`.
- A tarefa por (ativo, modelo) **restringe a série à janela da linha**
  (`first_price_date`…`as_of_date`) e confere a contagem contra `price_count`: pregão novo
  depois da abertura não entra, e série reconformada no meio
  ([D-53](D-53-evento-novo-rebusca-a-serie-inteira.md)) vira o erro `SeriesChanged` nas duas
  linhas do modelo. Reescrita de valor com a mesma contagem passa sem acusar — risco
  registrado, não resolvido.
- A validação de ticker mora em `apps/risk/compute.py`, que importa o motor no topo. O
  `--async` não sofre com isso, porque o comando roda no `worker`; **o M1.6, que enfileira da
  `web`, não herda essa validação de graça**.

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) (RF-03, RF-07).
