# D-42 — A CI avisa e não bloqueia

**Status:** aceita · 2026-09-06

## Contexto

A [ARQUITETURA](../ARQUITETURA.md#ambientes) promete: *"a cada mudança roda verificação de
estilo, verificação de tipos e testes. **Não passou, não entra.**"*

"Não entra" pressupõe um ponto de integração onde barrar — e a
[D-31](D-31-trabalho-direto-na-main.md) removeu esse ponto de propósito: trabalho direto na
`main`, sem ramo e sem PR, *"enquanto o time for uma pessoa"*.

As duas não podem valer juntas.

## Decisão

**A D-31 fica. A promessa da ARQUITETURA fica restringida.**

A CI roda a cada push na `main` e **reprova ruidosamente, sem impedir**. Não há proteção de
ramo, não há gatilho de `pull_request`, não há nada a barrar.

## Consequências

- **O valor da CI hoje não é barrar código.** É provar que o repositório funciona numa máquina
  que não é a do desenvolvedor — coisa que nenhuma execução local prova, por definição. Até o
  F5, nunca ninguém rodou este repositório em outro lugar.
- Barrar exigiria reintroduzir ramo e PR, que a D-31 removeu por não haver trabalho paralelo
  nem consumidor a proteger. Nada disso mudou.
- **A `main` pode ficar vermelha**, e é aceito. Quando ficar, o [ESTADO.md](../ESTADO.md) diz
  qual é a reprovação, de que bloco ela é e quem a paga — status verde com execução vermelha é
  o tipo de mentira que o passo FECHA existe para impedir.
- **Isto se inverte quando a D-31 se inverter.** No dia em que houver mais de uma pessoa
  desenvolvendo ao mesmo tempo, ou versão publicada, volta a haver o que proteger — e aí a
  promessa original da ARQUITETURA passa a ser implementável, com ramo, PR e proteção.

Origem: [spec F5 — Integração contínua](../specs/F5-integracao-continua.md).
