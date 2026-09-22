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
| [D-29](D-29-rigor-de-tipagem-por-origem-do-codigo.md) | Rigor de tipagem varia conforme a origem do código |
| [D-13](D-13-camadas-bronze-prata-ouro.md) | Bronze, prata e ouro como esquemas do PostgreSQL |
| [D-14](D-14-celery-e-redis.md) | Celery e Redis para execução assíncrona |
| [D-15](D-15-manifesto-de-execucao.md) | Todo resultado carrega um manifesto de execução |
| [D-16](D-16-resultado-e-imutavel.md) | Resultado é imutável |
| [D-17](D-17-monorepo-engine-sem-django.md) | Monorepo, com o motor numérico isolado do Django |
| [D-18](D-18-separacao-treino-previsao.md) | Separação entre treino e previsão em produção |
| [D-24](D-24-organizacao-desde-a-primeira-migration.md) | Organização existe desde a primeira migration |
| [D-28](D-28-frontend-em-typescript.md) | Frontend em TypeScript |
| [D-32](D-32-frontend-no-compose.md) | O frontend entra no `docker compose` |
| [D-34](D-34-banco-celery-e-redis-no-f3.md) | Banco, Celery e Redis chegam no F3, não no F4 |
| [D-35](D-35-compose-e-dockerignore-na-raiz.md) | `compose.yaml` e `.dockerignore` ficam na raiz, não em `infra/` |
| [D-36](D-36-versao-do-postgres.md) | A versão maior do Postgres é a 18 |
| [D-37](D-37-esquema-core-para-dado-operacional.md) | Existe um quarto esquema, `core`, para o dado operacional |
| [D-38](D-38-public-guarda-o-encanamento.md) | O `public` guarda o encanamento do Django, e a tabela declara o esquema no `db_table` |
| [D-39](D-39-usuario-proprio-autentica-por-email.md) | O usuário do projeto herda `AbstractBaseUser` e autentica por e-mail |
| [D-40](D-40-identificadores-de-esquema-em-ingles.md) | Os identificadores de esquema ficam em inglês |
| [D-41](D-41-filtro-por-organizacao-na-primeira-tabela-privada.md) | O filtro por organização é obrigação da primeira tabela privada; o usuário é exceção |
| [D-43](D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md) | ruff para Python, Biome para o frontend, e onde cada verificação roda |
| [D-44](D-44-o-motor-entra-no-estilo.md) | O motor entra no estilo, e como isso se prova |
| [D-45](D-45-a-ci-mora-em-github-workflows.md) | A CI mora em `.github/workflows/`, não em `infra/` |

## Processo e execução

| # | Decisão |
|---|---|
| [D-10](D-10-spec-do-existente-e-linha-de-base.md) | A spec do que já existe é a linha de base da revisão |
| [D-20](D-20-experimentos-em-cpu.md) | Experimentos do TCC em CPU, com paralelização por ativo |
| [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) | Motor de ML não é alterado antes da Etapa 6 |
| [D-22](D-22-treino-centralizado-em-container.md) | Treino centralizado em uma máquina, em container |
| [D-46](D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md) | O ajuste GARCH/EGARCH tenta de novo quando não converge; restringe a D-21 |
| [D-47](D-47-fonte-do-catalogo-e-o-site-da-b3.md) | A fonte do catálogo são os endpoints internos do site da B3 |
| [D-48](D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md) | O catálogo conformado mora em `silver`, um por ticker, atualizado por coleta; payload da `bronze` imutável |
| [D-49](D-49-catalogo-do-marco-1-so-acoes-e-ibovespa.md) | O catálogo do Marco 1 é só ações e o Ibovespa |
| [D-50](D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md) | O preço vem do `chart` v8 do Yahoo, por HTTP direto |
| [D-51](D-51-cobertura-e-o-que-tem-preco.md) | Cobertura é o que tem preço; sem coluna de cobertura |
| [D-52](D-52-a-janela-de-precos-so-cresce.md) | A janela de preços só cresce |
| [D-53](D-53-evento-novo-rebusca-a-serie-inteira.md) | Evento corporativo novo rebusca a série inteira |
| [D-54](D-54-transacao-por-ativo-restringe-a-d-48.md) | Na ingestão de preços a transação é por ativo; restringe a D-48 |
| [D-23](D-23-trabalho-dividido-por-bloco.md) | Trabalho dos devs dividido por bloco do sistema |
| [D-25](D-25-rebrand-ruvor.md) | Rebrand para Ruvor em toda a superfície |
| [D-26](D-26-processo-de-desenvolvimento.md) | Processo de desenvolvimento definido em PROCESSO.md |
| [D-30](D-30-portao-de-mockup-so-para-tela-de-produto.md) | Portão de mockup vale para tela de produto, não para casco técnico |
| [D-31](D-31-trabalho-direto-na-main.md) | Trabalho direto na `main` enquanto o time for uma pessoa |
| [D-27](D-27-commits-sem-assinatura.md) | Commits sem assinatura de ferramenta |
| [D-33](D-33-dia-a-dia-dentro-do-conteiner.md) | O dia a dia de backend e frontend roda dentro do contêiner |
| [D-42](D-42-ci-avisa-e-nao-bloqueia.md) | A CI avisa e não bloqueia, enquanto valer a D-31 |

## As três mais consequentes

Se for ler só três:

- **[D-18](D-18-separacao-treino-previsao.md)** — separar treino de previsão é o que torna o produto viável
- **[D-17](D-17-monorepo-engine-sem-django.md)** — `engine/` sem Django sustenta ciência, empacotamento e deploy
- **[D-26](D-26-processo-de-desenvolvimento.md)** — o processo, que rege todo o resto
