# Ruvor Implementation Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um pacote independente que permita implementar a identidade Ruvor sem interpretar cores, componentes ou telas a partir de imagens.

**Architecture:** O pacote ficará em `brand/ruvor`, sem alterar o frontend atual. Tokens primitivos e semânticos existirão em CSS e JSON; exemplos HTML consumirão uma única folha de estilos. Logos e documentação ficarão no mesmo diretório para que possam ser compactados e enviados como uma unidade.

**Tech Stack:** SVG, CSS custom properties, JSON, HTML estático e ZIP.

---

### Task 1: Consolidar tokens e contratos de interface

**Files:**
- Modify: `brand/ruvor/tokens.css`
- Create: `brand/ruvor/tokens.json`
- Create: `brand/ruvor/implementation.css`

- [ ] Definir tokens de cor primitivos e semânticos, tipografia, espaçamento, raios, elevação e estados.
- [ ] Espelhar os valores de cor e escala em JSON para ferramentas e implementações não-CSS.
- [ ] Criar estilos base para shell, navegação, cards, botões, chips, tabelas, alertas e gráfico de referência.
- [ ] Validar que todos os valores de cor presentes no CSS pertencem à paleta aprovada.

### Task 2: Entregar referências de tela consumindo os tokens

**Files:**
- Create: `brand/ruvor/examples/dashboard.html`
- Create: `brand/ruvor/examples/model-detail.html`
- Create: `brand/ruvor/examples/integration.html`

- [ ] Construir uma tela de visão de risco com ranking, estado crítico e séries comparadas.
- [ ] Construir uma tela de detalhe de modelo com backtests, evidência e ação de revisão.
- [ ] Construir uma tela de integração B2B com credenciais, status e exemplo de resposta.
- [ ] Garantir que cada exemplo carregue somente `../implementation.css` e `../tokens.css`.

### Task 3: Documentar e empacotar o handoff

**Files:**
- Modify: `brand/ruvor/README.md`
- Create: `brand/ruvor/component-guidelines.md`
- Create: `brand/ruvor/IMPLEMENTER-START-HERE.md`
- Create: `deliverables/ruvor-implementation-kit.zip`

- [ ] Documentar árvore de arquivos, ordem de leitura e regras de marca.
- [ ] Especificar cada componente e seus estados semânticos.
- [ ] Adicionar instruções de uso dos SVGs e dos exemplos.
- [ ] Validar XML dos SVGs, JSON e links locais dos exemplos antes de compactar.
