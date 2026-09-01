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

**Problema:** a primeira spec do projeto (F2) precisou de **cinco rodadas** de revisão para
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
