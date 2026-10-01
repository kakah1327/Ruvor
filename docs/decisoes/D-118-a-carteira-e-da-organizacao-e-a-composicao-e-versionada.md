# D-118 — A carteira é da organização, a composição é versionada e imutável, e o valor aplicado fica fora do cálculo; a chave lê carteira — estende a D-115

**Status:** aceita com a aprovação da [spec do M2.2a](../specs/M2.2a-carteira.md) · 2026-09-30 · frente `identidade`

## Contexto

A carteira é a primeira tabela privada de domínio
([D-41](D-41-filtro-por-organizacao-na-primeira-tabela-privada.md)). O risco de uma carteira
depende dos ativos e dos pesos, e um número de risco só é auditável com a base que o produziu
([D-15](D-15-manifesto-de-execucao.md)); se a composição pudesse mudar sob uma execução já
calculada, o resultado guardado passaria a descrever outra carteira
([D-16](D-16-resultado-e-imutavel.md)). O valor aplicado, em reais, não muda o VaR em %: só a
conversão dele.

A [D-115](D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md) deixou a chave
de leitura ler o relatório e mandou fazer a pergunta de novo para cada dado privado.

## Decisão

1. **A carteira é da organização**, como o relatório: `admin` e `member` da mesma organização leem,
   mudam e pedem o risco das carteiras uns dos outros. Quem criou e quem compôs cada versão ficam
   gravados.
2. **A composição é versionada.** Cada troca de ativos ou pesos cria uma versão nova,
   `core.portfolio_version`, com as posições em `core.portfolio_holding`; versão e posição **só
   crescem**, no Django e no banco, por gatilho
   ([D-114](D-114-tabela-que-so-cresce-e-guardada-tambem-no-banco-por-gatilho.md)). A execução de
   risco é de uma versão. Enviar a mesma composição não cria versão.
3. **O valor aplicado (`notional`) e o nome mudam sem versão.** O valor fica fora do cálculo; a perda
   em reais é calculada na leitura, com o valor atual: `notional × (1 − exp(−VaR))`, porque o VaR do
   motor é perda em log-retorno.
4. **Nada se apaga.** A carteira se arquiva e some da API; versões e execuções ficam.
5. **A chave de leitura lê carteira e risco de carteira** da organização da dona, com o escopo
   `read`; criar, mudar, arquivar, trocar a composição e pedir o risco são só pela sessão. Estende a
   D-115.

## Consequências

- O risco de uma versão antiga continua guardado e correto para sempre, mesmo depois de a pessoa
  trocar os pesos; a API, neste bloco, mostra só o da versão corrente.
- Numa organização com várias pessoas, todo `member` muda a carteira de todos.
- Uma chave vazada lê as carteiras, os pesos e o valor aplicado da organização, até ser revogada.
- A leitura não é auditada, como a do relatório — diverge da expectativa da
  [D-104](D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md) para o M2.2.

Origem: [spec M2.2a — Carteira](../specs/M2.2a-carteira.md) (decisões 5 e 6, RF-01 a RF-03, RF-11,
RF-12, RF-17, RF-19).
