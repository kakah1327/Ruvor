# D-116 — O parecer da CVM não bloqueia a spec nem o plano da carteira; segura a PR de implementação; restringe a D-153

**Status:** aceita com a aprovação da [spec do M2.2a](../specs/M2.2a-carteira.md) · 2026-09-30 · frente `identidade`

## Contexto

A [PRODUTO §6](../PRODUTO.md#6-restrições-de-produto) põe a fronteira regulatória entre
**informar/analisar** e **recomendar**, e aponta "montar carteira" como o ponto em que se atravessa
a linha com facilidade, se a plataforma sugerir pesos. A
[D-153](D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md), item 2, restringiu o pré-requisito do
parecer "aos blocos que tocam composição ou peso de carteira: o M2.2 e o que dele derivar". O
[ESTADO](../ESTADO.md#pendências-que-bloqueiam-trabalho-futuro) registra o parecer como bloqueio do
"Marco 2 (carteira)".

O parecer não tem data. Esperá-lo para escrever a spec e o plano deixaria o bloco inteiro parado, e
escrever é barato e reversível: o risco regulatório está no que a plataforma **entrega**, não no que
o time desenha.

## Decisão

1. **A spec e o plano do M2.2a seguem sem o parecer.** Decisão do dono da frente, 2026-09-30.
2. **A PR de implementação do M2.2a só é mesclada na `main` com o parecer registrado** — num
   registro de decisão novo, que o cite. O mesmo vale para o M2.2b (as telas, da `marco1`) e para
   todo bloco que derivar da carteira.
3. **O lado seguro é regra do desenho, desde já:** a pessoa escolhe os ativos e os pesos; a
   plataforma **não sugere, não completa, não normaliza, não otimiza e não ordena por mérito** — o
   peso gravado é o que a pessoa mandou, e soma diferente de 100 é erro, não ajuste. Nenhum corpo da
   API tem campo que sugira peso ou ativo, e os resultados seguem a
   [D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md): lista, sem eleger.
4. **Restringe a D-153, item 2**: o pré-requisito do parecer, para o M2.2, deixa de valer para o
   bloco inteiro e passa a valer para o merge da implementação.

## Consequências

- A implementação pode ficar pronta e parada no ramo, à espera do parecer.
- Se o parecer pedir mudança, ela entra como errata da spec antes do merge; se proibir a carteira, o
  bloco não entra, e esta decisão é substituída.
- O ESTADO, o ROADMAP e a PRODUTO §6 e §8 passam a dizer que o parecer segura o merge da carteira,
  não o trabalho.
- Não é parecer jurídico.

Origem: [spec M2.2a — Carteira](../specs/M2.2a-carteira.md) (decisão 1, RF-09).
