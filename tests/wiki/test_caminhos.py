"""Slug e confinamento, em unidade - sem passar pela WikiDeArquivos.

A primeira metade e o slug (RN-W-04, RN-W-05, PBT-U3-05): texto puro, sem
disco. A segunda e o confinamento (RN-W-07, PBT-U3-01): resolver_sob e o unico
produtor de Path do adaptador (DP-W-01), entao prova-lo aqui e prova-lo para
as quatro operacoes.
"""

import re
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fishingrod.adaptadores.wiki.caminhos import resolver_raiz, resolver_sob
from fishingrod.aplicacao.caminho_wiki import NOMES_RESERVADOS, caminho, slug, slug_valido
from fishingrod.aplicacao.portas.wiki import CaminhoForaDaRaiz, LocalizadorNaoReconhecido
from tests.wiki import estrategias as est

_FORMA_DO_SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


# --------------------------------------------------------------------------
# Slug (RN-W-04)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "titulo,esperado",
    [
        ("Dr. Marcelo & Cia", "dr-marcelo-e-cia"),  # o exemplo da propria regra
        ("ICP", "icp"),
        ("conceitos por disciplina", "conceitos-por-disciplina"),
        ("dúvidas recorrentes", "duvidas-recorrentes"),
        ("Ação e Reação", "acao-e-reacao"),
        ("  --Plano__Anual--  ", "plano-anual"),
        ("a...b///c", "a-b-c"),
        ("2026", "2026"),
        # largura cheia: a NFKD reduz, inclusive o "&" da tabela pre-slug
        ("\uff26\uff55\uff4c\uff4c\u3000\uff37\uff49\uff44\uff54\uff48 \uff06 \uff11", "full-width-e-1"),
    ],
)
def test_rn_w_04_slug(titulo, esperado):
    assert slug(titulo) == esperado


@pytest.mark.parametrize("titulo", ["", "   ", "...", "!!!", "--", "\u0301", "../..", "~"])
def test_rn_w_05_titulo_so_de_simbolos_tem_slug_vazio(titulo):
    assert slug(titulo) == ""
    assert not slug_valido(slug(titulo))


@pytest.mark.parametrize(
    "titulo",
    ["con", "CON", "Prn", "aux", "nul", "com1", "COM9", "lpt1", "Lpt9", " nul ", "con.", "c\u00f3n", "COM\u00b9"],
)
def test_rn_w_05_nome_reservado_do_windows_e_recusado(titulo):
    """"con" com acento e "COM" com 1 sobrescrito so viram reservados DEPOIS da
    NFKD - e por isso que a lista e conferida contra o slug, nao contra o
    titulo."""
    assert slug(titulo) in NOMES_RESERVADOS
    assert not slug_valido(slug(titulo))


@pytest.mark.parametrize("titulo", ["com0", "com10", "lpt", "console", "nula", "aux-1", "conta"])
def test_rn_w_05_parecido_com_reservado_e_aceito(titulo):
    assert slug_valido(slug(titulo))


@pytest.mark.parametrize(
    "nome,valido",
    [
        ("clientes", True),
        ("dr-marcelo-e-cia", True),
        ("index", True),
        ("Clientes", False),
        ("dr marcelo", False),
        ("-a", False),
        ("a-", False),
        ("a--b", False),
        ("index.md", False),
        ("con", False),
        ("", False),
    ],
)
def test_rn_w_03_slug_valido_e_o_nome_que_o_app_escreve(nome, valido):
    """E a peneira do que se encontra no disco: nome que nao passa aqui nao foi
    escrito pelo app (RN-W-02)."""
    assert slug_valido(nome) is valido


@given(titulo=st.text(est.QUALQUER) | est.titulos_hostis)
def test_pbt_u3_05_slug_idempotente_e_deterministico(titulo):
    gerado = slug(titulo)

    assert slug(gerado) == gerado
    assert slug(titulo) == gerado  # mesmo titulo, mesmo slug
    assert gerado == "" or _FORMA_DO_SLUG.fullmatch(gerado)


# --------------------------------------------------------------------------
# Caminho logico (RN-W-33, R-CG3-3)
# --------------------------------------------------------------------------


def test_rn_w_33_caminho_qualificado_e_canonico():
    assert caminho("Clientes", "Dr. Marcelo & Cia") == "clientes/dr-marcelo-e-cia"
    assert caminho("clientes", "dr-marcelo-e-cia") == "clientes/dr-marcelo-e-cia"


