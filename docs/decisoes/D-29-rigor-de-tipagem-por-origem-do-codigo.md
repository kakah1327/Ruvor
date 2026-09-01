# D-29 — Rigor de tipagem varia conforme a origem do codigo

**Status:** aceita · 2026-08-31

## Contexto

A [D-12](D-12-tipagem-obrigatoria.md) exige anotacoes de tipo obrigatorias, mas foi escrita antes de existir a distincao entre codigo migrado e codigo novo.

Exigir rigor total sobre o motor migrado obrigaria a **editar** codigo que a spec F2a promete apenas mover: o TensorFlow nao publica anotacoes e boa parte do motor nao tem retorno anotado. Editar logica de modelo e proibido pela [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) ate a conclusao da Etapa 6.

## Decisão

A D-12 continua valendo, com rigor **graduado pela origem do codigo**:

| Origem | Rigor |
|---|---|
| Codigo novo (`backend/`, `frontend/`) | estrito desde o primeiro arquivo |
| Codigo migrado do prototipo (`engine/`) | modo padrao, sem anotacao obrigatoria, com bibliotecas sem stubs ignoradas |


## Consequências

- Restringe a D-12; nao a revoga.
- O rigor do `engine/` sobe depois da Etapa 6, quando a D-21 deixar de congelar o motor. Ate la, subir o rigor exigiria alterar o motor, o que invalidaria a comparacao cientifica.
- Rigor alto em codigo novo e de graca; adicionado depois, custa caro.
