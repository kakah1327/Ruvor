# D-180 — "Carteiras" é um item da barra, só para quem entrou

**Status:** aceita · 2026-10-03, com a spec do M2.2b · registrada no fecho do bloco, 2026-10-07 · frente `marco1`

## Contexto

A carteira é a segunda pergunta do produto: depois de "quanto posso perder nesta ação", vem "quanto posso perder
no que eu tenho". O M2.2a pôs a carteira na API, mas a tela não tinha caminho até ela. A barra do casco já tinha a
marca, a busca, o alternador de leitura, o tema e, desde o M2.1b, o menu de conta. A carteira é dado privado da
organização, e quem não entrou não tem carteira.

## Decisão

1. **"Carteiras" é um item da barra**, logo depois da marca, que leva a `/carteiras`. É o item corrente em
   `/carteiras` e em `/carteiras/:id`.
2. **O item só aparece com a sessão logada e a conta pronta**, sem a troca obrigatória da senha pendente. O anônimo
   não o vê. Se o anônimo abrir `/carteiras` ou `/carteiras/:id` pelo endereço, vê o aviso "esta página é para quem
   entrou", com o `next`, e a tela não faz pedido à API.
3. **O lugar exato e o arranjo nas larguras estreitas são os do mockup aprovado** (`docs/mockups/M2.2b/lista.html`,
   portão da T2). Para caber o item sem apertar a busca, a barra estreita, em três linhas, vale até **920 px**, para
   todas as sessões. Antes valia até 840 px, desde o M2.1b. O item usa `.ruvor-nav.ruvor-nav--account`, que o kit não
   esconde abaixo de 1000 px.

## Consequências

- Nenhuma largura da barra rola na horizontal. A execução real do M2.2b mediu 1440, 1024, 921, 920, 768, 720 e 360 px.
- Em 1024 px, com a sessão logada, a busca da barra fica com 191 px. O portão da T2 aceitou essa largura.
- Se outro item entrar na barra para quem entrou, ele usa o mesmo modificador, e a largura da barra estreita é
  revista pelo mesmo critério.
