"""U5 - repartir e converter, por exemplos (RN-AC-16..20, G3, G4, G10,
R-CG5-1, R-CG5-4, R-CG5-6).

Usa os parametros do registro de verdade: o que se testa e a gramatica das 6
acoes, e nao uma gramatica de brinquedo. A validacao antes de tudo, gerada, e
PBT-U5-10.
"""

import pytest

from fishingrod.aplicacao.catalogo.argumentos import (
    ArgumentoRecusado,
    converter,
    repartir,
    sem_maiuscula_nem_acento,
)
from fishingrod.aplicacao.catalogo.registro import (
    ACOES,
    MAXIMO_AGENTE,
    MAXIMO_CHAVE,
    MAXIMO_DESCRICAO,
    MAXIMO_NOME,
    MAXIMO_VALOR,
)
from fishingrod.aplicacao.catalogo.tipos import Parametro, TipoParametro

PARAMETROS = {acao.nome: acao.parametros for acao in ACOES}


def _da_barra(acao: str, texto: str) -> dict[str, object]:
    parametros = PARAMETROS[acao]
    return converter(parametros, repartir(parametros, texto))


def _recusa(funcao, *argumentos) -> tuple:
    with pytest.raises(ArgumentoRecusado) as recusa:
        funcao(*argumentos)
    return recusa.value.parametro, recusa.value.problema, recusa.value.maximo


# --- a barra: business-logic-model.md 3.2 -------------------------------------


@pytest.mark.parametrize(
    ("acao", "texto", "argumentos"),
    [
        ("criar_frente", "comercial e ticket", {"nome": "comercial e ticket"}),
        ("criar_tarefa", "campanha de verao", {"nome": "campanha de verao"}),  # criterio 1
        ("criar_chat", "bibliotecario", {"agente": "bibliotecario"}),
        (
            "criar_chat",
            "bibliotecario pesquisa de ICP",
            {"agente": "bibliotecario", "nome": "pesquisa de ICP"},
        ),
        (
            "criar_etapa",
            "usuario assistir a aula 3",
            {"executor": "usuario", "descricao": "assistir a aula 3"},
        ),
        (
            "criar_etapa",
            "Usuário assistir a aula 3",
            {"executor": "usuario", "descricao": "assistir a aula 3"},
        ),
        ("concluir_etapa", "2", {"posicao": 2}),
        (
            "anotar_memoria",
            "travado-por esperando o cliente",
            {"chave": "travado-por", "valor": "esperando o cliente"},
        ),
    ],
)
def test_rn_ac_16_tabela_da_barra(acao, texto, argumentos):
    assert _da_barra(acao, texto) == argumentos


@pytest.mark.parametrize(
    ("acao", "texto", "recusa"),
    [
        ("criar_tarefa", "", ("nome", "ausente", None)),
        ("concluir_etapa", "dois", ("posicao", "tipo", None)),
        ("criar_etapa", "usuario", ("descricao", "ausente", None)),
        ("criar_etapa", "talvez ler", ("executor", "opcao", None)),
        ("anotar_memoria", "travado-por", ("valor", "ausente", None)),
        ("concluir_etapa", "2 3", ("posicao", "tipo", None)),
    ],
)
def test_rn_ac_16_a_19_recusas_da_barra(acao, texto, recusa):
    assert _recusa(_da_barra, acao, texto) == recusa


def test_rn_ac_16_o_ultimo_leva_o_resto_com_os_espacos_de_dentro():
    """TD-11: separadores quaisquer entre as palavras, e o ultimo parametro
    intacto."""
    texto = "  Agente \tler o material   com  calma  "

    assert _da_barra("criar_etapa", texto) == {
        "executor": "agente",
        "descricao": "ler o material   com  calma",
    }


def test_rn_ac_20_a_chave_na_barra_e_uma_palavra():
    """`travado por` vira chave `travado` e valor `por ...`. Pelo agente ou
    pelo botao, a chave pode ter espaco."""
    assert _da_barra("anotar_memoria", "travado por o cliente") == {
        "chave": "travado",
        "valor": "por o cliente",
    }
    assert converter(
        PARAMETROS["anotar_memoria"], {"chave": "travado por", "valor": "o cliente"}
    ) == {"chave": "travado por", "valor": "o cliente"}


def test_repartir_acabou_o_texto_os_restantes_ficam_ausentes():
    assert repartir(PARAMETROS["anotar_memoria"], "") == {}
    assert repartir(PARAMETROS["anotar_memoria"], "chave") == {"chave": "chave"}


