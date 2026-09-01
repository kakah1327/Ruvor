# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-08-29

---

## Onde estamos

**Marco:** Fundação
**Bloco:** F1 — Documentação de base
**Situação:** 🟡 em andamento

O projeto está na fase de fundação. **Nenhuma linha de código da plataforma nova foi
escrita ainda** — e isso é proposital. O que existe de código é o protótipo VaR Lab, que
será substituído (ver [`docs/prototipo/`](prototipo/)).

## O que foi concluído

- **Definição de produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos,
  requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução,
  auditoria, regimes
- **Processo de trabalho** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano,
  agentes, portões
- **27 decisões registradas** — [decisoes/](decisoes/)
- **Roadmap** — [ROADMAP.md](ROADMAP.md)
- **Identidade visual** — kit em [`brand/ruvor/`](../brand/ruvor/); histórico em
  `brand/ruvor/estudos/`
- **Limpeza do repositório** — ruído removido, documentos históricos separados e marcados,
  assinaturas de ferramenta removidas do histórico do git

## Próximo passo

**Escrever a spec do bloco F2 — Esqueleto do repositório.**

É a primeira spec de verdade, e a primeira a passar pelo ciclo completo do
[PROCESSO.md](PROCESSO.md).

Escopo previsto: monorepo com `engine/` + `backend/` + `frontend/` + `infra/`, com o rebrand
de VaR Lab para Ruvor aplicado, e o motor numérico migrado do protótipo para `engine/` sem
alteração de comportamento.

---

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| Carteira: caminho barato ou caro | [PRODUTO.md](PRODUTO.md#6-restrições-de-produto) |
| Quais requisitos candidatos entram no Marco 1 | [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos) |
| Política de cobertura e atualização de ativos | [PRODUTO.md](PRODUTO.md#8-pendências-de-produto) |
| Hospedagem de produção | [ARQUITETURA.md](ARQUITETURA.md#ambientes) |
| Tema claro vs escuro | kit é claro; protótipo é escuro |

## Pendências que bloqueiam trabalho futuro

| Pendência | Bloqueia |
|---|---|
| **Kit de marca incompleto** — falta modo escuro, estados de interação e componentes de formulário | O portão de mockup do Marco 1: a tela de configuração de análise é um formulário grande |
| **Parecer sobre fronteira CVM** | Marco 2 (carteira) |
| **Verificação de marca e domínio "Ruvor"** | Nada agora; risco se descoberto tarde |
| **Medir o gargalo do treino** | Decisão sobre GPU vs paralelização — ver [D-20](decisoes/D-20-experimentos-em-cpu.md) |

## Ações pendentes do time

- **Os 4 devs precisam clonar o repositório de novo** (ou `git fetch origin && git reset
  --hard origin/main`). O histórico foi reescrito em 2026-08-29 para remover assinaturas de
  ferramenta — os identificadores de commit mudaram. Quem tiver trabalho não enviado precisa
  salvar antes.

---

## Trilha paralela — TCC

Independente da plataforma, é tempo de máquina. Nada iniciado. Sequência obrigatória:

1. Fixar a semente das redes neurais
2. Refazer a Tabela 1
3. Executar a Etapa 6
4. Escrever §4.5 e o Capítulo 5

Ver [ROADMAP.md](ROADMAP.md#trilha-paralela--tcc).
