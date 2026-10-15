"""As duas leituras do frontmatter, e o que as obriga a concordar (DP-W-06).

Texto puro, sem disco: frontmatter.py nao abre arquivo. Para `ler_cabecalho`,
io.StringIO faz o papel do arquivo aberto - por padrao ele separa linha so em
LF e nao traduz nada, exatamente como o open com newline LF que o adaptador usa.

As propriedades de concordancia sao a contrapartida de Q5=B: com dois leitores
independentes, NFR-W-20 deixa de ser verdadeiro por construcao e passa a
depender daqui.
"""

import io

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fishingrod.adaptadores.wiki.frontmatter import (
    TETO_DO_CABECALHO,
    ler_cabecalho,
    ler_pagina,
    montar,
)
from fishingrod.aplicacao.caminho_wiki import normalizar_valor
from tests.wiki import estrategias as est


def _cabecalho(texto: str) -> tuple[str, str]:
    return ler_cabecalho(io.StringIO(texto))


def _bloco_com_chaves_extras(extras: int) -> str:
    chaves = [f"extra{numero}: x" for numero in range(extras)]
    return "\n".join(["---", "descricao: d", *chaves, "---", "corpo"])


def _linhas_vigiadas(texto: str, limite: int):
    """O arquivo aberto, mas que falha se alguem pedir uma linha alem de
    `limite` - e assim que se prova que o cabecalho parou de ler."""
    for numero, linha in enumerate(io.StringIO(texto), start=1):
        if numero > limite:
            raise AssertionError(f"leu a linha {numero}, alem de {limite}")
        yield linha


# --------------------------------------------------------------------------
# montar (RN-W-13)
# --------------------------------------------------------------------------


def test_rn_w_13_o_bloco_e_montado_pelo_adaptador():
    assert montar("Dr. Marcelo & Cia", "dentista, ticket alto", "Conversou em marco.") == (
        "---\n"
        "titulo: Dr. Marcelo & Cia\n"
        "descricao: dentista, ticket alto\n"
        "---\n"
        "\n"
        "Conversou em marco."
    )


# --------------------------------------------------------------------------
# normalizar_valor - o que torna o round-trip possivel para qualquer entrada
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("  Dr. Marcelo  ", "Dr. Marcelo"),
        ("linha um\nlinha dois", "linha um linha dois"),
        ("a\r\nb\tc", "a b c"),
        ('"x"', "x"),
        ("'x'", "x"),
        ('""x""', "x"),  # o caso que um par so nao resolve
        ('" x "', "x"),  # tirado o par, sobra espaco na borda
        ("\"x'", "\"x'"),  # desbalanceadas ficam
        ('"', '"'),
        ('""', ""),
    ],
)
def test_normalizar_valor(valor, esperado):
    assert normalizar_valor(valor) == esperado


@given(valor=est.textos_de_frontmatter)
def test_normalizar_valor_e_idempotente_e_cabe_numa_linha(valor):
    normalizado = normalizar_valor(valor)

    assert normalizar_valor(normalizado) == normalizado
    assert not any(quebra in normalizado for quebra in ("\n", "\r", "\t"))


# --------------------------------------------------------------------------
# ler_pagina e ler_cabecalho (RN-W-11, RN-W-15, RN-W-16)
# --------------------------------------------------------------------------


def test_rn_w_11_titulo_descricao_e_corpo():
    texto = montar("Dr. Marcelo", "dentista", "corpo\ncom duas linhas\n")

    assert ler_pagina(texto) == ("Dr. Marcelo", "dentista", "corpo\ncom duas linhas\n")
    assert _cabecalho(texto) == ("Dr. Marcelo", "dentista")


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "sem frontmatter nenhum",
        "\n---\ntitulo: x\n---\n",  # o bloco precisa comecar na primeira linha
        " ---\ntitulo: x\n---\n",  # espaco antes do delimitador nao vale
        "---\ntitulo: x\ndescricao: y\n",  # abre e nao fecha
    ],
)
def test_rn_w_15_sem_bloco_devolve_vazios_e_o_texto_inteiro(texto):
    assert ler_pagina(texto) == ("", "", texto)
    assert _cabecalho(texto) == ("", "")


