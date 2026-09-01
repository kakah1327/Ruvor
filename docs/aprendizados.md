# Aprendizados

Memória operacional **entre agentes**. Não é retrospectiva de equipe.

Todo agente de implementação nasce com contexto limpo. Sem memória compartilhada, a mesma
armadilha é redescoberta a cada tarefa. Este arquivo existe para evitar isso.

## Como usar

**Antes de implementar:** varra os campos *Quando* e leia só o que se aplica à sua tarefa.

**Ao terminar:** registre o que custou tempo para descobrir e não estava documentado, o que
é contraintuitivo ou específico de uma biblioteca, e o que outro agente com contexto limpo
erraria da mesma forma.

Não registre o que já é óbvio no código ou é convenção conhecida da linguagem.

## Formato

```markdown
## <titulo curto>
**Quando:** a situacao que dispara este aprendizado
**Problema:** o que acontece se nao souber
**Faca:** a acao correta
```

O campo **Quando** é o mais importante: é o que permite varrer sem ler tudo.

## Manutenção

O arquivo cresce e precisa de poda. Periodicamente: aprendizado que virou convenção do
código sai daqui e vira comentário ou teste; aprendizado sobre código que não existe mais é
removido. Arquivo longo demais deixa de ser lido, e aí não serve para nada.

---

*Nenhum aprendizado registrado ainda.*
