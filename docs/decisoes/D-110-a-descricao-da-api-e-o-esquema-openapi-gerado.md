# D-110 — A descrição da API é o esquema OpenAPI gerado pelo drf-spectacular, sem aviso nem erro

**Status:** aceita · 2026-09-28 · frente `identidade`

## Contexto

A D-11 previa, como custo do DRF, "documentação OpenAPI manual no Marco 4". As views são
`APIView` que montam o corpo à mão, e o gerador não adivinha o que devolvem.

## Decisão

`GET /api/v1/schema` devolve o esquema OpenAPI 3 em JSON, gerado pelo **drf-spectacular 0.30.0**
(versão fixa). O `DEFAULT_SCHEMA_CLASS` é `apps.accounts.schema.AutoSchema`, que põe a resposta
`default` apontando para o componente `ApiError` (o erro da D-86) em toda operação, e lista o
`apiKeyAuth` só nas operações de view com `api_key_scope = "read"`. Cada método declara
`extend_schema` com o corpo de entrada e o de sucesso; os envelopes montados à mão ganham
serializadores só de descrição. `manage.py spectacular --validate --fail-on-warn` passa, e um teste
confere o esquema contra o resolvedor, nos dois sentidos.

## Consequências

- Substitui a documentação manual que a D-11 previa; a lista de códigos de erro por rota continua
  nas specs, não no esquema.
- Toda view nova declara `extend_schema` em cada método, ou o teste do gerador reprova.
- Não há interface de documentação servida (Swagger, Redoc).
- Dois campos com o mesmo nome e escolhas diferentes precisam de nome em
  `SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"]`, ou o gerador avisa.

Origem: [spec M4.2 — API pública](../specs/M4.2-api-publica.md).