def test_rn_w_15_leitor_tolerante():
    texto = (
        "---   \n"  # espaco depois do delimitador vale
        "# comentario sem dois-pontos\n"
        "autor: alguem\n"  # chave desconhecida
        '  titulo  :  "Dr. Marcelo"  \n'  # bordas e aspas
        "descricao: 'primeira'\n"
        "descricao: a: b\n"  # repetida vale a ultima; partida no primeiro ":"
        "---\n"
        "corpo"
    )

    assert ler_pagina(texto) == ("Dr. Marcelo", "a: b", "corpo")
    assert _cabecalho(texto) == ("Dr. Marcelo", "a: b")


def test_rn_w_15_tira_um_par_de_aspas_e_so_um():
    """O leitor e tolerante, nao normalizador: arquivo editado a mao com aspas
    dobradas devolve uma camada delas."""
    texto = '---\ntitulo: ""x""\n---\n'

    assert ler_pagina(texto) == ('"x"', "", "")
    assert _cabecalho(texto) == ('"x"', "")


def test_rn_w_15_arquivo_salvo_com_crlf_continua_legivel():
    """Editado a mao num editor que grava CRLF: o CR sobra no fim de cada linha,
    e o corpo volta como esta no arquivo."""
    texto = "---\r\ntitulo: Dr. Marcelo\r\ndescricao: dentista\r\n---\r\n\r\ncorpo\r\n"

    assert ler_pagina(texto) == ("Dr. Marcelo", "dentista", "corpo\r\n")
    assert _cabecalho(texto) == ("Dr. Marcelo", "dentista")


def test_rn_w_16_so_o_primeiro_bloco_e_frontmatter():
    corpo = "antes\n---\ntitulo: falso\ndescricao: falsa\n---\ndepois"
    texto = montar("verdadeiro", "verdadeira", corpo)

    assert ler_pagina(texto) == ("verdadeiro", "verdadeira", corpo)
    assert _cabecalho(texto) == ("verdadeiro", "verdadeira")


@pytest.mark.parametrize(
    "corpo", ["", "\n", "\n\nx", "\r\nx", "\r", "x\n", "---", "---\n\n---\n", "   \nx"]
)
def test_rn_w_16_corpo_volta_byte_a_byte(corpo):
    assert ler_pagina(montar("t", "d", corpo)) == ("t", "d", corpo)


@given(titulo=est.textos_de_frontmatter, descricao=est.textos_de_frontmatter, corpo=est.corpos)
def test_pbt_u3_07_corpo_com_regua_horizontal_sobrevive(titulo, descricao, corpo):
    """O corpo e markdown de agente: `---` vai aparecer, inclusive na primeira
    linha. Um leitor ingenuo partiria a pagina ao meio na segunda leitura."""
    titulo, descricao = normalizar_valor(titulo), normalizar_valor(descricao)

    assert ler_pagina(montar(titulo, descricao, corpo)) == (titulo, descricao, corpo)


# --------------------------------------------------------------------------
# O cabecalho para cedo (NFR-W-01)
# --------------------------------------------------------------------------


def test_nfr_w_01_cabecalho_para_no_fechamento():
    """Dez mil linhas de corpo, e o leitor nao passa da quarta."""
    texto = montar("t", "d", "linha de corpo\n" * 10_000)

    assert ler_cabecalho(_linhas_vigiadas(texto, limite=4)) == ("t", "d")


def test_nfr_w_01_bloco_que_nao_fecha_no_teto_nao_e_bloco():
    """E o leitor nao passa do teto para descobrir."""
    texto = _bloco_com_chaves_extras(TETO_DO_CABECALHO)

    assert ler_cabecalho(_linhas_vigiadas(texto, limite=TETO_DO_CABECALHO)) == ("", "")


