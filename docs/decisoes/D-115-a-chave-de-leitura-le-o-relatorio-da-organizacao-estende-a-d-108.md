# D-115 — A chave de leitura lê o relatório da organização da dona; estende a D-108

**Status:** aceita · 2026-09-29 · frente `identidade`

## Contexto

A [D-108](D-108-a-api-aceita-chave-pessoal-de-leitura.md) deu à chave pessoal o escopo `read`, e
até o M4.1 todas as rotas que ele alcançava eram de dado público. A spec do M4.2 deixou a questão
para "o primeiro bloco que criar dado privado lido pela API" e orientou, em *Para o M2.2 e além*,
que "rota de dado privado que a chave deva ler pede escopo novo, por decisão". O relatório
([D-113](D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md)) é esse dado: é da organização que o
gerou.

## Decisão

As quatro views de relatório declaram `api_key_scope = "read"` e `AccountReady`. A chave de leitura
**lista, lê e baixa** os relatórios da organização da dona — o filtro automático
([D-112](D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)) posto pela autenticação da
chave. **Gerar continua só pela sessão**: o `POST reports` com chave cai na regra do método seguro
da D-108 → 403 `api_key_not_allowed`. Não nasce escopo novo, e as chaves que já existem passam a
ler relatório.

**Esta decisão substitui, para o relatório, a orientação do M4.2** de que dado privado lido por
chave pede escopo novo. A spec do M4.2, fechada, não se edita; é aqui que a mudança fica
registrada. Para outro dado privado, a pergunta volta a ser feita, por decisão.

## Consequências

- É o primeiro dado privado lido por chave. Uma chave vazada, até ser revogada, lê os relatórios da
  organização; valem as mitigações do M4.2 (revogar; desativar e redefinir a senha revogam tudo;
  `last_used_at`). Um escopo próprio (`reports`) isolaria isso, ao custo de as chaves atuais não
  lerem relatório.
- O relatório é da organização, não da pessoa: `admin` e `member` leem os relatórios um do outro.
- O download não é registrado: gerar fica registrado pela própria linha (`requested_by`,
  `created_at`), e quem baixou, não. Isso diverge da
  [D-104](D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md), que contava com o
  dado privado nascendo no M2.2 com registro de leitura: o relatório é dado privado anterior, lido
  sem registro, como a spec declara em *Riscos*.
- Anônimo recebe 401 `not_authenticated` nas cinco operações.

Origem: [spec M4.1 — Relatórios](../specs/M4.1-relatorios.md).
