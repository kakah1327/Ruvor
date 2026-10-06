#!/usr/bin/env bash
# Exporta do stack local os dados do TCC: os resultados do laboratório, a série de VaR do PETR4 e as telas.
#
# Uso (na raiz do repositório, com `docker compose up -d postgres redis web frontend`):
#   bash tools/tcc/exportar.sh [pasta-de-dados]        # padrão: tools/tcc/dados
#
# Grava lab_result.csv, lab_year.csv, serie.csv e telas/*.png na pasta. Não escreve no banco: as consultas são
# só de leitura, e serie.py roda só os modelos baratos (Histórico e GARCH(1,1)), que não têm retratos.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
DADOS="${1:-tools/tcc/dados}"
mkdir -p "$DADOS/telas"
ATIVOS="'IBOV','PETR4','VALE3','ITUB4'"
psql_() { docker compose exec -T postgres sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -A -F";"'; }

psql_ > "$DADOS/lab_result.csv" <<SQL
select a.ticker, l.model_name, l.model_category, l.alpha, l.test_count, l.violations,
       round(l.expected_violations,1) ev, l.kupiec_passed kp, round(l.kupiec_p_value,4) kpv,
       l.christoffersen_passed cp, round(l.christoffersen_p_value,4) cpv, l.dq_passed dp, round(l.dq_p_value,4) dpv,
       l.adequate, l.error, l.hyperparameters
  from gold.lab_result l join gold.lab_run r on r.id = l.run_id join silver.asset a on a.id = r.asset_id
 where a.ticker in ($ATIVOS) order by a.ticker, l.alpha, l.model_name;
SQL

psql_ > "$DADOS/lab_year.csv" <<SQL
select a.ticker, l.model_name, l.alpha, y.index, y.start_date, y.end_date, y.test_count, y.violations,
       round(y.expected_violations,2), y.kupiec_passed, y.christoffersen_passed, y.adequate
  from gold.lab_year y join gold.lab_result l on l.id = y.result_id join gold.lab_run r on r.id = l.run_id
  join silver.asset a on a.id = r.asset_id
 where a.ticker in ($ATIVOS) order by 1, 2, 3, 4;
SQL

# a série do VaR, no worker (o único com o motor)
MSYS_NO_PATHCONV=1 docker compose run --rm -T -v "$(pwd)/tools/tcc:/tcc:ro" worker \
  python manage.py shell -c "exec(open('/tcc/serie.py').read())" > "$DADOS/serie.csv"

# as telas, no Playwright, na rede do contêiner frontend (o Vite só aceita localhost)
MSYS_NO_PATHCONV=1 docker run --rm --network container:ruvor-frontend-1 \
  -v "$(pwd)/$DADOS/telas:/out" -v "$(pwd)/tools/tcc/telas.mjs:/out/telas.mjs:ro" \
  -v "$(pwd)/frontend/e2e/node_modules:/out/node_modules:ro" -w /out \
  mcr.microsoft.com/playwright:v1.63.0-noble node telas.mjs
echo "dados em $DADOS"
