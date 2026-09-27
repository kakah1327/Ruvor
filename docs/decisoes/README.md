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
| [D-55](D-55-metrica-de-comportamento-e-imutavel.md) | Métrica de comportamento é imutável, uma linha por (ativo, data de cálculo) |
| [D-56](D-56-tabela-de-metricas-larga-e-serie-em-tabela-propria.md) | A tabela de métricas é larga e tipada; série ganha tabela própria |
| [D-57](D-57-janela-estatistica-do-marco-1-e-60-meses.md) | A janela estatística do Marco 1 é 60 meses |
| [D-58](D-58-calculo-da-camada-2-mora-no-backend.md) | O cálculo da camada 2 mora no backend, não no motor |
| [D-59](D-59-sem-dependencia-numerica-nova-no-backend.md) | Sem dependência numérica nova no backend |
| [D-60](D-60-metrica-descritiva-sem-manifesto-restringe-a-d-15.md) | Métrica descritiva não carrega manifesto; restringe a D-15 |
| [D-61](D-61-backend-alimenta-o-motor-por-dataprovider.md) | O backend alimenta o motor por um `DataProvider`, e o motor não aprende a plataforma |
| [D-62](D-62-a-serie-que-vai-ao-motor-e-o-adj-close.md) | A série que vai ao motor é o `adj_close` |
| [D-63](D-63-semente-fixa-entra-no-manifesto.md) | A semente é fixa, aplicada no início de cada treino, e entra no manifesto |
| [D-64](D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md) | O veredito de adequação é Kupiec **e** Christoffersen; DQ e Basileia ficam de fora |
| [D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md) | A plataforma lista os modelos aprovados e não elege nenhum |
| [D-66](D-66-registry-incompleto-e-erro-restringe-o-silencio-do-motor.md) | Registry incompleto é erro, não silêncio; restringe, no consumo, o `except ImportError` do motor |
| [D-67](D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) | Uma tarefa por (ativo, modelo), e a transação acompanha; restringe o RF-12 do M1.4 |
| [D-68](D-68-o-estado-da-execucao-mora-no-banco.md) | O estado da execução mora no banco, não no Redis |
| [D-69](D-69-o-agendamento-e-encadeado.md) | O agendamento é encadeado, não por horário paralelo |
| [D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md) | A tarefa nunca levanta, e o fecho lê o banco |
| [D-71](D-71-a-risk-run-nasce-no-worker.md) | A `risk_run` nasce no `worker`, não em quem enfileira |
| [D-72](D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md) | O fecho escreve metadado de execução; restringe a D-16 |
| [D-73](D-73-o-cabecalho-do-chord-sai-por-custo.md) | O cabeçalho do `chord` sai por custo, não na ordem pedida |
| [D-74](D-74-o-marco-1-e-so-producao.md) | O Marco 1 é só produção; o laboratório vai para o Marco 2; restringe a PRODUTO §4 |
| [D-75](D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md) | As redes semeiam em cada retreino, com semente derivada da execução e da posição; estende a D-63 |
| [D-76](D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md) | Alteração no motor em lista fechada para os retratos; restringe a D-21 |
| [D-77](D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md) | Os retratos moram em `gold`, imutáveis, com impressão digital estrita sobre os preços, e guardam o estado do otimizador |
| [D-78](D-78-incremental-igual-ao-do-zero-e-full-e-a-referencia.md) | O critério é incremental igual ao do zero, e `--full` é a referência |
| [D-79](D-79-os-quatro-caros-usam-retratos-e-os-cinco-baratos-nao.md) | Os quatro modelos caros usam retratos; os cinco baratos, não |
| [D-80](D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md) | O retreino de produção é a cada 252 pregões, o do protocolo; restringe a D-18 |
| [D-81](D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md) | A imagem do `worker` é travada pelo lock do motor, e as versões das bibliotecas entram na identidade do retrato |
| [D-23](D-23-trabalho-dividido-por-bloco.md) | Trabalho dos devs dividido por bloco do sistema |
| [D-25](D-25-rebrand-ruvor.md) | Rebrand para Ruvor em toda a superfície |
| [D-26](D-26-processo-de-desenvolvimento.md) | Processo de desenvolvimento definido em PROCESSO.md |
| [D-30](D-30-portao-de-mockup-so-para-tela-de-produto.md) | Portão de mockup vale para tela de produto, não para casco técnico |
| [D-31](D-31-trabalho-direto-na-main.md) | Trabalho direto na `main` enquanto o time for uma pessoa — **substituída pela D-82** |
| [D-27](D-27-commits-sem-assinatura.md) | Commits sem assinatura de ferramenta |
| [D-33](D-33-dia-a-dia-dentro-do-conteiner.md) | O dia a dia de backend e frontend roda dentro do contêiner |
| [D-42](D-42-ci-avisa-e-nao-bloqueia.md) | A CI avisa e não bloqueia, enquanto valer a D-31 — **substituída pela D-83** |
| [D-82](D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md) | Ramo por bloco, e PR revisada por um dev de outra frente; substitui a D-31 |
| [D-83](D-83-a-ci-barra-na-pr.md) | A CI barra na PR; substitui a D-42 |
| [D-84](D-84-frentes-com-cerca-de-pastas.md) | Frentes simultâneas, cada uma com a sua cerca de pastas; restringe a D-23 |
| [D-85](D-85-o-dono-da-frente-aprova-a-propria-pr.md) | O dono da frente aprova e faz o merge da própria PR; restringe a D-82 |

## As três mais consequentes

Se for ler só três:

- **[D-18](D-18-separacao-treino-previsao.md)** — separar treino de previsão é o que torna o produto viável
- **[D-17](D-17-monorepo-engine-sem-django.md)** — `engine/` sem Django sustenta ciência, empacotamento e deploy
- **[D-26](D-26-processo-de-desenvolvimento.md)** — o processo, que rege todo o resto
