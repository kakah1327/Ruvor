# D-34 — Banco, Celery e Redis chegam no F3, não no F4

**Status:** aceita · 2026-09-02

## Contexto

A [spec do F2b](../specs/F2b-casco-da-aplicacao.md) empurrou três coisas para o F4: a tabela
de escopo põe *"Celery, Redis, fila"* no F4, e o texto repete *"Sem Celery, sem driver de
banco — entram no F4"*. Coerente com o F2b, que provava apenas que os dois processos sobem.

O F2b deixou `DATABASES` vazio de propósito, com o teste
`backend/tests/test_health.py::test_processo_nao_tem_banco` provando a ausência de banco por
acesso ativo.

Ao especificar o F3, o conflito apareceu: o [ROADMAP](../ROADMAP.md) atribui ao F3 subir
"Postgres, Redis, web e **worker**". Um worker sem Celery não tem o que executar, e um
Postgres que sobe sem ninguém conectar não prova ambiente nenhum — o que quebra na vida real
é a configuração da conexão e a ordem de subida, e as duas só aparecem quando alguém conecta.

## Decisão

**O F3 conecta o Django ao Postgres, e instala Celery e Redis.**

- Conexão real ao Postgres, **sem migrations e sem modelos**. `INSTALLED_APPS` não ganha app
  novo.
- Celery ligado ao Redis, com **uma tarefa de fumaça** (`config.tasks.ping`) — nenhuma tarefa
  de domínio.
- `test_processo_nao_tem_banco` é **removido** e substituído por um teste que prova a conexão.

## Consequências

- O F4 passa a criar migrations sobre uma conexão que já funciona. Se ele tivesse de criar
  **e** configurar, um `makemigrations` que falha não diria qual dos dois está errado.
- A suíte do backend passa a exigir um Postgres alcançável. Coerente com a
  [D-33](D-33-dia-a-dia-dentro-do-conteiner.md): a suíte roda dentro do contêiner, onde o
  Postgres existe.
- A suíte **não** passa a exigir Redis nem worker: a verificação da tarefa `ping` é comando
  sobre o conjunto, não teste da suíte. Foi escolha explícita, para que `pytest backend`
  continue rodando com o conjunto parcialmente de pé.
- O Redis ganha um quarto uso além dos três da [D-14](D-14-celery-e-redis.md) — depósito de
  resultado —, e **apenas** para que a verificação leia o retorno de `ping`. No modelo de
  produto, resultado de cálculo vai para o banco, imutável e com manifesto
  ([D-15](D-15-manifesto-de-execucao.md), [D-16](D-16-resultado-e-imutavel.md)). O M1.5 não
  deve herdar isto como padrão.
- Restringe a divisão de escopo da spec do F2b. Não revoga nada dela: o que o F2b entregou
  continua válido.

Origem: [spec F3 — Ambiente local](../specs/F3-ambiente-local.md).
