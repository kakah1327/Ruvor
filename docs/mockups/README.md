# Mockups

Um diretório por bloco. HTML estático, usando **os tokens reais** de
[`brand/ruvor/tokens.css`](../../brand/ruvor/tokens.css).

## Por que existem

Toda tarefa visual vira duas: primeiro o mockup, depois a implementação
([PROCESSO.md §7](../PROCESSO.md#7-portão-de-mockup)).

- **Revisar mockup é barato; revisar tela integrada é caro.** Mudar cor e reordenar bloco num
  HTML estático leva minutos; no componente já ligado a dados e estado, horas.
- **Usar os tokens reais** garante que o que se aprova é exatamente o que dá para construir —
  sem distância entre a arte e o que sai no navegador.
- **O mockup aprovado vira o critério da revisão** da implementação. Deixa de ser "ficou
  bonito?" e passa a ser "bate com o aprovado?", que é verificável.

## Regras

- Nada de valor de cor escrito à mão — só tokens
- Um arquivo por tela; nomes semânticos
- Iteração ganha sufixo de versão (`busca-v2.html`), nunca sobrescreve

## Mockups

| Bloco | Arquivo | O que é | Situação |
|---|---|---|---|
| M1.6a | [`M1.6a/kit.html`](M1.6a/kit.html) | a vitrine do kit: cada token e cada componente, em todos os estados, nos dois temas, com a chave de tema e os ícones do conjunto | ✅ aprovada pelo dono da frente em 2026-09-28 |
| M1.6a | [`M1.6a/icones-comparativo.html`](M1.6a/icones-comparativo.html) | Lucide, Phosphor e Radix aplicados ao kit, lado a lado, para a escolha da biblioteca de ícones | ✅ usado no portão; o Phosphor foi escolhido ([D-93](../decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md)) |
| M1.6b | [`M1.6b/graficos-comparativo.html`](M1.6b/graficos-comparativo.html) | Recharts, uPlot e lightweight-charts desenhando preço, distribuição de retornos e VaR por modelo, com dado real da API pelo proxy do Vite, nos dois temas, para a escolha da biblioteca de gráfico | ✅ usado na escolha; o uPlot foi escolhido ([D-94](../decisoes/D-94-os-graficos-sao-do-uplot.md)) |
| M1.6b | [`M1.6b/busca.html`](M1.6b/busca.html) | o casco e a busca: barra, chave de tema, rodapé com a ressalva, a página inicial em todos os estados e a lista suspensa; dado real pelo proxy | ✅ aprovado pelo dono em 2026-09-28 |
| M1.6b | [`M1.6b/ativo.html`](M1.6b/ativo.html) | a tela do ativo com dado real do ITUB4: cabeçalho, preço, proventos, comportamento, risco com discordância, não rejeitados e a tabela dos nove, trilha; com os textos de cada número | ✅ aprovado pelo dono em 2026-09-28, com cinco ajustes aplicados |
| M1.6b | [`M1.6b/ativo-estados.html`](M1.6b/ativo-estados.html) | os estados da seção de risco (E2 a E9, E6b, carregando e erro), as respostas do pedido, cada motivo, e os estados fora do risco (comportamento não calculado, sem preço, índice, ativo não encontrado, erro de seção) | ✅ aprovado pelo dono em 2026-09-28 |
| M1.6c | [`M1.6c/ativo-fundamentos.html`](M1.6c/ativo-fundamentos.html) | as seções Fundamentos e Comunicados da companhia à CVM depois do risco, com dado real da PETR4 e do ITUB4 pelo proxy (os pares, o filtro e o "mostrar mais"); os estados montados à mão num seletor — sem indicador (AZEV11 e IBOV reais), pares `subsector`/`none`/nulos, P/L negativo, cada motivo de `per_share_missing` e `market_cap_missing`, o plano de contas, a genérica, sem comunicados, filtro sem resultado, os dois `company: null`, carregando e erro —; e a tabela de todos os textos novos | ✅ aprovado pelo dono em 2026-09-29 |
| M1.7 | [`M1.7/busca-sugestao.html`](M1.7/busca-sugestao.html) | a sugestão vinda da API (`GET /api/v1/assets?has_risk=true&limit=8`) na página inicial e na tela "ativo não encontrado", num seletor de estados — carregando, erro, nenhum ativo com risco, a lista (`count` 6, o conjunto de `has_risk` de hoje) e o "e mais N" (`count` 11, montado à mão com tickers reais do catálogo) —; a barra fora de `/` sem sugestão; e a tabela dos textos novos | ✅ aprovado pelo dono em 2026-10-02 |
| M2.3 | [`M2.3/casco-e-preco.html`](M2.3/casco-e-preco.html) | o alternador Iniciante/Avançada no casco, ao lado do tema, em 1440 e 360 px (na 1ª linha em ≤720 px); o cabeçalho, o preço e os proventos do ITUB4 nos dois níveis, nos dois temas, com dado real pelo proxy; a conferência técnica em [`M2.3/conferencia-casco.md`](M2.3/conferencia-casco.md) | ✅ aprovado pelo dono em 2026-10-02, com as avançadas em palavras |
| M2.3 | [`M2.3/comportamento.html`](M2.3/comportamento.html) | as frases avançadas do comportamento do ITUB4 e o controle de recolher — a assimetria e a curtose recolhidas na iniciante ("Ver a assimetria e a curtose") e abertas na avançada; a conferência em [`M2.3/conferencia-comportamento.md`](M2.3/conferencia-comportamento.md) | ✅ aprovado pelo dono em 2026-10-02. **Mostra a iniciante antiga de `comportamento.return_ytd`**: a emenda aprovada no mesmo portão vale no código, não no mockup |
| M2.3 | [`M2.3/risco.html`](M2.3/risco.html) | as frases avançadas do risco do ITUB4; a tabela dos nove ("Ver os nove modelos"), as linhas de teste e a trilha ("Ver o que entrou no cálculo") recolhidas e abertas; a `risco.tabela.intro` avançada; a vista `d64`, com a expressão da D-64 por chave e ramo; a conferência em [`M2.3/conferencia-risco.md`](M2.3/conferencia-risco.md) | ✅ aprovado pelo dono em 2026-10-02, com a **alternativa** da D-64 — a expressão única "não do número de hoje", literal na vista `d64`. **A vista `itub4` ainda aplica a proposta antiga**: vale a `d64`. **Não reflete o M1.4b**: as avançadas de `risco.perda95` e `risco.perda99` são as do RF-14 da [spec do M1.4b](../specs/M1.4b-correcao-do-motor.md#rf-14), aprovadas no portão dela sem mockup novo (D-158); vale o código |
| M2.3 | [`M2.3/fundamentos.html`](M2.3/fundamentos.html) | as frases avançadas dos dezoito números da seção e da posição entre os pares, com o PETR4 (e a VALE3), nos dois níveis e nos dois temas; a conferência em [`M2.3/conferencia-fundamentos.md`](M2.3/conferencia-fundamentos.md) | ✅ aprovado pelo dono em 2026-10-02. **Mostra a iniciante antiga de `fundamentos.pares.abaixoDeTodas`**: a emenda aprovada no mesmo portão vale no código, não no mockup |
| M3.3 | [`M3.3/ativo-estresse.html`](M3.3/ativo-estresse.html) | o bloco "Em momentos de estresse" na seção Comportamento, depois de "Maior queda", com dado real do PETR4 e do IBOV (foto do `/metrics` de 2026-10-02, a página abre sem servidor); os estados do RF-12 montados à mão — cada motivo de "sem dado" com o Ibovespa mostrado, o índice nulo, a queda zero, a recuperação nula com a janela que difere do recorte, `stress: []` —; nos dois níveis e nos dois temas; e a tabela de todos os textos novos, com o trecho de `stress.py` que confere cada frase avançada | ✅ aprovado pelo dono em 2026-10-02, sem ajuste — com as duas chaves novas fora da tabela do plano (`semDado.rotulo` e `nadaARecuperar`) |
| M2.1b | [`M2.1b/entrada.html`](M2.1b/entrada.html) | a entrada (`/entrar`), fora do casco: a cena escura com a marca e a saudação neutra, o formulário ao lado, a nota sob a senha, "Criar conta" e "Continuar sem entrar"; vazio, enviando, os erros de campo e os gerais (o bloqueio com a espera); os dois temas e 360 px (a cena vira faixa); a tabela dos textos | ✅ aprovado pelo dono em 2026-10-03 — o bloqueio em minutos a partir de 60 s, os campos preenchidos depois do erro geral |
| M2.1b | [`M2.1b/cadastro.html`](M2.1b/cadastro.html) | o cadastro (`/cadastro`), na mesma cena: nome, e-mail, senha e confirmação, a dica dos requisitos antes do campo, a frase da conta pessoal, os erros por campo como a API os manda (a semelhança mostrando "name"), `email_taken` com o link para entrar, a confirmação diferente, 429, `csrf_failed` e rede | ✅ aprovado pelo dono em 2026-10-03 — a dica da senha compartilhada com as duas trocas |
| M2.1b | [`M2.1b/senha.html`](M2.1b/senha.html) | a troca de senha nos dois modos: a voluntária (`/conta/senha`) no casco, com o menu de conta, e a obrigatória na cena, com o porquê e o "Sair"; os erros, o 401 no lugar do formulário e o sucesso com "Continuar" | ✅ aprovado pelo dono em 2026-10-03 — o "Continuar" depois do sucesso, o 401 nas duas trocas |
| M2.1b | [`M2.1b/conta.html`](M2.1b/conta.html) | a conta no casco: a barra nos três estados (carregando, "Entrar", o botão de conta), o menu aberto na organização pessoal e na real, o convite a entrar para calcular no E7/E8, o aviso de sessão terminada e o "para quem entrou"; a barra estreita | ✅ aprovado pelo dono em 2026-10-03 — o menu de conta **por último**, depois da chave de tema, num lugar de largura fixa; só as iniciais abaixo de 1024 px; a barra em três linhas até 840 px; o Sair que falha mantém a sessão |
| M2.1b | [`M2.1b/usuarios.html`](M2.1b/usuarios.html) | a gestão de usuários (`/organizacao/usuarios`), no casco: a lista com "você", a senha provisória por trocar, "nunca entrou" e "mostrar mais"; criar, com o papel no segmentado; o diálogo da senha provisória com "copiar"; as confirmações de cada ação; os casos de membro e de organização pessoal; os erros | ✅ aprovado pelo dono em 2026-10-03 — o papel `admin` se mostra **"Administração"** |

A vitrine não é tela de produto: consome só `tokens.css` e `components.css`, e as classes de
estado forçado (`.is-hover`, `.is-focus`) existem só nela. O serviço `frontend` monta este
diretório só para leitura, e `frontend/tests/icones.test.ts` confere que todo ícone do conjunto
aparece na vitrine.
