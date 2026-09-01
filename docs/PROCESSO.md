# Processo de desenvolvimento — Ruvor

Como o trabalho nasce, é revisado, implementado e fechado. Vale para pessoas e para
agentes.

---

## 1. Princípio

> **Portão humano onde o erro é caro e a máquina não detecta.
> Autonomia onde o teste detecta.**

Spec, plano e decisão visual dependem de julgamento — nenhum teste diz "essa era a tela
certa". Código com critério de aceite executável, não: o teste diz.

### O teste do agente novo

Um subagente **não compartilha contexto**. Nasce zerado, lê o que recebe, devolve
resultado. Isso economiza a janela do orquestrador e é a origem do retrabalho quando os
artefatos são frouxos.

Daí o critério que define o nível de detalhe de tudo:

> **Todo artefato — spec, plano, tarefa — precisa ser executável por alguém que nunca
> participou da conversa.**

Se depende de ter estado na sala, não está pronto.

---

## 2. Artefatos

```
CLAUDE.md                 curto: regras de trabalho + para onde ir
docs/
├── PROCESSO.md           este documento
├── ROADMAP.md            módulos, ordem, status — até onde vamos
├── ESTADO.md             onde estamos agora — primeira leitura de toda sessão
├── decisoes/             uma decisão por arquivo, numerada, nunca reescrita
├── specs/                uma por módulo
├── planos/               um por spec
├── mockups/              por módulo, HTML com os tokens reais
└── aprendizados.md       memória operacional entre agentes
```

**`CLAUDE.md` é carregado em toda conversa, então precisa ser curto.** Tudo que estiver
nele sai da janela de contexto disponível para o trabalho. É mapa, não território: regras
em poucas linhas e ponteiros para o resto.

**`ESTADO.md`** é o que responde "onde paramos": módulo corrente, spec corrente, tarefa
aberta, pendências. Atualizado ao fim de cada sessão.

**`decisoes/`** é o que garante diretriz constante entre conversas. Registro numerado,
append-only: uma decisão nunca é editada — é substituída por outra que cita a anterior.

---

## 3. O ciclo

```
ROADMAP  →  escolhe o módulo
    ↓
SPEC              conversa com o humano; o orquestrador escreve
    ↓ auto-revisão
    ↓ revisão adversarial (agente sem o contexto da conversa)
    ↓ ✋ APROVAÇÃO HUMANA
PLANO             tarefas com contrato, aceite executável, cerca e dependência
    ↓ revisão contra a spec
    ↓ ✋ APROVAÇÃO HUMANA
IMPLEMENTAÇÃO     execução contínua, 1 agente por tarefa, commit por tarefa
    ↓
    ├── tarefa visual → mockup → ✋ APROVAÇÃO → implementa → revisa contra o mockup
    ↓
REVISÃO FINAL     código contra spec e plano
    ↓
FECHA             atualiza ESTADO, ROADMAP e aprendizados
```

Portões humanos: **spec, plano e cada mockup**. O resto corre sozinho.

Um módulo fecha depois de N specs concluídas. Fechado o módulo, o ROADMAP avança.

---

## 4. Anatomia de uma spec

Uma spec descreve **o que deve existir e por quê** — nunca como implementar.

```markdown
# <Módulo / Funcionalidade>

## Problema
O que não funciona hoje, ou o que não existe. Sem solução ainda.

## Resultado esperado
Como se sabe que ficou pronto, em termos observáveis.

## Escopo
### Dentro
### Fora            ← tão importante quanto o "dentro"

## Requisitos
RF-xx  numerados e rastreáveis

## Contratos externos
As superfícies que outros blocos vão consumir: endpoints, formato de dado,
nomes de tabela. É o que precisa ser combinado antes.

## Decisões que esta spec assume
Referência aos registros em docs/decisoes/. Não repete o conteúdo.

## Riscos e questões em aberto
Explícitas. Uma spec com lacuna declarada é melhor que uma que finge não ter.
```

