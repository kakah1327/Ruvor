# Mockups-matriz da Ruvor

Estas telas são referências visuais de implementação para o produto B2B da Ruvor. Não formam um protótipo navegável e não representam o escopo completo da plataforma. Cada arquivo é uma tela HTML completa, pensada para que o implementador reaproveite diretamente shell, componentes, hierarquia, densidade e estados.

## Telas

| Arquivo | Padrão que estabelece |
| --- | --- |
| `01-login.html` | Acesso institucional, confiança, SSO e tratamento de erro. |
| `02-visao-geral.html` | Home operacional, sinais prioritários, evidência e ranking de modelos. |
| `03-nova-analise.html` | Formulário analítico denso, seleção de parâmetros e resumo antes da execução. |
| `04-resultado-analitico.html` | Resultado completo, gráfico de VaR, backtests, comparação de modelos e trilha da execução. |

## Fonte de verdade

- `foundation.css` reúne os padrões compartilhados usados pelos quatro mockups.
- `../tokens.css` é a fonte oficial dos tokens da identidade.
- `../implementation.css` é a referência de componentes para o produto final.
- Os SVGs em `../` são os ativos oficiais da marca e não devem ser redesenhados.
- A pasta `../examples/` contém estudos anteriores; quando houver divergência visual, estes mockups prevalecem.

## Como derivar novas telas

Mantenha a barra superior, a largura de conteúdo, a tipografia, a semântica das cores e a linguagem de sinais. Combine os padrões existentes conforme a tarefa: formulários partem de `03`, leituras e auditoria partem de `04`, e telas operacionais partem de `02`.

Os dados são ilustrativos. O produto real deve manter a clareza metodológica, registrar fonte e horário dos dados e nunca apresentar um resultado analítico como recomendação de investimento.
