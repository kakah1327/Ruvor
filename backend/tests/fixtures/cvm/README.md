# Fixtures da CVM

Zips **recortados** dos zips reais de ITR e DFP do portal de dados abertos da CVM. Cada
fixture tem **todos os membros** do zip de origem, com o mesmo nome e a mesma data de membro;
cada membro tem o cabeçalho e **só as linhas** das companhias do recorte — pelo `CD_CVM`, ou
pelo `CNPJ_CIA` em `composicao_capital` e `parecer`, que não têm `CD_CVM`. As linhas estão
**sem edição**: os bytes foram copiados sem decodificar, então o latin-1 e o fim de linha
são os da origem.

O que a fonte não traz — conta duplicada, escala `MILHAO`, a v1 da Petrobras, LPA incoerente,
descrição de `3.01` nova — é inserido **no teste**, e declarado ali, nunca aqui.

## Como regerar

`recortar.py`, à mão, com rede — nunca na suíte. No contêiner `worker`, cujo diretório de
trabalho é o `backend/`; da raiz do repositório:

```bash
MSYS_NO_PATHCONV=1 docker compose exec -T worker python -m tests.fixtures.cvm.recortar /tmp/cvm-originais
```

O diretório de trabalho (`/tmp/cvm-originais`, no contêiner) guarda os zips originais, que
**não se versionam**. `MSYS_NO_PATHCONV=1` é necessário no Git Bash: sem ele, o `/tmp/...`
vira um caminho do Windows, relativo ao diretório de trabalho do contêiner — que é o
`backend/` montado —, e os originais caem dentro do repositório.

A CVM regera os zips dos anos recentes toda semana: regerar muda o `Last-Modified` e, se a
CVM mudou alguma linha das companhias do recorte, o conteúdo.

## As fixtures

Baixadas em **2026-09-27** (data UTC do contêiner; noite de 2026-09-26 em Brasília). O hash
é o `content_sha256` do zip **original** (RF-06), não o da fixture.

| Fixture | Origem | `Last-Modified` | `content_sha256` do original | Companhias |
|---|---|---|---|---|
| `itr_2016.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2016.zip> | Tue, 06 Aug 2024 00:37:48 GMT | `43d1a13e4402cc930a09c8c1cb783c62fd6f511ca350a1c4a3dcd09e634ef8d2` | BB Seguridade |
| `itr_2019.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2019.zip> | Tue, 06 Aug 2024 00:06:49 GMT | `07d753843167ea3a443f6619f4c96a8f74021433a8077a3e573b4a2247e82fdb` | Petrobras |
| `itr_2024.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2024.zip> | Sun, 20 Sep 2026 11:11:59 GMT | `d68f8b355ad88eca2570280e87bf550403dca06a042de85f85dff2a276daa8b0` | as nove |
| `dfp_2024.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2024.zip> | Sun, 20 Sep 2026 10:23:47 GMT | `6d356c3987c8049de67b9aab81a15d417b48b0d34d656233b6397b8aa2a7afe3` | as nove |
| `itr_2025.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2025.zip> | Sun, 20 Sep 2026 10:56:49 GMT | `108f1ade99d10aeb3fc1878e5a38cbe0df12aa131e825ff370c070db573afefc` | Petrobras |
| `dfp_2025.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2025.zip> | Sun, 20 Sep 2026 10:18:59 GMT | `b6409e6b938d3707841f3072b6d0a7226608e071f3a354f227ac94604072607d` | Camil |

`itr_2016.zip` e `itr_2019.zip` têm dezoito membros — não há `composicao_capital` antes de
2020 —; os outros, dezenove.

## As companhias

`CD_CVM` como vem na CVM, com seis dígitos, e `DENOM_CIA` do índice do ITR 2024:

| `CD_CVM` | `DENOM_CIA` | Nas fixtures |
|---|---|---|
| `009512` | PETROLEO BRASILEIRO S.A. PETROBRAS | ITR 2019, 2024, 2025; DFP 2024 |
| `004170` | VALE S.A. | ITR 2024; DFP 2024 |
| `019348` | ITAU UNIBANCO HOLDING S.A. | ITR 2024; DFP 2024 |
| `000906` | BCO BRADESCO S.A. | ITR 2024; DFP 2024 |
| `023159` | BB SEGURIDADE PARTICIPAÇÕES S.A. | ITR 2016, 2024; DFP 2024 |
| `024805` | VIVARA PARTICIPAÇÕES S.A. | ITR 2024; DFP 2024 |
| `018627` | CIA SANEAMENTO DO PARANA - SANEPAR | ITR 2024; DFP 2024 |
| `001228` | BCO NORDESTE DO BRASIL S.A. | ITR 2024; DFP 2024 |
| `024228` | CAMIL ALIMENTOS S.A. | ITR 2024; DFP 2024, 2025 |

A Camil está no ITR 2024 **e** no DFP 2025: é o par do 4º trimestre de exercício não civil,
que cruza o ano do zip.

## O IPE (M3.2)

`ipe_2025.zip` e `ipe_2026.zip` são recortados do IPE real **por registro**, não por
companhia: uma companhia grande tem centenas de linhas por ano. Cada fixture tem o membro
único `ipe_cia_aberta_<ano>.csv`, com a data de membro da origem, o cabeçalho e **só as
linhas dos casos abaixo**, na ordem do arquivo de origem e copiadas em bytes (latin-1 e
`\r\n` como vieram). Nenhuma linha está editada; o que a fonte não traz — link repetido com
campo idêntico ou divergente (RF-04b), registro mal formado (RF-06) — é declarado no teste.

