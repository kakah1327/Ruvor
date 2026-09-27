# D-81 — A imagem do `worker` é travada pelo lock do motor, e as versões das bibliotecas entram na identidade do retrato

**Status:** aceita · 2026-09-27

## Contexto

O `infra/backend.Dockerfile` instalava `./engine[traditional,garch,ml]` sem o
`engine/requirements-lock.txt`, e o `pyproject.toml` do motor pede `tensorflow>=2.16` sem teto.
A imagem já tinha saído do lock — `numpy` 2.5.3 e `pandas` 3.0.6 no `worker`, contra 2.5.2 e
3.0.5 no lock —, e todo `--build` podia trazer outro TensorFlow ou Keras: o que a
[D-21](D-21-motor-ml-congelado-ate-etapa-6.md) proíbe antes da Etapa 6 e a
[D-22](D-22-treino-centralizado-em-container.md) diz que o contêiner existe para impedir.

Com retratos guardados ([D-77](D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md)),
a deriva deixa de ser só um número diferente amanhã: um retrato treinado por uma versão seria
reaproveitado por outra.

## Decisão

**Duas medidas, que se somam e nenhuma basta sozinha:**

1. **O `pip install` do motor no alvo `worker` usa o lock como restrição**
   (`-c engine/requirements-lock.txt`). Um teste no `worker`
   (`backend/tests/test_versoes_travadas.py`) confere que `tensorflow`, `keras`, `numpy`,
   `scipy`, `pandas` e `arch` instalados são os do lock — e mora no backend porque roda no
   `worker` da CI e guarda a **imagem**; no motor rodaria sobre o `.venv` e passaria
   independentemente dela.
2. **As versões dessas seis bibliotecas entram na identidade do retrato**, lidas da metadata
   instalada, com o hash na unicidade. Se o lock for regenerado de propósito, os retratos
   antigos deixam de ser reaproveitados em vez de produzirem número de outro ambiente.

## Consequências

- A trava rebaixou 14 pacotes na imagem, `numpy` e `pandas` entre eles. As execuções do `0.2.0`
  antes e depois da trava saíram iguais em todos os campos gravados (T1 do M1.5b).
- Regenerar o lock passa a custar um cálculo completo por ativo coberto — é o preço declarado.
- A trava vale para o alvo `worker`; a `web` não tem o motor.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(RF-03, RF-15).
