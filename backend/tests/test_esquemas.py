"""F4-01 e F4-02: os quatro esquemas existem, e as tabelas sao a lista fechada.

Sao quarenta e uma tabelas. O F4 criou nove — as duas do `core`, as duas de juncao do usuario
e as cinco do Django no `public` —, o M1.1 acrescentou as quatro do catalogo de ativos —
tres na `bronze` (`collection_run`, `b3_company_listing`, `b3_company_detail`) e uma na
`silver` (`asset`) — e o M1.2 acrescentou as tres dos precos: uma na `bronze`
(`yahoo_chart`) e duas na `silver` (`price`, `corporate_event`). O M1.3 acrescentou as
duas da camada 2, ambas na `gold` (`behavior_metric`, `return_histogram_bin`), e o M1.4
acrescentou as duas da camada 3, tambem na `gold` (`risk_run`, `risk_result`). O M3.1
acrescentou as quatro dos fundamentos: uma na `bronze` (`cvm_file`), duas na `silver`
(`company`, `financial_statement`) e uma na `gold` (`fundamental_indicator`). O M1.5b
acrescentou a dos retratos dos modelos caros, na `gold` (`model_snapshot`). O M3.2
acrescentou as duas do contexto: uma na `silver` (`disclosure`) e uma na `gold`
(`peer_comparison`). O M1.6a acrescentou a do pedido de calculo sob demanda, no `core`
(`compute_request`). O M2.1a acrescentou duas: a da auditoria de acesso, no `core`
(`access_event`), e a da sessao do Django, no `public` (`django_session`). O M4.2
acrescentou a das chaves de API, no `core` (`api_key`), e o M4.1, a dos relatorios, tambem no
`core` (`report`). O M2.2a acrescentou as cinco da carteira: tres no `core` (`portfolio`,
`portfolio_version`, `portfolio_holding`) e duas na `gold` (`portfolio_risk_run`,
`portfolio_risk_result`). O M2.4 acrescentou as tres do laboratorio, na `gold` (`lab_run`,
`lab_result`, `lab_year`), e o M5.1, as duas do retorno, tambem na `gold` (`return_run`,
`return_result`).

Usa `django_db_blocker` e nao a marca `django_db` pelo mesmo motivo do
`test_conexao_com_o_banco`: a marca conecta em `test_<nome>`, um banco que o proprio
pytest-django cria e migra, e por isso nao diz nada sobre o banco configurado — que e
onde os esquemas precisam existir de verdade. Inspeciona o banco da conexao corrente —
configurado quando isolado, `test_<nome>` na suite inteira, porque os testes de
`tests/assets/` vem antes e a marca deles renomeia a conexao ate o fim da sessao.

A comparacao e de conjunto INTEIRO, nunca de amostra: `assertIn` aprovaria com uma
tabela de dominio nascida no `public`, que e exatamente o que F4-02 proibe.

Esta lista e a fonte da lista fechada. Ela aparece na forma literal `esquema.tabela`
porque o criterio de aceite a extrai deste arquivo e a confronta com o banco.
"""

from django.db import connection
from pytest_django.plugin import DjangoDbBlocker

ESQUEMAS = {"core", "bronze", "silver", "gold"}

TABELAS = {
    "bronze.b3_company_detail",
    "bronze.b3_company_listing",
    "bronze.collection_run",
    "bronze.cvm_file",
    "bronze.yahoo_chart",
    "core.access_event",
    "core.api_key",
    "core.compute_request",
    "core.organization",
    "core.portfolio",
    "core.portfolio_holding",
    "core.portfolio_version",
    "core.report",
    "core.user",
    "core.user_groups",
    "core.user_user_permissions",
    "gold.behavior_metric",
    "gold.fundamental_indicator",
    "gold.lab_result",
    "gold.lab_run",
    "gold.lab_year",
    "gold.model_snapshot",
    "gold.peer_comparison",
    "gold.portfolio_risk_result",
    "gold.portfolio_risk_run",
    "gold.return_histogram_bin",
    "gold.return_result",
    "gold.return_run",
    "gold.risk_result",
    "gold.risk_run",
    "gold.stress_episode",
    "public.auth_group",
    "public.auth_group_permissions",
    "public.auth_permission",
    "public.django_content_type",
    "public.django_migrations",
    "public.django_session",
    "silver.asset",
    "silver.company",
    "silver.corporate_event",
    "silver.disclosure",
    "silver.financial_statement",
    "silver.price",
}


def test_os_quatro_esquemas_existem(django_db_blocker: DjangoDbBlocker) -> None:
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata"
            " WHERE schema_name IN ('core', 'bronze', 'silver', 'gold')"
        )
        encontrados = {linha[0] for linha in cursor.fetchall()}

    assert encontrados == ESQUEMAS


def test_o_conjunto_de_tabelas_e_a_lista_fechada(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT schemaname || '.' || tablename FROM pg_tables"
            " WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        )
        encontradas = {linha[0] for linha in cursor.fetchall()}

    assert encontradas == TABELAS