@given(entidade=st.text(est.QUALQUER), propriedade=st.text(est.QUALQUER))
def test_pbt_u3_05_caminho_aceita_titulo_ou_slug(entidade, propriedade):
    """E o que deixa o agente passar a `ler` o caminho que leu no indice."""
    assert caminho(slug(entidade), slug(propriedade)) == caminho(entidade, propriedade)


# --------------------------------------------------------------------------
# Confinamento: resolver_raiz (RN-W-09, NFR-W-06)
# --------------------------------------------------------------------------


def test_rn_w_09_localizador_dados_resolve_sob_a_raiz_de_dados(tmp_path):
    assert resolver_raiz(tmp_path, "dados:wikis/teste") == (tmp_path / "wikis" / "teste").resolve()


@pytest.mark.parametrize(
    "localizador", ["nuvem:wikis/x", "DADOS:wikis/x", "wikis/x", "", ":wikis/x", "s3://balde/x"]
)
def test_rn_w_09_esquema_que_nao_e_dados_e_recusado(tmp_path, localizador):
    with pytest.raises(LocalizadorNaoReconhecido):
        resolver_raiz(tmp_path, localizador)


@pytest.mark.parametrize(
    "localizador",
    [
        "dados:",
        "dados:../fora",
        "dados:wikis/../../fora",
        "dados:/etc",
        "dados:C:\\Windows",
        "dados:wikis//x",
        "dados:wikis/x/",
    ],
)
def test_rn_w_07_localizador_que_sai_da_pasta_de_dados_e_recusado(tmp_path, localizador):
    """RaizWiki ja recusa caminho absoluto no dominio, mas nao recusa "..": um
    localizador adulterado no banco chegaria aqui."""
    with pytest.raises(CaminhoForaDaRaiz):
        resolver_raiz(tmp_path, localizador)


def test_nfr_w_06_resolver_nao_cria_nada(tmp_path):
    resolver_raiz(tmp_path / "dados", "dados:wikis/teste")
    resolver_sob(tmp_path / "dados" / "wikis" / "teste", "clientes/dr-marcelo", ".md")

    assert list(tmp_path.iterdir()) == []


# --------------------------------------------------------------------------
# Confinamento: resolver_sob (RN-W-07, NFR-W-05, PBT-U3-01)
# --------------------------------------------------------------------------


def test_rn_w_07_caminho_valido_fica_sob_a_raiz(tmp_path):
    assert resolver_sob(tmp_path, "clientes/dr-marcelo", ".md") == (
        tmp_path / "clientes" / "dr-marcelo.md"
    ).resolve()
    assert resolver_sob(tmp_path, "clientes") == (tmp_path / "clientes").resolve()


@pytest.mark.parametrize(
    "caminho_logico",
    [
        "..",
        "../x",
        "clientes/..",
        "clientes/../../x",
        "/etc/passwd",
        "C:\\Windows",
        "clientes//x",
        "",
        "clientes/",
        "Clientes/x",
        "con/x",
        "clientes/nul",
        "~/x",
        "a\x00b",
    ],
)
def test_rn_w_07_etapa_1_segmento_que_nao_e_slug_e_recusado(tmp_path, caminho_logico):
    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(tmp_path, caminho_logico, ".md")


