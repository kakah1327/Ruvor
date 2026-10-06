# D-193 — A tela do ativo é dividida em seis abas, cada uma com o seu endereço; a ordem das seções vira a ordem das abas — restringe a D-99, a D-187 e a D-192

**Status:** aceita · 2026-10-04 · frente `marco1`, no ramo `marco1/ajustes-de-tela`. A decisão foi do Kauã,
dono do repositório, numa sessão de ajustes de tela feitos na hora e vistos no navegador. O portão de
mockup ([PROCESSO §7](../PROCESSO.md#7-portão-de-mockup)) foi a aprovação dele na conversa, olhando a tela
rodando. O `frontend/` é da `marco1` (darkside171): a PR do ramo passa pela revisão dela.

## Contexto

Desde o M1.6b, a tela do ativo é uma página só, em rolagem. Cada bloco que entrou depois foi para baixo do
anterior: as camadas 4 e 5 depois do risco ([D-99](D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md)),
o laboratório logo depois do risco ([D-187](D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md))
e o retorno depois do laboratório ([D-192](D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md),
item 1). Com nove seções, a página do `ITUB4` passava de 6.600 px na leitura avançada, e o dono achou a
tela uma landing page cansativa, e não uma ferramenta.

## Decisão

1. **O cabeçalho do ativo fica fixo no topo**, com a identidade e o último fechamento. Abaixo dele vem uma
   barra de abas, e só a seção da aba escolhida aparece:

   | Aba | Endereço | Seções |
   |---|---|---|
   | Visão geral | `/ativos/{ticker}` | preço, proventos e comportamento |
   | Risco | `/ativos/{ticker}/risco` | o risco, com a trilha do cálculo na coluna lateral |
   | Laboratório | `/ativos/{ticker}/laboratorio` | o laboratório |
   | Retorno | `/ativos/{ticker}/retorno` | o retorno |
   | Fundamentos | `/ativos/{ticker}/fundamentos` | os fundamentos |
   | Comunicados | `/ativos/{ticker}/comunicados` | os comunicados |

2. **A ordem das seções da D-99, da D-187 e da D-192 passa a ser a ordem das abas**: risco, depois
   laboratório, depois retorno, depois Fundamentos, depois Comunicados. O que essas decisões dizem sobre
   cada seção continua valendo. Só a disposição em rolagem dá lugar às abas.
3. **Cada aba tem o seu endereço**, e o voltar do navegador anda entre elas. Segmento desconhecido vira a
   visão geral, com `replace`. O código em minúsculas continua virando maiúsculas, sem entrada nova no
   histórico.
4. **As rotas do ativo continuam pedidas todas ao montar a tela**, qualquer que seja a aba, e trocar de
   aba não as pede de novo. O acompanhamento do cálculo corre em qualquer aba. A exceção é `/disclosures`,
   que a seção Comunicados pede sozinha, como antes: ela só é pedida com a aba aberta.
5. **A trilha do cálculo só aparece na aba Risco.** O "Ir para o risco" do comportamento e o convite a
   entrar levam à aba Risco: o `next` do convite passa a ser `/ativos/{ticker}/risco`.
6. **O `data-ready` não muda**: o cabeçalho e o risco terminados, em qualquer aba.
7. **Os textos que apontavam para a "seção acima"** (o laboratório e o retorno) passam a dizer "aba Risco".

## Consequências

- Os testes de tela abrem cada um na aba da sua seção. Os testes de ordem entre seções viraram testes das
  abas: ordem, endereços, aba corrente, troca sem pedir de novo e segmento desconhecido.
- Os roteiros da execução real (`frontend/e2e/capturas.mjs`), escritos para a página em rolagem, precisam
  ser revistos antes da próxima execução real.
- O M2.2b recebe a tela em abas: a ordem "risco → laboratório → retorno → Fundamentos → Comunicados" do
  ESTADO vale como ordem das abas.
