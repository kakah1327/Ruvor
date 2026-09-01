# D-14 — Celery e Redis para execucao assincrona

**Status:** aceita · 2026-08-29

## Contexto

O modo A (D-07) exige que tarefas longas rodem fora do ciclo da requisicao, com progresso visivel.

## Decisão

**Celery + Redis**. Atualizacao de tela por **consulta periodica** (~2s), nao WebSocket.

## Consequências

- O Redis faz tres trabalhos: corretor de fila, cache e canal de progresso — reduz pecas em vez de somar.
- O Celery ja traz repeticao em falha, cancelamento e agendamento, que a ingestao diaria exige de qualquer forma.
- Consulta periodica evita Django Channels; para operacao de minutos, 2s de atraso e irrelevante. Trocar depois e facil.