### Revisão da spec

- **Spec de módulo, ou que cria contrato novo, ou que atravessa mais de um bloco** →
  revisão por agente, **sem o histórico da conversa**. Se ele aponta ambiguidade lendo só o
  documento, corrigimos. Se entende tudo e não acha nada, a spec sobrevive sozinha. Isso
  transforma "a spec está boa?" de opinião em experimento.
- **Spec pequena, mudança local** → revisão inline pelo orquestrador. Se o agente precisa
  aprender o projeto inteiro para revisar meia página, o custo do contexto supera o ganho
  do olhar novo.

---

## 5. Anatomia de um plano

> **O plano especifica contratos, não corpos.**

Código completo dentro do plano é desperdício: escreve-se duas vezes, e a segunda versão
diverge no minuto em que a realidade aparece. Além disso, revisar código em markdown é pior
que revisar código no editor.

Lista de tarefas soltas é pior ainda: o agente novo re-deriva decisões já tomadas, e cada um
deriva diferente. É a máquina de retrabalho.

O ponto certo, por tarefa:

```markdown
### Tarefa N — <título>

**Depende de:** tarefas que precisam estar prontas antes
**Visual:** sim/não        ← se sim, exige mockup aprovado antes

**Arquivos**
- cria: caminho
- altera: caminho

**Contrato**
Assinatura de função, formato do endpoint, colunas da tabela — a superfície onde
esta tarefa toca as outras. É a única coisa combinada de antemão.

**Critério de aceite**
O teste que passa a passar. Executável, sempre.

**Cerca de escopo**
O que esta tarefa NÃO faz.
```

### Por que cada campo existe

| Campo | Evita |
|---|---|
| Arquivos | dois agentes na mesma linha |
| Contrato | cada tarefa inventar sua própria interface |
| Critério de aceite | "pronto" virar opinião |
| Cerca de escopo | o agente "melhorar de passagem" e estourar o diff |
| Dependências | paralelizar o que não pode |
| Marca visual | tarefa de tela passar direto sem mockup |

### Regra dura

**Tarefa sem critério de aceite executável não entra no plano.** É o que torna a execução
contínua segura: com um teste como critério, o agente não consegue se enganar sobre ter
terminado. Com "ficou bom", consegue.

---

## 6. Execução

Depois do plano aprovado, a implementação **roda até o fim sem pedir permissão**. Cada
tarefa termina quando seu critério de aceite passa; a próxima começa.

**Um agente por tarefa.** Paralelo só entre tarefas sem dependência e com arquivos
disjuntos.

**Commit por tarefa**, **ramo por plano**. Dá para voltar ao ponto exato, e o ramo
principal nunca fica quebrado no meio da execução.

### Quando parar

Quatro situações, todas de "o plano estava errado" — nunca de "preciso de permissão":

1. **Um contrato precisa mudar.** Muda a superfície entre tarefas e quebra as vizinhas em
   silêncio. Para e devolve; não improvisa.
2. **Ambiguidade real** que não se resolve pela spec.
3. **O teste falha de um jeito que indica erro de plano**, não de código.
4. **Uma premissa da spec se mostrou falsa.**

### Defeito pequeno

Corrige inline, sem abrir agente. O custo de subir um agente que precisa aprender o
contexto para consertar um detalhe não se paga.

---

## 7. Portão de mockup

**Toda tarefa visual vira duas.**

```
Tarefa N     mockup HTML da tela, usando os tokens reais do Ruvor
             ↓ revisão do mockup
             ↓ ✋ aprovação humana
Tarefa N+1   implementação seguindo o mockup aprovado
             ↓ revisão da implementação contra o mockup
```

Três razões:

- **Os mockups usam `brand/ruvor/tokens.css`**, não são desenho livre. O que se aprova é
  exatamente o que dá para construir — sem distância entre a arte e o que sai no navegador.
