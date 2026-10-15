"""U6 - fronteira da sessao (RN-S-01, criterio 2, TD-02, NFR-S-07, TS-S-05, DP-S-23).

Duas provas, como decidido na Q5 do NFR Requirements:
- as varreduras ESTATICAS de import apontam a linha que quebrou a fronteira;
- um Python NOVO, com um bloqueador de import em `sys.meta_path`, importa todos
  os modulos de `dominio/` e `aplicacao/` como se o SDK estivesse
  desinstalado. Pega o que a varredura nao ve: import dinamico e transitivo.
"""

import ast
import pathlib
import subprocess
import sys

import fishingrod
from fishingrod.adaptadores.sessao import adaptador, conexao, falhas, ferramentas, opcoes, traducao
from fishingrod.aplicacao.ferramentas import acoes, registro, tipos
from fishingrod.aplicacao.portas import sessao as porta

RAIZ = pathlib.Path(fishingrod.__file__).parent
SESSAO = RAIZ / "adaptadores" / "sessao"


def _importados(caminho: pathlib.Path) -> set[str]:
    """Nomes completos dos modulos importados, inclusive sob TYPE_CHECKING:
    a aresta existe no codigo do mesmo jeito."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            importados.add(no.module)
    return importados


def _do_projeto(modulo: object) -> set[str]:
    return {m for m in _importados(pathlib.Path(modulo.__file__)) if m.startswith("fishingrod")}


def _raizes(caminho: pathlib.Path) -> set[str]:
    return {m.split(".")[0] for m in _importados(caminho)}


# --------------------------------------------------------------------------
# As varreduras estaticas
# --------------------------------------------------------------------------


def test_rn_s_01_so_adaptadores_sessao_importa_o_sdk():
    fora = [
        caminho
        for caminho in RAIZ.rglob("*.py")
        if SESSAO not in caminho.parents and {"claude_agent_sdk", "mcp"} & _raizes(caminho)
    ]

    assert fora == []


def test_rn_s_01_adaptador_py_nao_importa_o_sdk():
    """Tudo do SDK chega ao adaptador pelos outros cinco modulos."""
    assert {"claude_agent_sdk", "mcp", "anyio"} & _raizes(pathlib.Path(adaptador.__file__)) == set()


def test_dp_s_23_so_acoes_py_importa_o_catalogo():
    modulos_de_u6 = [porta, tipos, registro, opcoes, ferramentas, falhas, traducao, conexao, adaptador]
    for modulo in modulos_de_u6:
        assert not any(m.startswith("fishingrod.aplicacao.catalogo") for m in _do_projeto(modulo)), modulo.__name__
    assert any(m.startswith("fishingrod.aplicacao.catalogo") for m in _do_projeto(acoes))


def test_dp_s_23_o_init_de_ferramentas_nao_reexporta_acoes():
    init = pathlib.Path(tipos.__file__).parent / "__init__.py"

    assert "acoes" not in _importados(init) and "fishingrod.aplicacao.ferramentas.acoes" not in _importados(init)


def test_matriz_a_porta_so_conhece_o_dominio():
    assert _do_projeto(porta) == {"fishingrod.dominio"}


def test_matriz_tipos_e_registro_so_conhecem_porta_e_dominio():
    assert _do_projeto(tipos) <= {"fishingrod.dominio", "fishingrod.aplicacao.portas.sessao"}
    assert _do_projeto(registro) <= {
        "fishingrod.dominio",
        "fishingrod.aplicacao.portas.sessao",
        "fishingrod.aplicacao.ferramentas.tipos",
    }


def test_matriz_opcoes_nao_importa_outro_modulo_do_adaptador():
    assert not any(m.startswith("fishingrod.adaptadores") for m in _do_projeto(opcoes))


def test_matriz_o_adaptador_nao_conhece_acoes_nem_outro_adaptador():
    modulos = [opcoes, ferramentas, falhas, traducao, conexao, adaptador]
    for modulo in modulos:
        do_projeto = _do_projeto(modulo)
        assert "fishingrod.aplicacao.ferramentas.acoes" not in do_projeto, modulo.__name__
        assert not any(m.startswith("fishingrod.interface") for m in do_projeto), modulo.__name__
        outros = {
            m for m in do_projeto if m.startswith("fishingrod.adaptadores") and not m.startswith("fishingrod.adaptadores.sessao")
        }
        assert outros == set(), modulo.__name__


def test_o_codigo_antigo_nao_entra_no_pacote():
    """Ambiente/agente.py tambem importa o SDK, e fica intocado ate U9: nada
    do pacote novo o importa."""
    for caminho in RAIZ.rglob("*.py"):
        assert "Ambiente" not in _raizes(caminho), caminho


# --------------------------------------------------------------------------
# O Python novo com o SDK bloqueado (NFR-S-07, TS-S-05)
# --------------------------------------------------------------------------

_BLOQUEADOR = """
import importlib, pkgutil, sys

class Bloqueador:
    def find_spec(self, nome, caminho=None, alvo=None):
        if nome.split(".")[0] in ("claude_agent_sdk", "mcp"):
            raise ImportError(f"bloqueado: {nome}")
        return None

sys.meta_path.insert(0, Bloqueador())
"""


def _rodar(codigo: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-c", _BLOQUEADOR + codigo], capture_output=True, text=True)


def test_criterio_2_dominio_e_aplicacao_importam_sem_o_sdk():
    """TD-02: TODOS os modulos de dominio/ e aplicacao/, inclusive
    aplicacao/ferramentas/acoes.py, carregam com o SDK indisponivel."""
    codigo = """
import fishingrod.dominio, fishingrod.aplicacao
nomes = []
for pacote in (fishingrod.dominio, fishingrod.aplicacao):
    for info in pkgutil.walk_packages(pacote.__path__, pacote.__name__ + "."):
        importlib.import_module(info.name)
        nomes.append(info.name)
print(len(nomes))
print("fishingrod.aplicacao.ferramentas.acoes" in nomes, "fishingrod.aplicacao.portas.sessao" in nomes)
print(any(m.split(".")[0] in ("claude_agent_sdk", "mcp") for m in sys.modules))
"""
    saida = _rodar(codigo)

    assert saida.returncode == 0, saida.stderr
    quantos, cobertos, sdk_carregado = saida.stdout.split("\n")[:3]
    assert int(quantos) >= 20
    assert cobertos == "True True"
    assert sdk_carregado == "False"


def test_criterio_2_o_bloqueador_funciona():
    """Sem isto, o teste de cima passaria com um bloqueador quebrado: o
    adaptador, que importa o SDK, NAO carrega sob ele."""
    saida = _rodar("import fishingrod.adaptadores.sessao\n")

    assert saida.returncode != 0
    assert "bloqueado: claude_agent_sdk" in saida.stderr


def test_dp_s_23_importar_ferramentas_nao_carrega_o_catalogo():
    saida = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\nimport fishingrod.aplicacao.ferramentas\n"
            "import fishingrod.aplicacao.portas.sessao\n"
            "print(any(m.startswith('fishingrod.aplicacao.catalogo') for m in sys.modules))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert saida.stdout.strip() == "False"
