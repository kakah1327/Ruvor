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

**`ESTADO.md`** é o que responde "onde paramos": o que existe, pendências, dívidas. Com frentes
simultâneas, é atualizado **no fecho de cada bloco**; o andamento de cada frente,
sessão a sessão, mora em **`frentes/<frente>.md`**, e cada frente escreve só no seu
([`FRENTES.md`](FRENTES.md), [D-84](decisoes/D-84-frentes-com-cerca-de-pastas.md)).

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
FECHA             ver abaixo
```

### O passo FECHA

Fechar um bloco não é só marcar o roadmap. **Quatro artefatos apodrecem juntos se um deles
for esquecido**, e o sintoma só aparece na sessão seguinte, quando alguém age sobre status
mentiroso:

| Atualizar | Por quê |
|---|---|
| `ESTADO.md` | é a primeira leitura de toda sessão |
| `frentes/<frente>.md` | o próximo passo da frente passa a ser o bloco seguinte |
| `ROADMAP.md` | marca o bloco fechado |
| `aprendizados.md` | o que custou tempo e reincidiria |
| **cabeçalho de status da spec e do plano** | ficam dizendo "aguardando revisão" para sempre |
| **tabelas de `specs/README.md` e `planos/README.md`** | são o índice que alguém consulta antes de abrir o artefato |
| `CLAUDE.md`, se o bloco mudou o que existe no repositório | ele descreve o estado do código |

Os dois últimos itens da lista são os mais fáceis de esquecer e os que mais enganam: um
índice que diz "nenhum plano escrito ainda" faz o próximo agente escrever do zero em vez de
partir do modelo existente.

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

### Spec não é documento vivo

Distinção que evita duplicação e contradição:

| | Documento vivo | Spec |
|---|---|---|
| Responde | "como o sistema **é**" | "o que muda **agora**" |
| Vida | permanente, atualizado sempre | encerra quando o trabalho fecha |
| Onde | `PRODUTO.md`, `ARQUITETURA.md`, `decisoes/` | `specs/` |
| Escopo e critério de aceite | não tem | tem |

**A spec referencia; nunca repete.** Se a informação já está num documento vivo ou num
registro de decisão, a spec aponta para lá. Conteúdo duplicado começa igual e termina
divergente — e aí ninguém sabe qual dos dois manda.

Se ao escrever uma spec você percebe que ela está reescrevendo arquitetura, pare: ou aquilo
pertence ao documento vivo (e a spec só aponta), ou é decisão nova (e vira registro em
`decisoes/`).

### Antes de mandar revisar

A auto-revisão **não é formalidade** — é onde o defeito sai barato. Quem escreve tem o
contexto inteiro e acesso ao código; o revisor adversarial custa uma rodada completa de
leitura do projeto. A auto-revisão deve ser a cara, e a adversarial, confirmação.

Seis perguntas, cada uma derivada de defeito que já custou rodada neste projeto:

**1. Toda afirmação sobre o código existente foi conferida no código?**
Não vale "eu me lembro que". Abrir o arquivo. Afirmação plausível e falsa é o defeito mais
caro que existe: ela sobrevive à leitura de quem tem contexto e só cai na verificação.

**2. Todo requisito tem o comando ou o teste que o prova?**
Se não dá para escrever a verificação, o requisito não está pronto. "Configurado e passando",
sem dizer com que rigor, passa vazio — a checagem aprova por estar desligada.

**3. Todo artefato citado tem nome, local, conteúdo e dono?**
"Arquivo de trava", "metadados próprios", "dependência local" — substantivo sem definição
transfere a decisão para quem implementa, que decidirá diferente de você.

**4. Todo arquivo que existe hoje tem destino?**
Para spec de migração ou reestruturação, inventário explícito: cada arquivo migra, é
reescrito, é removido ou permanece. O que não está na lista fica sem dono — sobretudo quando
duas specs irmãs dividem o trabalho.

**5. Toda lista fechada foi derivada da fonte, não da memória?**
Opções de um comando: ler o arquivo do comando. Formatos de cor: ler o CSS. Lista fechada
incompleta é pior que lista aberta, porque parece decidida.

**6. A spec contradiz documento vivo ou decisão registrada?**
Listar o que ela toca e conferir um a um. Se contradiz, ou a spec muda, ou nasce decisão nova
que restrinja a antiga — nunca contradição silenciosa dentro da spec.

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

> **O plano especifica contratos, não corpos** — com duas exceções que valem mais que a regra.

Código completo em toda tarefa é desperdício: escreve-se duas vezes, e a segunda versão
diverge no minuto em que a realidade aparece. Revisar código em markdown também é pior que
revisar no editor.

Lista de tarefas soltas é pior ainda: o agente novo re-deriva decisões já tomadas, e cada um
deriva diferente. É a máquina de retrabalho.

### Quando o conteúdo entra no plano

Três casos, não dois:

**1. Quando o conteúdo *é* o contrato.** Arquivo de configuração, esquema, formato de
artefato gerado. `pyproject.toml`, configuração do verificador de tipos, `.gitattributes` —
não existe "implementação" separada do conteúdo. Descrevê-los em prosa transfere para quem
implementa uma decisão que já deveria estar tomada.

**2. Quando a lógica é sutil e a falha é silenciosa.** Teste que pode passar vazio,
comparação numérica com tolerância, verificação que ninguém percebe estar desligada. Aqui o
código no plano é barato, e o erro sem ele é caro — porque passa verde.

**3. Nos demais casos, não entra.** Mover arquivo, reescrever import, criar diretório: a
implementação é óbvia dado o contrato, e o comando exato já está no critério de aceite.

Numa base madura, o implementador infere pelo padrão do código existente. **Em projeto novo
não há padrão para imitar**, então a precisão precisa vir do plano — e pode afrouxar conforme
as convenções se estabelecem.

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

## 5.1 Ciclo de correção após revisão

Revisão que reprova **não reabre o portão humano**. O ciclo de correção é autônomo:

```
revisão reprova → orquestrador decide o que aceita → correção → nova revisão → ...
```

Roda até a revisão passar, **sem pedir permissão a cada volta**. Vale para spec, plano e
implementação.

O motivo: o portão humano existe para decidir **direção**, não para carimbar conserto. Se um
revisor aponta que falta um critério de aceite, corrigir é trabalho, não decisão.

### Quando escalar mesmo assim

Para e pergunta quando um achado exige **direção**, não conserto:

- a correção muda o **escopo** acordado
- o achado revela uma **decisão de produto** ainda não tomada
- há duas saídas válidas e a escolha depende de preferência, custo ou prazo — não de técnica
- corrigir contradiz uma **decisão registrada** em `decisoes/`

Nesses casos, junte as dúvidas e pergunte **de uma vez**, no fim da rodada — não uma a uma.

### O que o orquestrador faz com os achados

Ele **decide**, não obedece. Achado de revisor é informação, não ordem: pode ser aceito,
aceito em parte, ou recusado com motivo registrado. Quem responde pelo artefato é quem o
escreve.

## 6. Execução

Depois do plano aprovado, a implementação **roda até o fim sem pedir permissão**. Cada
tarefa termina quando seu critério de aceite passa; a próxima começa.

**Um agente por tarefa.** Paralelo só entre tarefas sem dependência e com arquivos
disjuntos.

**Commit por tarefa.** Dá para voltar ao ponto exato e revisar a execução passo a passo.

**Ramo por bloco, e PR para entrar na `main`**
([D-82](decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md), que substitui a
D-31). O ramo se chama `<frente>/<bloco>-<assunto>`. Do mesmo ramo saem três PRs — spec,
plano e implementação —, e **a aprovação de cada uma, por um dev de outra frente, é o portão
humano**. Merge com commit de merge, nunca _squash_, para o commit por tarefa sobreviver. A CI
roda em toda PR, e PR vermelha não entra ([D-83](decisoes/D-83-a-ci-barra-na-pr.md)).

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

### A que telas o portão se aplica

Vale para **tela de produto**: qualquer interface que um usuário final vá usar, ou que tenha
decisão de design a tomar.

Fica de fora o **casco técnico** — tela cuja única função é provar que a infraestrutura
responde, sem layout, navegação ou conteúdo de produto. Ver
[D-30](decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md).

Na dúvida, passa pelo portão: mockup é barato; tela errada implementada não é.

**Toda tarefa visual de produto vira duas.**

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

Ficam em `docs/mockups/<bloco>/`, versionados junto com a spec que os originou.

**Não confundir com `brand/ruvor/mockups/`**, que são as quatro telas de referência da
identidade visual — o vocabulário do produto, produzido no trabalho de marca. Os mockups do
portão são **derivados** delas para uma tela específica de um bloco. Aquilo é o vocabulário;
isto é a frase.

---

## 8. Agentes do projeto

Poucos, com papel nítido. Agente demais é overhead e vira loop.

Definidos em [`.claude/agents/`](../.claude/agents/) — versionados, porque são configuração
que o time compartilha.

| Agente | Papel | Nunca faz |
|---|---|---|
| [**explorador**](../.claude/agents/explorador.md) | lê código e documentos, devolve conclusão | escrever qualquer coisa |
| [**revisor**](../.claude/agents/revisor.md) | adversarial; usado em spec, plano e implementação | corrigir o que encontrou |
| [**implementador**](../.claude/agents/implementador.md) | executa **uma** tarefa do plano, dentro da cerca | sair da cerca, mudar contrato |

**A restrição vem da ferramenta, não da boa vontade.** O explorador e o revisor não têm
`Write` nem `Edit` — "não conserta o que encontrou" deixa de ser instrução que dá para
desobedecer e vira impossibilidade.

**O que vai na definição, e o que vai no despacho.** Regras invioláveis, condições de
parada e formato do relato pertencem à definição — repetir isso a cada despacho gasta token
e, pior, deixa o comportamento variar conforme quem escreveu o pedido. O despacho carrega só
o que é específico daquela tarefa.

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
bloco. Nunca direto na `main`.
