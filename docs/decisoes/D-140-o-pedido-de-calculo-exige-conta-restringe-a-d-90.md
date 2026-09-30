# D-140 — O pedido de cálculo sob demanda exige conta pronta; restringe a D-90 e a D-100

**Status:** aceita · 2026-09-29 · restringe a [D-90](D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md) e a [D-100](D-100-a-api-autentica-por-sessao-do-django-com-csrf.md)

## Contexto

A D-90 abriu o `POST /api/v1/assets/{ticker}/risk` a qualquer pessoa, com uma trava por ativo, um teto
global e a expiração do pedido. As consequências da D-90 deixaram um recado: cada pedido bem-sucedido
torna o ativo coberto para sempre, e "antes de expor a rota, a hospedagem precisa decidir limite por IP
ou login". Desde o M2.1a existe login, e o RF-26 do M2.1a guarda quem pediu — mas só quando quem pede
está logado, e o pedido anônimo continuaria sem autor.

## Decisão

1. **O `POST /api/v1/assets/{ticker}/risk` exige conta pronta** (`AccountReady`, RF-29 do M2.1a):
   sem sessão, **401 `not_authenticated`**; com a senha provisória por trocar, **403
   `password_change_required`**. Decisão do dono da frente `marco1`, 2026-09-29.
2. **O `GET` da mesma rota continua `AllowAny`**, e a chave de leitura do M4.2 continua lendo só o
   `GET`: a leitura do risco é pública, como a busca e a tela do ativo.
3. **A D-100 perde um caso**: ela registra que o `POST /risk` do M1.6a "segue aberto a anônimo sem
   CSRF"; a partir daqui, anônimo recebe 401, e todo `POST /risk` aceito vem de sessão e leva o CSRF.
4. **O resto da D-90 não muda**: só para ativo nunca calculado, um pedido aberto por ativo, teto global,
   expiração, o pedido fecha com a `risk_run`.

## Consequências

- **Não há mais pedido anônimo.** Todo pedido novo tem autor, e o `requested_by` do RF-26 do M2.1a
  deixa de ser nulo em pedido novo — continua nulo nos antigos, no 202 que aproveita pedido ou execução
  existentes e na rotina diária.
- A cobertura continua crescendo sem teto por pessoa: login não é cota. A cota por usuário (PRODUTO §6,
  "limite de análises pesadas por usuário") segue aberta.
- A tela do ativo troca, para quem não entrou, o botão "Calcular o risco" por um convite a entrar.
- A PR que aplica esta decisão toca `apps/api/views.py`, a mesma view que a T14 do M2.1a (frente
  `identidade`) altera para gravar o autor: as duas se combinam na revisão, e a spec do M2.1a deixa de
  ter o caso "pedido anônimo" a testar.
- O docstring de `ComputeRequest` que o M2.1m escreve ("nulo para o pedido anonimo e para todo pedido
  anterior ao M2.1a") fica falso para pedido novo: quem mesclar por último entre o M2.1m e o M2.1b o
  ajusta.

Origem: [spec M2.1b — Telas de acesso](../specs/M2.1b-telas-de-acesso.md).
