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
| [D-95](D-95-o-m1-6-em-tres-blocos.md) | O M1.6 em três blocos: as camadas 4 e 5 vão para o M1.6c, com as rotas escritas pela `marco1` |
| [D-96](D-96-discordancia-e-aprovados-entram-no-marco-1.md) | A discordância entre modelos e os não rejeitados por ativo entram no Marco 1 |
| [D-97](D-97-no-marco-1-cada-numero-tem-uma-frase-fixa.md) | No Marco 1, cada número tem uma frase fixa; as duas leituras continuam no M2.3 |
| [D-98](D-98-o-horizonte-do-marco-1-e-1-dia-restringe-a-d-05.md) | O horizonte do Marco 1 é 1 dia; restringe a D-05 |
| [D-99](D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md) | As camadas 4 e 5 entram depois do risco, e as tabelas da `fundamentos` que a tela lê são contrato |
| [D-140](D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md) | O pedido de cálculo sob demanda exige conta pronta; restringe a D-90 e a D-100 |
| [D-151](D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md) | O texto das duas leituras mora no frontend; restringe a D-97 e a PRODUTO §2 |
| [D-152](D-152-o-nivel-de-leitura-e-escolha-do-visitante.md) | O nível de leitura é escolha do visitante, global, lembrada no navegador; o padrão é iniciante |
| [D-153](D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md) | O parecer da CVM não bloqueia o M2.3; restringe o pré-requisito do Marco 2 e a PRODUTO §6 e §8 |
| [D-116](D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md) | O parecer da CVM não bloqueia a spec nem o plano da carteira; segura a PR de implementação, e o lado seguro é regra do desenho — restringe a D-153 |
| [D-160](D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md) | Sem comercialização, o parecer da CVM não segura a carteira; o parecer só vale antes de comercializar — substitui a D-116, item 2, e a D-153, item 2 |
| [D-117](D-117-a-carteira-e-uma-serie-unica-de-pesos-fixos-nos-nove-modelos.md) | A carteira é uma série única, de pesos fixos rebalanceados a cada pregão, sobre a interseção das datas, nos nove modelos sem mudar o motor — formaliza o caminho barato |
| [D-146](D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md) | O estresse histórico vira o bloco M3.3: só do ativo, só com preço |
| [D-147](D-147-os-episodios-de-estresse-sao-uma-lista-curada.md) | Os episódios de estresse são uma lista curada, com datas de calendário |
| [D-148](D-148-o-estresse-e-tabela-filha-da-metrica-e-sai-pelo-metrics.md) | O estresse é tabela filha da linha de métrica e sai pela rota `/metrics` |
| [D-184](D-184-a-decada-e-a-do-ativo-e-o-teste-se-le-em-anos-de-252-pregoes.md) | A década do laboratório é a do ativo, do primeiro pregão a dez anos de calendário depois, e o teste se lê em trechos de 252 pregões; veredito por ano só a 95% |
| [D-187](D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md) | A seção do laboratório fica na tela do ativo, logo depois do risco, para todos, pela rota `/lab`, sem eleger nem ordenar, com a diferença honesta nas duas leituras |
| [D-188](D-188-a-previsao-de-retorno-e-o-log-retorno-de-um-pregao-contra-o-retorno-zero.md) | A previsão de retorno é o log-retorno de um pregão, pontual, fora da amostra contra o retorno zero; cada modelo grava também a previsão do próximo pregão |
| [D-192](D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md) | A tela mostra a validação e, junto dela, a previsão do próximo pregão, nunca sozinha, com o aviso obrigatório; sem comercialização, o parecer da CVM não segura o M5.1 — estende a D-160 |

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
| [D-157](D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md) | Alteração no motor em lista fechada para a correção do M1.4b; restringe a D-76, a D-21 e a D-46 |
| [D-158](D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md) | Nos nove modelos, o VaR do dia *t* não usa o retorno de *t* nem posteriores, e o número mostrado tem a data do último pregão; os tradicionais reestimam a cada 252 pregões em janela expansiva; restringe a D-97 |
| [D-159](D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md) | A linha de base numérica passa a ser a do motor `0.4.0`, recapturada por script versionado; restringe a D-44 |
| [D-183](D-183-o-laboratorio-e-o-calculo-de-producao-recortado-na-decada-do-ativo-restringe-a-d-04.md) | O laboratório é o cálculo de produção recortado na década do ativo, calculado uma vez e guardado; restringe a D-04 e responde a D-74 |
| [D-185](D-185-o-experimento-mora-em-tres-tabelas-de-gold-imutaveis-e-um-ok-por-identidade.md) | O experimento mora em `gold.lab_run`, `lab_result` e `lab_year`, nasce fechado e é imutável no Django e no banco; um `ok` por identidade, e motor novo é experimento novo |
| [D-186](D-186-o-experimento-roda-pela-fila-depois-do-fecho-do-risco-de-producao.md) | O experimento roda pela fila depois do fecho do risco de produção, reaproveitando os retratos, uma tarefa por ativo, sem entrada no Beat; o operador tem `compute_lab` |
| [D-189](D-189-o-motor-ganha-o-pacote-engine-returns-em-lista-fechada-e-vai-a-0-5-0-restringe-a-d-21-a-d-76-e-a-d-157.md) | O motor ganha o pacote `engine.returns`, em lista fechada de arquivos novos, e vai a `0.5.0`; restringe a D-21, a D-76 e a D-157 |
| [D-190](D-190-a-validacao-do-retorno-e-o-diebold-mariano-contra-o-zero-e-nenhum-modelo-e-eleito.md) | A validação do retorno: `r2_os`, acerto ao lado da parcela de alta, Diebold-Mariano no veredito; Clark-West e Pesaran-Timmermann fora dele; nenhum modelo é eleito |
| [D-191](D-191-o-retorno-mora-em-apps-returns-e-roda-no-quinto-elo-da-rotina-estende-a-d-91.md) | O retorno mora em `apps/returns`, em `gold.return_run` e `gold.return_result`, imutáveis; roda no quinto elo da `rotina_diaria` e na cadeia sob demanda; sai pelo `/returns` — estende a D-91 |
| [D-120](D-120-fundamento-vem-dos-dados-abertos-da-cvm.md) | Fundamento vem dos dados abertos da CVM (DFP e ITR), por HTTP direto |
| [D-121](D-121-a-bronze-guarda-o-zip-inteiro-e-so-quando-o-conteudo-muda.md) | A `bronze` guarda o zip inteiro, e o conteúdo só de novo quando mudou |
| [D-122](D-122-conta-se-localiza-pela-descricao-sob-mae-fixa.md) | Conta se localiza pela descrição sob mãe fixa definida, não pelo código; a companhia tem plano de contas |
| [D-123](D-123-resultado-por-trimestre-isolado-e-12-meses-por-soma.md) | O resultado é guardado por trimestre isolado; o 4º trimestre é o DFP menos o ITR anterior; 12 meses é a soma de quatro trimestres |
| [D-124](D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md) | A capitalização soma as classes e é nula quando falta preço de alguma; a escala das ações é inferida pelo LPA |
| [D-126](D-126-companhia-e-entidade-ligada-ao-ticker-por-valor.md) | A companhia vira entidade em `silver.company`, ligada ao ticker por valor, sem FK em `silver.asset` |
| [D-127](D-127-coleta-de-fundamentos-semanal-e-encadeada-restringe-a-d-69.md) | A coleta de fundamentos é semanal e encadeia o cálculo; restringe a D-69 |
| [D-128](D-128-itr-e-dfp-na-mesma-data-vale-o-dfp.md) | ITR e DFP na mesma data: vale o DFP |
| [D-129](D-129-lucro-so-na-mae-vale-a-mae.md) | Lucro só na mãe: vale a mãe; e o LPA não cai para a `3.99` |
| [D-130](D-130-noticia-e-o-que-a-companhia-divulga-na-cvm.md) | A notícia do Ruvor é o que a companhia divulga na CVM (IPE), não a imprensa |
| [D-131](D-131-documento-do-ipe-se-identifica-pelo-link.md) | Um documento do IPE se identifica pelo link, e a `silver` guarda só a versão corrente |
| [D-132](D-132-pares-sao-o-segmento-da-b3-pela-tupla.md) | Os pares são o segmento da B3, ou o subsetor, pela tupla; a posição é o percentil |
| [D-133](D-133-coleta-de-comunicados-diaria-restringe-a-d-127.md) | A coleta de comunicados é diária, em entrada própria do Beat; restringe a D-127 |
| [D-134](D-134-tarefas-celery-tipadas-por-celery-types.md) | As tarefas Celery são tipadas por `celery-types` |
| [D-143](D-143-a-busca-ignora-acento-pelo-unaccent.md) | A busca ignora acento pela extensão `unaccent` do PostgreSQL |
| [D-144](D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md) | A classificação da B3 se corrige na saída da API, por tabela fechada; estende a D-47 |
| [D-100](D-100-a-api-autentica-por-sessao-do-django-com-csrf.md) | A API autentica por sessão do Django, com CSRF; 401 com `WWW-Authenticate: Session` |
| [D-101](D-101-cadastro-aberto-com-organizacao-pessoal.md) | Cadastro aberto, com organização pessoal; organização real só por comando |
| [D-102](D-102-papeis-admin-e-member-por-organizacao.md) | Dois papéis por organização, `admin` e `member`; `is_staff` é da plataforma; toda view que exige conta declara `AccountReady` |
| [D-103](D-103-senha-provisoria-gerada-pelo-servidor.md) | Usuário de organização real nasce com senha provisória gerada pelo servidor, mostrada uma vez, e troca obrigatória |
| [D-104](D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md) | A auditoria de acesso mora em `core.access_event`, que só cresce; ninguém a lê neste bloco, e o filtro por organização é do primeiro bloco que a ler — restringe a D-41 |
| [D-105](D-105-superusuario-mora-na-ruvor-restringe-a-d-39.md) | O superusuário mora na organização `ruvor`, como `admin` — restringe a D-39 |
| [D-106](D-106-limite-de-tentativas-no-redis-e-email-sem-caixa.md) | O limite de tentativas conta no cache do Django, no Redis, num banco próprio: por IP e por (e-mail, IP); o e-mail é único sem diferença de caixa |
| [D-107](D-107-m2-1a-em-duas-fases-restringe-a-d-82.md) | O M2.1a implementa em duas fases, com uma PR cada — restringe a D-82 |
| [D-108](D-108-a-api-aceita-chave-pessoal-de-leitura.md) | A API aceita chave pessoal de leitura, que age como a dona e só lê rotas com `api_key_scope = "read"`, por método seguro; o padrão é recusar — estende a D-100 |
| [D-109](D-109-toda-rota-da-api-tem-taxa.md) | Toda rota da API tem taxa: por chave, por usuário e, para anônimo, por IP, ajustável por variável |
| [D-110](D-110-a-descricao-da-api-e-o-esquema-openapi-gerado.md) | A descrição da API é o esquema OpenAPI gerado pelo drf-spectacular, sem aviso nem erro — substitui a documentação manual que a D-11 previa |
| [D-111](D-111-a-chave-guarda-so-o-hash-e-a-conta-mudada-revoga.md) | A chave guarda só o SHA-256 do segredo, mostrado uma vez; desativar e redefinir a senha revogam as chaves |
| [D-112](D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md) | O filtro automático por organização nasce no M4.2, em `core.api_key`: gerente que falha fechado, contexto posto pela autenticação e pelo serviço — cumpre a D-41 |
| [D-113](D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md) | O relatório é uma foto guardada: o JSON entregue, byte a byte, com o SHA-256 dele, em `core.report`; o CSV deriva dele, e um formato publicado nunca muda — estende a D-16 |
| [D-114](D-114-tabela-que-so-cresce-e-guardada-tambem-no-banco-por-gatilho.md) | Tabela que só cresce é guardada também no banco, por gatilho; `core.report` é a primeira, e o `TRUNCATE` continua passando |
| [D-115](D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md) | A chave de leitura lê o relatório da organização da dona, com o escopo `read`; gerar só pela sessão — estende a D-108 e substitui, para o relatório, a orientação do M4.2 de escopo novo |
| [D-118](D-118-a-carteira-e-da-organizacao-e-a-composicao-e-versionada.md) | A carteira é da organização, a composição é versionada e imutável, e o valor aplicado fica fora do cálculo; a chave lê carteira — estende a D-115 |
| [D-119](D-119-o-risco-da-carteira-e-sob-demanda-em-gold-na-app-da-frente.md) | O risco da carteira é sob demanda, em tabelas próprias de `gold` na app da `identidade`, sem retratos, com teto global e um por organização — restringe a D-84 |
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
| [D-86](D-86-convencoes-da-api-http.md) | As convenções da API HTTP: prefixo, formato de erro, permissão declarada, dados |
| [D-87](D-87-os-mockups-sao-a-referencia-visual-do-kit.md) | Os mockups são a referência visual; tokens e componentes derivam deles, e o texto das tags é escurecido o mínimo para 4,5:1 |
| [D-88](D-88-o-kit-tem-dois-temas-pelos-mesmos-tokens.md) | O kit tem dois temas, claro e escuro, pelos mesmos tokens de cor |
| [D-89](D-89-a-web-enfileira-pelo-nome-da-tarefa.md) | A `web` enfileira pelo nome da tarefa, e os nomes são contrato interno |
| [D-90](D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md) | Cálculo sob demanda só para ativo nunca calculado: um pedido aberto por ativo, teto global estrito e expiração; o pedido fecha com a `risk_run` |
| [D-91](D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md) | A rotina diária é `preços → métricas → risco`; estende a D-69 |
| [D-92](D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md) | Nunca duas execuções do mesmo ativo ao mesmo tempo: a abertura pula o ativo em cálculo |
| [D-93](D-93-os-icones-do-produto-vem-do-phosphor.md) | Os ícones do produto vêm do Phosphor, num conjunto fechado dentro do kit |
| [D-94](D-94-os-graficos-sao-do-uplot.md) | Os gráficos são do uPlot, com a cor dos tokens; a comparação dos modelos é tabela |
| [D-149](D-149-a-execucao-presa-e-fechada-pela-regra-do-fecho.md) | A execução presa é fechada pela regra do fecho, na rotina diária e por comando |
| [D-150](D-150-o-fecho-so-escreve-sobre-execucao-em-running.md) | O fecho só escreve sobre execução em `running`, e o que chega depois é descartado; estende a D-72 e restringe a D-70 |
| [D-125](D-125-indicadores-em-gold-na-app-da-frente-restringe-a-d-84.md) | Os indicadores fundamentalistas moram em `gold`, na app da frente, e a cerca se amplia; restringe a D-84 |

## As três mais consequentes

Se for ler só três:

- **[D-18](D-18-separacao-treino-previsao.md)** — separar treino de previsão é o que torna o produto viável
- **[D-17](D-17-monorepo-engine-sem-django.md)** — `engine/` sem Django sustenta ciência, empacotamento e deploy
- **[D-26](D-26-processo-de-desenvolvimento.md)** — o processo, que rege todo o resto