def test_r_cg5_1_acao_sem_parametro_com_texto_sobrando():
    """Nenhuma das 6 cai nisto - o ultimo parametro sempre leva o resto -, mas
    a gramatica e total para qualquer registro."""
    assert repartir((), "") == {}
    assert repartir((), "   ") == {}
    assert _recusa(repartir, (), "algo") == (None, "sobrando", None)


# --- G3: so espacos e ausente, nas duas entradas --------------------------------


@pytest.mark.parametrize("espacos", [" ", "   ", "\t", " ", "  \n"])
def test_g3_so_espacos_e_ausente_por_argumentos(espacos):
    assert _recusa(converter, PARAMETROS["criar_frente"], {"nome": espacos}) == (
        "nome",
        "ausente",
        None,
    )


def test_g3_so_espacos_e_ausente_pela_barra():
    """Na barra, os espacos das pontas ja sairam: so espacos e nada sao o
    mesmo texto."""
    assert _recusa(_da_barra, "criar_frente", " \t  ") == ("nome", "ausente", None)


def test_g3_o_valor_da_anotacao_e_obrigatorio():
    """O dominio aceita valor vazio; o catalogo, nao."""
    assert _recusa(converter, PARAMETROS["anotar_memoria"], {"chave": "k", "valor": ""}) == (
        "valor",
        "ausente",
        None,
    )


# --- R-CG5-4: None e ausente; o opcional ausente e omitido ----------------------


def test_r_cg5_4_none_e_ausente():
    assert _recusa(converter, PARAMETROS["criar_tarefa"], {"nome": None}) == (
        "nome",
        "ausente",
        None,
    )


@pytest.mark.parametrize("nome", [None, "", "   "])
def test_r_cg5_4_opcional_ausente_e_omitido(nome):
    """O padrao e do efetivar, e nao daqui: `nome` nao aparece."""
    assert converter(PARAMETROS["criar_chat"], {"agente": "bibliotecario", "nome": nome}) == {
        "agente": "bibliotecario"
    }


def test_texto_valido_nao_e_normalizado():
    """Como o dominio (RN-02 de U1): recusa o invalido, nao reescreve o que
    foi escrito."""
    assert converter(PARAMETROS["criar_frente"], {"nome": "  Comercial  "}) == {
        "nome": "  Comercial  "
    }


# --- tipo (RN-AC-19) --------------------------------------------------------------


@pytest.mark.parametrize("valor", [3, 2.5, True, ["a"], b"x", {"a": 1}])
def test_rn_ac_19_texto_de_outro_tipo(valor):
    assert _recusa(converter, PARAMETROS["criar_frente"], {"nome": valor}) == ("nome", "tipo", None)


@pytest.mark.parametrize("valor", [1, True, ["agente"]])
def test_rn_ac_19_escolha_de_outro_tipo(valor):
    argumentos = {"executor": valor, "descricao": "ler"}

    assert _recusa(converter, PARAMETROS["criar_etapa"], argumentos) == ("executor", "tipo", None)


# --- G4: escolha sem maiuscula nem acento ---------------------------------------


@pytest.mark.parametrize(
    ("escrito", "canonico"),
    [
        ("usuario", "usuario"),
        ("Usuário", "usuario"),
        ("USUÁRIO", "usuario"),
        ("ÚsÜáRiÓ", "usuario"),
        ("agente", "agente"),
        ("AGENTE", "agente"),
        ("Ágente", "agente"),
    ],
)
def test_g4_escolha_sem_maiuscula_nem_acento(escrito, canonico):
    convertidos = converter(PARAMETROS["criar_etapa"], {"executor": escrito, "descricao": "ler"})

    assert convertidos["executor"] == canonico


@pytest.mark.parametrize("escrito", ["usuarios", "user", "agentes", " usuario", "usu ario", "ag"])
def test_g4_o_que_nao_e_opcao_continua_recusado(escrito):
    argumentos = {"executor": escrito, "descricao": "ler"}

    assert _recusa(converter, PARAMETROS["criar_etapa"], argumentos) == ("executor", "opcao", None)


def test_g4_a_normalizacao():
    assert sem_maiuscula_nem_acento("Usuário") == "usuario"
    assert sem_maiuscula_nem_acento("ﬁ") == "fi"  # NFKD desfaz a ligadura
    assert sem_maiuscula_nem_acento("STRASSE") == sem_maiuscula_nem_acento("straße")


