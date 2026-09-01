# Specs

Uma spec por bloco do [ROADMAP](../ROADMAP.md). Descreve **o que deve existir e por quê** —
nunca como implementar.

Nomeação: `<bloco>-<nome-curto>.md` — por exemplo `F2-esqueleto-do-repositorio.md`.

## Antes de escrever

Leia [PROCESSO.md §4](../PROCESSO.md#4-anatomia-de-uma-spec), que traz o modelo completo e o
critério de revisão.

## O teste que a spec precisa passar

**Executável por alguém que nunca participou da conversa.** Se depende de ter estado na
sala, não está pronta. É por isso que a revisão adversarial é feita por um agente **sem** o
histórico da conversa.

## Ciclo

```
escrita → auto-revisão → revisão adversarial → ✋ aprovação humana → plano
```

Spec pequena e local pode ser revisada inline, sem agente. Spec de bloco, que cria contrato
novo ou atravessa mais de um bloco, vai para revisão por agente.

*Nenhuma spec escrita ainda.*
