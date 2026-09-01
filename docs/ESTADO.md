# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-08-29

---

## Onde estamos

**Marco:** Fundação
**Bloco:** F2a e F2b — specs em revisão
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
- **30 decisões registradas** — [decisoes/](decisoes/)
- **Roadmap** — [ROADMAP.md](ROADMAP.md)
- **Identidade visual** — kit em [`brand/ruvor/`](../brand/ruvor/), incluindo as **quatro
  telas de referência** em `brand/ruvor/mockups/` (login, visão geral, nova análise,
  resultado analítico); histórico em `brand/ruvor/estudos/`
- **Limpeza do repositório** — ruído removido, documentos históricos separados e marcados,
  assinaturas de ferramenta removidas do histórico do git

## Próximo passo

**Aprovar as specs F2a e F2b**, e então escrever os planos.

As duas estão escritas e passaram por duas rodadas de revisão adversarial:

- [F2a — Migração do motor](specs/F2a-migracao-do-motor.md): `engine/` isolado, rebrand,
  empacotamento `ruvor-engine`, linha de base numérica
- [F2b — Casco da aplicação](specs/F2b-casco-da-aplicacao.md): Django e React funcionais,
  identidade Ruvor

O bloco F2 do roadmap foi dividido em dois porque código migrado e código novo exigem rigor
de tipagem oposto ([D-29](decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md)).

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
| **Kit de marca incompleto** — faltam estados de interação (só `:active`) e modo escuro | O portão de mockup do Marco 1 |
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
