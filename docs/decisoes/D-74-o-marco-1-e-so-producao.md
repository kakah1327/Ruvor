# D-74 — O Marco 1 é só produção; o laboratório vai para o Marco 2

**Status:** aceita · 2026-09-25 · restringe a [PRODUTO §4](../PRODUTO.md#4-marcos)

## Contexto

A [D-04](D-04-dois-regimes-de-operacao.md) separou dois regimes: **laboratório**, que valida o
método ao longo de uma década, e **produção**, que entrega o número de hoje. A
[PRODUTO §4](../PRODUTO.md#4-marcos) prometia a camada 3 "nos dois regimes" já no Marco 1.

O M1.4 entregou só produção, e a spec dele assumiu "o Marco 1 é só produção" **para poder
existir**, marcando a escolha como pendente. Nenhum bloco do ROADMAP retomava o laboratório —
nem o M1.5, nem o M1.6. Enquanto ninguém escolhesse, adiar era descartar sem dizer.

Três saídas estavam abertas: (1) o Marco 1 vira só produção; (2) um bloco M1.7 para o
laboratório; (3) o `ruvor run` declarado suficiente.

## Decisão

**O Marco 1 entrega a camada 3 só no regime de produção.** O regime de laboratório vai para o
**Marco 2**, como bloco próprio (**M2.4**).

Por que não as outras:

- **M1.7** atrasaria o Marco 1 por uma funcionalidade que pede parâmetros escolhidos pelo
  usuário e cálculo sob demanda — e antes do M2.1 não há usuário.
- **`ruvor run` suficiente** confundiria ferramenta de pesquisa do TCC com produto: ele valida
  o método para quem o roda, não mostra a validação a quem usa a plataforma.

## Consequências

- A PRODUTO §4 passa a dizer "camada 3 no regime de produção" no Marco 1, e o laboratório
  entra no Marco 2.
- **O Marco 1 não fica sem validação.** Cada `risk_result` de produção já carrega os quatro
  backtests e o veredito de adequação sobre a série do próprio ativo
  ([D-64](D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md)) — é validação por ativo, não
  o experimento de uma década que o laboratório faz.
- O laboratório segue existindo fora da plataforma, pelo `ruvor run`, que é o que a Etapa 6 do
  TCC usa.
- A spec do M2.4 decide o que o laboratório é na plataforma: parâmetros, período, quem pode
  rodar e onde o resultado fica.

Origem: pendência "o regime de laboratório sai do Marco 1", aberta pela spec do M1.4 e decidida
pelo humano em 2026-09-25.
