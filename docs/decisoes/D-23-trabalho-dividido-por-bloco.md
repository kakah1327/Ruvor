# D-23 — Trabalho dos devs dividido por bloco do sistema

**Status:** aceita · 2026-08-29

## Contexto

Surgiu a pergunta de como dividir o trabalho de treinamento entre os 4 devs.

## Decisão

**Treinar nao e trabalho de dev, e tempo de maquina.** O que se divide e a construcao do sistema, por bloco.

## Consequências

- Dividir uma execucao entre quatro pessoas nao acelera nada e cria o problema de D-22.
- Os blocos do Marco 1 sao independentes o suficiente para quatro frentes: ingestao e catalogo, camada de comportamento, integracao do motor com fila e manifesto, frontend.
- Em producao, nenhuma maquina de dev participa do calculo.