### Como regerar

Modo próprio, que grava **só** os dois zips do IPE — sem `--only`, o `recortar.py` baixaria
de novo ITR e DFP, que a CVM regera, e mudaria as fixtures do M3.1:

```bash
MSYS_NO_PATHCONV=1 docker compose exec -T worker python -m tests.fixtures.cvm.recortar /tmp/cvm-originais --only ipe
```

Um caso depende do catálogo (a companhia fora dele), que o `recortar.py` lê de
`silver.asset` (`kind = stock`) no banco configurado: o modo IPE precisa do banco de pé e do
catálogo importado, e recusa catálogo vazio. A CVM regera o zip do ano corrente **todo dia**
(spec, "A fonte, medida"): regerar pode mudar as linhas escolhidas.

| Fixture | Origem | `Last-Modified` | `content_sha256` do original | Linhas (origem → fixture) | Bytes da fixture |
|---|---|---|---|---|---|
| `ipe_2025.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2025.zip> | Sun, 27 Sep 2026 10:01:25 GMT | `39ff61aaf973b877ec9682b0633013f027af7bb2074a28fb2b305b419080f20a` | 49.277 → 65 | 4.341 |
| `ipe_2026.zip` | <https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2026.zip> | Sun, 27 Sep 2026 10:00:39 GMT | `f10fcbeea612ee49ae25191b9d0745684e77f02910573065ab7304b285c9169d` | 35.408 → 69 | 5.245 |

Baixadas em **2026-09-27** (data UTC do contêiner).

### As linhas escolhidas

As regras estão em `ipe_cases`, no `recortar.py`, e cada caso imprime o `Codigo_CVM` e o
link — os daqui foram copiados dessa saída. Os links abaixo abreviam o prefixo comum
`https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE&CodigoInstituicao=1&`.

**As nove de `CODES`, nos dois anos.** Por companhia e por ano: até **5 linhas** das três
categorias ("Fato Relevante", "Comunicado ao Mercado", "Aviso aos Acionistas"), em rodízio
entre elas e na ordem do arquivo (RF-03); a primeira de **`Assembleia`**, a categoria de fora
mais frequente (a mutação 3 da T11 depende dela); e a primeira de **outra categoria de fora**.
São 7 linhas por companhia e ano, menos a Camil em 2026, com 6: ela não tem "Fato Relevante"
em 2026, só três "Comunicado ao Mercado" e um "Aviso aos Acionistas". O rodízio pegou também
reapresentações (`RE`) e, em 2025, o `(Protocolo_Entrega, Versao)` repetido do Itaú (abaixo).

**Os casos**, cada um com o motivo:

| Ano | Caso | `Codigo_CVM` | Link (`numProtocolo`, `numSequencia`, `numVersao`) |
|---|---|---|---|
| 2025 | `(Protocolo_Entrega, Versao)` com dois links, do catálogo (RF-04): o primeiro repetido nas nove, `009512IPE200220250104570805-02`, versão 1, dois "Comunicado ao Mercado" | `9512` | `1337188`, `861914`, `1` e `1337189`, `861915`, `1` |
| 2026 | o fato relevante da Petrobras de 2026-09-19, "Petrobras informa sobre adesão à nova subvenção econômica" (V-06) | `9512` | `1569745`, `1094451`, `1` |
| 2026 | `Assunto` vazio em "Comunicado ao Mercado" (RF-05): o primeiro das nove | `9512` | `1544497`, `1069203`, `1` |
| 2026 | `Assunto` vazio em "Aviso aos Acionistas" (RF-05): nenhuma das nove tem; o primeiro do catálogo | `14451` | `1497199`, `1021905`, `1` |
| 2026 | o `Assunto` de **761** caracteres, o maior das três categorias em 2026, "Aviso aos Acionistas" (RF-05) | `3077` | `1525123`, `1049829`, `1` |
| 2026 | reapresentação: a primeira `RE` com `Versao` > 1 das nove, "Comunicado ao Mercado", versão 2 | `1228` | `1491850`, `1016556`, `2` |
| 2026 | duas linhas de companhia **fora do catálogo** e de `CODES` (RF-03): a primeira da ordem do arquivo, nas três categorias, e as duas primeiras linhas dela | `26190` | `1483373`, `1008079`, `1` e `1528345`, `1053051`, `1` |

`14451` (COMPANHIA ENERGÉTICA DE BRASÍLIA - CEB) e `3077` (COMPANHIA DE FIACAO E TECIDOS CEDRO
E CACHOEIRA) estão no catálogo mas fora de `CODES`: entram em `IPE_EXTRA_CODES`, na
`conftest.py`, e o teste que precisa deles os põe no catálogo. `26190` (CARAMURU ALIMENTOS
S.A.) não está no catálogo nem em nenhuma das duas constantes.

Um `(Protocolo_Entrega, Versao)` a mais veio pelo rodízio, sem regra própria: o do Itaú em
2025, `019348IPE050220250104569311-51`, versão 1, com um "Fato Relevante" (`1330895`,
`855621`, `1`) e um "Comunicado ao Mercado" (`1330899`, `855625`, `1`) — categorias
diferentes na mesma entrega. A fixture de 2025 tem, então, dois dos três que a spec mede.

A linha de "Assembleia" da Petrobras em 2026 (`1510187`, `1034893`, `1`) tem `Assunto` de
775 caracteres: é de categoria de fora, e não conta para o maior `Assunto` das três.
