# F5 — Integração contínua

**Bloco:** Fundação · F5
**Status:** ✅ **aprovada** (2026-09-06) — plano em escrita
Três reprovações antes da aprovação, todas por erro de medição: contagem feita antes da
formatação, piso de regras fixado sem remedir sob ele, e `ruff --isolated`, que usa a
versão-alvo padrão de Python em vez da do projeto. Os números desta spec foram medidos sob o
conjunto que ela declara: piso sem `E501`, `line-length 88`, `--target-version py312`, depois
de formatar.
**Depende de:** [F4 — Fundação de dados](F4-fundacao-de-dados.md)

---

## Problema

**Nunca ninguém rodou este repositório numa máquina limpa.**

Tudo que se sabe sobre ele funcionar vem de execuções nesta máquina: Windows 11, Docker com
dados no `E:`, Node por `fnm`, um `.env` local que não está versionado. Não existe uma única
evidência de que o repositório funcione em outro lugar.

O estado do envio mede o tamanho disso: **38 commits não enviados**, e o último push foi em
**2026-09-01**. Os blocos F3 e F4 inteiros — o ambiente em contêiner e a fundação de dados —
existem apenas neste disco.

E há três lacunas concretas:

- **Não existe ferramenta de estilo em lugar nenhum.** Nem em `backend/`, nem em `engine/`,
  nem em `frontend/`. É pendência com dono declarado desde o F2b, cujo plano registra:
  *"Ferramenta de estilo — fora deste bloco. A spec do F5 é dona da escolha."*
