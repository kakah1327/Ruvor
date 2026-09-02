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


## `DATABASES = {}` não fica vazio, e "sem banco" se prova pelo acesso

**Quando:** ao escrever teste que garante que o processo Django não tem banco configurado.

**Problema:** o Django preenche `settings.DATABASES` com um backend `dummy` no **primeiro
acesso a `connections`**, mutando o mesmo dicionário. `assert settings.DATABASES == {}` passa
ou reprova conforme a ordem dos testes — critério que depende de ordem é critério vazio.

**Faça:** prova ativa: `with pytest.raises(ImproperlyConfigured): connection.cursor()`. Se
alguém configurar um banco, o teste reprova (com `RuntimeError` do bloqueio do pytest-django,
que não é `ImproperlyConfigured`).


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
