# D-86 — Convenções da API HTTP

**Status:** aceita pelo dono da frente `marco1` · 2026-09-27 · contrato entre frentes: a PR que
a traz passa pela frente `fundamentos`. [`FRENTES.md`](../FRENTES.md#contratos-entre-frentes)
pedia a revisão das duas frentes que produzem o contrato, `marco1` e `identidade`; a
`identidade` está sem dono, e quem revisa por ela é a outra frente ativa

## Contexto

O DRF está decidido desde a [D-11](D-11-pilha-tecnologica.md), mas nada além disso: o
`settings.py` não tem `REST_FRAMEWORK`, e a única rota é `GET /health`. O M1.6 publica a primeira
API de negócio, e o M2.1 vai precisar das mesmas convenções. [`FRENTES.md`](../FRENTES.md#contratos-entre-frentes)
registra isso como contrato aberto, a decidir **antes da primeira spec que publicar rota**,
revisado pelas frentes que o consomem.

## Decisão

1. **Prefixo e versão:** toda rota de negócio mora em `/api/v1/`. Infraestrutura fica fora —
   `GET /health` não muda. Versão nova (`/api/v2/`) só quando uma resposta mudar de forma
   incompatível; acrescentar campo não é mudança incompatível.
2. **Recurso pelo nome que o usuário conhece:** plural, em inglês, identificado pela chave de
   negócio, não pelo `id` interno — `/api/v1/assets/ITUB4`, `/api/v1/assets/ITUB4/risk`.
3. **Um formato de erro, em toda a API:**
   ```json
   {"error": {"code": "asset_not_found", "message": "Ativo ITUB9 não existe.", "details": {}}}
   ```
   `code` é estável, em inglês e `snake_case`, e é o que o frontend trata; `message` é para
   gente, em português; `details` sempre aparece, vazio (`{}`) quando não há o que dizer. Os códigos HTTP seguem o uso comum (400, 401, 403,
   404, 405, 409, 422, 429, 500). Erro não previsto não vaza traceback. **Rota inexistente sob
   `/api/`** também responde neste formato, por uma view final da própria API — não pelo
   `handler404` do Django, que o `DEBUG` ligado ignora.
4. **Autorização explícita em toda rota:** cada view declara a sua classe de permissão; não há
   padrão silencioso. No Marco 1 a leitura é pública (`AllowAny`, "sem login", como a
   [PRODUTO](../PRODUTO.md#4-marcos) diz). O M2.1 escolhe o mecanismo de autenticação e troca a
   permissão onde precisar — ligar o login é mudar a classe declarada, não procurar rota aberta.
5. **Dados:** datas e instantes em ISO 8601 (instante com fuso); **decimais como string**, para
   não perder precisão — é o que o DRF já faz com `Decimal`; nomes de campo em `snake_case`, os
   mesmos das colunas quando o campo é a coluna.
6. **Listas paginadas** por cursor ou limite/deslocamento, com o total quando for barato; a
   forma exata é da spec que publicar a primeira lista. Série de um ativo com tamanho limitado
   pela própria coleta (preços, proventos) pode sair inteira, se a spec declarar a exceção.

## Consequências

- O M1.6 configura `REST_FRAMEWORK` (tratador de exceção que produz o formato de erro;
  permissão padrão **`IsAuthenticated`**, para que uma rota que esqueça de declarar a sua nasça
  fechada, não aberta) e publica as primeiras rotas em `/api/v1/`.
- O M2.1 herda o formato de erro e a regra de permissão declarada, e decide só o mecanismo.
- A frente `fundamentos`, quando expuser fundamentos, segue as mesmas convenções.
- Esta decisão é da faixa da `marco1` e vale para todas as frentes; por ser contrato, a PR que a
  traz passa pela revisão da `fundamentos` ([D-85](D-85-o-dono-da-frente-aprova-a-propria-pr.md)).
