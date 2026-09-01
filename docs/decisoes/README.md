# Decisões

Um registro por decisão, numerado. **Append-only:** uma decisão nunca é editada — é
substituída por outra que cita a anterior. É o que garante diretriz constante entre
conversas e entre agentes.

## Produto

| # | Decisão |
|---|---|
| [D-01](D-01-nome-do-produto-e-ruvor.md) | O nome do produto é Ruvor |
| [D-02](D-02-produto-continua-depois-do-tcc.md) | O produto continua depois do TCC |
| [D-03](D-03-carteira-montada-pelo-usuario.md) | Carteira é montada pelo usuário, não importada |
| [D-04](D-04-dois-regimes-de-operacao.md) | Dois regimes: laboratório e produção |
| [D-05](D-05-horizonte-semanas-primeiro.md) | Horizonte de semanas primeiro, meses depois |
| [D-06](D-06-perda-e-o-foco.md) | Perda é o foco; retorno é o último módulo |
| [D-07](D-07-resposta-progressiva-modo-a.md) | Resposta progressiva: rápidos na hora, ML depois |
| [D-09](D-09-uma-camada-por-vez.md) | Construção de uma camada por vez |
| [D-19](D-19-cobertura-de-ativos-em-camadas.md) | Cobertura de ativos em camadas |

## Arquitetura

| # | Decisão |
|---|---|
| [D-08](D-08-dono-do-dado-no-schema.md) | Dono do dado no schema desde a primeira migration |
| [D-11](D-11-pilha-tecnologica.md) | Pilha: Python, Django, DRF, React, PostgreSQL |
| [D-12](D-12-tipagem-obrigatoria.md) | Tipagem obrigatória, verificada no CI |
| [D-13](D-13-camadas-bronze-prata-ouro.md) | Bronze, prata e ouro como esquemas do PostgreSQL |
| [D-14](D-14-celery-e-redis.md) | Celery e Redis para execução assíncrona |
| [D-15](D-15-manifesto-de-execucao.md) | Todo resultado carrega um manifesto de execução |
| [D-16](D-16-resultado-e-imutavel.md) | Resultado é imutável |
| [D-17](D-17-monorepo-engine-sem-django.md) | Monorepo, com o motor numérico isolado do Django |
| [D-18](D-18-separacao-treino-previsao.md) | Separação entre treino e previsão em produção |
| [D-24](D-24-organizacao-desde-a-primeira-migration.md) | Organização existe desde a primeira migration |

## Processo e execução

| # | Decisão |
|---|---|
| [D-10](D-10-spec-do-existente-e-linha-de-base.md) | A spec do que já existe é a linha de base da revisão |
| [D-20](D-20-experimentos-em-cpu.md) | Experimentos do TCC em CPU, com paralelização por ativo |
| [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) | Motor de ML não é alterado antes da Etapa 6 |
| [D-22](D-22-treino-centralizado-em-container.md) | Treino centralizado em uma máquina, em container |
| [D-23](D-23-trabalho-dividido-por-bloco.md) | Trabalho dos devs dividido por bloco do sistema |
| [D-25](D-25-rebrand-ruvor.md) | Rebrand para Ruvor em toda a superfície |
| [D-26](D-26-processo-de-desenvolvimento.md) | Processo de desenvolvimento definido em PROCESSO.md |
| [D-27](D-27-commits-sem-assinatura.md) | Commits sem assinatura de ferramenta |

## As três mais consequentes

Se for ler só três:

- **[D-18](D-18-separacao-treino-previsao.md)** — separar treino de previsão é o que torna o produto viável
- **[D-17](D-17-monorepo-engine-sem-django.md)** — `engine/` sem Django sustenta ciência, empacotamento e deploy
- **[D-26](D-26-processo-de-desenvolvimento.md)** — o processo, que rege todo o resto
