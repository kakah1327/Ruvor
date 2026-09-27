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
