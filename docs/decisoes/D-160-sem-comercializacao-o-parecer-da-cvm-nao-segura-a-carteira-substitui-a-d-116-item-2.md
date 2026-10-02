# D-160 — Sem comercialização, o parecer da CVM não segura a carteira; substitui a D-116, item 2, e a D-153, item 2

**Status:** aceita · 2026-10-02 · frente `identidade`, decisão do dono (Kauã)

## Contexto

A [D-116](D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md),
item 2, segurava a PR de implementação do M2.2a — e o M2.2b e tudo que derivasse da carteira — até
um parecer sobre a fronteira regulatória da CVM. A
[D-153](D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md), item 2, já tinha posto o parecer como
pré-requisito dos blocos que tocam composição ou peso de carteira.

A preocupação da [PRODUTO §6](../PRODUTO.md#fronteira-regulatória-cvm) é a atividade regulada de
recomendar investimento a terceiros. **A plataforma não vai ser comercializada por enquanto**, e o
parecer não tem data: segurar a carteira por ele parava o trabalho sem proteger nada que esteja em
jogo hoje.

A PR #34 (a implementação do M2.2a) entrou na `main` em 2026-10-02, antes desta decisão.

## Decisão

1. **O parecer da CVM deixa de ser pré-requisito** do merge do M2.2a, do M2.2b e de tudo que derivar
   da carteira. Substitui a D-116, item 2, e a D-153, item 2. A entrada da PR #34 na `main` fica
   regularizada por esta decisão.
2. **O lado seguro continua regra do desenho:** a D-116, item 3, segue valendo. A pessoa escolhe os
   ativos e os pesos; a plataforma não sugere, não completa, não normaliza, não otimiza e não ordena
   por mérito; os resultados seguem a [D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md).
3. **O parecer volta a ser pré-requisito antes de comercializar** — cobrar, ou abrir a plataforma a
   terceiros como serviço. Quem decidir comercializar registra o parecer numa decisão nova antes.

## Consequências

- O M2.2a fecha na `main`; o M2.2b, da `marco1`, não espera mais nada além do próprio portão.
- O ESTADO, o ROADMAP, a FRENTES, a PRODUTO §4, §6 e §8, o `CLAUDE.md` e a página da frente deixam
  de dizer que o parecer segura a carteira. A pendência passa a ser "antes de comercializar".
- A página da `marco1` cita o parecer como espera do M2.2 e do M5.1; quem a corrige é a `marco1`.
- Não é parecer jurídico.
