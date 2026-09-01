# D-27 — Commits sem assinatura de ferramenta

**Status:** aceita · 2026-08-29

## Contexto

Os commits do prototipo carregavam linhas de coautoria e link de sessao de assistente de IA.

## Decisão

**Nenhum commit leva `Co-Authored-By`, referencia a Claude, link de sessao ou marca de qualquer assistente.** A autoria do repositorio e do time.

## Consequências

- Vale para todo commit, de qualquer agente, sem excecao.
- O historico anterior foi reescrito: 5 dos 6 commits tinham assinatura, removidas em 2026-08-29 preservando autores, datas e conteudo.
- Agente nao faz commit nem envio por iniciativa propria, exceto o commit por tarefa dentro do ramo do plano.
