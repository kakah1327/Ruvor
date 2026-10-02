# Aprendizados

Memória operacional **entre agentes**. Não é retrospectiva de equipe.

Todo agente de implementação nasce com contexto limpo. Sem memória compartilhada, a mesma
armadilha é redescoberta a cada tarefa. Este arquivo existe para evitar isso.

## Como usar

**Antes de implementar:** varra os campos *Quando* e leia só o que se aplica à sua tarefa.

**Ao terminar:** registre o que custou tempo para descobrir e não estava documentado, o que
é contraintuitivo ou específico de uma biblioteca, e o que outro agente com contexto limpo
erraria da mesma forma.

Não registre o que já é óbvio no código ou é convenção conhecida da linguagem.

## Formato

```markdown
## <titulo curto>
**Quando:** a situacao que dispara este aprendizado
**Problema:** o que acontece se nao souber
**Faca:** a acao correta
```

O campo **Quando** é o mais importante: é o que permite varrer sem ler tudo.

## Manutenção

O arquivo cresce e precisa de poda. Periodicamente: aprendizado que virou convenção do
código sai daqui e vira comentário ou teste; aprendizado sobre código que não existe mais é
removido. Arquivo longo demais deixa de ser lido, e aí não serve para nada.

---

## Spec nasce incompleta nos mesmos seis padrões

**Quando:** ao escrever uma spec ou um plano, antes de mandar para revisão adversarial.

**Problema:** a primeira spec do projeto (F2, depois dividida em F2a e F2b) precisou de **cinco rodadas** de revisão para
ser aprovada — 431 mil tokens só nos revisores, mais as rodadas de correção. O revisor não
errou: a spec é que nascia incompleta, e sempre pelos mesmos motivos.

Os 72 achados caíram em seis padrões, todos de quem escreveu:

1. afirmação sobre o código feita de memória, sem abrir o arquivo — e falsa
2. requisito escrito como resultado desejado, sem o meio de verificá-lo
3. artefato citado por substantivo, sem nome, local, conteúdo nem dono
4. trabalho dividido entre specs irmãs sem inventariar os arquivos existentes
5. lista fechada montada de memória em vez de derivada da fonte
6. contradição com documento vivo ou decisão registrada que o próprio autor escreveu

