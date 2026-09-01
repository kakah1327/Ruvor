# D-30 — Portao de mockup vale para tela de produto, nao para casco tecnico

**Status:** aceita · 2026-08-31

## Contexto

O [PROCESSO](../PROCESSO.md) declara que toda tarefa visual passa por mockup aprovado, e o `CLAUDE.md` repete isso entre as regras invioláveis.

A spec F2b cria uma tela que apenas prova que o React sobe, que os tokens carregam e que a marca aparece. Nao tem layout, navegacao, hierarquia nem conteudo de produto — nao ha o que aprovar. Um implementador que leia o `CLAUDE.md` primeiro encontra uma regra inviolavel e uma spec que a dispensa, sem saber qual vence.

## Decisão

O portao de mockup vale para **tela de produto** — qualquer interface que um usuario final va usar, ou que tenha decisao de design a tomar.

Fica de fora o **casco tecnico**: tela cuja unica funcao e provar que a infraestrutura responde, sem layout, navegacao ou conteudo de produto.

## Consequências

- A dispensa nao e decidida caso a caso dentro de cada spec: ou a tela cabe na definicao de casco tecnico, ou passa pelo portao.
- Na duvida, passa pelo portao. Mockup e barato; tela errada implementada nao e.
- O `PROCESSO` e o `CLAUDE.md` foram emendados para refletir esta distincao.
