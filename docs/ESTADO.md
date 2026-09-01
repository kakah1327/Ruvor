# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-09-01

---

## Onde estamos

**Marco:** Fundação
**Bloco:** F2a fechado; **F2b é o próximo**
**Ramo:** `f2a-migracao-do-motor`, 13 commits acima de `main`, **ainda não integrado**

O motor numérico existe como pacote isolado e verificado. A plataforma web ainda não foi
construída.

## O que foi concluído

### Documentação e processo (F1)

- **Produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos, requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução, auditoria, regimes
- **Processo** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano, agentes, portões
- **30 decisões registradas** — [decisoes/](decisoes/)
- **Identidade visual** — kit em [`brand/ruvor/`](../brand/ruvor/), com as quatro telas de
  referência em `brand/ruvor/mockups/`

### F2a — Migração do motor

O motor saiu de `varlab/` e virou o pacote `engine/`, com layout `src/`, empacotamento
próprio (`ruvor-engine`) e o rebrand aplicado. O protótipo Flask, a persistência SQLite e o
`pyproject.toml` da raiz foram removidos.

| Verificação | Resultado |
|---|---|
| `import engine` sem Django instalado | ✅ |
| Linha de base numérica | ✅ 12 combinações, diferença **zero** |
| Suíte de testes | ✅ 58 passando |
| Verificação de tipos | ✅ mypy limpo em 33 módulos |
| `engine/` não importa plataforma | ✅ detecção comprovada por mutação |
| Empacotamento | ✅ wheel e sdist gerados, sem `tests/` dentro |

**Revisão adversarial: aprovada**, sem achado grave. O revisor recriou o `varlab` original num
worktree de `main` e recalculou as 12 combinações — a linha de base é bit a bit idêntica ao
que o protótipo produzia.

## Próximo passo

**Integrar o ramo `f2a-migracao-do-motor` ao `main`**, e então escrever o plano do
[F2b — Casco da aplicação](specs/F2b-casco-da-aplicacao.md), cuja spec já está aprovada.

O F2b cria o projeto Django e o projeto React funcionais, com a identidade Ruvor. Depois dele
vêm F3 (ambiente local), F4 (banco e migrations), F5 (CI) e F6 (agentes do projeto).

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
| `ignore_errors` do mypy em `engine.models.ml._quantile_nn` e `engine.models.garch._conditional` | `engine/pyproject.toml`, comentado no próprio arquivo | Depois da Etapa 6, quando a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) deixar de congelar o motor |

Nenhum dos dois é defeito em execução. Corrigi-los exigiria anotar o motor, o que a D-21
proíbe até o experimento comparativo do TCC estar rodado.

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| Carteira: caminho barato ou caro | [PRODUTO.md](PRODUTO.md#6-restrições-de-produto) |
| Quais requisitos candidatos entram no Marco 1 | [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos) |
| Política de cobertura e atualização de ativos | [PRODUTO.md](PRODUTO.md#8-pendências-de-produto) |
| Hospedagem de produção | [ARQUITETURA.md](ARQUITETURA.md#ambientes) |
| Tema claro vs escuro | kit é claro; decisão de produto pendente |

## Pendências que bloqueiam trabalho futuro

| Pendência | Bloqueia |
|---|---|
| **Kit de marca incompleto** — faltam estados de interação (só `:active`) e modo escuro | O portão de mockup do Marco 1 |
| **Parecer sobre fronteira CVM** | Marco 2 (carteira) |
| **Verificação de marca e domínio "Ruvor"** | Nada agora; risco se descoberto tarde |
| **Medir o gargalo do treino** | Decisão sobre GPU vs paralelização — ver [D-20](decisoes/D-20-experimentos-em-cpu.md) |

---

## Trilha paralela — TCC

Independente da plataforma, é tempo de máquina. Nada iniciado. Sequência obrigatória:

1. Fixar a semente das redes neurais
2. Refazer a Tabela 1
3. Executar a Etapa 6
4. Escrever §4.5 e o Capítulo 5

O motor já roda por linha de comando (`ruvor run`), então a Etapa 6 pode ser executada assim
que a semente for corrigida.

Ver [ROADMAP.md](ROADMAP.md#trilha-paralela--tcc).
