# D-11 — Pilha: Python, Django, DRF, React, PostgreSQL

**Status:** aceita · 2026-08-29

## Contexto

O time tem experiencia em C#/.NET, Java, Laravel, Angular e React — nao em Python nem Django. Mas o ecossistema numerico (arch, TensorFlow, scipy, pandas) so existe em Python.

## Decisão

**Python + Django + Django REST Framework** no backend, **React** no frontend, **PostgreSQL** no banco.

## Consequências

- Django e o framework Python que mais se parece com Laravel e .NET: ORM oficial, migrations, autenticacao pronta, estrutura convencionada. O mapa mental e quase direto.
- Login, permissao e auditoria sao obrigatorios e completamente commodity; cada hora reimplementando isso e hora que nao foi para o motor de risco.
- DRF sobre django-ninja: ecossistema maior e mais material disponivel, o que pesa para um time aprendendo Django agora. O custo e documentacao OpenAPI manual no Marco 4.
- React sobre Angular (ambos no repertorio): este e um produto de visualizacao de dados, e o ecossistema de graficos e tabelas do React e mais rico nessa area.
