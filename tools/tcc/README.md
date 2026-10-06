# Scripts do TCC

Geram a versão do TCC II (`TCC_II_VaR_ML_v4`) a partir do `.docx` anterior e dos resultados que a plataforma
grava no banco. **Não fazem parte da plataforma**: são da trilha paralela do TCC ([ROADMAP](../../docs/ROADMAP.md)).

| Arquivo | O que faz |
|---|---|
| `exportar.sh` | exporta do stack local os resultados do laboratório (`lab_result.csv`, `lab_year.csv`), a série de VaR do PETR4 (`serie.csv`, por `serie.py` no `worker`) e as telas (`telas/*.png`, por `telas.mjs` no Playwright) |
| `figuras.py` | calcula as estatísticas do ranking (`stats.json`) e desenha as Figuras 1, 2, 6 e 7 (`fig/*.png`) |
| `conteudo.py`, `cap45.py` | o texto novo: Resumo, Abstract, trocas nos capítulos 1 a 3, a seção 3.2 e os capítulos 4 e 5 |
| `montar.py` | aplica o texto, as tabelas e as figuras ao `.docx`, e as normas do TCC II: espaço simples, texto contínuo, itálico só em inglês, a matriz sem posição fixa |
| `word.ps1` | abre no Word, atualiza o sumário e grava o `.docx` e o `.pdf` finais |

## Passo a passo

Na raiz do repositório, com o stack de pé (`docker compose up -d postgres redis web frontend`, sem o `beat`):

```bash
bash tools/tcc/exportar.sh                      # grava em tools/tcc/dados/ (fora do git)
python tools/tcc/figuras.py tools/tcc/dados
python tools/tcc/montar.py docs/tcc/TCC_II_VaR_ML_v3_cap1.docx tools/tcc/dados/v4.docx tools/tcc/dados
powershell -File tools/tcc/word.ps1 tools/tcc/dados/v4.docx TCC_II_VaR_ML_v4.docx TCC_II_VaR_ML_v4.pdf
```

Precisa de `python-docx` e `matplotlib` no Python do hospedeiro e do Word instalado (o `word.ps1` usa o Word
pela automação COM). O `montar.py` imprime os trechos que não achou no `.docx`; as duas linhas `matriz:` com
`PETR4.SA` são esperadas (a variante com `PETR4` é a que casa).

## Cuidados

- Os números saem de `gold.lab_*`, o experimento da década de cada ativo (M2.4). Se o laboratório for refeito
  (motor novo, outra década), **o texto de `cap45.py` cita números fixos** — violações, p-valores, posições do
  ranking, datas — e precisa ser revisto à mão contra o novo `stats.json` e as tabelas.
- O critério do ranking (casos adequados, depois os três testes, o DQ e o desvio médio) é dos autores e está em
  `figuras.py` e `montar.py`; mudar num exige mudar no outro e no texto da Seção 4.6.
- O Apêndice B declara o uso de IA nesta versão; quem revisar o texto ajusta a declaração.
