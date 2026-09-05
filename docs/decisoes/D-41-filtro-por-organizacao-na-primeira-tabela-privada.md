# D-41 — O filtro automático por organização é obrigação da primeira tabela privada, e o usuário é exceção permanente

**Status:** aceita · 2026-09-04

## Contexto

A [D-24](D-24-organizacao-desde-a-primeira-migration.md) diz: *"o que isola não é a coluna, é
a consulta filtrar. Uma classe base aplica o filtro por organização **por padrão**, para que
esquecer deixe de ser possível."* A
[ARQUITETURA](../ARQUITETURA.md#isolamento-por-organização) repete, e é mais dura:
*"coluna sem filtro automático é teatro"* — e lista **Usuários** entre os dados privados da
organização.

O F4 é a primeira migration, e a leitura literal manda entregar a classe base ali. A revisão
adversarial da [spec do F4](../specs/F4-fundacao-de-dados.md) mediu por que isso não
funciona.

Um gerente padrão que levanta erro em consulta sem escopo colide com o ORM em pontos que o
F4 não alcança — conferido na fonte do Django 6.1:

| Onde | O que quebra |
|---|---|
| `db/models/base.py:1571` e `:1612` | `_perform_unique_checks` passa por `_default_manager` — todo `full_clean()`/`validate_unique()` levantaria |
| `db/models/fields/related_descriptors.py:680` e `:1060` | o acessor reverso é construído a partir de `_default_manager.__class__`; `org.portfolios.all()` nasceria levantando |
| `db/models/fields/related.py:1298` e `:2138` | `formfield` também passa por `_default_manager` |

E o F4 **não tem modelo concreto** — a primeira tabela privada de domínio é a carteira, no
M2.2. O bloco entregaria verde um contrato que o primeiro consumidor real não conseguiria
usar.

## Decisão

**O F4 entrega a coluna; o mecanismo do filtro é obrigação do bloco que criar a primeira
tabela privada de domínio — o M2.2.**

Não existe tabela privada nova sem o filtro automático: é obrigação do bloco que a cria, não
dívida difusa.

**O `user` é exceção permanente, não pendência.** Os backends de autenticação do Django
alcançam o modelo por `UserModel._default_manager` — dez ocorrências em
`django/contrib/auth/backends.py` —, e um gerente que recusasse consulta sem escopo quebraria
`authenticate` inteiro.

## Consequências

- **Contradiz a ARQUITETURA por escrito**, e é por isso que existe este registro. A frase
  *"coluna sem filtro automático é teatro"* continua sendo a diretriz; o que muda é **quando**
  o filtro nasce.
- A busca do usuário no login é necessariamente anterior a saber a qual organização ele
  pertence. A exceção do `user` é principiada, não conveniência — mas significa que **o M2.1
  precisa isolar listagem de usuário por outro meio**, e não pelo ORM.
- O M2.2 recebe a lista do que precisa provar, que o F4 não tinha contra o que provar:
  acessor reverso, `full_clean`, e se `Meta.base_manager_name` entra.
- **A dívida fica registrada em `ESTADO.md`**, na tabela de dívida, e é o que impede que
  "adiado" vire "esquecido".
- Se a dívida não for honrada, o defeito é exatamente o que a D-24 descreve. Este registro é
  o que permite alguém cobrar.

Origem: [spec F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md).