def test_nfr_w_01_bloco_que_fecha_exatamente_no_teto_vale():
    # abre (1) + descricao (1) + extras + fecha (1) == TETO_DO_CABECALHO
    texto = _bloco_com_chaves_extras(TETO_DO_CABECALHO - 3)

    assert _cabecalho(texto) == ("", "d")


# --------------------------------------------------------------------------
# Concordancia (DP-W-06, NFR-W-20)
# --------------------------------------------------------------------------


@given(titulo=est.textos_de_frontmatter, descricao=est.textos_de_frontmatter, corpo=est.corpos)
def test_nfr_w_20_as_duas_leituras_concordam_em_toda_pagina_montada(titulo, descricao, corpo):
    """A propriedade dedicada que DP-W-06 exige. PBT-U3-03 e PBT-U3-04 cruzam os
    dois caminhos de lado; aqui eles sao postos frente a frente, para qualquer
    titulo, descricao e corpo - que e o dominio de toda pagina escrita pelo app.
    """
    texto = montar(normalizar_valor(titulo), normalizar_valor(descricao), corpo)

    assert _cabecalho(texto) == ler_pagina(texto)[:2]


_SEM_LF = est.textos_de_frontmatter.map(lambda texto: texto.replace("\n", ""))

_LINHAS_EDITADAS_A_MAO = st.one_of(
    st.sampled_from(
        [
            "---",
            "--- ",
            "---\r",
            " ---",
            "",
            "titulo: a",
            "descricao: b",
            "descricao:",
            'titulo: "c"',
            "titulo: 'd",
            "Titulo: maiuscula",
            "descricao: e: f",
            "  descricao  :  g  ",
            "sem dois-pontos",
        ]
    ),
    _SEM_LF,
    st.builds(
        "{}:{}".format,
        st.sampled_from(["titulo", "descricao", " titulo ", "outra"]),
        _SEM_LF,
    ),
)


@st.composite
def _arquivos_editados_a_mao(draw) -> str:
    """Abertura, miolo, fechamento e corpo, cada um podendo vir certo ou torto.

    Montado em partes para que o bloco aberto E fechado seja comum: com linhas
    soltas, quase todo exemplo comparava ("", "") com ("", "") e a propriedade
    passava sem ter lido chave nenhuma - verificado injetando um leitor que
    tirava aspas duas vezes, que passou.
    """
    abertura = draw(st.sampled_from(["---", "---", "--- ", "---\r", " ---", "texto"]))
    miolo = draw(st.lists(_LINHAS_EDITADAS_A_MAO, max_size=12))
    fechamento = draw(st.sampled_from(["---", "---", "---\t", "---\r", "", "fim"]))
    corpo = draw(st.lists(_LINHAS_EDITADAS_A_MAO, max_size=5))
    return "\n".join([abertura, *miolo, fechamento, *corpo])


@given(texto=_arquivos_editados_a_mao())
def test_nfr_w_20_as_duas_leituras_concordam_em_arquivo_editado_a_mao(texto):
    """Dentro do teto, para texto que o app nao escreveu: bloco bem e mal
    formado, aberto e nao fechado, com CR, com aspas soltas, chave repetida."""
    assert _cabecalho(texto) == ler_pagina(texto)[:2]


def test_dp_w_06_a_divergencia_declarada_alem_do_teto():
    """A unica divergencia entre as duas leituras, e ela e de desenho: o teto
    vive so no cabecalho (DP-W-06). A pagina que o app escreve tem bloco de
    quatro linhas e nunca chega perto; um bloco de 65 linhas ou mais so existe
    editado a mao - sai do indice, com WARNING, e continua legivel por `ler`.
    """
    texto = _bloco_com_chaves_extras(TETO_DO_CABECALHO)

    assert _cabecalho(texto) == ("", "")
    assert ler_pagina(texto) == ("", "d", "corpo")