**Faça:** rodar a lista de verificação de
[PROCESSO §4 — Antes de mandar revisar](PROCESSO.md#antes-de-mandar-revisar) **antes** de
despachar o revisor. Ela é a versão acionável desses seis padrões.

E tratar a auto-revisão como o passo caro: quem escreve tem o contexto e o código à mão; o
revisor adversarial gasta uma rodada inteira só para reconstruir o que o autor já sabia.


## O diretório do repositório se chama `varlab` e contamina varredura de nome

**Quando:** ao escrever ou executar qualquer verificação que procure o nome antigo
(`varlab`) em arquivos — varredura de rebrand, `grep -r`, teste de limpeza.

**Problema:** o repositório está em `E:\Temp\Trilobit\varlab`. Todo artefato que embute
caminho absoluto passa a conter a palavra: `.pyc` em `__pycache__`, e potencialmente
`dist/`, `build/` e `*.egg-info/`. Uma varredura de diretório encontra esses casamentos e
reprova sem causa real — ou escapa por acidente, porque bytecode é binário e cai no
tratamento de erro de decodificação. Depender do acidente é frágil.

Agrava: limpar `__pycache__` **antes** de rodar o `pytest` não resolve, porque a execução
dos testes regenera o bytecode.

**Faça:** enumerar por `git ls-files`, não por varredura de disco — o rebrand vale para o
que está versionado, não para artefato gerado. Quando a varredura de diretório for
inevitável, limpe o `__pycache__` **depois** da última execução de teste e imediatamente
antes da verificação.


## Migração de arquivo: prove a igualdade contra o original, não olhando

**Quando:** ao mover ou renomear código em lote, onde o contrato é "só muda o nome".

**Problema:** critério de aceite que conta arquivos e faz `grep` pelo nome antigo **não
detecta alteração de lógica**. Uma linha trocada de passagem atravessa, e o defeito só
aparece muito depois — ou nunca, se não houver linha de base.

**Faça:** reconstruir cada arquivo a partir do original no git aplicando **apenas** a
substituição mecânica, e comparar byte a byte:

```
git show HEAD:<caminho antigo>  →  aplicar substituição  →  comparar com o arquivo em disco
```

Os que divergirem são exatamente os que precisam de justificativa. Na migração do motor, 32
de 33 arquivos saíram idênticos e o único delta tinha as três mudanças autorizadas — prova
que nenhum critério de contagem daria.


## `pandas` não publica anotações de tipo

**Quando:** ao configurar mypy sobre código que importa pandas.

**Problema:** o pandas não embarca `py.typed`; o mypy exige o pacote `pandas-stubs`, à parte.
Sem ele nem `ignore_missing_imports`, cada arquivo que importa pandas gera um erro
`import-untyped` — no motor, 17 erros em 17 arquivos, todos só pelo import.

O risco não é o erro: é a "solução" errada. Silenciar por módulo com `ignore_errors`
desligaria a verificação em mais da metade do pacote e tornaria "mypy passa" vacuamente
verdadeiro.

**Faça:** `ignore_missing_imports` para `pandas.*`. `numpy` **não** precisa — publica
anotações próprias. E `keras` também não: o acesso é `from tensorflow import keras`, já
coberto por `tensorflow.*`; um override para `keras.*` não casa com nada e, com
`warn_unused_configs`, emite aviso permanente.


## `git mv` para diretório existente move para dentro

**Quando:** ao mover um diretório cujo destino já existe.

**Problema:** `git mv tests engine/tests`, com `engine/tests/` já criado, produz
`engine/tests/tests/`. O layout fica errado e critérios ingênuos (`pytest passa`,
`grep não acha o nome antigo`) **passam do mesmo jeito** — erro silencioso.

Relacionado: `git add --renormalize .` implica `-u` e só toca arquivo já rastreado. Arquivo
novo precisa de `git add` explícito antes, ou fica pendente e o critério reprova sem causa.

**Faça:** mover o **conteúdo**, não o diretório, e verificar explicitamente que o aninhamento
não existe (`! test -d engine/tests/tests`).


## Import diferido escapa da inspeção de módulos carregados

**Quando:** ao verificar quais bibliotecas um pacote Python carrega — por exemplo, o teste
que garante que `engine/` não importa Django.

**Problema:** import dentro do corpo de uma função só acontece quando a função é chamada.
Inspecionar `sys.modules` após importar o pacote **não detecta** esse caso. No protótipo,
`varlab/cli.py` importa Flask exatamente assim.

**Faça:** combinar as duas verificações — inspeção em execução (pega import em nível de
módulo) **e** varredura estática do fonte pelos nomes proibidos (pega import diferido).
Nenhuma das duas sozinha fecha o buraco.


## Carregar registry não carrega o pacote inteiro

**Quando:** ao escrever verificação que dependa de "todos os módulos estarem carregados".

**Problema:** `load_all_model_modules()` e `load_all_backtest_modules()` varrem apenas
`models/{traditional,garch,ml}` e `backtesting/`. **Não carregam** `data/`, `experiments/`
nem `cli.py` — que são justamente os módulos de fronteira com a plataforma, onde um import
indevido apareceria.

**Faça:** varrer a árvore com `pkgutil.walk_packages` sobre o pacote, não chamar os
carregadores de registry. E tolerar falha de import por dependência opcional ausente: sem
TensorFlow, os módulos de ML falham ao importar de propósito.


## `conftest.py` não consegue preparar o ambiente antes do pytest-django

**Quando:** ao configurar testes de um projeto Django cujas settings exigem variável de
ambiente (`RUVOR_SECRET_KEY`).

**Problema:** o pytest-django chama `django.setup()` na varredura inicial do projeto, **antes**
de carregar qualquer `conftest.py` — na raiz ou em `tests/`. Um `os.environ.setdefault` no
conftest chega tarde; a suíte morre com `ImproperlyConfigured` antes do primeiro teste. O
plugin do django-stubs para o mypy importa as settings do mesmo jeito e cai no mesmo erro.

**Faça:** um módulo de settings de teste (`config/settings_test.py`) que preenche as
variáveis e reexporta `config.settings` com `from config.settings import *`; apontar
`DJANGO_SETTINGS_MODULE` do pytest **e** `django_settings_module` do django-stubs para ele.


## Provar conexão com o banco **configurado** exige desbloquear o pytest-django

**Quando:** ao escrever teste que prove que a aplicação alcança o banco do `compose`.

**Problema:** o caminho óbvio, `@pytest.mark.django_db`, alcança o servidor mas conecta num
banco `test_<nome>` que o próprio pytest-django cria. Com isso ele **não exercita
`RUVOR_DB_NAME`** — um nome de banco errado no `.env` atravessa sem ser notado, que é
justamente o erro que uma verificação de ambiente existe para pegar. E sem marca nenhuma, o
pytest-django bloqueia o acesso e levanta `RuntimeError`.

**Faça:** peça o acessório `django_db_blocker` e abra o cursor dentro de `unblock()`,
conferindo `SELECT current_database()` contra a variável de ambiente. É o que prova a
configuração inteira, e não só que existe um Postgres em pé.

Ressalva desde o M1.1: a marca `django_db` de **qualquer** teste da sessão renomeia a conexão
para `test_<nome>` até o fim dela (`django/db/backends/base/creation.py:78-79`), e o pytest
coleta `tests/assets/` antes de `tests/test_*.py`. Um teste sem marca que venha depois
inspeciona o banco de teste, não o configurado; por isso o `test_conexao_com_o_banco`
aceita os dois nomes.

> Substitui o verbete anterior sobre `DATABASES = {}`, que descrevia o
> `test_processo_nao_tem_banco` — removido no F3, quando o Django passou a conectar.


## npm sob Node incompatível pula binding nativo em silêncio

**Quando:** ao instalar dependências de frontend numa máquina cujo Node não satisfaz o
`engines` de alguma dependência (Vite 8, jsdom 30, rolldown).

**Problema:** sem `engine-strict`, o npm só avisa `EBADENGINE` e **omite as dependências
opcionais** que não casam — entre elas o binding nativo do rolldown. A instalação "termina
bem" e o `vite build` quebra depois com `Cannot find native binding`, mensagem que culpa o
`package-lock.json` e não a versão do Node.

**Faça:** `engine-strict=true` em `frontend/.npmrc`, e `engines.node` no `package.json` com o
piso real das dependências (jsdom 30 exige `^22.22.2 || ^24.15.0`). Assim a instalação sob
Node errado falha alto, na hora. O Node 24 desta máquina vem por `fnm`, não pelo PATH global;
no Git Bash, chame o `fnm` pelo caminho completo tanto no `env` quanto no `use`.


## Vite escuta em `localhost`, que é IPv6 no Windows

**Quando:** ao verificar o servidor de desenvolvimento do Vite com `curl` ou script.

**Problema:** o Vite 8 anuncia `http://localhost:5173/`, e no Windows `localhost` resolve
para `::1`. `curl http://127.0.0.1:5173` é recusado com o servidor funcionando perfeitamente
— parece que o proxy ou o servidor está fora do ar.

**Faça:** use `http://localhost:5173` (ou `[::1]`) nas verificações. O alvo do proxy para o
Django pode continuar `127.0.0.1:8000`, porque o `runserver` escuta em IPv4.


## Servidor de teste: encerre pelo PID certo, nunca por porta

**Quando:** ao subir `runserver` ou `vite` em segundo plano num critério de aceite.

**Problema:** duas armadilhas encadeadas. (1) Encerrar "tudo que escuta na porta" pode
derrubar programa alheio — nesta máquina a porta 5173 já estava ocupada por outro projeto do
usuário, e uma limpeza por porta o matou. (2) No Git Bash, `$!` de um lançamento em subshell
`(cd dir && cmd) &` é o PID do invólucro: `kill $!` não encerra o servidor. E `taskkill` com
`$!` usa o PID do MSYS, que não é o do Windows.

**Faça:** confirme a porta livre antes (`netstat -ano | grep ":PORTA "` vazio); lance o
comando direto com `&` quando puder; se lançou em subshell, localize o filho real em
`ps -ef` pela hora de início e use `kill` nele. Nunca `taskkill` por porta.


## Arquivo copiado de plano por heredoc perde barras invertidas

**Quando:** ao materializar um conteúdo literal do plano que contém `\` (expressão regular
em string JavaScript, por exemplo) via heredoc ou `printf` no Git Bash.

**Problema:** dependendo do caminho até o shell, `\s` chega ao disco como `\s`. O arquivo
parece igual ao plano, compila, e o padrão que deveria casar não casa — a varredura de cores
teria deixado passar `color: white`.

**Faça:** depois de gravar, extraia o bloco do plano (`awk` entre as cercas) e faça `diff`
contra o arquivo em disco. Foi esse `diff` que pegou o caso real. `startproject` no Windows
tem armadilha parecida com fim de linha: gera CRLF, e `diff` contra template só bate com
`--strip-trailing-cr`.


## O Postgres 18 mudou o ponto de montagem do volume

**Quando:** ao declarar o volume de dados do Postgres em `compose.yaml`, ou ao subir a versão
maior da imagem.

**Problema:** o caminho que todo tutorial ensina, `/var/lib/postgresql/data`, **deixou de
valer na 18**. O `PGDATA` da imagem passou a ser `/var/lib/postgresql/18/docker`, e o volume
vai um nível acima, em `/var/lib/postgresql`. Com o caminho antigo o contêiner **recusa
subir**, falando de compatibilidade com `pg_ctlcluster` — mensagem que não parece ser sobre
montagem.

**Faça:** monte em `/var/lib/postgresql`. Ao trocar a versão maior, confira o `PGDATA`
declarado na imagem antes de confiar na memória: `docker image inspect postgres:NN --format
'{{range .Config.Env}}{{println .}}{{end}}'`.


## `.env` ausente não faz o `docker compose` falhar

**Quando:** ao escrever critério de aceite que dependa de o `compose` ler o `.env`.

**Problema:** sem o arquivo, o Compose **não reprova**. Ele emite `variable is not set.
Defaulting to a blank string` e segue com **código de saída 0** — as portas sobem vazias, e o
que deveria ser falha alta vira comportamento estranho depois. Um critério do tipo "renomeie
o `.env` e veja falhar" passa vazio.

**Faça:** declare as variáveis com a sintaxe de obrigatoriedade — `${VAR:?mensagem}`. Aí a
ausência sai com código 1 e nomeia a variável que falta. Vale para toda variável sem padrão
sensato.


## `grep` na saída casa com a linha ecoada no traceback

**Quando:** ao verificar que um comando produziu certo texto, sobretudo em prova de mutação.

**Problema:** o traceback do Python **ecoa a linha de código que falhou**, e essa linha
costuma conter a própria string procurada. Uma checagem do tipo `saida | grep "resultado"`
casa com o traceback e **aprova a falha**. Aconteceu de verdade aqui, verificando que a fila
reprova com o worker parado: a mutação passou por isso.

**Faça:** apoie o critério no **código de saída**, não em casamento de texto. Quando o texto
for mesmo o contrato, ponha o `grep -q` dentro da cadeia que decide o código de saída, nunca
como leitura humana da saída.


## Montagem Windows→contêiner não propaga aviso de alteração de arquivo

**Quando:** ao rodar servidor de desenvolvimento com recarga a quente dentro de contêiner,
com o código montado do Windows.

**Problema:** o contêiner **enxerga** o arquivo alterado — `tail` mostra a mudança —, mas o
observador de arquivos não recebe evento nenhum. O Vite não emite `hmr update`, a tela não
muda, e nada indica a causa. Pior: o Vite normalmente se reinicia sozinho quando o próprio
`vite.config.ts` muda, e isso depende do mesmo aviso quebrado — então ligar a sondagem exige
reiniciar o serviço à mão.

**Faça:** verifique antes de supor, editando um arquivo e olhando o log do contêiner. Se não
houver evento, ligue `server.watch.usePolling` e **reinicie o serviço**. Sondagem custa CPU
contínua, então não a ligue por precaução.


## `@app.task` reprova sob mypy estrito, e `ignore_missing_imports` não resolve

**Quando:** ao escrever a primeira tarefa Celery num projeto com `disallow_untyped_decorators`.

**Problema:** o Celery não publica tipos, então o `mypy` estrito emite dois erros de natureza
diferente. O `import-untyped` some com `ignore_missing_imports` restrito a `celery.*` — mas o
`untyped-decorator` **sobrevive**: com o Celery virando `Any`, o decorador continua não
tipado. Quem só configurar o `ignore_missing_imports` fica travado, e a saída fácil vira
`# type: ignore` ou, pior, `ignore_errors` no módulo.

**Faça:** aplique o decorador como chamada sobre uma função anotada —
`ping = app.task(name="…")(_ping)`. Nada é suprimido e a função segue verificada. Saiba a
ressalva: a tarefa resultante é `Any` de qualquer forma, então isso remove o aviso, não a
perda de tipagem. Adotar o pacote `celery-types` é a saída de verdade, quando houver tarefas
o bastante para pagar por ela.

**Desfecho (M3.2, 2026-09-27):** o `celery-types==0.26.0` entrou no extra `dev`, e o override de
`celery`/`celery.*` saiu ([D-134](decisoes/D-134-tarefas-celery-tipadas-por-celery-types.md)).
Com os tipos, `@app.task` passa limpo no `mypy` estrito, e o único erro novo na suíte inteira foi
um `object` sem `startswith` num teste. A forma `app.task(name=...)(_funcao)` **ficou**, mas
agora pelo ponto de teste, não pelo `mypy`.

**E a volta do override passa calada (M1.6a):** com o `celery-types` instalado, um
`[[tool.mypy.overrides]]` que devolvesse `celery`/`celery.*` ao `ignore_missing_imports` não
faz o `mypy` reprovar nem avisar — a seção conta como usada. Quem pega é
`backend/tests/test_tipos.py`, que lê o `pyproject.toml` com `tomllib`.


## Volume anônimo de `node_modules` sobrevive à recriação do contêiner

**Quando:** ao acrescentar dependência ao `package.json` de um frontend em contêiner.

**Problema:** o volume anônimo que protege o `node_modules` do hospedeiro **não é recriado**
com o contêiner. Reconstruir a imagem instala a dependência nova dentro dela, mas o volume
antigo é montado por cima e a apaga — a dependência "não existe", e a imagem parece errada.

**Faça:** `docker compose up -d --build --renew-anon-volumes` depois de mexer no
`package.json`.


## `Set-Content -Encoding utf8` do PowerShell 5.1 grava BOM e corrompe o arquivo

**Quando:** ao escrever arquivo de código por script do PowerShell no Windows — em sonda,
mutação ou geração de conteúdo.

**Problema:** o Windows PowerShell 5.1 escreve **marca de ordem de bytes** com `-Encoding
utf8`. Num `.ts` ou `.py` o arquivo continua abrindo e quase sempre compilando, mas o diff
mostra a primeira linha inteira alterada, e ferramentas que leem o começo do arquivo se
confundem. Aconteceu aqui num teste de recarga a quente: a sonda sujou o `App.tsx` sem que
nada acusasse.

**Faça:** para restaurar arquivo versionado, use `git checkout --`, não reescrita. Para
escrever de fato, prefira as ferramentas de edição do agente, ou `-Encoding utf8NoBOM` onde
existir.


## O esquema no `db_table` mora em dois lugares, e só um deles cria a tabela

**Quando:** ao mexer no esquema de uma tabela — mudar, ou escrever mutação que o estrague de
propósito.

**Problema:** o identificador em duas partes (`db_table = 'core"."user'`) existe no **modelo**
e nas `options` do `CreateModel` da migration. Quem cria a tabela é a migration. Mexer só no
`models.py` deixa a tabela nascendo no esquema certo, e quem acusa é o `makemigrations
--check` — ou seja, a verificação de *sincronia entre modelo e migration*, não a de *esquema*.
Uma mutação escrita assim parece válida e ataca o requisito errado. Aconteceu no F4, e nenhuma
das quatro rodadas de revisão pegou: só apareceu na execução.

**Faça:** ao mudar o esquema de uma tabela, mude nos dois. Ao escrever mutação sobre esquema,
aplique nos dois — é o defeito de verdade, alguém que escreveu o `db_table` errado desde o
começo.


## `pytest.mark.django_db` concede acesso ao banco, nunca exige uso

**Quando:** ao escrever verificação de que uma rota ou função **não** toca o banco.

**Problema:** a intuição é que acrescentar a marca a um teste o faria falhar se o código não
usasse o banco. É o contrário: a marca libera o acesso que o pytest-django bloqueia por
padrão. Uma mutação que só acrescenta a marca **não reprova nada** — medido no F4, sobre o
teste do `/health`.

**Faça:** apoie a garantia no **bloqueio** do pytest-django sobre o teste sem marca, e mute o
**código** — faça a view tocar o banco e confirme que o teste quebra com `Database access not
allowed`.


## Idempotência de migration de dados só se testa com `--fake`

**Quando:** ao verificar que uma migration de dados pode rodar duas vezes sem duplicar.

**Problema:** o caminho óbvio — desaplicar e reaplicar — executa a função de reversão, que
apaga a linha. A reaplicação encontra o banco vazio, e uma implementação com `create()` no
lugar de `get_or_create()` **passa**. A verificação existe justamente para pegar essa
implementação, e não pega.

**Faça:** `migrate <app> <n> --fake`. Conferido na fonte: `unapply_migration(..., fake=True)`
não executa as operações, só desfaz o registro — a linha fica no banco, e a reaplicação roda
contra o estado que `get_or_create` existe para tratar.


## `! grep` sobre status aprova vazio, e o padrão pode casar com o próprio critério

**Quando:** ao escrever varredura que prove que um documento parou de mentir.

**Problema:** dois modos de aprovar sem trabalho. (1) A negativa (`! grep -q "aguardando
revisão"`) passa assim que o texto muda por **qualquer** motivo — no F4 o cabeçalho já dizia
outra coisa desde o portão humano, e a verificação aprovava com o arquivo intocado. (2) A
afirmativa desancorada casa com a **própria linha do critério**, quando o critério mora no
arquivo verificado.

**Faça:** verifique por afirmação do texto final e **ancorada** —
`grep -q '^\*\*Status:\*\* ✅ \*\*executado e fechado\*\*'`. E rode a varredura **antes** de
editar, confirmando que ela acusa: varredura que já passa antes não prova nada.


## Lista fechada é o ponto fraco recorrente, e envelhece calada

**Quando:** ao escrever spec com "lista fechada" de trechos, arquivos ou tabelas.

**Problema:** é a terceira vez no projeto que a lista fechada é o defeito. No F4 ela estava
incompleta em dois pontos, e os dois só apareceram na revisão final: a frase do `README` e do
`ESTADO` sobre *"`pytest` no hospedeiro reprova **um** teste"* — que virou cinco e nenhuma
verificação podia pegar, porque a linha não estava na lista — e a seção "Isolamento por
organização" da ARQUITETURA, que ficou descrevendo no presente um mecanismo adiado.

**Faça:** ao declarar que a suíte, o ambiente ou um contrato **mudam de exigência**, procure
imediatamente todo texto que descreva a exigência antiga, e ponha cada um na lista. A
pergunta que fecha o buraco é: *"que documento afirma um número, uma contagem ou um verbo no
presente sobre o que eu acabei de mudar?"*

## Medir com a ferramenta isolada da configuração não é medir o projeto

**Quando:** ao contar violações, arquivos afetados ou qualquer número que vá virar critério de
aceite — sobretudo com `ruff`, `mypy` ou linter que leia configuração do `pyproject.toml`.

**Problema:** `ruff --isolated` ignora a configuração do projeto, **inclusive o
`requires-python`**, e cai na versão-alvo padrão. Regras que dependem da versão de Python se
calam. No F5, `UP042` não aparecia com `--isolated` e dispara no projeto real, porque
`StrEnum` só existe a partir do 3.11 — e ela acusava código congelado pela D-21, com uma
sugestão não equivalente.

O mesmo vale para o **momento** da medição: contar lint antes de formatar infla o número, com
violações que a formatação resolve. E para o **escopo**: `src` e `.` são conjuntos diferentes,
e o comando do contrato usava `.` enquanto a medição usava `src`.

**Faça:** meça sob a configuração real, no escopo do comando que vai para o contrato, e na
ordem em que o bloco vai executar. Se o número vira critério de aceite, ele precisa ter sido
medido nas condições em que o critério vai rodar — senão a tarefa reprova a si mesma.


## Teste de reprovação que nunca foi aplicado não é teste

**Quando:** ao escrever a tabela de mutações de um plano.

**Problema:** três mutações deste projeto pareciam corretas na leitura e não reprovavam nada.
Uma procurava serviço **ausente** no `compose` quando a mutação **acrescentava** um. Outra
mandava alterar um arquivo antes de rodar a prova por árvore sintática — mas a prova captura a
referência **depois** da edição, então a alteração está nos dois lados da comparação e ela sai
0. A terceira era um `! grep` sobre cabeçalho de status, que já passava porque o texto tinha
mudado por outro motivo.

O padrão: a mutação precisa atacar o **instrumento**, e não o insumo, quando o que está sendo
testado é a capacidade do instrumento de detectar.

**Faça:** aplique cada mutação de verdade antes de escrevê-la como verificada, e apoie o
resultado no **código de saída**. Uma mutação que passa é achado sobre o plano, não sobre o
código.


## `write_text()` no Windows converte o arquivo inteiro para CRLF, em silêncio

**Quando:** ao editar arquivo versionado por script Python no Windows.

**Problema:** `pathlib.Path.write_text()` usa a tradução de fim de linha do sistema, então
`\n` vira `\r\n` e o arquivo inteiro muda de fim de linha — contra o `* text=auto eol=lf` do
`.gitattributes`. O `git diff --stat` continua parecendo limpo, porque o git normaliza na
leitura; a única pista é o aviso `CRLF will be replaced by LF`.

**Faça:** `write_text(..., newline="")` ou `io.open(..., newline="")`. É irmã do verbete do
`Set-Content -Encoding utf8`, com gatilho diferente: Python, não PowerShell.


## Arquivo de configuração literal precisa passar pela própria ferramenta

**Quando:** ao pôr conteúdo literal de configuração num plano — `biome.json`, `pyproject.toml`,
qualquer coisa que a própria ferramenta também formate.

**Problema:** o `biome.json` do plano do F5 tinha uma linha de 96 colunas declarando
`lineWidth: 88`. Gravado como estava, o primeiro `biome check` reprovava o arquivo de
configuração — e o critério de aceite da tarefa ficava insatisfazível.

**Faça:** rode a ferramenta sobre o próprio arquivo antes de fechar o plano, e **prove que a
configuração não mudou** — por igualdade profunda de estrutura, não por `diff` de texto.


## Linha de base numérica não é portátil entre plataformas

**Quando:** ao levar para outro sistema operacional qualquer teste que compare número contra
valor gravado, com tolerância.

**Problema:** arquivo de travamento congela **versão, não plataforma**. `numpy`, `scipy` e
`arch` usam bibliotecas de álgebra e ordem de redução diferentes em Linux e Windows. Onde há
otimização iterativa, a diferença se amplifica: no F5, o `garch_1_1` desviou ~1e-6, no limiar
da tolerância, e o **EGARCH desviou ~1,2e-2, convergindo para outro ótimo** e mudando o
veredito de um backtesting.

Pior que o número: a mensagem do teste dizia *"se a comparação divergir, o defeito está na
migração"* — apontando para um bloco que não tinha nada a ver.

**Faça:** trate linha de base numérica como referência **do ambiente em que foi capturada**, e
não como portão entre ambientes. Se a CI precisar rodá-la, ou o ambiente é reproduzido por
inteiro — inclusive plataforma —, ou a exclusão é declarada com o número real de testes que
deixam de rodar.


## Lista fechada escrita como "esta frase fica falsa" vira "esta frase não pode existir"

**Quando:** ao escrever varredura de documentação com `! grep`.

**Problema:** o critério `! grep -q "A CI espelha o contêiner"` obriga a frase a sumir do
arquivo — **inclusive de uma redação que a restrinja corretamente**. Quem for corrigir o
documento não pode citar o texto antigo nem para explicar o que mudou.

**Faça:** ao escrever a lista, pergunte se o trecho precisa **sumir** ou apenas **deixar de ser
afirmado**. No segundo caso, o padrão tem de ser mais estreito que a frase — ou a verificação
vira proibição de vocabulário.


## `docker compose exec -w /caminho` falha no Git Bash com "Cwd must be an absolute path"

**Quando:** ao executar comando dentro de um contêiner a partir do Git Bash, com `-w` ou
qualquer argumento que seja caminho POSIX do contêiner (`/repo`, `/app`).

**Problema:** o MSYS converte argumentos que parecem caminho Unix para caminho Windows
antes de entregá-los ao `docker`. `/repo` chega como `E:/Git/repo` (ou parecido), e o
runtime responde `OCI runtime exec failed: exec failed: Cwd must be an absolute path`. A
mensagem culpa o caminho, não a conversão, e o mesmo comando funciona no PowerShell.

**Faça:** prefixe com `MSYS_NO_PATHCONV=1` — `MSYS_NO_PATHCONV=1 docker compose exec -T -w
/repo worker ...`. Vale também para `docker run -v /x:/y` e para qualquer `--flag=/caminho`.

**Não é só o `-w`: argumento posicional também é convertido.** Um caminho do contêiner passado
como argumento comum ao comando executado lá dentro (`... python script.py /tmp/saida`) chega
convertido, e **sem erro nenhum** — o comando grava em outro lugar e sai 0. Na T2 do M3.1 isso
gravou 47 MB de download **dentro do repositório**. Use `MSYS_NO_PATHCONV=1` em todo `docker
compose exec` que leve caminho do contêiner, em qualquer posição, e confira `git status` depois
de comando que grava arquivo.


## Ajuste do `arch` com `convergence_flag != 0` não é estimativa; e o ponto de partida padrão muda com a plataforma

**Quando:** ao usar `arch_model(...).fit()` (GARCH, EGARCH) em código que vai rodar em mais
de um sistema operacional, ou ao interpretar uma divergência numérica entre plataformas.

**Problema:** o `fit` **devolve resultado mesmo quando o SLSQP não converge** — só emite
`ConvergenceWarning` e preenche `convergence_flag`. Quem não olha o flag usa parâmetros sem
sentido (`alpha = 11`, variância condicional na casa dos milhares) como se fossem MLE. E o
ponto de partida padrão vem de uma busca em grade cujo resultado depende da ordem de redução
do BLAS: a mesma série, as mesmas versões, convergem no Windows e caem em `code 4` no Linux.
Medido em 2026-09-15 sobre a série da linha de base — ver
[D-46](decisoes/D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md).

Agrava: sobre série sem estrutura GARCH (ruído i.i.d.), a superfície de verossimilhança é
quase plana, e mesmo ajustes convergidos caem em ótimos diferentes por plataforma. Uma
linha de base assim não é referência do modelo — é referência do ambiente.

**Faça:** confira `convergence_flag == 0` antes de usar `params`; quando não convergir,
tente de novo a partir de valores iniciais explícitos (`starting_values=`), e recuse o
resultado se nenhum convergir. É o que `ConditionalVolatilityVaR._fit_arch` faz. Para
comparar plataformas, compare **log-verossimilhança e flag**, não a série de VaR: é o que
separa "outro ótimo" de "otimização que falhou".


## Migration gerada pelo `makemigrations` reprova no `ruff format --check`

**Quando:** ao criar uma migration com `makemigrations` (ou `--empty`) num projeto em que o
`ruff format --check .` cobre `migrations/`.

**Problema:** o arquivo nasce com aspas simples e linhas longas, no estilo do gerador do
Django, e o critério de aceite do bloco reprova por formatação — não por conteúdo. O
`pyproject.toml` só isenta `migrations/` da regra `RUF012` do lint; o formatador vale para
todo arquivo.

**Faça:** `ruff format <arquivo>` logo depois de gerar, antes de rodar o critério. O
`accounts/0001` e o `assets/0001` passaram pelo mesmo. Vale também para a migration de dados
copiada literal de um plano — confira com `ruff format --check` antes de commitar.


## `git checkout --` não reverte arquivo que ainda não foi commitado

**Quando:** ao aplicar uma mutação de prova num arquivo criado na própria tarefa, antes do
commit — o padrão "aplica, mede, reverte" das tabelas de mutação.

**Problema:** `git checkout -- <arquivo>` só restaura o que o índice conhece. Num arquivo novo
ele não faz nada (ou acusa `pathspec did not match`), e a mutação fica no lugar; a segunda
mutação empilha sobre a primeira, e o critério "verde depois de reverter" mede código sujo.
Aconteceu na T4 do M1.2, com duas mutações empilhadas antes de alguém notar, e **de novo
na T7 do M1.3**, na tabela de vinte e oito mutações — o verbete existia e não foi lido.

**Faça:** mutação antes do commit → copie o arquivo para o scratchpad e restaure por cópia,
conferindo com `diff`. Ou commite primeiro e mute depois, que é o que a tarefa de mutações
do plano faz. Nunca confie no `git status` limpo como prova de reversão de arquivo não
rastreado: ele nunca esteve sujo aos olhos do git.


## `git diff` vazio não prova árvore intocada, neste repositório

**Quando:** ao confirmar que uma mutação foi revertida, ou que uma tarefa não tocou em arquivo
fora da sua cerca, usando `git diff` como prova.

**Problema:** o `.gitattributes` fixa `* text=auto eol=lf`, e o `core.autocrlf` vale `true` —
**pelo gitconfig do sistema**, o que o Git for Windows instala, não pela configuração local do
repositório. Conferir com `git config --local core.autocrlf` devolve vazio e faz o verbete
parecer falso; a forma que mostra a origem é `git config --show-origin core.autocrlf`. Em
Linux a armadilha não se reproduz. O git normaliza na leitura, então um arquivo **reescrito inteiro
em CRLF** — por editor, por script, por ferramenta — some do `git diff` e do `git diff
--stat`: os dois saem vazios, e o critério "árvore intocada" passa sobre um arquivo alterado.
A única pista é `git status --porcelain`, que lista o arquivo, e o aviso `CRLF will be
replaced by LF` quando ele entra no índice.

**Faça:** para provar reversão ou árvore intocada, use `git status --porcelain` — vazio ali é
prova; vazio no `git diff` não é. Vale junto com os verbetes do `write_text()` e do
`Set-Content`, que são as **causas** mais comuns da reescrita; este é sobre a **verificação**
que não a enxerga.


## `CASCADE` do Django não vira DDL: não se prova no `psql`

**Quando:** ao verificar um `on_delete=models.CASCADE` (ou `PROTECT`, `SET_NULL`) inspecionando
a tabela com `\d` no `psql`, ou ao supor que apagar a linha pai pelo banco limpa as filhas.

**Problema:** o Django implementa as ações de `on_delete` **em Python**, no coletor do ORM, e
emite a FK sem `ON DELETE`. `\d gold.return_histogram_bin` mostra só `FOREIGN KEY (metric_id)
REFERENCES gold.behavior_metric(id) DEFERRABLE INITIALLY DEFERRED` — nenhuma palavra
`CASCADE`. Quem procura a cláusula conclui que o modelo está errado; quem apaga a métrica por
`DELETE` em `psql` não limpa os baldes. Pior: como a FK é `DEFERRABLE INITIALLY DEFERRED`, o
`DELETE` **responde `DELETE 1`** e só estoura no `COMMIT` — medido em 2026-09-24, com `SET
CONSTRAINTS ALL IMMEDIATE` forçando a checagem dentro da transação.

**Faça:** prove `on_delete` pelo ORM — `metric.delete()` e conte as filhas —, nunca pela DDL.
A DDL só prova o que o banco garante sozinho: tipo, nulabilidade, unicidade e a existência da
FK.


## O `mypy` do motor roda de dentro de `engine/`, nunca da raiz

**Quando:** ao verificar tipos do motor — em tarefa que altera `engine/src/`, ou ao conferir
o critério de aceite de um plano que diz "mypy".

**Problema:** `mypy engine/src` a partir da raiz **não lê** o `engine/pyproject.toml`: ele
procura a configuração no diretório corrente. O resultado são ~37 erros que **já existem
hoje** e não são regressão nenhuma — `import-untyped` de pandas, scipy e tensorflow, mais os
dois módulos que a `ignore_errors` da [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md)
cobre (`_quantile_nn`, `_conditional`). Quem mede assim conclui que quebrou o motor e sai
consertando o que não está errado. Medido na T2 do M1.4.

**Faça:** `cd engine && mypy` — sem argumento, porque a configuração já traz `files = ["src"]`.
É a forma que a CI usa e a que o `README.md` documenta. O `ruff`, ao contrário, roda **da
raiz** (`ruff check engine`): de dentro de `engine/` o caminho `engine` não existe.


## `_REGISTRY` do motor é global de processo, e isso esconde mutação

**Quando:** ao escrever ou medir teste que dependa de `load_all_model_modules()` /
`load_all_backtest_modules()` terem sido chamadas — e ao mirar uma mutação que as remova.

**Problema:** `list_models()` lê um dicionário de módulo, populado por `load_all_*`. Como ele
é **global de processo**, qualquer teste anterior da mesma sessão do pytest já o terá
populado. Remover as duas chamadas do código de produção deixa a suíte **verde** em quase
todo critério que se escolha para apontar: a mutação só morde em execução real — onde o
processo é novo — ou num teste escrito para limpar/observar o registry. Na T9 do M1.4 ela
reprovou em `test_o_registry_e_carregado_antes_de_ser_consultado`, **e só nele**; mirar em
outro critério teria produzido um falso "a mutação passou".

**Faça:** ao provar que uma verificação sabe reprovar, escolha o teste que **de fato** isola o
estado global, e registre no plano qual é. Estado global de processo faz a suíte inteira
parecer cúmplice.


## Substituição em massa em documento de contrato precisa ser relida linha a linha

**Quando:** ao aplicar `sed`, `str.replace` ou "substituir tudo" num arquivo que é contrato —
spec, plano, `README.md`, workflow da CI, tabela de comandos.

**Problema:** a substituição acerta o padrão e erra o contexto. Aconteceu **duas vezes no
M1.4**: a troca de `web` por `worker` na tabela de comandos atingiu linhas que a tarefa
mandava explicitamente **não** mover, e uma das substituições deixou um comando **depois de
um `#`**, dentro de um bloco de critério de aceite — onde ele nunca executaria, e onde
ninguém que leia rápido percebe que ele sumiu. O texto continua plausível, o diff parece
pequeno, e o defeito só aparece quando alguém tenta rodar o critério.

**Faça:** depois de qualquer substituição em massa em documento de contrato, releia **o diff
inteiro linha a linha** — não o resumo, não o `--stat`. Em bloco de código de critério de
aceite, confira que nenhuma linha executável foi comentada. Vale junto com o verbete da lista
fechada: os dois são sobre afirmação que envelhece calada.


## Teste de determinismo com um parâmetro só não localiza o ponto de semeadura

**Quando:** ao escrever verificação de reprodutibilidade — semente, cache, estado global —
em que o requisito não é só "duas execuções dão o mesmo número", mas **onde** a semeadura
acontece.

**Problema:** o V-03 do M1.4 roda os três modelos neurais com **um** alpha e compara as
séries de VaR. Com um alpha só, nada consome aleatoriedade entre o `fit()` preguiçoso e o
único `_fit_for_alpha`, então mover `seeding.apply()` do segundo para o primeiro — a
implementação que a spec gasta 40 linhas rejeitando — dá **resultado idêntico e o teste
passa**. Medido duas vezes: na revisão final do bloco, por monkeypatch, e na T11, aplicando
a mutação no arquivo. O V-14c, do lado do backend, também não pega.

**Faça:** exercite o eixo que distingue os dois pontos — no caso, **dois alphas em ordem
trocada** na mesma instância: cada `_fit_for_alpha` semeia, então a ordem não pode mudar
valor nenhum; com a semeadura no `fit()`, o segundo alpha continua de onde o primeiro parou
e muda. Espião que substitui a função de semeadura prova a contagem de chamadas, não a
consequência — e, ao substituir, deixa de semear.


## A ordem posicional do `crontab` do Celery não é a do cron

**Quando:** ao transformar uma expressão cron de cinco campos (variável de ambiente, arquivo
de configuração) num `celery.schedules.crontab`.

**Problema:** o construtor é `crontab(minute, hour, day_of_week, day_of_month,
month_of_year)` — o dia da semana vem em **terceiro**, e o cron o põe em quinto.
`crontab(*"30 19 * * 1-5".split())` não falha: entrega `*` como dia da semana e `1-5` como
**mês**, e a agenda vira "todo dia, de janeiro a maio". Ninguém percebe até junho.

**Faça:** desempacote com nomes (`minute, hour, day_of_month, month_of_year, day_of_week =
campos`) e passe **argumentos nomeados**. E teste com um valor em que as duas leituras
divergem — dia do mês e dia da semana diferentes, como `"15 21 3 * 2"`; com `*` nos dois, o
teste aprova as duas formas.


## `chord` e `--concurrency` baixa: o fecho vai para o fim da fila, e a ordem do cabeçalho decide quem espera

**Quando:** ao prometer "os rápidos primeiro" com um `chord` do Celery, ou ao ler o `status`
escrito pelo corpo do `chord` para saber se o trabalho acabou.

**Problema:** o Celery executa na ordem da fila, e a fila é uma para tudo. Com duas vagas, as
tarefas lentas que chegam primeiro ocupam as duas, e as rápidas que vêm depois no cabeçalho
esperam; os grupos dos ativos do fim da fila esperam os do começo. E o corpo do `chord` é
enfileirado **quando** a última tarefa termina — atrás de tudo o que já estava na fila. Na
execução real do M1.5, o IBOV ficou 2 min 15 s `running` com os dezoito resultados já
gravados, e os modelos baratos depois das redes, na ordem alfabética, esperaram até 2 min 25 s.

**Faça:** a ordem do cabeçalho e o número de filas são decisão de desenho, não detalhe; meça
o instante da primeira linha de **cada** ativo e o atraso entre a última linha e o fecho,
nunca só o tempo total.


## Filho do *prefork* guarda a memória entre tarefas: meça depois, não só durante

**Quando:** ao medir a memória de um worker Celery que roda TensorFlow (ou qualquer
biblioteca que aloque muito e não devolva), para decidir `--concurrency` ou o tamanho do
contêiner.

**Problema:** os processos-filhos vivem entre tarefas, e o que eles alocam numa tarefa não
volta na seguinte — a memória do contêiner **só sobe**: 157 MiB ocioso, 2,9 GiB
depois da primeira rodada de quatro ativos, 5,0 GiB depois da segunda — e parada em 5,0 GiB
com o worker ocioso, medido no M1.5 com `docker stats`, que não separa por processo. O pico
de uma execução isolada mede a primeira rodada, não o regime.

**Faça:** meça duas rodadas seguidas e o ocioso depois de cada uma. Se a curva sobe, o número
que decide é o da rodada N, não o da primeira; o Celery tem `--max-tasks-per-child` e
`--max-memory-per-child` para reciclar filhos, e escolher entre eles é decisão, não remendo.

**Medido por processo no M1.5b** (soma do `VmRSS` de `/proc/<pid>/status` dos processos
`celery`, a cada 5 s — `ps` não existe na imagem): picos de **3,8 → 5,9 → 6,7 GiB** em três
rodadas `--full` seguidas, não os 2,9 → 5,0 do `docker stats`. E **não existe um número de
tarefas a partir do qual o filho passa a reter**: ele retém desde a primeira, ~190 MiB por
tarefa de rede. O `--max-tasks-per-child=5` saiu do teto do pior caso, não de um joelho na
curva; com ele, as três rodadas ficaram em 3,0, 2,6 e 2,8 GiB.


## A máquina trava se o TensorFlow rodar no hospedeiro e no `worker` ao mesmo tempo

**Quando:** ao rodar a suíte do motor no `.venv` do hospedeiro, ou qualquer coisa que importe o
TensorFlow no Windows, enquanto o `worker` calcula — rodada de `compute_risk`, suíte do
backend, medição de memória.

**Problema:** a máquina travou duas vezes no M1.5b. O WSL2 não tinha teto de memória, e os dois
lados carregando TensorFlow — mais os filhos do `worker` retendo memória entre tarefas —
esgotaram a RAM do hospedeiro inteiro. Desde então o WSL está limitado a **8 GB** por
`.wslconfig`, e o `worker` chegou a ~360 MiB livres nas rodadas sem `--max-tasks-per-child`.

**Faça:** um comando pesado por vez. Nunca a suíte do motor no hospedeiro durante uma rodada
no `worker`, nem a suíte do backend no `worker` durante a do motor. Antes de uma medição longa,
confira a memória livre do `worker` (`/proc/meminfo`). Processo morto por falta de memória é
parada e relato, não nova tentativa.


## `up -d --build` não recria o `worker` quando só mudou código montado

**Quando:** ao recriar o `worker` depois de um commit em `engine/` ou `backend/`, para o
processo pai do Celery carregar o código novo antes de uma medição.

**Problema:** o código do motor e do backend é **montado**, não copiado para a imagem. Se nada
que a imagem copia mudou, o `--build` produz a mesma imagem, e o compose **não recria** o
contêiner: o processo pai segue com o `runner`, o `compute.py` e o `tasks.py` antigos, e a
medição mede código velho sem avisar. E sem `--no-deps` o `up` religa as dependências —
inclusive o `beat`, que precisava ficar parado.

**Faça:** `docker compose up -d --force-recreate --no-deps worker` (com `--build` antes, se o
`Dockerfile` ou o lock mudaram), e confira o `Created` do contêiner
(`docker inspect … --format '{{.Created}}'`) contra a hora do último commit.


## Retomar o treino do Adam: construir o otimizador, depois pesos, depois variáveis por posição

**Quando:** ao salvar e restaurar uma rede Keras para continuar o treino (`fit`) em outro
processo, e a exigência for número igual ao do treino sem interrupção.

**Problema:** restaurar só os pesos e ressemear diverge em 6,1e-3. As variáveis do otimizador
são **preguiçosas** — não existem antes do primeiro passo —, então `assign` sobre elas falha
ou não há o que atribuir. E os `path` delas levam o nome automático do modelo
(`sequential_…`), que muda entre processos: casar por nome não acha nada. Errar a ordem não
levanta — produz número diferente.

**Faça:** `model.optimizer.build(model.trainable_variables)`, depois `model.set_weights(...)`,
depois `var.assign(valor)` para cada variável de `model.optimizer.variables`, **por posição**
(`zip(..., strict=True)`). No `npz`, reconstrua a ordem pelo **sufixo inteiro** da chave:
em ordem lexicográfica `o_10` vem antes de `o_2`. E reuse o mesmo objeto de modelo trocando
pesos — montar um modelo por retrato custa 4× mais.


## `npz` não é determinístico em bytes: compare desempacotando

**Quando:** ao conferir que dois retratos (ou qualquer `numpy.savez`) são iguais, ou ao pensar
em usar o hash do `payload` como identidade.

**Problema:** o `npz` é um `zip`, e o `zip` grava a hora de cada membro. Dois retratos com os
mesmos arrays saem com bytes diferentes; comparar `payload == payload` reprova o que é igual —
e hash do `payload` na unicidade duplicaria retrato a cada gravação.

**Faça:** compare com `unpack_arrays` e `np.array_equal` por chave. A identidade do retrato
mora nas colunas da `gold.model_snapshot`, nunca no hash do conteúdo.


## Contagem calculada do que foi pedido não prova o que o modelo fez

**Quando:** ao verificar "não treinou" (ou "não recalculou", "usou o cache") por um contador
gravado no manifesto.

**Problema:** no M1.5b, `reused_snapshots` é o número de retratos **passados** ao motor, e
`trained_snapshots` sai por diferença. A mutação "o modelo ignora o `restore` e treina tudo"
**não muda as contagens** — o motor devolve o mesmo número de retratos —, e o critério só
reprova porque o V-03 tem **espiões** nas chamadas de treino. E duas mutações da T3 (otimizador
casado por `path`, chaves do `npz` em `sorted`) reprovam **levantando erro de forma**, não por
número diferente: acusam, mas por um caminho que outra mutação mais sutil não seguiria.

**Faça:** para provar que algo **não** aconteceu, espione a chamada que faria acontecer. O
contador serve de manifesto, não de prova. E ao registrar uma mutação, anote **como** ela
reprova — erro ou número —, não só que reprovou.


## Mutação em `backend/config/*.py` derruba a `web`, e ela não volta sozinha

**Quando:** ao aplicar uma mutação de prova, ou qualquer edição que quebre a importação, em
`backend/config/` com o ambiente de pé — **ou em qualquer módulo que o `runserver` carrega no
começo**, como a classe de `DEFAULT_AUTHENTICATION_CLASSES` (medido na mutação 26 do M2.1a, em
`apps/accounts/authentication.py`).

**Problema:** a `web` roda o `runserver` com recarga automática. A edição quebrada derruba o
processo, e o contêiner não se recupera quando o arquivo é revertido — a recarga não tem mais
quem a faça. Os critérios seguintes que dependem da `web` reprovam por outra causa, e a
mutação parece ter morto mais do que devia. **O `docker compose ps` continua dizendo
`healthy`** por um tempo, enquanto o proxy do Vite já responde 502.

**Faça:** depois de reverter uma mutação que quebre import, não confie no `ps`: peça
`curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health` e, se não for 200,
`docker compose restart web` antes do próximo critério.


## `docker compose pause` marca o contêiner `unhealthy` por conta própria

**Quando:** ao provar que um `healthcheck` sabe reprovar congelando o processo em vez de
quebrá-lo.

**Problema:** o Docker marca contêiner pausado como `unhealthy` com **qualquer**
`healthcheck` — inclusive um que seja literalmente `true`. A prova aprova o `healthcheck`
certo e também a mutação que tira a condição que se queria provar. E, ao despausar, o
processo retoma com o relógio monotônico adiantado e pode se recuperar na hora.

**Faça:** estrague a condição que o `healthcheck` observa — pare a dependência, envelheça o
arquivo com `touch -d` — e execute o **próprio comando** do `healthcheck` (extraído do
`docker compose config`), olhando o código de saída dele, não o estado `unhealthy` do Docker.


## `chain(...)` do Celery não é instância de `celery.chain`

**Quando:** ao conferir em teste que uma função montou uma corrente do Celery.

**Problema:** `celery.chain(a, b)` devolve um `celery.canvas._chain`; `isinstance(sig,
celery.chain)` sai falso para uma corrente correta, e a "correção" natural — relaxar o teste —
o esvazia.

**Faça:** identifique pela assinatura serializada: `sig["subtask_type"] == "chain"`, e
confira os elos em `sig.tasks` — inclusive `immutable` no elo que não deve receber o retorno
do anterior.


## CSV dos dados abertos da CVM tem registro mal formado

**Quando:** ao ler os CSVs dos zips de ITR e DFP da CVM (`dados.cvm.gov.br`) — ou qualquer CSV de
dado aberto governamental — com o módulo `csv`.

**Problema:** há registros com **aspas desbalanceadas** e com **quebra de linha dentro de
campo**. O `csv` não levanta: junta linhas, ou parte uma em duas, e devolve registro com mais ou
menos campos que o cabeçalho. Com `DictReader`, o valor de uma coluna vai parar em outra, ou
vira `None`, e a conta segue calada com número errado.

**Faça:** compare o número de campos de cada registro com o do cabeçalho, **descarte** o que
difere e **conte** por membro do zip — o relatório diz quantos (`registros mal formados
descartados`). Nunca aceite em silêncio nem tente consertar. É o que `apps/fundamentals/documents.py`
faz.


## Conta da CVM se localiza por descrição sob mãe definida, nunca por código

**Quando:** ao extrair um campo — patrimônio, lucro, dívida, caixa — das demonstrações (BPA, BPP,
DRE) dos dados abertos da CVM.

**Problema:** o código não diz o que a conta é: o PL é `2.03` no plano geral, `2.07` ou `2.08`
nos bancos; o lucro é `3.11`, `3.09` ou `3.13`. E a **mesma descrição aparece em dois níveis**:
no BPP da Petrobras (DFP 2024), `2.01.04` "Empréstimos e Financiamentos" (R$ 68,8 bi, com
arrendamento) e a filha `2.01.04.01`, de mesma descrição (R$ 15,9 bi, sem). Procurar a
descrição em qualquer nível soma os dois ou pega o errado. A grafia também varia: "Atribuído a"
e "Atribuído aos", "Não" e "não".

**Faça:** localize a mãe de nível 1, **fixa** (`ST_CONTA_FIXA = S`), por descrição, e a filha
**só direta** (código da mãe mais um segmento), por descrição igual, depois de `strip()`. Zero
ou mais de uma linha → nulo, contado. Antes de acrescentar grafia à regra, **meça na fonte** que
ela existe: a spec do M3.1 chegou a listar uma que não existe nos 22 zips. Regra em
[D-122](decisoes/D-122-conta-se-localiza-pela-descricao-sob-mae-fixa.md).


## A quantidade de ações da CVM não tem escala

**Quando:** ao usar a `composicao_capital` dos dados abertos da CVM — capitalização, LPA, VPA.

**Problema:** `QT_ACAO_*` vem **sem escala declarada**, e ela varia por companhia: a Petrobras
informa em unidades (7.442.454.142 ON), a Vale e o Itaú em **milhares** (4.539.008 ON). Nenhuma
coluna diz qual. Tratar tudo como unidade faz a capitalização da Vale sair mil vezes menor, sem
erro. E a tabela só existe de 2020 em diante.

**Faça:** infira a escala pelo LPA que a própria companhia informa (filhas de "Lucro Básico por
Ação", no **acumulado**, sem `ESCALA_MOEDA`), aceite só dentro de uma tolerância estreita e
devolva **nulo** fora dela. Espere nulo em cerca de um terço dos documentos, quase todos por
insumo ausente ([D-124](decisoes/D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md)).


## `Index.name` do Django tem limite de 30 caracteres

**Quando:** ao declarar `models.Index(..., name=...)` num modelo, sobretudo com nome derivado da
tabela.

**Problema:** nome com mais de 30 caracteres reprova no `manage.py check` com `models.E034` — e o
`makemigrations`, que roda as mesmas verificações. O limite é só do `Index`: o `UniqueConstraint` do mesmo
modelo, `fundamental_indicator_asset_calculated_at`, tem 41 e passa, então copiar o padrão de
nome da restrição para o índice quebra.

**Faça:** abrevie o nome do índice (`fund_indicator_asset_recent`) e declare o nome **no plano**,
já dentro do limite, para a tarefa não descobrir no `check`.


## Conteúdo literal do plano sai do `ruff format` com outra quebra de linha

**Quando:** ao verificar, por `grep` ou comparação de texto, que um trecho literal do plano entrou
no código — registro de tarefa, entrada do Beat, lista de constantes.

**Problema:** o critério de aceite roda `ruff format --check`, e o formatador quebra a linha
longa do literal. No M3.1, `importar_fundamentos = app.task(name="...")(_importar_fundamentos)`
tinha uma linha no plano e três no código; no M1.5, o literal do Beat também foi reformatado. Um
`grep` pela linha do plano não acha nada, e parece que o contrato não foi cumprido — ou, numa
varredura negativa, aprova vazio.

**Faça:** procure por **conteúdo**, não por linha: o nome registrado, a chave, o valor — ou compare
a árvore sintática. E escreva no plano que o literal é contrato de conteúdo, sujeito ao
formatador.


## Cenário de teste que não isola o eixo deixa a mutação passar

**Quando:** ao escrever o teste de um filtro ou de uma regra que vem numa cadeia ordenada — "a
primeira que casa decide" —, e ao medir a mutação que o tira.

**Problema:** no M3.1, a mutação 35 (tirar o filtro de ticker **ativo** da classe) **passava**. O
teste punha um ticker inativo numa classe **sem ticker ativo**, e a regra seguinte da cadeia
(`missing_class_price`) dava o mesmo resultado com ou sem o filtro. O teste existia, estava
verde, e não observava o filtro.

**Faça:** monte o cenário em que **só** o eixo testado muda o resultado — aqui, um código antigo
inativo **na mesma classe** de um ticker ativo, que sem o filtro vira `ambiguous_class`. Pergunte "que
outra regra daria esta mesma saída?" antes de dar o teste por bom, e aplique a mutação de verdade
([Teste de reprovação que nunca foi aplicado não é teste](#teste-de-reprovação-que-nunca-foi-aplicado-não-é-teste)).


## O worktree não é o que o contêiner monta

**Quando:** ao implementar num `git worktree` (em `.claude/worktrees/`) e rodar a suíte "no
`worker`", como o PROCESSO manda.

**Problema:** o `compose.yaml` monta `./backend` e `./engine` do diretório em que o `docker
compose up` rodou, o checkout principal. `docker compose exec worker pytest` roda o código
**do checkout principal**, não o do worktree: o teste novo "não existe", ou pior, a suíte passa
sobre o código velho. O worktree também não tem `.env`, e `docker compose` dentro dele reprova na
interpolação.

**Faça:** do checkout principal, rode um contêiner avulso com o worktree montado por cima:
`MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v "<worktree>/backend:/repo/backend" -v
"<worktree>/engine:/repo/engine" worker sh -c "python -m pytest ..."`. Ele usa o mesmo banco do
serviço; duas suítes ao mesmo tempo disputam o banco de teste, então rode uma de cada vez. Para
`docker compose config` no worktree, passe `--env-file` apontando para o `.env` do principal.


## A contagem da medição tem de usar a identidade que a spec decidiu

**Quando:** ao medir a fonte para a spec e escrever o número que a execução real vai conferir.

**Problema:** a spec do M3.2 mediu **80.842** comunicados e a carga real gravou **80.900**. A
diferença não era da fonte: a medição contou pares (protocolo, versão) distintos, e a spec
decidiu que a identidade é o link ([D-131](decisoes/D-131-documento-do-ipe-se-identifica-pelo-link.md)).
Os 58 pares repetidos com links diferentes, que a própria spec cita, somam uma linha cada. A
diferença só se explicou porque o número esperado era "perto de", e a consulta por par devolveu
exatamente 80.842.

**Faça:** conte a medição pela mesma chave que o requisito usa, e registre a consulta junto do
número. Quando a execução divergir, recalcule pelas duas chaves antes de supor que a fonte mudou.

## O `flush` do `transaction=True` não vê as tabelas com esquema no `db_table`

**Quando:** ao escrever o primeiro teste `transaction=True` (duas conexões, trava, corrida) em
qualquer app.

**Problema:** o `flush` que o pytest-django roda no fim lista as tabelas por
`connection.introspection.django_table_names(only_existing=True)`, que olha o `search_path` —
e só acha **cinco** tabelas do `public` (medido em 2026-09-27). Duas consequências, as duas
silenciosas até o primeiro teste desse tipo (o do M2.1a):

1. **O `TRUNCATE` falha**: `cannot truncate a table referenced in a foreign key constraint —
   Table "user_user_permissions" references "auth_permission"`. A tabela de junção mora em
   `core`, o `flush` não a vê, e o `TRUNCATE` de `auth_permission` sem `CASCADE` é recusado.
2. **O que o teste gravou em `core`, `bronze`, `silver` e `gold` fica** para os testes
   seguintes: o `flush` não apaga — e, pelo mesmo motivo, não apaga a `ruvor` nem o `IBOV`.

**Faça:** declare `available_apps` na marca (`pytest.mark.django_db(transaction=True,
available_apps=[...])`): com ele, o Django usa `TRUNCATE ... CASCADE`. E limpe o que o teste
gravou numa fixture **de módulo** que desmonta depois do último `flush` — o molde é
`restaura_dados_de_migracao` em `backend/tests/accounts/conftest.py`. Uma fixture de função
pedida pelo teste desmonta **antes** do `flush` do `_django_db_helper`.

## `remove_constraint` do Django não acha índice em esquema que não seja o `public`

**Quando:** ao remover, em teste ou migration, uma restrição que o Django implementa como
índice — `UniqueConstraint` com expressão (`Lower("email")`), com condição, ou `Index` — numa
tabela com esquema no `db_table`.

**Problema:** o Django emite `DROP INDEX IF EXISTS "nome"`, sem esquema. O índice mora no
esquema da tabela (`core`), o `search_path` é `public`, e o `IF EXISTS` faz o comando passar
**em silêncio** sem remover nada. O teste que dependia da remoção falhou com a própria restrição
(`duplicate key value violates unique constraint "user_email_lower_uniq"`); a volta de uma
migration com `AddConstraint` passaria sem erro e deixaria o índice no banco.

**Faça:** remova com SQL qualificado — `DROP INDEX core.user_email_lower_uniq` — e, na volta de
migration, confira no `pg_indexes` que o índice saiu.

## O `flush` do Django não enxerga tabela com esquema no `db_table`, e sem `available_apps` nem roda

**Quando:** ao escrever o primeiro teste `transaction=True` (ou `TransactionTestCase`) num
projeto cujas tabelas declaram o esquema no `db_table` (`'gold"."risk_run'`), como todas as
deste.

**Problema:** o pytest-django roda o `flush` do Django na saída de cada teste `transaction=True`,
e a premissa natural — "o banco sai vazio, basta recriar os dados de migration" — é falsa aqui.
A introspecção do `flush` só enxerga as tabelas do `public` (`auth`, `contenttypes`); as de
`core`, `bronze`, `silver` e `gold` ficam de fora. E o `TRUNCATE` que ele emite **sem
`CASCADE`** falha por FK de `core.user_groups`: todo teste `transaction=True` dá ERROR na
desmontagem, e nada é apagado. O M1.6a aprovou o plano com essa premissa e só a mediu na T6.

**Faça:** use a marca e a fixture de `backend/tests/api/migracao.py` — `TRANSACIONAL`
(`django_db(transaction=True, available_apps=list(settings.INSTALLED_APPS))`: com
`available_apps`, o Django trunca com `CASCADE` e o `flush` passa) e `banco_limpo` (trunca toda
tabela dos quatro esquemas, pela lista de `pg_tables`, com `RESTART IDENTITY CASCADE`, e recria a
organização e o `IBOV`). **Todo** teste `transaction=True` usa as duas, pedindo a fixture por
`usefixtures`. A guarda é o `tests/test_organizacao.py` na suíte inteira.

**O M2.1a achou o mesmo** (verbete acima) e resolveu por uma fixture de **módulo** que
restaura depois do último `flush`; o M1.6a, por uma de função que limpa **antes** dele. As duas
convivem na suíte — cada uma nos testes da sua frente.


## Num teste `db` comum, o `on_commit` só roda quando a captura termina

**Quando:** ao testar código que faz algo no `transaction.on_commit` — enfileirar depois do
commit, ler o estado confirmado — e a ordem entre o commit e o efeito é o que se quer provar.

**Problema:** o teste `django_db` comum roda inteiro dentro de um `atomic`; o `atomic` do
código sob teste vira ponto de salvamento, e não há commit. Com
`django_capture_on_commit_callbacks(execute=True)`, os callbacks rodam **ao sair do bloco da
captura** — depois de a função devolver. Duas coisas ficam invisíveis: uma escrita feita
**depois** do `atomic` do código ainda está lá quando o callback roda (a mutação "grava a ligação
fora da transação" passa), e uma resposta montada depois do `atomic` não vê o que o callback
gravaria (a resposta 202 com o pedido `failed` do broker).

**Faça:** para provar ordem entre commit e efeito, use `transaction=True` — o commit é de
verdade, e o `on_commit` roda na saída do `atomic` do próprio código. No `db` comum, a captura
serve para "o callback foi registrado, com estes argumentos" e para "sem `execute=True`, nada
saiu". E no projeto, `transaction=True` exige `TRANSACIONAL` e `banco_limpo` (ver acima).


## Especificidade na folha de componentes: `:where` baixa a regra, e `flex` na regra base quebra conteúdo

**Quando:** ao mexer em `brand/ruvor/components.css` — uma regra que vale "dentro de" um contexto
(a barra, o bloco de código) ou um arranjo que só alguns usos precisam (ícone ao lado do rótulo).

**Problema:** duas armadilhas, as duas do M1.6a. **`:where(...)` zera a especificidade do que está
dentro dele**: pôr a regra do anel sobre fundo escuro sob `:where(.ruvor-topbar, .ruvor-code)
:focus-visible`, para não anular o recuo do link da barra, baixou-a a (0,1,0), e um botão ou
campo dentro da barra passou a ganhar o anel claro do componente — 1,98:1 sobre a barra.
**`display: flex` com `gap` na regra base** de botão, dica, erro de campo e `callout`, para
alinhar o ícone, fez de cada pedaço de texto e de cada `<b>` um item separado pelo `gap`, e o
`text-align` deixou de valer — no uso sem ícone, que é o dos mockups.

**Faça:** resolva conflito de cascata pela **especificidade explícita e pela ordem** — a regra
geral depois dos componentes, na mesma especificidade deles, e a exceção com um seletor a mais
—, e deixe um teste conferindo a ordem e as especificidades. O arranjo que só existe com ícone
vai sob `:has(> .ruvor-glyph)`, e o conteúdo ao lado do ícone num só filho. Confira na vitrine o
caso **sem** o elemento opcional, não só o com.


## Duas suítes no mesmo `worker` usam o mesmo banco de teste

**Quando:** ao rodar a suíte do backend enquanto outra roda — uma mutação e a suíte, dois agentes
em trilhas paralelas, duas rodadas "para ganhar tempo".

**Problema:** toda execução do `pytest` no `worker` usa o mesmo banco de teste, `test_ruvor`,
no mesmo Postgres. A segunda cria ou apaga o banco da primeira, e os testes `transaction=True`
truncam as tabelas de todo mundo. O resultado são falhas que parecem defeito do código — e uma
mutação pode "reprovar" pelo motivo errado, ou uma suíte verde passar por acaso.

**Faça:** uma suíte do backend por vez **em cada banco de teste**: o `worker` e o contêiner avulso
usam o mesmo `test_ruvor` se nada mudar (ver
[O worktree não é o que o contêiner monta](#o-worktree-não-é-o-que-o-contêiner-monta)). Para rodar
duas ao mesmo tempo, dê à segunda um banco de teste próprio pelo `RUVOR_DB_NAME` — ver
[Duas suítes ao mesmo tempo](#duas-suítes-ao-mesmo-tempo-banco-de-teste-próprio-pelo-ruvor_db_name).
Na T13, as mutações rodam em série, e a suíte inteira duas vezes seguidas, depois delas.

## O Vite recusa o `Host` de outro contêiner: a automação entra na rede do próprio `frontend`

**Quando:** ao rodar um navegador automatizado (Playwright) ou qualquer cliente de fora contra o
servidor de desenvolvimento do Vite, a partir de outro contêiner.

**Problema:** `http://frontend:5173/` responde **403** "Blocked request. This host ("frontend") is not
allowed" — o Vite só aceita `localhost` e IP sem configurar `server.allowedHosts`. Medido no M1.6b.

**Faça:** rode o contêiner da automação **na rede do próprio `frontend`** e use `localhost:5173`:
`MSYS_NO_PATHCONV=1 docker run --network "container:$(docker compose ps -q frontend)" … ` (o roteiro
`frontend/e2e/capturas.mjs` roda assim). Não mude o `vite.config.ts` para isso.

## O uPlot põe `uplot` e `u-hz` no mesmo elemento: seletor de descendente não casa

**Quando:** ao sobrepor as cores fixas da folha do uPlot (`.u-select`, as linhas do cursor) com
tokens.

**Problema:** o raiz do gráfico tem as classes `uplot` **e** `u-hz`/`u-vt` juntas
(`placeDiv(UPLOT)` + `addClass(root, ORI_HZ)`); `.uplot .u-hz .u-cursor-x` nunca casa, a regra fica
morta e a linha sai `#607D8B` no tema escuro. Um teste que só confere se a regra **está escrita**
aprova o seletor morto.

**Faça:** seletor composto, `.uplot.u-hz .u-cursor-x`, e um teste que monte no jsdom a árvore do uPlot
e confira com `element.matches` (`frontend/tests/graficos.test.tsx`).

## Importar o uPlot no jsdom quebra: ele chama `matchMedia` no import

**Quando:** um teste do frontend renderiza qualquer coisa que, direta ou indiretamente, importa o
`uplot` — inclusive o `App`, que chega nele pela tela do ativo.

**Problema:** o jsdom não tem `matchMedia` nem canvas; o import cai com `TypeError: matchMedia is not a
function` antes de o teste começar, em suítes que nem falam de gráfico.

**Faça:** `vi.mock("uplot", () => ({ default: class {} }))` nas suítes que importam a aplicação, e um
duplo completo onde o gráfico é o assunto. O desenho de verdade se prova pelas capturas da execução
real.

## Supressão do Biome em JSX depende de onde fica

**Quando:** ao suprimir uma regra do Biome num elemento JSX (`useSemanticElements`,
`noNoninteractiveElementToInteractiveRole`).

**Problema:** o comentário no lugar errado não tem efeito, e o lint segue reprovando — ou a supressão
fica sobrando e o Biome avisa "suppression unnecessary". Medido no M1.6b: `useSemanticElements` pede
`{/* biome-ignore … */}` **antes do elemento**; `noNoninteractiveElementToInteractiveRole` só vale **na
linha do atributo `role`**.

**Faça:** ponha a supressão, rode `npm run lint`, e confira que ela suprime algo; a varredura de texto em
JSX (`jsx-texto.test.ts`) já ignora esses comentários.

## `StrictMode` dobra as requisições em desenvolvimento

**Quando:** ao medir quantas vezes, ou em quanto tempo, a tela pede a API no servidor de
desenvolvimento.

**Problema:** o `main.tsx` usa `<StrictMode>`, e em desenvolvimento o React roda cada efeito duas vezes:
a tela do ativo faz dez pedidos a `/api/v1/`, não cinco. Quem lê o `PerformanceResourceTiming` sem saber
disso conclui que o custo da API é o dobro.

**Faça:** diga no relato que a medida é de desenvolvimento, ou meça sobre o `vite build` servido.

## `docker compose start` reaproveita a configuração antiga do contêiner

**Quando:** ao religar um serviço parado (`docker compose stop beat` na execução real, e `start` no fim)
depois que o `compose.yaml` ganhou variável nova.

**Problema:** o `start` sobe o contêiner **como ele foi criado**, sem a variável acrescentada depois. No
fecho do M1.6b, o `beat` — criado antes da fase 1 do M2.1a — não subiu: `ImproperlyConfigured:
variavel de ambiente obrigatoria ausente: RUVOR_CACHE_URL`, e ficou parado sem ninguém notar.

**Faça:** religue com `docker compose up -d --no-deps <serviço>`, que recria o contêiner se a
configuração mudou, e confira `docker compose ps` e o log depois.

## A classe de autenticação padrão do DRF é importada no meio do import do DRF

**Quando:** ao escrever a classe que vai em `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`,
ou qualquer módulo que ela importe no topo.

**Problema:** `rest_framework/views.py:18` importa `rest_framework.schemas`, e
`schemas/__init__.py:32` avalia `DEFAULT_AUTHENTICATION_CLASSES` num argumento padrão — antes de
`views.py` definir `set_rollback`. Se a classe importar, no topo, algo que importe
`rest_framework.views` (o `apps/api/errors.py` faz isso), o primeiro import do DRF no processo
quebra com `ImportError: cannot import name 'set_rollback' from partially initialized module
'rest_framework.views'`. Nos testes, cai já na coleta; na `web`, derruba o `runserver`.

**Faça:** o que a classe precisar de `apps.api` entra **dentro do método**, com um comentário
dizendo por quê (`apps/accounts/authentication.py`). Um teste em subprocesso —
`django.setup(); import rest_framework.views` como primeiro import do DRF — guarda a regra.


## O `EXCEPTION_HANDLER` próprio perde os cabeçalhos do 401 e do 429

**Quando:** ao mapear `NotAuthenticated` ou `Throttled` num tratador de exceção do DRF que
substitui o padrão (`apps/api/errors.py`).

**Problema:** a `APIView` põe o `WWW-Authenticate` em `exc.auth_header`, e o `Throttled` guarda
a espera em `exc.wait`; quem copia os dois para a resposta é o `exception_handler` padrão do
DRF. O tratador próprio que só devolve `Response(corpo, status=…)` responde 401 sem
`WWW-Authenticate` e 429 sem `Retry-After`. E o 401 fixo por `isinstance(exc,
NotAuthenticated)` esconde o rebaixamento: sem autenticador que dê cabeçalho, a `APIView` muda
`exc.status_code` para 403, e o teste que devia pegar isso passa. Os stubs do DRF também não
declaram `wait` nem `auth_header` — o `mypy` recusa o acesso direto.

**Faça:** copie os cabeçalhos no tratador (`getattr(exc, "auth_header", None)`,
`getattr(exc, "wait", None)`) e tire o status de `exc.status_code`.


## O `ScopedRateThrottle` conta por usuário, não por IP

**Quando:** ao limitar tentativas "por IP" numa rota que aceita, ou exige, quem está logado.

**Problema:** o `get_cache_key` do `ScopedRateThrottle` (`throttling.py:235-250`) usa
`request.user.pk` quando há login, e o IP só para anônimo. Numa rota como `auth/password`, que
exige login, o limite vira por usuário, em silêncio. E a taxa (`THROTTLE_RATES`) é lida no
import da classe (`throttling.py:66`): mudar `REST_FRAMEWORK` no teste não muda nada.

**Faça:** classe própria sobre `SimpleRateThrottle` com `get_cache_key` sempre por
`self.get_ident(request)` (`AuthRateThrottle`, em `apps/accounts/views.py`). No teste, baixe a
taxa com `monkeypatch.setattr(Classe, "THROTTLE_RATES", …)`, e prove o eixo com dois usuários
no mesmo IP — é o caso que separa IP de usuário.


## O Windows reserva faixas de porta, e o contêiner não sobe

**Quando:** ao rodar `docker compose up` no Windows e um serviço falhar com
`ports are not available: exposing port TCP 0.0.0.0:<porta> … bind: Foi feita uma tentativa de
acesso a um soquete de uma maneira que é proibida pelas permissões de acesso`.

**Problema:** o Hyper-V e o WinNAT reservam faixas de porta dinâmicas, que mudam entre
reinicializações. Em 2026-09-28 a faixa 56319–57018 estava reservada e engolia a porta do Redis
do `.env.example` (`RUVOR_PORT_REDIS=56379`). Nada no repositório mudou; a máquina mudou. Na mesma
noite, depois de reiniciar, foi a vez da 55415–55514, com a do PostgreSQL (`55432`).

**Faça:** `netsh interface ipv4 show excludedportrange protocol=tcp` mostra as faixas. Troque a
porta publicada no `.env` local (as portas `RUVOR_PORT_*` existem para isso), para uma fora
delas — a porta interna dos contêineres não muda.


## Depois de dependência nova na `main`, a imagem velha dá erro de `mypy` que não é seu

**Quando:** ao voltar a trabalhar depois de mesclar a `main`, com contêineres criados antes
dela, e o `mypy` do `worker` acusar `module is installed, but missing library stubs or py.typed
marker` em código que você não tocou.

**Problema:** as dependências vivem na imagem, não no código montado. O M1.6a trouxe os
`djangorestframework-stubs`; a imagem de antes dele não os tem, e o `mypy` reprova dezenas de
linhas de `apps/api/`.

**Faça:** `docker compose build web worker` e
`docker compose up -d --wait --force-recreate web worker beat` antes da primeira verificação.


## O `--fail-on-warn` do drf-spectacular reprova enum com o mesmo nome de campo

**Quando:** ao gerar o esquema OpenAPI com `manage.py spectacular --validate --fail-on-warn` e
aparecer `enum naming encountered a non-optimally resolvable collision for fields named "kind"`.

**Problema:** o gerador nomeia o enum pelo nome do campo (`KindEnum`). Dois campos `kind` com
escolhas diferentes — `Asset.Kind` e `CorporateEvent.Kind`, e o mesmo com `status` — colidem, e
ele resolve com sufixo de hash (`KindF56Enum`) e um aviso. O aviso basta para o `--fail-on-warn`
reprovar.

**Faça:** dê nome a cada conjunto em `SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"]`, pelo caminho
da classe de escolhas (`"AssetKindEnum": "apps.assets.models.Asset.Kind"`).

**Mas não suponha a colisão sem medir:** com os dois `kind` já nomeados, um terceiro campo `kind`
(`ChoiceField` em `ReportOut`, M4.1) **não** avisou — o enum nasceu `ReportOutKindEnum` e o
`--fail-on-warn` saiu com 0. A spec do M4.1 supôs o contrário e a mutação que dependia disso não
reprovou (errata na T5). Rode o `spectacular --validate --fail-on-warn` com o campo novo antes de
escrever que ele colide.


## A contagem de avisos do drf-spectacular é de classe e sobrevive entre testes

**Quando:** ao testar o esquema com `call_command("spectacular", "--fail-on-warn")` na suíte.

**Problema:** `GENERATOR_STATS` acumula avisos e erros no processo inteiro, e o comando não a
zera antes de gerar. Um aviso emitido por outro teste no mesmo processo reprovaria este.

**Faça:** `GENERATOR_STATS.reset()` logo antes do `call_command`.

## `git add backend` falha pelo `backend/nul`

**Quando:** ao fazer `git add` de um diretório inteiro do backend (`git add backend`, `git add -A`).

**Problema:** existe um `backend/nul` não rastreado — `nul` é nome reservado do Windows, criado por algum redirecionamento
para `nul` num shell que o tratou como arquivo. O `git add` do diretório para com `error: open("backend/nul"): No such file
or directory` e `fatal: adding files failed`, e nada é adicionado.

**Faça:** adicione pelos caminhos (`git add backend/apps/api backend/tests/api …`). Não tente apagar o `nul` pelo Explorer;
se precisar, `rm //?/E:/…/backend/nul` pelo prefixo de caminho longo.

## A medida da taxa conta do lado do cliente, e o `StrictMode` inflaciona

**Quando:** ao medir quantos pedidos a tela faz até a taxa responder 429.

**Problema:** o roteiro conta os pedidos pela rede do navegador; em desenvolvimento o `StrictMode` faz cada rota duas vezes e
aborta parte delas, e esses abortados entram na conta. No M1.6c, 84 pedidos contados para 81 respondidos antes do primeiro
429 — com o limite em 60.

**Faça:** registre os dois números (o do cliente e as respostas 200 antes do 429) e diga que a medida é de
desenvolvimento; para medir o servidor, conte no servidor ou meça sobre o `vite build`.

## A região viva repete o texto do painel, e o `getByText` acha dois

**Quando:** ao pôr uma região `aria-live` só com o andamento (fora da vista, `ruvor-sr-only`) numa seção que já mostra o
mesmo texto num painel visível.

**Problema:** `within(section()).getByText(t)` reprova com `Found multiple elements with the text`: o texto está no
painel e na região. No M1.6d, seis testes antigos de `risco.test.tsx` quebraram assim.

**Faça:** busque o texto fora da região — `getAllByText(t).filter((el) => el.closest("[aria-live]") === null)`, com
exatamente um resultado (o ajudante `inBody` de `risco.test.tsx`) —, e confira a região à parte, pelo seletor
`[aria-live]` e pelo `textContent` exato: sozinho, o filtro aceita cópias a mais dentro da região.

## `operationId` de lista e item colide no drf-spectacular

**Quando:** ao pôr no esquema duas `APIView` (não `ViewSet`) em `recurso` e `recurso/{id}`, as duas
com `GET` — `assets` e `assets/{ticker}` no M4.2, `reports` e `reports/{id}` no M4.1.

**Problema:** o `get_operation_id` do `AutoSchema` tira do caminho os parâmetros (`{id}`) e só chama a
ação de `list` quando reconhece a view como lista; uma `APIView` comum sai como `retrieve` nas duas.
Os dois `operationId` ficam iguais, o gerador avisa `operationId "…" has collisions` e resolve com
sufixo numérico — e o aviso basta para o `--fail-on-warn` reprovar.

**Faça:** fixe o `operation_id` da lista no `extend_schema` do `get` dela
(`operation_id="v1_assets_search"`, `"v1_reports_list"`), com um comentário do porquê. A mutação
que o tira é pega pelo teste que roda o `spectacular --validate --fail-on-warn`.


## O `JSONRenderer` devolve os mesmos bytes, e a comparação de bytes fica cega à troca por `Response`

**Quando:** ao testar que uma rota devolve bytes guardados sem transformação — um `HttpResponse` do
Django, e não um `Response` do DRF —, comparando o corpo da resposta com os bytes guardados.

**Problema:** se os bytes foram gerados com `json.dumps(..., ensure_ascii=False, separators=(",",
":"))`, o `JSONRenderer` do DRF 3.18.1, sobre o `json.loads` deles, devolve **os mesmos bytes**: um
`Response(json.loads(content))` passaria no teste. A única diferença é que o renderizador escapa
U+2028 e U+2029 (`rest_framework/renderers.py:106`).

**Faça:** ponha no dado do teste um U+2028 (no M4.1, o `name` da organização, que vai para o
conteúdo) e confira que ele está nos bytes da resposta; confira também que a resposta não tem o
atributo `data`, que só o `Response` tem.


## Editor converte o escape `\u2028` no caractere, e o `ruff` recusa

**Quando:** ao escrever, num teste Python, uma string com U+2028 ou U+2029 pelo escape `"\u2028"`.

**Problema:** a ferramenta de edição gravou o caractere literal no lugar do escape; o arquivo parece
certo na tela, e o `ruff check` reprova com `RUF001` (caractere ambíguo na string).

**Faça:** escreva `chr(0x2028)` numa constante com nome (`U2028 = chr(0x2028)`, em
`tests/accounts/test_report_rotas.py`), e não o escape dentro da string.


## `TRUNCATE` na transação do teste falha com `pending trigger events`

**Quando:** ao provar, num teste `django_db` comum, que um `TRUNCATE` passa por uma tabela — no
M4.1, que o gatilho `report_so_cresce` de `core.report` não o barra —, depois de inserir linhas na
mesma transação.

**Problema:** as FKs que o Django cria são `DEFERRABLE INITIALLY DEFERRED`. A inserção deixa a
checagem delas pendente até o fim da transação do teste, e o PostgreSQL recusa o `TRUNCATE` com
`pending trigger events` — o erro não é do gatilho da
tabela, e o teste reprova pelo motivo errado. O `banco_limpo` e o `psql` não veem isso: truncam em
transação própria.

**Faça:** `cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")` antes do `TRUNCATE`, no mesmo cursor
(o molde está em `tests/accounts/test_report_modelo.py`).


## Data no corpo da API: pelo serializador sai em `-03:00`, crua no dict sai em `Z`

**Quando:** ao montar um corpo de resposta com um instante, e comparar com outra rota da API.

**Problema:** o `DateTimeField` do DRF converte para o `TIME_ZONE` do projeto
(`America/Sao_Paulo`, `-03:00`); um `datetime` posto cru no dict passa pelo `JSONEncoder` do DRF
(`rest_framework/utils/encoders.py`), que o escreve como veio do banco, em UTC, com `Z`. O
`api_key_body` do M4.2 sai em `Z`; o `report_body` do M4.1, que o `/risk` e a spec tomaram por
molde, sai em `-03:00` (`timezone.localtime(...).isoformat()`). As duas formas convivem na API.

**Faça:** decida o fuso na spec e confira contra a rota que é o molde — nos testes, compare com o
texto que o serializador daria (`_iso` de `tests/api/test_risco.py`), e não com `str(datetime)`.


## Duas suítes ao mesmo tempo: banco de teste próprio pelo `RUVOR_DB_NAME`

**Quando:** ao rodar a suíte do backend enquanto outra sessão roda a dela — duas frentes na mesma
máquina, ou um worktree e o checkout principal.

**Problema:** sem nada mudar, as duas usam o `test_ruvor` e se atropelam (ver
[Duas suítes no mesmo `worker` usam o mesmo banco de teste](#duas-suítes-no-mesmo-worker-usam-o-mesmo-banco-de-teste)).
O nome do banco de teste é `test_` mais o `NAME` do banco, que vem do `RUVOR_DB_NAME`. O cache não
é problema: nos testes é `LocMemCache` (`config/settings_test.py:33`), um por processo. O custo é a
memória: medido no M4.1, cada suíte usa uns 3,2 GiB, e o WSL tinha 5,8 GiB — duas ao mesmo tempo
podem derrubar uma por falta de memória.

**Faça:** rode a segunda num contêiner avulso com `-e RUVOR_DB_NAME=<outro>` — medido no M4.1:
`docker compose run --rm --no-deps … -e RUVOR_DB_NAME=ruvor_m41 worker …` usa o
`test_ruvor_m41`, separado do `test_ruvor` (conferido com `connection.creation._get_test_db_name()`
e no `pg_database`). Rode do diretório que tem o `.env` e monte o worktree por `-v`; o
`docker compose exec worker` monta o checkout principal.


## O `worker` roda o código de quando subiu, mesmo com o arquivo novo montado

**Quando:** na execução real de uma tarefa que mudou código de `apps/*/tasks.py` ou de algo que a
tarefa importa, com o `worker` de pé desde antes do commit.

**Problema:** o código está montado no contêiner, mas o Celery não recarrega. O processo pai
importa os módulos das tarefas na partida, e os filhos do prefork nascem por `fork` dele. O
`--max-tasks-per-child=5` troca o filho, mas o filho novo herda o mesmo código antigo. Na T16 do
M2.1a, o `POST /risk` logado gravou o autor no pedido, porque a `web` recarrega sozinha. A
`risk_run` aberta pelo `worker` nasceu com `requested_by_id` nulo. A suíte não pega isso: ela roda
num processo novo.

**Faça:** antes da execução real, rode `docker compose restart worker` (e `beat`, se a tarefa for
agendada). Não reinicie com uma execução em andamento: o fecho não roda, e a `risk_run` fica
`running`. Espere ela fechar.


## O `worker` morto: a tarefa em execução se perde, e as reservadas voltam só depois de uma hora

**Quando:** ao derrubar o `worker` (`docker compose kill worker`, falta de memória) com um leque de risco em curso, ou ao
esperar que as tarefas dele "voltem sozinhas".

**Problema:** sem `acks_late`, o Celery confirma a tarefa ao começar a executá-la: a que estava rodando no `kill` se
perde. As reservadas pelo pré-carregamento (até `concurrency × 4`) só voltam à fila depois do `visibility_timeout` do
transporte Redis, ~3600 s. Na execução real do M1.5c, as de `garchnet` e `caviar` se perderam e as de `lstm` e `gru`
voltaram 1 h depois; o `chord` nunca completou, e o fecho não rodou.

**Faça:** não espere a execução fechar sozinha: a varredura (`close_stale_runs`, ou o primeiro elo da `rotina_diaria`)
a fecha pela regra depois de `RUVOR_RISK_STALE_AFTER_MIN`. As que voltarem depois rodam sobre execução fechada e
descartam (`modelo … descartado` no log). Para medir isso, reduza o prazo no `.env` e aplique com `docker compose up -d`.


## `FOR UPDATE OF` não aceita o esquema que o `db_table` carrega

**Quando:** ao travar linha com `select_for_update(of=...)` num modelo cujo `db_table` tem o esquema
dentro (`'gold"."risk_run'`, `'core"."report'`) — toda tabela fora do `public` neste repositório.

**Problema:** o Django monta o `OF` com o alias da tabela, que é o `db_table` inteiro, e gera
`FOR UPDATE OF "gold"."risk_run"`. O PostgreSQL recusa com `ProgrammingError: FOR UPDATE must
specify unqualified relation names` (reproduzido no `ruvor-web-1`, Django 6.1.1, na revisão 2 da spec
do M2.2a; `of=("self",)` e `of=("asset",)` falham igual). `select_for_update()` sem `of` funciona,
mas trava **todas** as tabelas da junção — e o gerente com escopo por organização junta as tabelas
do caminho do `organization_field`.

**Faça:** não use `of=`. Para serializar escritas sobre uma linha, use a trava consultiva na forma de
dois inteiros, `pg_advisory_xact_lock(classe, id)` (o molde de `apps/api/ondemand.py`), e releia a
linha depois de pegar a trava. Se precisar mesmo de trava de linha, `select_for_update()` sem `of`
numa consulta **sem junção**.

## Filtrar por campo de `annotate` atrás de uma função tipada `QuerySet[Modelo]` reprova no `mypy`

**Quando:** uma função auxiliar anota o queryset (`_with_has_risk`, `_with_has_prices` em `apps/api/views.py`) e
devolve `QuerySet[Asset]`, e quem a chama filtra pelo campo anotado (`found.filter(has_risk=...)`).

**Problema:** o plugin dos `django-stubs` só conhece os campos do modelo. A anotação existe em tempo de execução, mas o
tipo de retorno `QuerySet[Asset]` a apaga, e o `mypy` estrito acusa o `filter` com um erro `misc` sobre o campo. Na T2
do M1.7 a assinatura era literal do plano, e não dava para mudá-la.

**Faça:** ponha `# type: ignore[misc]` **só nessa linha**, com um comentário dizendo que o campo vem da anotação (o
molde está em `AssetListView.get`, `backend/apps/api/views.py`). Não alargue para `ignore_errors` no módulo, nem tire o tipo de retorno da função. Se a
assinatura não for contrato, prefira anotar e filtrar na mesma função.

## O efeito de montagem pode correr depois de o título aparecer

**Quando:** num teste do Vitest com a Testing Library, ao contar pedidos (`vi.mocked(fetch).mock.calls`) logo depois
de um `findBy…` de algo que a montagem desenha, como o título da tela "ativo não encontrado".

**Problema:** o `findBy…` volta assim que o elemento aparece, e o pedido que sai do efeito de montagem do componente de
dentro (a sugestão da caixa de página, no M1.7) pode não ter saído ainda. Contar nesse ponto vê 0 pedidos e reprova, ou
passa por acaso, conforme a ordem dos efeitos. Na T6 do M1.7, o teste do 404 de `ativo.test.tsx` contava cedo demais.

**Faça:** espere pelo efeito **visível** do pedido (`waitFor` dos atalhos da sugestão na tela) antes de contar, e
confira a contagem exata de novo no `afterEach`, com tudo assentado.

## `getByText` não acha frase com valor em reais

**Quando:** ao procurar na tela, com o Testing Library, uma frase de `textos.ts` ou `avancado.ts` montada com um valor
de `format/numbers.ts` em moeda (`R$ 100,00`).

**Problema:** o `Intl.NumberFormat` em `pt-BR` põe um espaço inseparável (U+00A0) depois do `R$`. O normalizador padrão
do Testing Library troca todo espaço do texto **da tela** por espaço comum, mas não mexe na string **procurada**, que
continua com o U+00A0: `getByText(frase)` reprova com a frase visivelmente igual. No M2.3 (T7), a prova por seção do
comportamento caiu assim.

**Faça:** compare o `textContent` cru do elemento com a frase (`expect(el.textContent).toBe(frase)`), ou normalize os
dois lados do mesmo jeito. Não troque o U+00A0 no formatador para o teste passar: ele é o que a tela mostra.

## Iniciante que devolve união de literais trava a avançada pelo `Leitura<T>`

**Quando:** ao escrever em `avancado.ts` a frase avançada de uma chave-função cuja iniciante, em `textos.ts`, devolve
um ternário de duas strings literais sem tipo de retorno declarado.

**Problema:** o TypeScript infere o retorno da iniciante como a união dos dois literais, e `Leitura<T>` (string vira
string; função fica a mesma função) obriga a avançada a devolver **os mesmos literais** — qualquer outra frase não
compila. No M2.3 (T13), quatro iniciantes de `fundamentos.*` estavam assim (`ebit_ttm`, `net_income_ttm`, `net_debt`,
`equity_parent`).

**Faça:** declare `: string` no retorno da iniciante em `textos.ts`. O texto, a aridade e o contrato de `Leitura<>`
ficam iguais; não afrouxe o `Leitura<T>`, que é o que garante a mesma assinatura nos dois níveis.

## O mockup aprovado não acompanha a emenda aprovada no portão

**Quando:** ao conferir a tela contra um mockup do M2.3, ou ao aprovar num portão uma mudança de texto que o mockup
não aplica em todas as vistas.

**Problema:** o portão pode aprovar uma frase diferente da que o mockup mostra — a emenda de uma iniciante, ou a
alternativa de uma proposta, desenhada numa vista só. O código segue a emenda, e o mockup fica com a frase antiga: no
M2.3, o `comportamento.html` e o `fundamentos.html` mostram as iniciantes anteriores às emendas, e a vista `itub4` do
`risco.html` aplica a proposta da D-64 que o portão não escolheu (vale a vista `d64`). Quem confere a tela contra o
mockup acha divergência que não é defeito — ou, pior, "corrige" a tela para a frase velha.

**Faça:** antes de conferir texto contra o mockup, leia as "Correções registradas na execução" do plano e o índice de
[`docs/mockups/README.md`](mockups/README.md), que marca o que o mockup não reflete. Ao aprovar uma emenda no portão,
registre no plano, no mesmo commit, qual vista do mockup fica para trás — ou atualize o mockup antes da implementação.

## A diferença de um ulp na soma some no passo seguinte, e a mutação da ordem sobrevive

**Quando:** ao provar que um cálculo em `float` soma numa ordem fixa (a série da carteira do M2.2a
soma as posições na ordem do ticker, para a web e o `worker` darem o mesmo índice bit a bit).

**Problema:** o plano mandava afirmar, como pré-condição, que a soma dos termos em ordem inversa
difere bit a bit da soma na ordem certa. A pré-condição passou e a mutação "somar na ordem do
`dict`" **sobreviveu**: a diferença de um ulp em `R ≈ 0,1` desaparece no `1 + R` do índice, que é o
número que o teste compara. Necessário, não suficiente.

**Faça:** afirme a pré-condição sobre o **mesmo número que o teste compara** — aqui,
`1.0 * (1 + soma_inversa) != I_2` —, e escolha os dados até ela valer (com `R ≈ −0,08`, a
diferença sobrevive). Exerça a mutação antes de confiar no teste.