- A [ARQUITETURA](../ARQUITETURA.md#ambientes) promete: *"a cada mudança roda verificação de
  estilo, verificação de tipos e testes. Não passou, não entra."* Nada disso existe.
- O F4 mudou o que a suíte do backend exige — ela agora precisa de um banco **migrado**, não
  só alcançável — e essa exigência nunca foi exercitada fora daqui.

O M1.1 é o próximo bloco, e é o primeiro que produz código de domínio de verdade. Entrar nele
sem rede é entrar acumulando risco que ninguém mede.

---

## Resultado esperado

1. Cada push na `main` dispara verificação **em máquina limpa**, e o resultado é visível
2. Estilo, tipos e testes rodam para as três partes: backend, frontend e motor
3. O backend é verificado **dentro do contêiner**, com o banco migrado
4. O motor é verificado com todas as extras, **inclusive ML**
5. Existe ferramenta de estilo, e ela vale para os **três projetos** — motor incluído. `tools/`
   fica de fora, e o porquê está em [`tools/` não tem projeto](#tools-não-tem-projeto-e-por-isso-fica-fora)
6. A imagem `worker`, de 3,79 GB, **não** é construída em execução nenhuma da CI

---

## Escopo

### Dentro

- A definição da CI, em `.github/workflows/ci.yml`
- **ruff** em `backend/` e `engine/`; **Biome** em `frontend/`
- Configuração das duas ferramentas, e correção do código existente para conformar
- **Formatação e lint do motor**, com as provas descritas em [O motor entra no estilo](#o-motor-entra-no-estilo)
- Os comandos de estilo documentados no `README.md`
- Fechamento da pendência "ferramenta de estilo", aberta desde o F2b
- **Quatro registros novos em `docs/decisoes/`** — ver [decisões novas](#decisões-novas-que-este-bloco-produz)

### Fora

| Fora do escopo | Onde entra |
|---|---|
| CI que **bloqueia** integração | quando houver mais de uma pessoa desenvolvendo ou versão publicada — ver [o portão](#o-portão-que-não-existe) |
| Proteção de ramo no GitHub | consequência da linha acima; sem portão, não há o que proteger |
| **Corrigir defeito que a CI encontrar no F3 ou no F4** | bloco próprio ou dívida registrada — ver [se a primeira execução reprovar](#se-a-primeira-execução-reprovar) |
| Deploy, publicação de imagem, release | quando houver hospedagem decidida ([ARQUITETURA](../ARQUITETURA.md#ambientes)) |
| Medida de cobertura de testes | nada previsto; ninguém pediu |
| Verificação de dependência vulnerável, Dependabot | nada previsto |
| Otimização de tempo de execução além do cache trivial | quando o tempo doer, e com medição |
| Ampliar a linha de base numérica para os três modelos de ML | trilha do TCC, depois da Etapa 6 — ver [o que a prova não cobre](#o-que-a-prova-não-cobre) |
| `frontend/.env.example` | não é lido pela CI: `VITE_API_BASE_URL` tem padrão vazio no próprio código |
| Ferramenta de estilo para Markdown ou YAML | nada previsto |

---

## Requisitos

| ID | Requisito |
|---|---|
| **F5-01** | Um push na `main` dispara a CI, e os quatro trabalhos **executam até o fim** — cada um chegando aos seus comandos de verificação, e não abortando na preparação do ambiente. O **resultado** deles pode ser vermelho: ver [se reprovar](#se-a-primeira-execução-reprovar) |
| **F5-02** | O backend é verificado **dentro do contêiner**, contra um banco **migrado** |
| **F5-03** | O frontend é verificado na **imagem do frontend**, não no Node do runner |
| **F5-04** | O motor é verificado com as extras completas: os **58** testes e o mypy dele |
| **F5-05** | A imagem `worker` **não** é construída em nenhum trabalho da CI |
| **F5-06** | `ruff` — lint **e** formatação — passa em `backend/` e em `engine/`, com conjunto de regras **explícito** |
| **F5-07** | `biome` — lint **e** formatação — passa em `frontend/` |
| **F5-08** | A formatação **não altera a árvore sintática de nenhum arquivo**, e a linha de base numérica continua passando |
| **F5-09** | Cada família de verificação da CI sabe reprovar |
| **F5-10** | `README.md`, `CLAUDE.md`, `ESTADO.md`, `ARQUITETURA.md`, `ROADMAP.md` e os dois índices em `docs/specs/` e `docs/planos/` descrevem o estado novo, e a pendência da ferramenta de estilo fecha |

---

## Contratos externos

Congelados a partir da aprovação. O M1.1 em diante herda os comandos de estilo e a exigência
de que todo código novo passe por eles.

### O portão que não existe

A [ARQUITETURA](../ARQUITETURA.md#ambientes) diz *"não passou, não entra"*. Isso pressupõe um
ponto de integração onde barrar — e a [D-31](../decisoes/D-31-trabalho-direto-na-main.md)
removeu esse ponto de propósito: trabalho direto na `main`, sem ramo e sem PR, *"enquanto o
time for uma pessoa"*.

**Esta spec mantém a D-31 e restringe a promessa da ARQUITETURA.** A CI roda a cada push na
`main` e **reprova ruidosamente, sem impedir**.

O motivo é que o valor da CI hoje não é barrar código. É provar que o repositório funciona
numa máquina que não é esta — coisa que nenhuma execução local prova, por definição. Barrar
exigiria reintroduzir ramo e PR, que a D-31 removeu por não haver trabalho paralelo nem
consumidor a proteger; nada disso mudou.

### Onde a definição mora, e por que não em `infra/`

`.github/workflows/ci.yml`. Não existe `.github/` hoje.

**Isto contradiz a [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) por escrito**, que
reserva `infra/` para *"arquivos de construcao de imagem, e CI a partir do F5"*. A contradição
não é escolha: **o GitHub só lê `.github/workflows/`**. Um arquivo em `infra/` não seria
executado, e o sintoma seria a ausência de execução — falha silenciosa, sem erro.

É a mesma forma da [D-35](../decisoes/D-35-compose-e-dockerignore-na-raiz.md), em que
`compose.yaml` e `.dockerignore` ficaram na raiz porque é onde as ferramentas os procuram. Vira
registro pelo mesmo motivo: para o próximo bloco ler, em vez de re-derivar.

**Disparo:** `push` na `main`, mais disparo manual. **Não** há gatilho de `pull_request`: não
existem PRs neste repositório, e um gatilho que nunca dispara é configuração morta que alguém
vai tomar por garantia.

### Os quatro trabalhos

| Trabalho | O que verifica | Como obtém o ambiente |
|---|---|---|
| **estilo** | `ruff` sobre `backend/` e `engine/` — **só Python** | ferramenta no runner, com versão fixada — ver [abaixo](#por-que-estilo-e-motor-não-rodam-em-contêiner) |
| **backend** | `pytest` e `mypy` | `compose`, dentro do contêiner `web`, com o banco migrado |
| **frontend** | `npm run lint`, `npm test`, `npm run typecheck`, `npm run build` | `compose`, dentro do contêiner `frontend` |
| **motor** | `pytest engine/tests` e `mypy` | Python 3.12 no runner, instalando pelo **lock** — ver [abaixo](#o-motor-instala-pelo-lock) |

**O Biome roda no contêiner, junto com o resto do frontend, e não no trabalho de estilo.** Uma
versão anterior desta spec dizia as duas coisas. A escolha é o contêiner, por três razões: o
Biome já está em `devDependencies` e vem instalado pelo `npm ci` da imagem, então rodá-lo lá não
custa nada; F5-03 exige que o frontend seja verificado na imagem, e lint é verificação de
frontend; e assim o comando é literalmente o mesmo dentro e fora da CI. O trabalho de estilo
fica sendo o do Python, onde a justificativa de rodar no runner se sustenta sozinha.

Os quatro são independentes e podem correr em paralelo. Nenhum depende do resultado de outro.

### Por que estilo e motor não rodam em contêiner

A [D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) fecha dizendo que *"a CI espelha o
contêiner, não o `.venv`"*. **Esta spec restringe isso a dois dos quatro trabalhos**, e a
restrição vira registro.

**O `ruff` não executa código.** Ele lê o fonte e nunca o importa — nem dependência instalada,
nem versão de Python, nem variável de ambiente mudam a saída. O que muda a saída é a versão da
ferramenta, e ela é fixada.

**E o motivo decisivo é o `engine/`:** a única imagem que o contém é a `worker`, que F5-05
proíbe construir. Ou o `ruff` do motor roda no runner, ou o motor fica sem estilo. O
`backend/` acompanha, para que o trabalho seja um só e a versão da ferramenta seja a mesma
para os dois projetos Python.

**O motor executa, mas não é a aplicação.** Ele é pacote Python independente que não fala com
serviço nenhum ([D-17](../decisoes/D-17-monorepo-engine-sem-django.md)), e a própria D-33 o
deixa fora do contêiner no dia a dia, pelo mesmo motivo. Construir 3,79 GB para rodar 58 testes
de um pacote isolado é o que F5-05 existe para impedir.

**Backend e frontend, que são a aplicação, seguem a D-33 sem exceção.**

### O motor instala pelo lock

`engine/requirements-lock.txt` existe desde o F2a, versionado, com **59 pacotes fixados** e um
cabeçalho que diz ser *"o ambiente de referência da linha de base"*. O `README.md` já o usa
para reproduzi-la.

**O trabalho do motor instala por ele**, e não por resolução livre de `engine[all]`. A razão é
que `engine/tests/baseline/test_linha_de_base.py` compara contra `valores.json` com tolerância
de 1e-6 e diz, no próprio docstring, que o arquivo *"não pode ser regenerado: se a comparação
divergir, o defeito está na migração"*. Com dependência flutuante, uma versão nova de `arch` ou
`scipy` faria o teste acusar defeito de migração onde há só deriva de biblioteca — reprovação
falsa, e da pior espécie, porque a mensagem aponta para o lugar errado.

**Consequência aceita, e listada em [o que a CI não vai pegar](#o-que-a-ci-não-vai-pegar):** a
CI deixa de detectar quebra por dependência nova. O lock é atualizado à mão, quando alguém
decidir atualizá-lo.

**O lock não basta sozinho, e isto é contrato:** ele traz `pytest`, `setuptools` e `wheel`, mas
**não traz `mypy`** — conferido no arquivo, apesar de o cabeçalho dizer que foi gerado com o
grupo `dev`. E instalar por ele não instala o próprio pacote `engine`, nem registra o comando
`ruvor`. O trabalho do motor faz **dois** passos, nesta ordem:

```
pip install -r engine/requirements-lock.txt                        # as 59, fixadas
pip install -e "./engine[all]" -c engine/requirements-lock.txt     # o pacote e as ferramentas
```

**É `[all]`, e não `[dev]`, porque o requisito diz "extras completas, inclusive ML".** Com
`[dev]` o ambiente final seria o mesmo — TensorFlow, `arch`, `scipy` e `pandas` já vêm do passo
1 —, mas a cobertura de ML passaria a **depender** de o lock conter o que o `pyproject.toml`
declara, em vez de ser declarada. No dia em que os dois divergissem, o trabalho ficaria sem
TensorFlow e os testes de ML falhariam por `ImportError`, com F5-04 afirmando "extras
completas". `[all]` sob restrição produz o mesmo ambiente e diz o que faz.

**O segundo passo usa o lock como arquivo de restrição, e é isso que fecha o contrato sem
uma terceira cópia de número de versão.** A restrição segura tudo que está no lock e deixa
entrar o que não está. Medido com `pip install --dry-run`: `pytest` sai em `9.1.1`, que é
exatamente o pino do lock, enquanto `mypy` e `build`, ausentes dele, resolvem livremente.

**A versão das ferramentas vem do `engine/pyproject.toml`, e de lugar nenhum além dele.** Sem
isso o `ci.yml` carregaria a própria cópia do número, e o dia a dia e a CI passariam a usar
ferramentas diferentes em silêncio — que é o buraco que a linha do `engine[dev]` na tabela de
versões existe para fechar, reaberto num lugar novo.

**Regenerar o lock para incluir o `mypy` seria pior:** o cabeçalho manda regenerá-lo recriando
o ambiente, o que reescreveria os 59 pinos — e a linha de base compara com tolerância de 1e-6
contra números produzidos naquele ambiente exato. Acrescentar uma ferramenta não pode custar a
referência numérica do projeto.

### A CI precisa criar o `.env`

`compose.yaml` usa a sintaxe de obrigatoriedade (`${VAR:?}`) em **onze ocorrências, de oito
variáveis distintas** — as três de banco aparecem duas vezes, em `postgres` e em `web`. O
`.env` é ignorado pelo git e não vem no clone, de propósito. Sem ele o `compose` sai com código
1 nomeando a variável que falta.

**A CI copia `.env.example` da raiz para `.env` antes de subir qualquer coisa.** As oito estão
todas lá, com valores usáveis e sem segredo real, como o próprio arquivo diz.

### Como a `worker` fica de fora

Três camadas, e a primeira já basta:

1. **`worker` não é dependência de ninguém.** `web` depende de `postgres` e `redis`; `frontend`
   depende de `web`. Subir `web` ou `frontend` **pelo nome** nunca a puxa.
2. No `infra/backend.Dockerfile`, `worker` é estágio **irmão** de `web`, não pai — os dois
   partem de `base`. Construir o alvo `web` não constrói o `worker`.
3. O que puxaria é `docker compose build` ou `up` **sem argumento**. A CI sempre nomeia os
   serviços.

### Onde a configuração de estilo mora

**Duas configurações de Python, não uma.** `backend/pyproject.toml` e `engine/pyproject.toml`
ganham cada um o seu bloco de `ruff`, como já têm o de `mypy` e o de `pytest`. É o que a
[ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) fixa — *"um projeto Python por
diretório"* — e é o que permite rigor diferente por origem, como a
[D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md) já estabelece para tipagem.

O frontend recebe `frontend/biome.json`, que é o nome e o local que a ferramenta procura.

### O conjunto de regras tem piso

A spec **não** fixa o conjunto final — escolher regra sem ver o que ela acusa no código real é
decidir no escuro, e o plano deriva o resto da medição em Linux. Mas fixa duas coisas, porque
sem elas F5-06 aprova vazio:

**Piso obrigatório, nos dois projetos Python:**

| Família | Por quê |
|---|---|
| `E`, `W` | erro e aviso de estilo — o mínimo de qualquer linter |
| `F` | Pyflakes: import não usado, variável não definida, f-string sem campo |
| `I` | ordem de import — é o que evita diff de import em toda revisão |
| `UP` | sintaxe obsoleta para a versão mínima do projeto |
| `RUF` | as regras próprias da ferramenta |

**`E501` sai do piso, e `line-length = 88` fica fixado.** As duas coisas andam juntas: o
formatador é quem impõe o comprimento de linha, e o `E501` só sobra para o que ele **não sabe
quebrar** — literal de texto longo, comentário, URL. Manter os dois ligados é pedir supressão
manual em linha que nenhuma ferramenta consegue arrumar. É a orientação da própria ferramenta
quando o formatador está em uso.

**Medido sob a configuração real dos projetos, escopo `.`, depois de formatar.** No motor: **68**
violações com o piso inteiro, **26** sem o `E501` — a diferença são **42 linhas longas**. No
backend, **7** contra **2**.

**`line-length` é decisão de spec, não de plano**, porque muda quantos arquivos do motor
congelado são tocados: a 88 o formatador reescreve **25** arquivos de `engine/src`; a 100,
**24**. Fica em **88**, que é o padrão da ferramenta, para que o número não dependa de
preferência de ninguém.

**Consequência que precisa de comentário no próprio `engine/pyproject.toml`:** com `E501`
desligado, sobram **42 linhas acima de 88 colunas** no motor — comentário, docstring e texto,
que o formatador não quebra. Quem abrir o arquivo e vir `line-length = 88` ao lado de uma linha
de 97 colunas vai tomar por defeito se não houver a explicação ali.

**O conjunto é declarado explicitamente** no `pyproject.toml`, e não herdado do padrão
implícito: padrão implícito muda quando a ferramenta atualiza, e aí a CI reprova sozinha num
dia em que ninguém mexeu em nada.

**As versões são fixadas em dois lugares, e é deliberado:**

| Onde | O quê |
|---|---|
| `backend/pyproject.toml`, grupo `dev` | `ruff`, para que o comando do dia a dia dentro do contêiner use a mesma versão |
| `engine/pyproject.toml`, grupo `dev` | `ruff` **e** `mypy` — o motor declara as próprias ferramentas, como manda a ARQUITETURA, e o `mypy` já era exigido por ele sem estar no lock |
| `frontend/package.json`, `devDependencies` | `@biomejs/biome`, pelo mesmo motivo |
| `.github/workflows/ci.yml` | **nenhum número.** Os dois trabalhos que rodam no runner instalam a partir dos `pyproject.toml`, não de versões repetidas aqui — ver [o contrato do motor](#o-motor-instala-pelo-lock) |

**A segunda linha fecha um buraco.** Sem ela, o `ruff` do comando `cd engine && ruff check .`
viria do `backend[dev]` instalado no mesmo `.venv/` — dependência cruzada do motor para o
backend, que contradiz o *"um projeto Python por diretório: cada um declara as próprias
dependências"* da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório), e que faria a
versão do dia a dia divergir da da CI sem nada acusar.

Consequência declarada, porque muda arquivos: acrescentar `ruff` ao grupo `dev` do backend
**muda a imagem `web`**, que instala `./backend[dev]`; acrescentar o Biome muda
`frontend/package-lock.json` e obriga a reconstruir a imagem do frontend com
`--renew-anon-volumes`, como o [aprendizados.md](../aprendizados.md) registra. Os dois estão no
inventário.

No momento da escrita, o registro devolvia `ruff 0.16.6` e `@biomejs/biome 2.5.12`; o plano
reconfirma antes de fixar.

### `tools/` não tem projeto, e por isso fica fora

`tools/` tem código Python versionado — `docx/docx2md.py`, `garch_rcheck/export_for_r.py` — e
o F5 acrescenta um terceiro, a prova de formatação. **Nenhum deles fica sob estilo**, e é
decisão, não esquecimento.

O motivo é estrutural: o `ruff` lê sua configuração de um `pyproject.toml`, e `tools/` não é
projeto Python — não tem um, e a [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório)
proíbe `pyproject.toml` na raiz (*"um projeto Python por diretório"*). Cobrir `tools/` exigiria
ou criar um projeto para utilitários avulsos, ou apontar o `ruff` para a configuração de outro
diretório — as duas coisas maiores que o problema.

**Fica como dívida registrada**, com dono no bloco que der um lar a `tools/`. A ironia de a
prova de F5-08 morar no único diretório sem estilo está declarada, e não escondida: ela é
executada por `python`, não por `ruff`, e o que a valida é o próprio código de saída dela.

### Os comandos, que são o contrato que o M1.1 herda

Três, e os nomes são congelados aqui — um contrato de comandos que não nomeia os comandos não
é contrato:

| O quê | Comando |
|---|---|
| Estilo do backend | `docker compose exec -T web sh -c "ruff check . && ruff format --check ."` |
| Estilo do motor | `cd engine && ruff check . && ruff format --check .` — nativo, como o resto do motor |
| Estilo do frontend | `docker compose exec -T frontend npm run lint` |

**O caminho é `.` e o `sh -c` não é enfeite.** O diretório de trabalho do contêiner `web` já é
`/repo/backend`, então `ruff check backend` procuraria um subdiretório que não existe. E sem o
`sh -c`, o `&&` seria interpretado pelo **hospedeiro**: a segunda metade rodaria fora do
contêiner, onde `ruff` provavelmente nem está instalado, e o critério passaria a medir outra
coisa.

O `frontend/package.json` ganha o script **`lint`**, ao lado de `test`, `typecheck` e `build`.
A tabela "Comandos do dia a dia" do `README.md` tem hoje nove linhas; passa a ter as três
acima.

---

## O motor entra no estilo

A [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) congela o motor até a Etapa 6.
**O motor entra no estilo assim mesmo — formatação e lint** —, e esta seção existe para que a
autorização seja explícita e provada, não presumida.

Medido com `ruff 0.16.6` num contêiner Linux descartável, **na ordem em que o bloco vai
executar**: formatar primeiro, contar o lint depois. A ordem importa — contar antes infla o
número com violações que a formatação já resolve.

**O escopo é o projeto inteiro, `.`, e não só `src`** — é o que o comando do contrato diz, e é
o que mantém `engine/tests/` com dono. Medido **sob a configuração real dos projetos**, nunca
com `--isolated`:

| | `ruff format` reescreve | violações de lint, já formatado |
|---|---|---|
| `engine/` inteiro | **33 arquivos**, de 44 | **26** |
| — dos quais `engine/src` | 25, de 33 | 23 |
| — dos quais `engine/tests` | 8, de 11 | 3 |
| `backend/` | 4, de 25 | **2** |

**A distinção `src`/`tests` importa para a [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md),
e só para ela:** o que a decisão congela é o motor, que é `src`. `engine/tests/` é código de
teste, e as três violações dele — duas `UP033` e uma `F841` — não têm nada a ver com
comportamento numérico.

### As duas operações são separadas, porque as provas são diferentes

**Formatação não muda a árvore sintática.** É o que a operação é. E isso não precisa ser
afirmado: comparar `ast.dump()` de cada arquivo antes e depois **prova**, arquivo a arquivo.
Medido: **69 arquivos** — 33 de `engine/src`, 11 de `engine/tests` e 25 de `backend` —, zero
divergência. Sem amostragem, e cobre os nove modelos.

**A prova é completa para a árvore sintática, que é menos que "nada mudou".** O `ast` não
carrega comentário, e a formatação **move** comentário de fim de linha. Isso importa num caso:
o repositório tem quatro `# noqa` em fim de linha — dois em `engine/src/engine/experiments/runner.py`,
um em `backend/config/celery.py`, um em `backend/config/settings_test.py` —, e um `# noqa` que
muda de linha deixa de suprimir. **Quem cobre esse buraco é o próprio `ruff check` da tarefa
seguinte**, que passaria a acusar o que a supressão escondia. As duas verificações de F5-08 e
F5-06 se cobrem, e é por isso que nenhuma delas basta sozinha.

**Lint edita código**, e aí a prova é outra: enumeração. As **23 de `engine/src`**, que é o que
a D-21 congela, derivadas da fonte já formatada. As três de `engine/tests` estão logo abaixo.

| Regra | Quantas | Onde | O que muda |
|---|---|---|---|
| `UP006` | 8 | `models/registry.py`, `backtesting/registry.py` | `typing.Type` → `type` |
| `UP037` | 8 | oito arquivos, um cada | remove aspas de anotação |
| `I001` | 2 | `cli.py:59`, `models/registry.py:60` — os dois são blocos de import **dentro de função**, do carregamento diferido | ordena imports |
| `UP035` | 2 | os dois registries | import depreciado |
| `RUF012` | 1 | `models/ml/_quantile_nn.py` | exige `ClassVar` |
| `RUF100` | 2 | `experiments/runner.py` | ver abaixo — **é a única que não é mecânica** |

**Vinte e uma das 23 são de anotação de tipo ou de ordem de import, e nenhuma toca expressão
numérica.** As outras duas são as `RUF100`, tratadas abaixo. A `UP042` **não entra nesta
conta** — ela é a 24ª, e a spec manda não aplicá-la. Em código congelado mudam, portanto, as
**23**.

**As três de `engine/tests`, que não são de código congelado:** duas `UP033` em
`baseline/test_linha_de_base.py:42,51` — `@functools.lru_cache(maxsize=None)` vira
`@functools.cache`, que é o mesmo objeto — e uma `F841` em `models/test_ml_diagnostics.py:17`,
variável atribuída e nunca usada. As três são corrigidas.

**As duas `RUF100` merecem cuidado, e a correção automática está errada aqui.** Elas apontam
`# noqa: BLE001 — isola falha de 1 modelo do restante`, em `experiments/runner.py`. A regra as
chama de inúteis porque `BLE` não está no piso — e está certa. Mas o `--fix` **apagaria o
comentário inteiro**, e com ele a intenção escrita. A correção é **converter em comentário
comum**, preservando a explicação e removendo só o `# noqa` que não suprime nada.

**A 24ª é `UP042`, e ela é a única que a spec manda NÃO aplicar.**

`UP042` acusa `class ModelCategory(str, Enum)` em `engine/src/engine/models/base.py:12` e
sugere `enum.StrEnum`. **A troca não é equivalente:** `str()` e f-string se comportam de forma
diferente entre as duas no 3.12, e `ModelCategory` é comparado e formatado em todo o motor.

**Decisão: `UP042` fica ignorada em `engine/pyproject.toml`, com o motivo escrito no próprio
arquivo, e reavaliada depois da Etapa 6.** É a única exceção ao piso, e ela é nomeada aqui em
vez de deixada para quem implementa — que, vendo a regra acusar código congelado, teria de
escolher sozinho entre mudar semântica e silenciar sem registro.

**Como eu quase não a vi, que é aprendizado:** medir com `ruff --isolated` faz a ferramenta
usar a versão-alvo padrão de Python, e `StrEnum` não existe lá — a regra se cala. Com o
`requires-python = ">=3.12"` real do motor, ela dispara. **Medição com `--isolated` não é
medição do projeto.**

### O que a prova não cobre

A honestidade que faltava na primeira versão desta spec:

**A linha de base numérica cobre seis dos nove modelos.** `engine/tests/baseline/valores.json`
declara `parametric`, `historical`, `monte_carlo`, `garch_1_1`, `egarch` e `caviar` — seis
modelos × 2 níveis = as 12 combinações. **`lstm`, `gru` e `garchnet` não têm número comparado
contra nada**; o que os cobre é teste de propriedade, que confere tamanho, índice e finitude.

O que salva o caso, e é medição pós-formatação, sob o piso desta spec:

- **`lstm.py` e `gru.py` não têm violação de lint nenhuma.** Recebem **só formatação**, que a
  prova por árvore sintática cobre inteiramente.
- Dos três fora da linha de base, só `garchnet.py` é editado, e por **um** `UP037` — remoção de
  aspas de anotação.
- `_quantile_nn.py`, compartilhado pelos modelos de ML, recebe `UP037` e `RUF012`, os dois de
  anotação.

**Essa afirmação depende do `E501` estar fora do piso, e isso é medido, não conveniente.** Com
`E501` ligado, `lstm.py`, `gru.py` e `garchnet.py` ganham uma linha longa cada, e
`_quantile_nn.py` seis — e a frase acima seria falsa. É a razão de a
[decisão sobre o piso](#o-conjunto-de-regras-tem-piso) vir antes desta seção, e não depois:
ela é o que torna esta verdadeira.

**O risco residual, declarado:** três arquivos de ML sofrem quatro edições de anotação sem
guarda numérica. Ampliar a linha de base para cobri-los é trabalho da trilha do TCC, depois da
Etapa 6, e está em [Fora](#fora).

### As duas do backend, e as quatro que a configuração absorve

| Regra | Quantas | Onde | O que a spec decide |
|---|---|---|---|
| `RUF012` | 1 | `apps/accounts/models.py:61` | corrigir — é código do projeto, e `ClassVar` está certo ali |
| `RUF100` | 1 | `config/settings_test.py:22` | **remover só o `E402` do `# noqa`, mantendo o `F403`.** É a mesma armadilha do motor: o `--fix` mexe em supressão deliberada |
| `RUF012` | 4 | `migrations/0001_*.py` e `0002_*.py`, em `dependencies` e `operations` | **não são corrigidas:** `per-file-ignores` com exatamente `["RUF012"]`, e nada mais, para `"**/migrations/*.py"`. São atributos que o Django escreve em formato canônico; anotá-los com `ClassVar` é editar artefato gerado, e o `makemigrations --check` do F4 é o incentivo para não mexer |

**A lista de regras do `per-file-ignores` é fechada de propósito.** `["ALL"]` desligaria o lint
num diretório inteiro — inclusive para todas as migrations que o M1.1 em diante vai criar, que
é justamente onde este contrato deveria estar protegendo. E o glob precisa atravessar dois
níveis (`apps/accounts/migrations/`), então `*/migrations/*` não casa: o `*` não cruza `/`.

**Por que são duas, e não nove.** Uma versão anterior desta spec dizia nove, porque mediu com
`--isolated`. Sob a configuração real, o `ruff` lê o `backend/pyproject.toml`, reconhece
`config`, `apps` e `tests` como pacotes de **primeira parte**, e as três `I001` que apareciam
em `tests/` deixam de existir — a ordenação já estava certa. As outras quatro somem pelo
`per-file-ignores` acima. É o mesmo erro de método que o `UP042` expôs, e ele reincidiu duas
vezes nesta spec: **medição com `--isolated` não é medição do projeto.**

---

## Se a primeira execução reprovar

A primeira execução não vai julgar o F5 — vai julgar o F3 e o F4 de uma vez, num sistema
operacional em que nada disso jamais rodou. **É provável que ela reprove, e isso é o ganho do
bloco, não o fracasso dele.**

**O F5 entrega a rede, não a limpeza.** Ele fecha quando a CI está correta e executou, com o
resultado conhecido e registrado. Defeito que ela encontre em bloco anterior vira **dívida
registrada com dono**, e não incha este bloco. Defeito da **própria CI** — configuração errada,
passo faltando — é conserto do F5.

**Consequência que precisa estar escrita, não escondida:** o ROADMAP pode marcar o F5 fechado
com a `main` vermelha. Se isso acontecer, o `ESTADO.md` diz qual é a reprovação, de que bloco
ela é, e quem a paga — porque status verde com execução vermelha é exatamente o tipo de mentira
que o passo FECHA existe para impedir.

---

## Verificação

### Critérios executáveis

| Requisito | Verificação |
|---|---|
| **F5-01** | Um push real na `main` dispara a execução, e ela **executa até o fim** com o resultado registrado — ver [se reprovar](#se-a-primeira-execução-reprovar). É o único requisito que não se prova localmente |
| **F5-02** | O trabalho do backend sobe `web` pelo `compose`, roda `migrate` e então `pytest` e `mypy`; os 16 testes passam |
| **F5-03** | O trabalho do frontend roda os **quatro** comandos dentro do contêiner `frontend` — `lint` incluído |
| **F5-04** | O trabalho do motor coleta e executa **58** testes e o mypy do `engine/` |
| **F5-05** | Depois da execução, `docker image ls` **não** contém `ruvor-worker`. Lista fechada, não amostra |
| **F5-06** | `ruff check` e `ruff format --check` saem 0 nos dois projetos, com o conjunto declarado no `pyproject.toml` cobrindo o piso — **com as duas exceções nomeadas por esta spec, e nenhuma outra:** `E501` fora do piso nos dois projetos, e `UP042` ignorada em `engine/` |
| **F5-07** | `npm run lint` sai 0 dentro do contêiner do frontend |
| **F5-08** | **Duas provas, as duas exigidas:** (a) para cada arquivo `.py` tocado pela formatação, `ast.dump()` antes e depois é idêntico; (b) `pytest engine/tests` passa, incluindo `tests/baseline/` |
| **F5-09** | As mutações abaixo |
| **F5-10** | Varredura sobre a [lista fechada](#o-que-fica-falso), e a linha "Ferramenta de estilo" sai de "Aberto e aguardando decisão" no `ESTADO.md` |

### Onde cada verificação mora

| Forma | Quais | Onde |
|---|---|---|
| **Comando local** | F5-02 a F5-08, F5-10 | invocação de uma linha, escrita literalmente no critério de aceite da tarefa |
| **Mutação local** | F5-09 | a tarefa das mutações, como no F3 e no F4 |
| **Só provável por push** | F5-01, e a confirmação de F5-05 no runner | a execução no GitHub, com o registro dela |

**F5-01 é o primeiro requisito deste projeto que não se prova na máquina.** Os comandos que os
trabalhos executam se provam aqui, um a um; que o GitHub os dispare e os execute em máquina
limpa, não.

### Cada família de verificação prova que sabe reprovar

| Mutação | Precisa reprovar |
|---|---|
| Desformatar um arquivo de `backend/` | F5-06, formatação |
| Introduzir import não usado em `engine/src` | F5-06, lint |
| Desformatar um arquivo de `frontend/src` | F5-07 |
| Quebrar um teste do backend | F5-02 |
| **Tirar o `migrate` do trabalho do backend** | F5-02 |
| Alterar um valor de `valores.json` | F5-08(b) |
| Trocar uma linha por outra semanticamente diferente durante a formatação | F5-08(a) |
| Acrescentar `worker` à lista de serviços que a CI sobe | F5-05 |

**A mutação do `migrate` é a mais importante.** É a exigência que o F4 criou e que nunca foi
exercitada fora desta máquina. **Sem o `migrate`, reprovam quatro testes**, não cinco:
`test_esquemas.py` (dois), `test_organizacao.py` (um) e
`test_usuario.py::test_a_coluna_organization_id_e_not_null` (um).

**Cuidado com um cinco parecido, que é de outro cenário.** O `README.md` e o `ESTADO.md` dizem
que `pytest backend` **no hospedeiro** reprova **cinco** — ali o banco é inalcançável, e o
`test_conexao_com_o_banco` cai junto. Na CI o banco existe e responde: esse teste só faz
`SELECT current_database()` e **passa sem `migrate`**. São quatro, e confundir os dois números
faz a mutação mais importante do bloco parecer ter falhado.

**A mutação de F5-05 é pela lista de serviços, não por `docker compose build` sem argumento** —
esse comando construiria os 3,79 GB que o Resultado esperado 6 proíbe.

---

## Inventário dos arquivos existentes

### Altera

| Arquivo | O que muda |
|---|---|
| `backend/pyproject.toml` | bloco do `ruff`, e `ruff` no grupo `dev` |
| `engine/pyproject.toml` | bloco do `ruff`, e `ruff` + `mypy` no grupo `dev` |
| `docs/decisoes/README.md` | as quatro linhas novas no índice |
| `frontend/package.json` | script `lint`, e `@biomejs/biome` em `devDependencies` |
| `frontend/package-lock.json` | consequência obrigatória da linha acima |
| `backend/` — 4 arquivos | formatação |
| `engine/src/` — 25 arquivos por formatação, 12 por lint | as duas provas de F5-08 |
| `frontend/src/` e `frontend/tests/` | formatação e lint, na medida que o Biome apontar |
| `README.md` | os três comandos de estilo; a seção de CI, que não existe |
| `CLAUDE.md` | o parágrafo de estado do repositório, e a linha do `frontend/` que descreve as verificações |
| `docs/ESTADO.md` | passo FECHA, a pendência que fecha, e a contagem de decisões |
| `docs/ARQUITETURA.md` | a promessa da CI, e a linha que põe a CI em `infra/` |
| `docs/ROADMAP.md` | F5 fechado |
| `docs/aprendizados.md` | o que custou tempo |
| `docs/specs/README.md`, `docs/planos/README.md` | as tabelas de índice |
| cabeçalho de status **desta** spec e do plano dela | PROCESSO §3 |

### Cria

| Arquivo | Conteúdo |
|---|---|
| `.github/workflows/ci.yml` | os quatro trabalhos, o gatilho e o disparo manual |
| `frontend/biome.json` | as regras do Biome |
| `docs/decisoes/D-42-*.md` | a CI avisa e não bloqueia |
| `docs/decisoes/D-43-*.md` | ruff e Biome, e onde cada verificação roda |
| `docs/decisoes/D-44-*.md` | o motor entra no estilo, e como isso se prova |
| `docs/decisoes/D-45-*.md` | a CI mora em `.github/workflows/`, não em `infra/` |

O último registro hoje é o [D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md);
`decisoes/` é append-only, um arquivo por decisão, e o índice `docs/decisoes/README.md` recebe
as quatro linhas.

### O que fica falso

Lista fechada, derivada dos arquivos:

| Onde | Trecho |
|---|---|
| `docs/ESTADO.md` | a linha **"Ferramenta de estilo"** em "Aberto e aguardando decisão" — a pendência fecha |
| `docs/ESTADO.md` | "**Bloco:** F4 fechado e integrado; **F5 é o próximo**" |
| `docs/ESTADO.md` | a seção "Próximo passo" inteira |
| `docs/ESTADO.md` | "**41 decisões registradas**" — passam a 45 |
| `docs/ROADMAP.md` | a linha do F5 marcada ⬜ |
| `docs/ARQUITETURA.md` | *"Não passou, não entra."* — **a frase está quebrada entre as linhas 317 e 318**, e `grep` pela sentença inteira **não casa**; casa `passou, não entra` |
| `docs/ARQUITETURA.md` | `├── infra/  # arquivos de construcao de imagem, e CI a partir do F5` |
| `docs/ARQUITETURA.md` | *"A CI espelha o contêiner, não o `.venv`."* — a D-43 a restringe a dois dos quatro trabalhos |
| ~~`docs/decisoes/README.md`~~ | ✅ **já feito** — as quatro entraram junto com a aprovação desta spec, como o PROCESSO manda. Fica na lista para não parecer esquecido |
| `CLAUDE.md` | *"uma varredura automatizada reprova cor literal em `frontend/src/`"* é a única verificação citada do frontend; passa a haver estilo |
| `README.md` | "Comandos do dia a dia", que não tem linha de estilo |
| `docs/specs/README.md`, `docs/planos/README.md` | as tabelas de índice, que vão até o F4 |
| `docs/planos/F2b-casco-da-aplicacao.md` | *"Ferramenta de estilo — fora deste bloco. A spec do F5 é dona da escolha"* — a promessa que este bloco cumpre |

A última é a mais fácil de esquecer: é um plano fechado, e planos fechados não costumam ser
revisitados — mas ele contém uma promessa que este bloco cumpre.

---

## Decisões que esta spec assume

- [D-11](../decisoes/D-11-pilha-tecnologica.md) — a pilha
- [D-12](../decisoes/D-12-tipagem-obrigatoria.md) — tipagem obrigatória, verificada no CI
- [D-17](../decisoes/D-17-monorepo-engine-sem-django.md) — o motor é pacote isolado
- [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) — o motor está congelado, e esta spec declara como o lê
- [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md) — rigor por origem do código
- [D-31](../decisoes/D-31-trabalho-direto-na-main.md) — trabalho direto na `main`, que é o que remove o portão
- [D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) — a CI espelha o contêiner, e esta spec restringe a dois trabalhos
- [D-35](../decisoes/D-35-compose-e-dockerignore-na-raiz.md) — o precedente de arquivo que fica onde a ferramenta o procura
- [D-38](../decisoes/D-38-public-guarda-o-encanamento.md) — o esquema vai no `db_table`, e a CI é o primeiro ambiente Linux a exercitá-lo

### Decisões novas que este bloco produz

Quatro registros, escritos **junto com a aprovação desta spec**:

| # | Decisão | Contradiz, ou fecha |
|---|---|---|
| **D-42** | A CI **avisa e não bloqueia** enquanto valer a D-31 | contradiz a [ARQUITETURA](../ARQUITETURA.md#ambientes): *"não passou, não entra"* |
| **D-43** | **ruff** para Python, **Biome** para o frontend, e a regra de onde cada verificação roda | fecha a pendência do F2b; **restringe a [D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)**, que manda a CI espelhar o contêiner |
| **D-44** | O motor entra no estilo; formatação provada por árvore sintática, lint com as 23 de `src` enumeradas | é uma leitura da [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md), que diz *"não é alterado"* |
| **D-45** | A CI mora em `.github/workflows/`, não em `infra/` | contradiz o diagrama da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório), que nomeia o F5 |

---

## Riscos e questões em aberto

### O primeiro push carrega tudo desde 2026-09-01

**38 commits.** O que pode aparecer, e nunca foi exercitado fora do Windows:

- **O `db_table` com aspas embutidas** (`'core"."user'`). Foi medido contra o `postgres:18` do
  `compose`, mas sempre a partir daqui.
- **Fim de linha.** O `.gitattributes` normaliza tudo para LF (`* text=auto eol=lf`), o que deve
  bastar — mas é a primeira vez que alguém confere.
- **Diferença de caixa em nome de arquivo**, que o Windows perdoa e o Linux não.
- **A linha de base numérica, e este é o candidato mais provável dos quatro.** O lock congela
  **versão**, não **plataforma**: `valores.json` foi capturado no Windows, e `numpy`, `scipy` e
  `arch` usam no Linux bibliotecas de álgebra e ordem de redução diferentes. Versões idênticas
  não garantem resultado bit a bit entre sistemas, e `garch_1_1`, `egarch` e `caviar` passam por
  otimização iterativa, onde a diferença se amplifica acima da tolerância de 1e-6.
  **A mensagem que aparece engana:** o docstring do teste diz *"se a comparação divergir, o
  defeito está na migração"*, apontando para o F2a, que não tem nada a ver. Divergência de 1e-6
  na linha de base é "o F5 encontrou coisa", não "o motor quebrou".

O que fazer com o que aparecer está resolvido em
[se a primeira execução reprovar](#se-a-primeira-execução-reprovar).

### ✅ Publicar — resolvido

A verificação de F5-01 exige um push, e push é ação para fora: envia ao GitHub 38 commits mais
o que este bloco acrescentar.

**`kakah1327/Ruvor` é privado**, confirmado em 2026-09-06. Os documentos de produto, de
processo e as decisões não ficam visíveis, e o push não é publicação. O risco que esta seção
levantava está fechado — mas a escolha continua tendo consequência, na seção seguinte.

### Cota de execução

**O repositório é privado, então a cota vale.** Execução em repositório privado consome a
franquia mensal de minutos da conta; em público seria gratuita. A spec não fixa o número da
franquia, que depende do plano e muda — o que ela fixa é a obrigação de **medir**.

O trabalho do motor é o caro: o lock traz TensorFlow, que passa de meio giga, e ele roda em
todo push. Os outros três também constroem imagem.

**O plano registra a duração de cada um dos quatro trabalhos na primeira execução**, e é esse
número que decide se alguma coisa precisa mudar — cache, gatilho mais estreito, ou o motor
saindo de todo push. Decidir agora, sem medida, seria otimizar no escuro; e a alternativa
óbvia (rodar só em parte dos pushes) enfraqueceria justamente o que o bloco entrega.

Não é problema com um push a cada poucos dias. Vira problema se a CI passar a rodar a cada
commit numa sequência longa como a do F4, que teve onze.

### O que a CI não vai pegar

Vale escrever, para ninguém confundir cobertura com garantia:

- **A `worker` nunca é construída**, então a CI não prova que ela ainda constrói. O que a
  protege é F3-02/F3-03, e eles só rodam à mão.
- **A fila não é exercitada.** A prova de que o worker executa o que o web enfileira segue sendo
  comando manual do F3.
- **Deriva de dependência do motor.** O lock congela as 59; uma versão nova que quebrasse o
  motor passaria despercebida até alguém atualizar o lock à mão.
- **O motor roda no runner, não na `worker`.** Se as duas divergirem, a CI não vê.
- **Os três modelos de ML seguem sem guarda numérica** — ver [o que a prova não
  cobre](#o-que-a-prova-não-cobre).

A primeira, a terceira e a quarta são consequência de F5-05 e do lock; a segunda é do desenho
dos trabalhos; a quinta é da [decisão sobre o motor](#o-que-a-prova-não-cobre), tomada com o
risco medido. **As cinco são trocas deliberadas** — nenhuma é descuido.
