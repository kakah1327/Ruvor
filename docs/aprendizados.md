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
