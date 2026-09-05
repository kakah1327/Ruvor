# D-37 — Existe um quarto esquema, `core`, para o dado operacional

**Status:** aceita · 2026-09-04

## Contexto

A [D-13](D-13-camadas-bronze-prata-ouro.md) nomeia três camadas — bronze, prata e ouro — e
cala sobre o dado que não é de linhagem: organização, usuário, e depois carteiras, limites e
chaves de API. A [ARQUITETURA](../ARQUITETURA.md#banco-e-camadas-de-dado) repete as mesmas
três.

O F4 é o bloco que cria as primeiras tabelas, e precisou resolver onde a organização e o
usuário moram. Sem decisão, eles cairiam no `public` por omissão.

## Decisão

Existe um **quarto esquema, `core`**, para o dado operacional. As camadas de linhagem
continuam sendo três; `core` não é uma quarta camada, é o lugar do que não é linhagem.

## Consequências

- A fronteira entre dado operacional e dado analítico passa a ser **estrutura**, e não
  convenção — é consultável no catálogo do banco.
- Nada cai em esquema padrão por descuido: um modelo sem esquema declarado é defeito
  visível, porque o `public` tem dono conhecido — ver [D-38](D-38-public-guarda-o-encanamento.md).
- A [D-13](D-13-camadas-bronze-prata-ouro.md) **não é revogada.** Ela continua valendo para
  as três camadas de linhagem; esta decisão acrescenta o que ela não cobria.
- Os quatro esquemas nascem juntos, na primeira migration do projeto, mesmo que `bronze`,
  `silver` e `gold` fiquem vazios até o M1.2 e o M1.4. Criá-los depois custaria mais do que
  criá-los agora, e deixaria o M1.1 decidindo sozinho.

Origem: [spec F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md).
