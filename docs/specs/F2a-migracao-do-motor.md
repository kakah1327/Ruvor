# F2a — Migração do motor

**Bloco:** Fundação · F2a
**Status:** revisão adversarial aprovada · aguardando portão humano
**Antecede:** [F2b — Casco da aplicação](F2b-casco-da-aplicacao.md)

---

## Problema

O motor numérico vive hoje em `varlab/`, um pacote plano que mistura os modelos de risco com
a API Flask e a persistência SQLite. Enquanto estiverem juntos, a regra central da
arquitetura — [`engine/` não importa Django](../ARQUITETURA.md#a-regra-estrutural-inegociável)
— não pode nem ser expressa, e o motor não pode ser empacotado nem publicado por si só.

Também não existe o nome Ruvor no código: pacote, comando e variáveis ainda dizem VaR Lab.

## Resultado esperado

1. `import engine` funciona **sem Django instalado**
2. Os modelos determinísticos reproduzem a linha de base dentro da tolerância definida
3. A suíte de testes passa
4. A verificação de tipos passa
5. `python -m build` gera artefatos distribuíveis do motor
6. Nenhuma ocorrência de `varlab` ou `VaR Lab` nos alvos definidos abaixo

## Escopo

### Dentro

- Criar `engine/` e migrar o que tem valor
- Rebrand: pacote, comando, variáveis de ambiente, empacotamento
- Empacotamento próprio do motor, instalável e publicável
- Verificação de tipos sobre o código migrado
- `.gitattributes`
- Remover o que não será aproveitado

### Fora

| Fora do escopo | Onde entra |
|---|---|
| Projeto Django, projeto React | F2b |
| `infra/`, `docker compose` | F3 |
| Migrations, modelos de dados | F4 |
| Integração contínua | F5 |
| Reimplementar a API Flask ou a interface | Marco 1 — descartados, não portados |
| Correção da semente das redes neurais | trilha do TCC |
| Alterar lógica de qualquer modelo | proibido por [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) |

## Requisitos

| ID | Requisito |
|---|---|
| **F2a-01** | Linha de base numérica capturada **antes** de qualquer remoção (ver [abaixo](#a-linha-de-base-vem-primeiro)) |
| **F2a-02** | `engine/` contém modelos, backtesting, dados, orquestrador e CLI |
| **F2a-03** | `engine/` não importa nenhum módulo da lista de proibidos, verificado por teste |
| **F2a-04** | Modelos determinísticos reproduzem a linha de base com tolerância relativa de `1e-6` |
| **F2a-05** | Suíte de testes migrada e passando, com os imports reescritos |
| **F2a-06** | `tools/` permanece onde está, com os imports reescritos e importando sem erro |
| **F2a-07** | Rebrand aplicado nos alvos definidos |
| **F2a-08** | Motor com empacotamento próprio, com os grupos opcionais preservados |
| **F2a-09** | Verificação de tipos configurada, rodando e passando |
| **F2a-10** | `.gitattributes` normaliza fim de linha conforme a política definida abaixo |
| **F2a-11** | Código sem valor removido |

---

## A linha de base vem primeiro

**F2a-01 é a primeira tarefa do plano, sem exceção.** Depois que `varlab/` for removido, não
existe mais com o que comparar — e o F2a-04 se torna impossível de verificar.

A linha de base é um **teste de valores de referência**, não uma execução manual:

- **Sem rede.** Usa série sintética determinística, como `tests/conftest.py` já faz. Depender
  do yfinance tornaria a comparação irreproduzível — inclusive porque o histórico de preços é
  reescrito retroativamente ([D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md)).
- **Parâmetros fixos**, gravados junto dos valores e definidos aqui para que dois
  implementadores produzam o mesmo artefato:

  | Parâmetro | Valor |
  |---|---|
  | Série | ruído gaussiano, semente `42`, **552 dias úteis** a partir de 2020-01-01, desvio `0.01` — mesmo gerador de `tests/conftest.py`, série mais longa |
  | Divisão | 252 dias de treino, **300 de teste** |
  | `alpha` | `0.05` e `0.01` |
  | `horizon` | `1` |

  **Por que 552 e não os 500 da fixture atual:** o teste de Basileia exige janela mínima de
  **250 dias úteis** e levanta erro abaixo disso. Com 500 dias e 252 de treino sobrariam 248
  de teste, e o backtest de Basileia falharia nas 12 combinações — a linha de base ficaria
  impossível de capturar. 552 dá 300 dias de teste, com folga sobre o mínimo.
- **Cobre os seis modelos determinísticos**: `parametric`, `historical`, `monte_carlo`,
  `garch_1_1`, `egarch`, `caviar`.
- Os valores esperados ficam versionados no repositório, em arquivo JSON ao lado do teste, e
  o teste falha se divergirem.

**O que o JSON congela**, para não ficar a cargo do implementador:

| Congelado | Por quê |
|---|---|
| A **série de VaR completa** de cada modelo determinístico, para cada `alpha` | valor único ou estatística resumida esconderia divergência no meio da série |
| O **resultado dos 4 testes de backtesting** sobre essas séries | são igualmente determinísticos e migram no mesmo bloco; sem isso ficariam sem linha de base |
| Os parâmetros de entrada | série, `alpha`, `horizon`, janela de treino |

Os testes de backtesting já têm validação independente contra fórmula
(`tests/backtesting/test_formulas.py`), mas isso prova a **fórmula**, não a preservação na
migração. São coisas diferentes.

### Tolerância e ambiente

**Tolerância relativa de `1e-6`.** Não igualdade bit a bit.

Metade dos modelos determinísticos passa por otimizador numérico — `caviar` usa Nelder-Mead
com múltiplos reinícios, `garch_1_1` e `egarch` passam pela biblioteca `arch` — e otimizador
pode variar no último dígito entre versões de patch das dependências. Exigir igualdade exata
produziria reprovação sem que nada da migração estivesse errado.

`1e-6` é ordens de grandeza mais apertado do que qualquer diferença com significado numa
estimativa de risco, e frouxo o suficiente para sobreviver a ruído de ponto flutuante.

**O ambiente de referência é travado antes da captura**, para que a linha de base seja
reproduzível.

| Item | Definição |
|---|---|
| Arquivo | `engine/requirements-lock.txt`, versionado |
| Conteúdo | **o ambiente inteiro**, com versões exatas e transitivas — não só as numéricas |
| Grupos instalados | `traditional`, `garch`, `ml` e `dev` — os três primeiros para servir à [D-22](../decisoes/D-22-treino-centralizado-em-container.md), o último porque o teste de linha de base roda dentro deste ambiente. **Sem** `web` e `storage`, que deixam de existir |
| Geração | `pip freeze`, com **as linhas** de instalação editável removidas — tanto o `-e file:///…` quanto o comentário `# Editable install…` que o acompanha. O comentário cita o nome do pacote, e deixá-lo colocaria `varlab` dentro de um arquivo em `engine/`, que é alvo da varredura de rebrand |
| Versão do Python | **3.12**. O comentário no topo da trava registra a versão exata usada; o `engine/pyproject.toml` declara `requires-python = ">=3.12"` — é biblioteca, e faixa é o correto ali |

O `engine/pyproject.toml` mantém **faixas** de versão — é biblioteca e precisa conviver com
outros pacotes. A trava é para execução de referência, não para distribuição.

**Ordem obrigatória**, porque a leitura ingênua de "F2a-01 é a primeira tarefa" capturaria o
JSON num ambiente não travado, e aí a trava não garantiria nada sobre os números congelados:

```
1. criar ambiente limpo a partir do pyproject.toml ATUAL, com todos os grupos,
   e congelar a trava a partir dele
2. capturar a linha de base DENTRO desse ambiente, rodando contra varlab.*
3. só então iniciar a migração
```

**O ambiente do passo 1 nasce do `pyproject.toml` do protótipo**, não do
`engine/pyproject.toml` — este último é entregável do F2a-08 e ainda não existe no passo 1.
É coerente: a trava precisa descrever o ambiente que **produziu** os números congelados.

O diretório `engine/` é criado nesse momento para receber a trava e o JSON, antes do resto da
migração.

Quando o `engine/pyproject.toml` for criado, suas faixas precisam ser compatíveis com essa
trava — e a prova disso é o teste de linha de base continuar passando.

Serve também à [D-22](../decisoes/D-22-treino-centralizado-em-container.md): o container do
TCC instala a partir desta trava, e o F3 e o F5 a consomem.

### Onde o teste vive durante a captura

O artefato que precisa sobreviver é o **JSON de valores esperados**, não o código que o
gerou.

1. Um script descartável gera o JSON rodando contra `varlab.*`, antes de qualquer remoção
2. O JSON é versionado
3. O teste que o consome nasce direto em `engine/tests/`, importando `engine.*`

Assim nenhum arquivo precisa ser reescrito no meio da migração, e a comparação é entre o JSON
congelado e o motor migrado.

### Os modelos de ML não entram no F2a-04

`lstm`, `gru` e `garchnet` **não fixam semente**: duas execuções seguidas já divergem, sem
migração nenhuma. Não há como provar preservação de comportamento para eles.

Para esses, a verificação é **estrutural**: mesma arquitetura de rede, mesmos
hiperparâmetros, mesmo fluxo de treino. Como a migração é movimentação de arquivo sem
alteração de lógica, o risco é baixo — e alterar a lógica é proibido por
[D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md).

---

## O que migra e o que morre

| Origem | Destino | Motivo |
|---|---|---|
| `varlab/models/` | `engine/src/engine/models/` | 9 modelos validados — o ativo científico |
| `varlab/backtesting/` | `engine/src/engine/backtesting/` | 4 testes validados |
| `varlab/data/preprocessing.py`, `providers/` | `engine/src/engine/data/` | pequeno, correto, necessário |
| `varlab/experiments/` | `engine/src/engine/experiments/` | orquestrador; a Etapa 6 depende |
| `varlab/cli.py` | `engine/src/engine/cli.py` | a Etapa 6 depende |
| `tests/` | `engine/tests/` | ver [layout do projeto e do pacote](#layout-do-projeto-e-do-pacote) |
| `tools/garch_rcheck/`, `tools/docx/` | mantidos, imports reescritos | verificação com R e conversor do TCC |

A verificação do F2a-06 é **importação sem erro**, não execução: `export_for_r.py` busca dados na rede e seu par exige R instalado — nenhum dos dois é verificável num critério automatizado. Só `export_for_r.py` importa do motor; `docx2md.py` não depende do pacote.
| `varlab/data/cache.py` | **removido** | código morto — `load_cached`/`save_cache` nunca são chamados |
| `varlab/web/` | **removido** | Flask será substituído por Django; não é portado |
| `varlab/storage/` | **removido** | SQLite será substituído por PostgreSQL no F4 |
| `pyproject.toml` (raiz) | **removido** | ver [empacotamento](#empacotamento) |
| `.env.example` | **mantido, esvaziado** | ver [variáveis de ambiente](#variáveis-de-ambiente) |
| `README.md` | **atualizado (parte Python)** | as instruções citam `varlab web` e `--save`, que deixam de existir. A seção do frontend é do F2b |

### O que se perde nesta etapa, por inteiro

Registrado para que a expectativa fique clara: sai a **funcionalidade completa de histórico
de execuções** — persistência, listagem, detalhe e exportação em CSV/JSON — junto com a API
e as telas correspondentes. Não é só a opção `--save`.

A Etapa 6 não depende disso: o ranking é impresso na saída padrão. A persistência volta no
F4, sobre PostgreSQL.

### Layout do projeto e do pacote

Fixado, porque muda comandos de instalação e afeta F2b, F3 e F5:

```
engine/                      <- raiz do PROJETO (nao e o pacote)
├── pyproject.toml               metadados de ruvor-engine
├── src/
│   └── engine/                  <- raiz do PACOTE importavel
│       ├── models/
│       ├── backtesting/
│       ├── data/
│       ├── experiments/
│       └── cli.py
└── tests/                       fora do pacote distribuido
```

**Layout `src/`**, e não o pacote na raiz do projeto. O motivo é direto: com `src/`,
`import engine` só funciona se o pacote estiver **instalado** — não se resolve por acaso a
partir do diretório de trabalho. É o que torna a verificação do F2a-08 ("instala em ambiente
limpo") significativa em vez de decorativa.

Instalação: `pip install -e ./engine`.

Os testes ficam em `engine/tests/`, **fora** do pacote distribuído: pertencem ao projeto do
motor — atendendo o [D-17](../decisoes/D-17-monorepo-engine-sem-django.md), que exige o motor
testável isoladamente — sem inchar o artefato publicado.

A configuração do pytest e do mypy vive em `engine/pyproject.toml`.

---

## Contratos externos

Congelados a partir da aprovação desta spec.

### Pacote `engine`

```python
from engine.models import get_model, list_models, load_all_model_modules
from engine.backtesting import get_backtest, list_backtests, load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, ExperimentResult, run_experiment
from engine.data.providers.yfinance_provider import YFinanceProvider
```

As interfaces `VaRModel` e `BacktestTest` e os decoradores de registro **permanecem como
estão** — ver [`docs/prototipo/02-arquitetura.md`](../prototipo/02-arquitetura.md#contratos).
Esta spec move esses contratos; não os altera.

### Linha de comando

```
ruvor run --ticker <T> --start <D> --end <D>
          --model <M>...  --backtest <B>...
          [--alpha <A>...]        # repetível, padrão: 0.05 e 0.01
          [--train-window <N>]    # padrão: 252
```

**`--alpha` e `--train-window` permanecem, com os mesmos padrões.** `--train-window` altera
diretamente o número produzido, então mudá-la ou removê-la quebraria o F2a-04.

**Saem:** `--save` (a persistência é removida) e o comando `ruvor web` (o Flask deixa de
existir).

### Módulos proibidos em `engine/`

Lista fechada, verificada por teste. Importar qualquer um destes, direta ou indiretamente a
partir de `import engine`, reprova:

```
django · rest_framework · celery · flask · fastapi · sqlalchemy
```

A lista é fechada de propósito. "Nenhuma biblioteca web" seria ambíguo e reprovaria o motor
legítimo — o `yfinance` faz HTTP para buscar preços, e isso é esperado.

**A verificação não pode ser sobre `import engine` nu.** Hoje `varlab/__init__.py` contém
apenas uma docstring, e os submódulos só são carregados por `load_all_model_modules()` e
`load_all_backtest_modules()`, chamados explicitamente. Um teste que apenas importe o pacote
raiz carregaria zero módulos e **aprovaria qualquer coisa** — justamente o requisito que
materializa a regra inegociável da [D-17](../decisoes/D-17-monorepo-engine-sem-django.md).

**Chamar os dois carregadores de registry também não basta.** Eles cobrem apenas
`models/traditional`, `models/garch`, `models/ml` e `backtesting/` — **nada carrega `data/`,
`experiments/` nem `cli.py`**.

E é justamente ali que a violação aconteceria: o orquestrador e a CLI são o ponto de contato
com a plataforma. Um import de biblioteca de plataforma em nível de módulo em `data/`,
`experiments/` ou `cli.py` **não seria alcançado por nenhum carregador de registry**.

A verificação tem **duas partes**, porque uma sozinha deixa buraco:

**a) Inspeção em execução** — importa todos os submódulos do pacote, varrendo a árvore com
`pkgutil.walk_packages` sobre `engine`, e reprova se algum proibido aparecer entre os módulos
carregados. Pega import em nível de módulo, que é o caso mais comum.

**b) Varredura estática do fonte** de `engine/src/`, procurando os nomes proibidos em
qualquer instrução de import. Pega o que a inspeção em execução **não** pega: **import
diferido**, dentro do corpo de função.

O import diferido não é hipótese: `varlab/cli.py` importa Flask exatamente assim, dentro do
comando `web`. Importar o módulo não carrega Flask — só chamar o comando carrega. Sem a
varredura estática, esse padrão atravessaria o teste sem ser notado.

**Regra de aceite da varredura:** falha de importação por **dependência opcional ausente** é
tolerada — é o comportamento esperado quando o TensorFlow não está instalado, e é o que
mantém o motor funcional sem ele. Só a presença de um módulo proibido reprova.

**Sem TensorFlow instalado**, os módulos de ML são silenciosamente ignorados no carregamento
e a cobertura do teste encolheria sem ninguém perceber. A verificação automatizada cobre essa
condição **simulando a ausência da biblioteca dentro do próprio teste**, para que ambas as
condições rodem num ambiente só. Uma matriz de ambientes reais é assunto do F5.

### Variáveis de ambiente

O motor **não usa variável de ambiente nenhuma**. As duas existentes (`VARLAB_ENV`,
`VARLAB_SECRET_KEY`) pertencem à configuração do Flask, que é removida.

Portanto o `.env.example` da raiz é **mantido como arquivo**, contendo apenas um comentário
indicando que as variáveis chegam no F2b com o Django. Não é apagado — continua sendo alvo da
varredura de rebrand do F2a-07, e apagá-lo tornaria esse alvo inexistente.

O prefixo `RUVOR_*` fica reservado.

### Diretório de dados

`~/.ruvor/` fica **reservado, não criado**. Os dois lugares que usavam `~/.varlab/` —
`data/cache.py` e `storage/repository.py` — são removidos, então nada no F2a lê ou escreve
ali. Volta a existir no F4, com o PostgreSQL.

### Empacotamento

**Não existe `pyproject.toml` na raiz do repositório.** Ele é removido, não reescrito.

O monorepo passa a ter **um projeto Python por diretório**: `engine/pyproject.toml` neste
bloco, `backend/pyproject.toml` no F2b. Cada um declara suas dependências e a configuração
das suas ferramentas.

Motivo: os dois têm dependências e rigor de tipagem opostos
([D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md)), e o F3 vai construir
imagens Docker diferentes — a web sem TensorFlow, o worker com. Um projeto guarda-chuva na
raiz obrigaria a instalar tudo em todo lugar, exatamente o que a
[regra do `engine/`](../ARQUITETURA.md#a-regra-estrutural-inegociável) existe para evitar.

Nome de distribuição do motor: **`ruvor-engine`**.

Os grupos opcionais de dependência do protótipo são preservados — `traditional`, `garch`,
`ml` — mantendo a propriedade de que os modelos de ML **somem do registry** quando o
TensorFlow não está instalado, sem quebrar o resto
([`docs/prototipo/02-arquitetura.md`](../prototipo/02-arquitetura.md#carga-dos-módulos)).

Os grupos `web` e `storage` **deixam de existir**: Flask e SQLAlchemy saem.

O grupo `dev` passa a declarar tudo que os requisitos deste bloco exigem — `pytest` (F2a-05),
`mypy` (F2a-09) e `build` (F2a-08). O grupo `all` é reconstruído sobre os grupos
sobreviventes.

Verificação do F2a-08: `python -m build` gera os artefatos, e o motor instala em ambiente
limpo, sem Django.

---

## Verificação de tipos

**Ferramenta:** mypy. **Rigor definido pela
[D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md)** — graduado pela origem do
código, porque exigir rigor total sobre código migrado obrigaria a **editar** o que esta spec
promete apenas mover, contra a [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md).

Configuração exata do F2a, para que "passa" não seja vácuo:

| Ajuste | Valor |
|---|---|
| Modo | padrão do mypy — **sem** `--strict` |
| `disallow_untyped_defs` | desligado |
| `ignore_missing_imports` | ligado **apenas** para `tensorflow.*`, `arch.*`, `yfinance.*`, `scipy.*`, `pandas.*` |
| Alvo | `engine/src/` |
| `warn_unused_ignores` | ligado — impede que supressão vire hábito |

Ignorar biblioteca fora dessa lista reprova. É o que impede que a checagem passe por estar
desligada.

> **Corrigido durante a execução.** A lista original trazia `keras.*` e não trazia `pandas.*`.
> Nenhum módulo do motor faz `import keras` — o acesso é `from tensorflow import keras`, já
> coberto —, então aquele override não casaria com nada e emitiria aviso permanente. E o
> `pandas` não embarca `py.typed`: sem ele na lista, são 17 erros de importação não tipada.

Código novo nasce com rigor alto — isso é o F2b.

---

## Fim de linha

O time trabalha em Windows e produção roda em Linux. Sem normalização, um arquivo inteiro
aparece como alterado por diferença invisível, o que polui revisão.

Política mínima do F2a-10:

| Regra | Efeito |
|---|---|
| `* text=auto eol=lf` | tudo que é texto é armazenado com fim de linha Unix |
| `*.svg`, `*.R`, `*.csv`, `*.json` marcados como texto | garante tratamento uniforme |
| Binários (`*.docx`, `*.png`, `*.zip`) marcados como binário | evita corrupção por conversão |

O arquivo fica na raiz do repositório. Declarar a política **não basta**: num repositório com
histórico, é preciso renormalizar o que já está versionado (`git add --renormalize .`), senão
a regra vale só para arquivo novo — e o problema que ela existe para resolver permanece.

---

## Alvo do rebrand

O F2a-07 e o item 6 do resultado esperado se aplicam **apenas** a:

```
engine/  tools/  .env.example  .gitignore
```

O `pyproject.toml` da raiz não entra: ele é **removido**, não renomeado. O
`engine/pyproject.toml` nasce já com os nomes certos.

**O `README.md` também fica fora da varredura, e é reescrito em vez de varrido.** Ele contém
menção legítima e deliberada ao protótipo — o bloco de aviso "este repositório está em
reconstrução" diz que o código presente é o VaR Lab. Depois do F2a essa afirmação fica falsa
por outro motivo (o protótipo deixou de existir), então o bloco precisa ser **reescrito**, não
ter um nome substituído. Varredura cega apagaria conteúdo com significado.

**A varredura precisa ser normalizada, não linha a linha.** No `README.md` atual, "VaR Lab"
aparece quebrado entre duas linhas — um `grep` comum passaria em branco e a verificação seria
vácuo.

**Fora da varredura:** `docs/prototipo/`, `docs/tcc/`, `docs/decisoes/`, `docs/ROADMAP.md`,
`docs/ESTADO.md` e as specs — todos citam "VaR Lab" e `varlab/` como referência histórica, e
devem continuar citando.

**`ARQUITETURA.md` já reflete o layout `src/`** e a ausência de `pyproject.toml` na raiz —
nada a fazer nela neste bloco.

**`CLAUDE.md` também fica fora da varredura, mas por outro motivo, e tem dono:** ele descreve
`varlab/`, `frontend/src/` e `tests/` como *código atual do repositório*. Depois do F2a e do
F2b essas afirmações ficam falsas. A atualização acontece no passo **FECHA** do
[PROCESSO §3](../PROCESSO.md#3-o-ciclo), junto de `ESTADO.md` — não por varredura automática,
porque exige reescrever conteúdo, não substituir nome.

A verificação é um comando de varredura restrito a esses caminhos, definido no plano.

---

## Decisões que esta spec assume

- [D-10](../decisoes/D-10-spec-do-existente-e-linha-de-base.md) — o protótipo é linha de base de revisão
- [D-12](../decisoes/D-12-tipagem-obrigatoria.md) — tipagem obrigatória
- [D-17](../decisoes/D-17-monorepo-engine-sem-django.md) — monorepo, `engine/` sem Django
- [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) — motor de ML congelado até a Etapa 6
- [D-22](../decisoes/D-22-treino-centralizado-em-container.md) — treino em container, com ambiente congelado
- [D-25](../decisoes/D-25-rebrand-ruvor.md) — rebrand em toda a superfície
- [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md) — rigor de tipagem graduado pela origem

## Riscos e questões em aberto

### Renomear o diretório local

O repositório remoto já se chama `Ruvor`; a pasta local ainda é `varlab`. Renomear a pasta é
ação manual de cada dev, sem efeito no código, e não é tarefa desta spec.

### Ordem em relação à Etapa 6

Mover arquivo não altera resultado, então a Etapa 6 roda antes ou depois do F2a — desde que
use a **mesma versão do motor do começo ao fim**. Metade em `varlab/` e metade em `engine/`
invalidaria a comparação.

A linha de base do F2a-01 reduz esse risco: se os números baterem, as duas versões são
equivalentes para os modelos determinísticos.
