"""V-02 do M1.4: a lista fechada de `VaRModel.hyperparameters`.

Sem este teste, uma implementacao em que a propriedade existe em `base.py` e nenhum
modelo a sobrescreve grava NOVE dicionarios vazios no manifesto e passa em tudo — e a
segunda alteracao autorizada no motor perde a propria justificativa. Por isso a
verificacao percorre os nove modelos do registry e compara as CHAVES com a lista da spec,
em vez de so checar que a propriedade existe ou que devolve um dicionario.

O `{}` de `parametric` e `historical` e resposta legitima — conferido no codigo: nenhum
dos dois tem construtor nem constante configuravel —, mas so vale porque esta declarado
aqui, ao lado dos outros sete. A diferenca entre "nao tem hiperparametro" e "ninguem
implementou a propriedade" e invisivel na coluna e total no significado.

Nenhuma linha aqui ajusta modelo: a propriedade e leitura pura, e `get_model(nome)()`
basta porque os nove construtores tem padrao para tudo.
"""

from __future__ import annotations

import pytest

from engine.models import get_model, list_models, load_all_model_modules
from engine.models.ml import caviar

#: a lista fechada da spec do M1.4, derivada dos atributos que cada modelo ja tem no
#: codigo — nao da memoria.
CHAVES_ESPERADAS: dict[str, set[str]] = {
    "parametric": set(),
    "historical": set(),
    "monte_carlo": {"n_simulations", "random_state"},
    "garch_1_1": {"dist", "refit_frequency_days", "vol", "p", "q"},
    "egarch": {"dist", "refit_frequency_days", "vol", "p", "o", "q"},
    "caviar": {"refit_frequency_days", "n_restarts"},
    **{
        neural: {
            "window",
            "refit_frequency_days",
            "grid",
            "learning_rate",
            "batch_size",
            "search_epochs",
            "refit_epochs",
            "patience",
            "val_fraction",
        }
        for neural in ("garchnet", "lstm", "gru")
    },
}


@pytest.fixture(scope="module", autouse=True)
def registry_completo() -> None:
    load_all_model_modules()


def test_o_registry_tem_exatamente_os_nove_da_lista() -> None:
    """Se um modelo entrar ou sair do registry, a lista fechada tem de ser revista —
    senao o modelo novo grava `{}` sem que ninguem tenha conferido."""
    assert sorted(list_models()) == sorted(CHAVES_ESPERADAS)


@pytest.mark.parametrize("nome", sorted(CHAVES_ESPERADAS))
def test_as_chaves_declaradas_batem_com_a_lista_fechada(nome: str) -> None:
    hiperparametros = get_model(nome)().hyperparameters
    assert isinstance(hiperparametros, dict)
    assert set(hiperparametros) == CHAVES_ESPERADAS[nome]


def test_sete_dos_nove_nao_devolvem_vazio() -> None:
    """A trava contra a implementacao que so existe em `base.py`: se a propriedade
    nascer devolvendo `{}` para todos, o teste acima ainda passaria para `parametric` e
    `historical`, e este reprova."""
    vazios = {
        nome for nome in CHAVES_ESPERADAS if not get_model(nome)().hyperparameters
    }
    assert vazios == {"parametric", "historical"}


def test_os_valores_do_caviar_seguem_as_constantes_de_modulo() -> None:
    """O `caviar` escreve os dois literalmente, porque sao constantes de MODULO e `self.`
    nao as alcanca. Duplicar valor convida a divergencia — aqui ela reprova."""
    declarados = get_model("caviar")().hyperparameters
    assert declarados["refit_frequency_days"] == caviar.REFIT_FREQUENCY_DAYS
    assert declarados["n_restarts"] == caviar.N_RESTARTS