def test_rn_w_07_raiz_sem_resolver_so_pode_recusar_demais(tmp_path, monkeypatch):
    """resolver_sob recebe a raiz ja resolvida - e o que resolver_raiz devolve -
    para nao resolve-la de novo a cada arquivo. Se alguem passar uma raiz crua,
    o erro possivel e recusar o valido, nunca aceitar o que sai: um caminho
    resolvido nunca fica "dentro" de um caminho relativo ou com symlink."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(Path("raiz"), "clientes/dr-marcelo", ".md")


@given(caminho_logico=est.caminhos_hostis, sufixo=st.sampled_from(["", ".md"]))
def test_pbt_u3_01_resolver_sob_nunca_devolve_caminho_fora_da_raiz(tmp_path, caminho_logico, sufixo):
    raiz = tmp_path / "raiz"
    try:
        resolvido = resolver_sob(raiz, caminho_logico, sufixo)
    except CaminhoForaDaRaiz:
        return

    assert resolvido.is_relative_to(raiz.resolve())
    assert resolvido != raiz.resolve()


@given(entidade=est.titulos_hostis, titulo=est.titulos_hostis)
def test_pbt_u3_01_titulo_hostil_vira_caminho_dentro_da_raiz_ou_e_recusado(tmp_path, entidade, titulo):
    """A camada de titulo hostil (NFR-W-18), que roda em toda plataforma.

    Escrita e leitura produzem o caminho de uma pagina sempre assim:
    resolver_sob(raiz, caminho(entidade, titulo), ".md"). Ou o resultado esta
    exatamente dois niveis abaixo da raiz, ou e recusado - e so e recusado
    quando o slug nao serve.
    """
    raiz = tmp_path / "raiz"
    try:
        arquivo = resolver_sob(raiz, caminho(entidade, titulo), ".md")
    except CaminhoForaDaRaiz:
        assert not (slug_valido(slug(entidade)) and slug_valido(slug(titulo)))
        return

    assert arquivo.parent.parent == raiz.resolve()
    assert arquivo.name == slug(titulo) + ".md"


# --------------------------------------------------------------------------
# Confinamento: symlink, a etapa 3 (NFR-W-18)
# --------------------------------------------------------------------------
# Teste proprio e nomeado, nao cobertura presumida: na maquina do dono (Windows
# sem modo de desenvolvedor) estes sao pulados, e a saida do pytest diz isso.
# As etapas 1 e 2 rodam em toda plataforma, logo acima.


def _symlink_disponivel() -> bool:
    with tempfile.TemporaryDirectory() as pasta:
        alvo = Path(pasta) / "alvo"
        alvo.mkdir()
        try:
            (Path(pasta) / "link").symlink_to(alvo, target_is_directory=True)
        except (OSError, NotImplementedError):
            return False
    return True


com_symlink = pytest.mark.skipif(
    not _symlink_disponivel(),
    reason="o sistema recusou criar symlink (Windows sem modo de desenvolvedor) - NFR-W-18",
)


@com_symlink
def test_rn_w_07_etapa_3_entidade_que_e_symlink_para_fora_e_recusada(tmp_path):
    raiz = tmp_path / "raiz"
    raiz.mkdir()
    fora = tmp_path / "fora"
    fora.mkdir()
    (raiz / "clientes").symlink_to(fora, target_is_directory=True)

    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(raiz, "clientes")
    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(raiz, "clientes/dr-marcelo", ".md")


@com_symlink
def test_rn_w_07_etapa_3_pagina_que_e_symlink_para_fora_e_recusada(tmp_path):
    """O titulo e inocente; o link ja estava no disco. So a etapa 3 pega."""
    raiz = tmp_path / "raiz"
    (raiz / "clientes").mkdir(parents=True)
    segredo = tmp_path / "segredo.md"
    segredo.write_text("nao e da wiki", encoding="utf-8")
    (raiz / "clientes" / "dr-marcelo.md").symlink_to(segredo)

    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(raiz, "clientes/dr-marcelo", ".md")


@com_symlink
def test_rn_w_07_etapa_3_compara_componente_e_nao_prefixo_de_texto(tmp_path):
    """"wiki2" comeca com o texto "wiki", mas nao esta dentro de "wiki" - e o
    erro que uma comparacao por startswith deixaria passar (TS-W-01)."""
    raiz = tmp_path / "wiki"
    raiz.mkdir()
    vizinha = tmp_path / "wiki2"
    vizinha.mkdir()
    (raiz / "atalho").symlink_to(vizinha, target_is_directory=True)

    with pytest.raises(CaminhoForaDaRaiz):
        resolver_sob(raiz, "atalho/x", ".md")


@com_symlink
def test_rn_w_07_etapa_3_symlink_que_fica_dentro_da_raiz_e_aceito(tmp_path):
    """A etapa 3 compara o destino, nao proibe symlink."""
    raiz = tmp_path / "raiz"
    (raiz / "clientes").mkdir(parents=True)
    (raiz / "atalho").symlink_to(raiz / "clientes", target_is_directory=True)

    assert resolver_sob(raiz, "atalho/x", ".md") == (raiz / "clientes" / "x.md").resolve()


@com_symlink
def test_rn_w_07_localizador_atravessando_symlink_para_fora_e_recusado(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    fora = tmp_path / "fora"
    fora.mkdir()
    (dados / "wikis").symlink_to(fora, target_is_directory=True)

    with pytest.raises(CaminhoForaDaRaiz):
        resolver_raiz(dados, "dados:wikis/teste")
