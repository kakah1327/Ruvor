# Ruvor

Plataforma de análise de risco em ações. O usuário quer saber **quanto pode perder** se
aplicar em uma ação ou carteira, e a plataforma responde com transparência sobre o método.

**Diferencial:** múltiplos algoritmos comparados sobre a mesma base, com validação
estatística de qual deles merece confiança para aquele ativo.

---

## Comece por aqui

1. **[`docs/ESTADO.md`](docs/ESTADO.md)** — onde paramos e o que está aberto. **Leia sempre.**
2. **[`docs/PROCESSO.md`](docs/PROCESSO.md)** — como se trabalha aqui. **Leia antes de produzir qualquer coisa.**
3. **[`docs/aprendizados.md`](docs/aprendizados.md)** — armadilhas já descobertas. Leia antes de implementar.

Antes de mandar spec ou plano para revisão, rode a
[lista de verificação](docs/PROCESSO.md#antes-de-mandar-revisar). A primeira spec do projeto
custou cinco rodadas de revisão pelos seis defeitos que ela cobre.

---

## Autoridade dos documentos

Nem tudo no repositório é referência. Esta tabela resolve dúvida.

### Manda

| Documento | Sobre |
|---|---|
| [`docs/PROCESSO.md`](docs/PROCESSO.md) | como spec, plano e código nascem e são revisados |
| [`docs/PRODUTO.md`](docs/PRODUTO.md) | o que a plataforma é, para quem, marcos |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | pilha, estrutura, banco, execução, auditoria |
| [`docs/decisoes/`](docs/decisoes/) | decisões tomadas, com o porquê — **append-only** |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | ordem dos blocos e status |
| [`docs/ESTADO.md`](docs/ESTADO.md) | posição atual |
| [`docs/specs/`](docs/specs/) e [`docs/planos/`](docs/planos/) | o trabalho corrente |
| [`brand/ruvor/`](brand/ruvor/) | tokens, logo, regras e as quatro telas de referência (`mockups/`) |

### NÃO é referência

| Caminho | O que é | Cuidado |
|---|---|---|
| [`docs/prototipo/`](docs/prototipo/) | documentação do protótipo **VaR Lab**, que está sendo substituído | linha de base de revisão, **não** modelo de spec nem de código |
| `frontend/src/` | frontend do protótipo | não fala com o motor: a API que consumia deixou de existir. Substituído no F2b |
| [`docs/tcc/`](docs/tcc/) | trabalho acadêmico | escopo de pesquisa, **não** especificação de produto |
| `brand/ruvor/estudos/` | histórico de como se chegou à marca | em divergência com o kit, **o kit vence** |
| `brand/ruvor/examples/` | estudos visuais anteriores | em divergência, **`brand/ruvor/mockups/` vence** |

Se um documento antigo contradiz um destes, **estes vencem**.

---

## Regras invioláveis

**Commits sem assinatura de ferramenta.** Nenhum commit leva `Co-Authored-By`, referência a
assistente de IA ou link de sessão. A autoria é do time. Sem exceção
([D-27](docs/decisoes/D-27-commits-sem-assinatura.md)).

**Não commitar nem enviar por iniciativa própria.** Exceto o commit por tarefa dentro do
ramo do plano.

**Nunca inventar.** Não existe função, parâmetro, caminho ou endpoint "provável". Verifica
antes de usar.

**Perguntar quando** a resposta muda o resultado e não dá para derivar da spec, das decisões
ou do código. **Não perguntar quando** é derivável, convenção, ou barato de reverter.

**O lugar de perguntar é a spec, não a implementação.**

**Contrato congelado durante a implementação.** Mudou, para e escala.

**Relatar fielmente.** Teste falhou, diz que falhou, com a saída. Etapa pulada, diz que
pulou. Não existe "deve funcionar".

**`engine/` não importa Django.** Nunca ([D-17](docs/decisoes/D-17-monorepo-engine-sem-django.md)).

**Toda tela de produto passa por mockup aprovado antes de virar código**
([PROCESSO.md §7](docs/PROCESSO.md#7-portão-de-mockup)). Casco técnico — tela que só prova
que a infraestrutura responde — está fora
([D-30](docs/decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md)).

---

## Como o trabalho anda

```
ROADMAP → SPEC → ✋ → PLANO → ✋ → IMPLEMENTAÇÃO (contínua) → REVISÃO → fecha
                                    └ tarefa visual → mockup → ✋ → implementa
```

**Portões humanos:** spec, plano e cada mockup. O resto roda sozinho.
**Princípio:** portão humano onde o erro é caro e a máquina não detecta; autonomia onde o
teste detecta.

Detalhe completo, incluindo a anatomia de spec e de plano, em
[`docs/PROCESSO.md`](docs/PROCESSO.md).

---

## Idioma

Documentação, specs, planos, decisões, comentários e mensagens de commit **em português**.
Código — nomes de variável, função, classe — em inglês.

---

## Estado do repositório

A **plataforma web ainda não foi construída** — não há Django, banco nem API.

O que existe é o **motor numérico**, em `engine/`: pacote Python isolado, instalável e
publicável por si só (`ruvor-engine`), com 9 modelos de VaR, 4 testes de backtesting, 58
testes automatizados e uma linha de base numérica que prova que o comportamento não mudou na
migração. Roda por linha de comando: `ruvor run`.

O protótipo Flask e a persistência SQLite foram removidos. O `frontend/` ainda é o do
protótipo e sai no F2b.
