# D-194 — As explicações ficam atrás de um botão, desligado por padrão, e o detalhe longo abre recolhido — restringe a D-97 e a D-187

**Status:** aceita · 2026-10-04 · frente `marco1`, no ramo `marco1/ajustes-de-tela`. A decisão foi do Kauã,
dono do repositório, na mesma sessão da [D-193](D-193-a-tela-do-ativo-em-seis-abas-com-endereco-restringe-a-d-99-a-d-187-e-a-d-192.md).
Ele escolheu a "explicação sob demanda" entre cortar textos e dividir mais as abas. O portão de mockup foi
a aprovação dele na conversa, olhando a tela rodando. A PR do ramo passa pela revisão da `marco1`.

## Contexto

A [D-97](D-97-no-marco-1-cada-numero-tem-uma-frase-fixa.md) põe uma frase fixa ao lado de cada número de
análise, e o RF-21 do M1.6b cobra que ela apareça junto do número. Cada seção também abre com um parágrafo
de introdução. Mesmo com as abas, o dono achou as telas carregadas de texto e cansativas.

## Decisão

1. **Um botão "Explicações" no fim da barra de abas**, desligado por padrão e com `aria-pressed`. A escolha
   é lembrada no navegador, em `localStorage`, na chave `ruvor-explain` (`src/explain.ts`).
2. **Desligado, a folha esconde a introdução de cada seção e a frase de cada número** (`.ruvor-sub` e
   `.ruvor-note` debaixo de `[data-explain="off"]`). Esconde também o quadro do laboratório que diz por que
   o veredito dele pode diferir do da aba Risco (`.ruvor-lab-honest`). **O texto não sai da página**: o
   botão o traz de volta, e a frase continua existindo para cada número, nas duas leituras
   ([D-151](D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md)).
3. **Fica sempre à vista o que não é explicação**:
   - o texto de estado (`.ruvor-state`);
   - o erro de modelo;
   - "ativo sem preço";
   - o convite a entrar;
   - o aviso de sessão terminada;
   - a falta de comparação entre pares;
   - o gráfico sem dados.

   Esses levam a classe `ruvor-keep`. O aviso do retorno (`retorno.aviso`) continua sempre aberto, como
   manda a [D-192](D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md),
   item 3. A ressalva do rodapé também não muda.
4. **O detalhe longo abre recolhido**, cada um com o seu controle:
   - **Proventos:** os cinco mais novos da janela de 12 meses, e o "Ver todos" para a série inteira.
   - **Comportamento:** Retornos, Volatilidade e Maior queda à vista. Estresse, Ibovespa, proventos,
     distribuição e volume ficam atrás de "Ver mais".
   - **Laboratório:** cada grade abre com a década por modelo, e o botão "Ano a ano" mostra os anos. Isso
     restringe a D-187, que mostrava a grade modelo × ano aberta.

## Consequências

- A D-97 continua valendo para o que existe: todo número de análise tem a sua frase. O que muda é a frase
  estar à vista por padrão. A PRODUTO §2 ("junto do dado") passa a valer com o botão ligado.
- Os testes não carregam a folha, então o texto escondido segue na árvore e os testes de frase continuam
  valendo. Um teste novo cobre o botão (`data-explain` e a escolha lembrada). Outros cobrem os cinco
  proventos e o "Ano a ano".
- Quem lê com leitor de tela também não ouve as explicações com o botão desligado (`display: none`). O
  botão é o caminho para elas, nas duas leituras.