# --- POSICAO (RN-AC-23) --------------------------------------------------------


@pytest.mark.parametrize(
    ("valor", "posicao"),
    [(1, 1), (7, 7), ("1", 1), ("007", 7), ("999999999", 999_999_999), (999_999_999, 999_999_999)],
)
def test_rn_ac_23_posicao_valida(valor, posicao):
    assert converter(PARAMETROS["concluir_etapa"], {"posicao": valor}) == {"posicao": posicao}


@pytest.mark.parametrize(
    "valor",
    [
        0,
        -1,
        True,  # bool e int em Python, mas True nao e a posicao 1
        False,
        1.0,
        2.5,
        float("nan"),
        "0",
        "-1",
        "+1",
        "1.0",
        "dois",
        "٢",  # digito arabe-indico: int() aceita, a posicao nao
        "1234567890",  # dez digitos
        1_000_000_000,
        " 2",
        [1],
    ],
)
def test_rn_ac_23_posicao_invalida_e_tipo(valor):
    assert _recusa(converter, PARAMETROS["concluir_etapa"], {"posicao": valor}) == (
        "posicao",
        "tipo",
        None,
    )


# --- G10: cada maximo, no limite e um acima --------------------------------------


@pytest.mark.parametrize(
    ("acao", "parametro", "maximo", "outros"),
    [
        ("criar_frente", "nome", MAXIMO_NOME, {}),
        ("criar_tarefa", "nome", MAXIMO_NOME, {}),
        ("criar_chat", "agente", MAXIMO_AGENTE, {}),
        ("criar_chat", "nome", MAXIMO_NOME, {"agente": "bibliotecario"}),
        ("criar_etapa", "descricao", MAXIMO_DESCRICAO, {"executor": "agente"}),
        ("anotar_memoria", "chave", MAXIMO_CHAVE, {"valor": "v"}),
        ("anotar_memoria", "valor", MAXIMO_VALOR, {"chave": "k"}),
    ],
)
def test_g10_limite_de_tamanho(acao, parametro, maximo, outros):
    no_limite = {**outros, parametro: "x" * maximo}
    acima = {**outros, parametro: "x" * (maximo + 1)}

    assert converter(PARAMETROS[acao], no_limite)[parametro] == "x" * maximo
    assert _recusa(converter, PARAMETROS[acao], acima) == (parametro, "longo_demais", maximo)


def test_g10_os_numeros():
    assert (MAXIMO_NOME, MAXIMO_AGENTE, MAXIMO_CHAVE, MAXIMO_DESCRICAO, MAXIMO_VALOR) == (
        200,
        100,
        100,
        1_000,
        20_000,
    )


# --- a ordem dentro de ARGUMENTO_INVALIDO ----------------------------------------


def test_desconhecidas_primeiro_em_ordem_alfabetica():
    argumentos = {"zeta": 1, "autor": "eu", "nome": None}

    assert _recusa(converter, PARAMETROS["criar_frente"], argumentos) == (
        "autor",
        "desconhecido",
        None,
    )


def test_rn_ac_13_autor_vindo_de_fora_e_parametro_desconhecido():
    argumentos = {"chave": "k", "valor": "v", "autor": "orquestrador"}

    assert _recusa(converter, PARAMETROS["anotar_memoria"], argumentos) == (
        "autor",
        "desconhecido",
        None,
    )


def test_depois_os_parametros_na_ordem_do_registro():
    """`chave` vem antes de `valor`: o problema da chave e o que aparece."""
    argumentos = {"chave": 5, "valor": "x" * (MAXIMO_VALOR + 1)}

    assert _recusa(converter, PARAMETROS["anotar_memoria"], argumentos) == ("chave", "tipo", None)


def test_dentro_do_parametro_ausente_tipo_opcao_tamanho():
    """Para o mesmo parametro, a primeira verificacao que falha decide."""
    parametros = (Parametro("p", TipoParametro.TEXTO, "", maximo=3),)

    assert _recusa(converter, parametros, {})[1] == "ausente"
    assert _recusa(converter, parametros, {"p": 12345})[1] == "tipo"
    assert _recusa(converter, parametros, {"p": "abcd"})[1] == "longo_demais"


def test_chave_desconhecida_longa_volta_cortada():
    chave = "k" * 500

    parametro, problema, _ = _recusa(converter, PARAMETROS["criar_frente"], {chave: 1})

    assert (parametro, problema) == ("k" * 100, "desconhecido")