- **Revisar mockup é barato; revisar tela integrada é caro.** Mudar cor e reordenar bloco
  num HTML estático é questão de minutos; no componente já ligado a dados e estado, horas.
- **O mockup aprovado vira o critério da revisão.** Deixa de ser "ficou bonito?" e passa a
  ser "bate com o aprovado?", que é verificável.

Ficam em `docs/mockups/<módulo>/`, versionados junto com a spec que os originou.

---

## 8. Agentes do projeto

Poucos, com papel nítido. Agente demais é overhead e vira loop.

| Agente | Papel | Nunca faz |
|---|---|---|
| **explorador** | lê código e documentos, devolve conclusão | escrever qualquer coisa |
| **revisor** | adversarial; usado em spec, plano e implementação com listas diferentes | corrigir o que encontrou |
| **implementador** | executa **uma** tarefa do plano, dentro da cerca | sair da cerca, mudar contrato |

**O orquestrador nunca implementa.** Conversa, escreve spec, despacha, integra, decide. É
assim que a janela dele permanece pequena e ele aguenta o módulo inteiro.

**O revisor reporta, não conserta.** Se o revisor edita, ele e o implementador entram em
ping-pong e ninguém sabe qual é a versão boa. O revisor devolve achados; o orquestrador
decide o que vira correção.

**Escrever spec não é trabalho de agente.** Spec nasce da conversa com o humano.

---

## 9. Aprendizados

Todo agente de implementação nasce com contexto limpo. Sem memória compartilhada, **a mesma
armadilha é redescoberta a cada tarefa.** `docs/aprendizados.md` existe para evitar isso.

Não é retrospectiva de equipe — é **memória operacional para agentes**.

### Quando registrar

Ao encontrar, durante implementação ou revisão, algo que:

- custou tempo para descobrir e não estava documentado
- é contraintuitivo ou específico de uma biblioteca
- outro agente, com contexto limpo, erraria da mesma forma

Não registrar o que já está óbvio no código ou é convenção conhecida da linguagem.

### Formato

```markdown
## <título curto>
**Quando:** a situação que dispara este aprendizado
**Problema:** o que acontece se não souber
**Faça:** a ação correta
```

O campo **Quando** é o mais importante: é o que permite a um agente varrer o arquivo e
achar o que se aplica a ele sem ler tudo.

### Manutenção

O arquivo cresce e precisa de poda. Periodicamente: aprendizado que virou convenção do
código sai daqui e vira comentário ou teste; aprendizado sobre código que não existe mais é
removido. Arquivo longo demais deixa de ser lido, e aí não serve para nada.

---

## 10. Regras invioláveis

**Nunca inventar.** Não existe função, parâmetro, caminho de arquivo ou endpoint "provável".
Verifica antes de usar.

**Perguntar quando** a resposta muda o resultado e não dá para derivar da spec, das decisões
registradas ou do código.
**Não perguntar quando** é derivável, é convenção, ou é barato de reverter.

**O lugar de perguntar é a spec, não a implementação.** Pergunta que aparece durante a
implementação volta como correção da spec — e serve de termômetro: muitas perguntas na
implementação significam spec fraca.

**Contrato congelado durante a implementação.** Mudou, para e escala.

**Relatar fielmente.** Teste falhou, diz que falhou, com a saída. Etapa pulada, diz que
pulou. Não existe "deve funcionar".

**Commit sem assinatura de ferramenta.** Nenhum commit leva `Co-Authored-By`, referência a
Claude, link de sessão ou marca de qualquer assistente. A autoria do repositório é do time,
e só. Vale para todo commit, de qualquer agente, sem exceção.

**Commitar e enviar só quando pedido.** Agente não faz `commit` nem `push` por iniciativa
própria — exceto o commit por tarefa previsto na [§6](#6-execução), dentro do ramo do
plano.
