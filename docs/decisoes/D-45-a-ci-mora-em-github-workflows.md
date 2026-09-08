# D-45 — A CI mora em `.github/workflows/`, não em `infra/`

**Status:** aceita · 2026-09-06

## Contexto

O diagrama da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) reserva, nominalmente
para este bloco:

```
├── infra/             # arquivos de construcao de imagem, e CI a partir do F5
```

O repositório é `github.com/kakah1327/Ruvor`, e a CI é o GitHub Actions.

## Decisão

A definição da CI fica em **`.github/workflows/ci.yml`**.

## Consequências

- **Não é escolha: o GitHub só lê `.github/workflows/`.** Um arquivo em `infra/` não seria
  executado, e o sintoma seria a **ausência de execução** — sem erro, sem aviso, sem nada. É a
  pior forma de falha que existe neste projeto.
- É a mesma forma da [D-35](D-35-compose-e-dockerignore-na-raiz.md), em que `compose.yaml` e
  `.dockerignore` ficaram na raiz porque é onde as ferramentas os procuram, e não onde o
  diagrama gostaria.
- **`infra/` continua sendo dos arquivos de construção de imagem**, que é o resto do que a
  linha do diagrama dizia. O que sai dela é só a CI.
- Registrado para que o próximo bloco leia daqui, em vez de re-derivar — e para que o diagrama
  da ARQUITETURA, corrigido no F5, não volte a divergir.

Origem: [spec F5 — Integração contínua](../specs/F5-integracao-continua.md).
