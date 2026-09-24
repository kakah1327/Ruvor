# D-66 — Registry incompleto é erro, não silêncio; restringe, no consumo, o `except ImportError` do motor

**Status:** aceita · 2026-09-24

## Contexto

O registry do motor (`engine/src/engine/models/registry.py`) descarta em silêncio o modelo
cuja dependência não está instalada — `except ImportError: continue`. É **adequado para uma
biblioteca**: quem instalou `engine[traditional]` não quer que o pacote quebre por causa do
TensorFlow que não pediu.

É **inaceitável para uma execução que se diz completa**. Uma imagem construída sem o extra
`ml` produziria doze resultados em vez de dezoito, gravaria o manifesto do mesmo jeito, e
ninguém notaria — a execução pareceria bem-sucedida e a comparação entre modelos, que é o
diferencial do produto, estaria silenciosamente incompleta.

## Decisão

No consumo pela plataforma, **modelo pedido que não está no registry é erro alto, com nome**.

```python
load_all_model_modules()
load_all_backtest_modules()
faltando = [m for m in pedidos if m not in list_models()]
if faltando:
    raise ModelsMissing(faltando)
```

A regra vale sobre o que foi **pedido**: os nove por padrão — e aí ela denuncia registry
incompleto — ou os de `--model`, e aí denuncia nome errado. É a mesma regra, e é o que
impede a seleção de virar porta dos fundos.

O comando sai com **código 1** e **nada é gravado**.

## Consequências

- O motor **não muda**: ele continua descartando em silêncio, como biblioteca. Quem restringe
  é o consumidor, no molde da [D-54](D-54-transacao-por-ativo-restringe-a-d-48.md), que
  restringe a D-48 em vez de substituí-la.
- **A lista dos nove é constante de módulo** (`MODELS`, em `apps/risk/compute.py`), nunca
  `list_models()`: comparar o registry consigo mesmo faria `faltando` sair sempre vazio e a
  denúncia nunca disparar — critério passando vazio. Um teste confere
  `sorted(MODELS) == list_models()` num ambiente completo, para a lista não envelhecer calada.
- **As duas chamadas de `load_all_*` são parte da decisão, não detalhe de implementação.**
  Sem elas, `list_models()` lê um dicionário vazio e toda execução levanta `ModelsMissing`
  com os nove. Falha alto, então não passa despercebido — mas o `_REGISTRY` é **global de
  processo**, e por isso apenas um teste da suíte sabe reprovar a remoção delas.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-17).
