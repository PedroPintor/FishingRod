"""U5 - fronteira do catalogo (RN-AC-01, RN-AC-04, criterio 4).

Como em U4: verifica o GRAFO DE IMPORT, e nao a ausencia dos pacotes no
ambiente. O que nao pode existir e a aresta.
"""

import ast
import pathlib
import subprocess
import sys

from fishingrod.aplicacao.catalogo import argumentos, catalogo, parser, registro, tipos
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.portas import confirmacao

PROIBIDOS = {"claude_agent_sdk", "sqlite3", "textual", "os", "pathlib", "shutil"}

MODULOS = {
    "tipos": pathlib.Path(tipos.__file__),
    "parser": pathlib.Path(parser.__file__),
    "argumentos": pathlib.Path(argumentos.__file__),
    "registro": pathlib.Path(registro.__file__),
    "catalogo": pathlib.Path(catalogo.__file__),
    "confirmacao": pathlib.Path(confirmacao.__file__),
}

SERVICO = "fishingrod.aplicacao.servicos.servico_de_ambiente"


def _importados(caminho: pathlib.Path) -> set[str]:
    """Nomes completos dos modulos importados, inclusive os que so aparecem
    sob TYPE_CHECKING: a aresta existe no codigo do mesmo jeito."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            importados.add(no.module)
    return importados


def test_rn_ac_01_nenhum_modulo_importa_sdk_banco_tela_nem_disco():
    for nome, caminho in MODULOS.items():
        raizes = {modulo.split(".")[0] for modulo in _importados(caminho)}

        assert raizes & PROIBIDOS == set(), nome


def test_rn_ac_01_so_dominio_servico_e_portas():
    """Do projeto, so o dominio, o servico de U4, as portas (os erros de
    persistencia e de wiki entram como tipos, para o mapeamento) e o proprio
    catalogo. Nenhum adaptador."""
    permitidos = {
        "fishingrod.dominio",
        SERVICO,
        "fishingrod.aplicacao.portas.confirmacao",
        "fishingrod.aplicacao.portas.persistencia",
        "fishingrod.aplicacao.portas.wiki",
    }
    for nome, caminho in MODULOS.items():
        do_projeto = {m for m in _importados(caminho) if m.startswith("fishingrod")}

        assert not any(m.startswith("fishingrod.adaptadores") for m in do_projeto), nome
        fora = {m for m in do_projeto - permitidos if not m.startswith("fishingrod.aplicacao.catalogo.")}
        assert fora == set(), nome


def test_catalogo_init_fica_vazio():
    """Decisao declarada no plano: com um __init__ que reexportasse o
    catalogo, importar a porta de confirmacao primeiro entraria em ciclo."""
    init = MODULOS["tipos"].parent / "__init__.py"

    assert init.read_text(encoding="utf-8").strip() == ""


def test_parser_e_argumentos_nao_conhecem_o_servico():
    """O parser nao importa nada do projeto; argumentos.py, so os tipos."""
    assert {m for m in _importados(MODULOS["parser"]) if m.startswith("fishingrod")} == set()
    assert {m for m in _importados(MODULOS["argumentos"]) if m.startswith("fishingrod")} == {
        "fishingrod.aplicacao.catalogo.tipos"
    }


def test_importar_parser_e_argumentos_nao_carrega_o_servico():
    """O servico aparece em tipos.py so sob TYPE_CHECKING. Em tempo de
    execucao, importar o parser e a conversao de argumentos nao o carrega -
    nem a porta de confirmacao, que depende dos tipos."""
    codigo = (
        "import sys\n"
        "import fishingrod.aplicacao.catalogo.parser\n"
        "import fishingrod.aplicacao.catalogo.argumentos\n"
        "import fishingrod.aplicacao.portas.confirmacao\n"
        f"print({SERVICO!r} in sys.modules)\n"
    )
    saida = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, check=True
    ).stdout.strip()

    assert saida == "False"


def test_criterio_4_conversar_nao_esta_no_catalogo():
    """RN-AC-04, criterio 4: o registro e exatamente as 7 acoes de ambiente, e
    nenhuma delas e de conversa."""
    nomes = [acao.nome for acao in ACOES]

    assert nomes == [
        "criar_frente",
        "criar_tarefa",
        "criar_sessao",
        "criar_chat",
        "criar_etapa",
        "concluir_etapa",
        "anotar_memoria",
    ]
    for proibido in ("mensagem", "enviar", "conversa", "responder"):
        assert not any(proibido in nome for nome in nomes)
