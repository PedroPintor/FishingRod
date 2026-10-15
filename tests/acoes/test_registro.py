"""U5 - o registro (RN-AC-05..09, R-CG5-3, criterio 2).

As 6 acoes como dado, `listar` e `buscar`, e um CatalogoInvalido para cada
defeito que RN-AC-08 e R-CG5-3 recusam na construcao. Sem propriedade, de
proposito (business-logic-model.md 7): sao 6 entradas fixas.
"""

import dataclasses

import pytest

from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes, comando_de, nome_de
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    CatalogoInvalido,
    ErroDoCatalogo,
    Escopo,
    Parametro,
    TipoParametro,
)
from fishingrod.dominio import Chamador

POS = TipoParametro.POSICAO
TEXTO = TipoParametro.TEXTO
ESCOLHA = TipoParametro.ESCOLHA
OS_DOIS = frozenset({Chamador.USUARIO, Chamador.AGENTE})


async def _nada(*_):
    return None


def _catalogo(acoes=ACOES) -> CatalogoDeAcoes:
    # O servico e a porta nao sao usados por listar, buscar nem pela
    # verificacao do registro.
    return CatalogoDeAcoes(servico=None, confirmacao=None, acoes=acoes)


def _acao(nome="acao", escopo=Escopo.TAREFA, parametros=(), chamadores=OS_DOIS) -> Acao:
    return Acao(nome, "descricao", escopo, tuple(parametros), frozenset(chamadores), _nada)


def _texto(nome="p", obrigatorio=True, maximo=10) -> Parametro:
    return Parametro(nome, TEXTO, "", obrigatorio=obrigatorio, maximo=maximo)


# --- as 6 acoes (domain-entities.md 2.5) -------------------------------------


def _forma(acao: Acao) -> tuple:
    return (
        acao.nome,
        comando_de(acao.nome),
        acao.escopo,
        tuple(
            (p.nome, p.tipo, p.obrigatorio, p.opcoes, p.maximo) for p in acao.parametros
        ),
        acao.chamadores,
    )


def test_rn_ac_05_as_6_acoes_com_escopo_parametros_e_quem_aciona():
    assert [_forma(acao) for acao in ACOES] == [
        ("criar_frente", "criar-frente", Escopo.AMBIENTE, (("nome", TEXTO, True, (), 200),), OS_DOIS),
        ("criar_tarefa", "criar-tarefa", Escopo.FRENTE, (("nome", TEXTO, True, (), 200),), OS_DOIS),
        (
            "criar_chat",
            "criar-chat",
            Escopo.TAREFA,
            (("agente", TEXTO, True, (), 100), ("nome", TEXTO, False, (), 200)),
            OS_DOIS,
        ),
        (
            "criar_etapa",
            "criar-etapa",
            Escopo.TAREFA,
            (
                ("executor", ESCOLHA, True, ("agente", "usuario"), None),
                ("descricao", TEXTO, True, (), 1_000),
            ),
            OS_DOIS,
        ),
        ("concluir_etapa", "concluir-etapa", Escopo.TAREFA, (("posicao", POS, True, (), None),), OS_DOIS),
        (
            "anotar_memoria",
            "anotar-memoria",
            Escopo.TAREFA,
            (("chave", TEXTO, True, (), 100), ("valor", TEXTO, True, (), 20_000)),
            OS_DOIS,
        ),
    ]


def test_rn_ac_11_e_13_nenhum_parametro_e_identidade_nem_autor():
    nomes = {p.nome for acao in ACOES for p in acao.parametros}

    assert not any(nome.startswith("id") for nome in nomes)
    assert "autor" not in nomes
    assert "frente" not in nomes and "tarefa" not in nomes and "ambiente" not in nomes


def test_toda_acao_e_todo_parametro_tem_descricao():
    """A paleta mostra e o esquema da ferramenta do agente carrega (U6)."""
    for acao in ACOES:
        assert acao.descricao.strip(), acao.nome
        for parametro in acao.parametros:
            assert parametro.descricao.strip(), (acao.nome, parametro.nome)


def test_o_registro_padrao_e_valido():
    assert _catalogo().listar() == ACOES


# --- RN-AC-07: um nome, dois jeitos de escrever --------------------------------


@pytest.mark.parametrize("acao", ACOES, ids=lambda acao: acao.nome)
def test_rn_ac_07_comando_e_o_nome_com_hifen(acao):
    comando = comando_de(acao.nome)

    assert "_" not in comando
    assert nome_de(comando) == acao.nome


@pytest.mark.parametrize("comando", ["criar_tarefa", "criar-tarefa_", "_"])
def test_rn_ac_07_g7_comando_com_sublinhado_nao_e_comando(comando):
    assert nome_de(comando) is None


# --- RN-AC-09: listar e buscar --------------------------------------------------


def test_rn_ac_09_listar_por_escopo_na_ordem_do_registro():
    catalogo = _catalogo()

    assert [a.nome for a in catalogo.listar(Escopo.AMBIENTE)] == ["criar_frente"]
    assert [a.nome for a in catalogo.listar(Escopo.FRENTE)] == ["criar_tarefa"]
    assert [a.nome for a in catalogo.listar(Escopo.TAREFA)] == [
        "criar_chat",
        "criar_etapa",
        "concluir_etapa",
        "anotar_memoria",
    ]


def test_rn_ac_09_listar_por_quem_aciona():
    so_usuario = _acao("so_usuario", chamadores={Chamador.USUARIO})
    so_agente = _acao("so_agente", chamadores={Chamador.AGENTE})
    catalogo = _catalogo((so_usuario, *ACOES, so_agente))

    assert [a.nome for a in catalogo.listar(chamador=Chamador.USUARIO)][:2] == [
        "so_usuario",
        "criar_frente",
    ]
    assert "so_agente" not in [a.nome for a in catalogo.listar(chamador=Chamador.USUARIO)]
    assert [a.nome for a in catalogo.listar(Escopo.TAREFA, Chamador.AGENTE)] == [
        "criar_chat",
        "criar_etapa",
        "concluir_etapa",
        "anotar_memoria",
        "so_agente",
    ]


def test_rn_ac_09_q2_b_o_orquestrador_recebe_as_6():
    assert _catalogo().listar(chamador=Chamador.AGENTE) == ACOES


def test_buscar_pelo_nome_da_acao_e_nao_pelo_comando():
    catalogo = _catalogo()

    assert catalogo.buscar("criar_tarefa") is ACOES[1]
    assert catalogo.buscar("criar-tarefa") is None
    assert catalogo.buscar("enviar_mensagem") is None


def test_registro_vazio_e_valido():
    assert _catalogo(()).listar() == ()


# --- RN-AC-08 e R-CG5-3: um CatalogoInvalido para cada defeito -----------------

DEFEITOS = {
    "item que nao e acao": [object()],
    "nome com hifen": [_acao("criar-frente")],
    "nome com maiuscula": [_acao("Criar")],
    "nome com sublinhado no fim": [_acao("criar_")],
    "nome com sublinhado duplo": [_acao("criar__frente")],
    "nome comecando com digito": [_acao("1acao")],
    "nome com acento": [_acao("anotação")],
    "nome vazio": [_acao("")],
    "acao repetida": [_acao("a"), _acao("a")],
    "sem chamadores": [_acao(chamadores=())],
    "chamador que nao e Chamador": [_acao(chamadores={"agente"})],
    "parametro com nome fora do padrao": [_acao(parametros=[_texto("Nome")])],
    "parametro repetido": [_acao(parametros=[_texto("p"), _texto("p")])],
    "obrigatorio depois de opcional": [
        _acao(parametros=[_texto("a", obrigatorio=False), _texto("b")])
    ],
    "escolha sem opcoes": [_acao(parametros=[Parametro("e", ESCOLHA, "")])],
    "opcoes fora de escolha": [
        _acao(parametros=[Parametro("t", TEXTO, "", opcoes=("a",), maximo=5)])
    ],
    "opcoes que so diferem no acento": [
        _acao(parametros=[Parametro("e", ESCOLHA, "", opcoes=("usuario", "Usuário"))])
    ],
    "texto sem maximo": [_acao(parametros=[_texto(maximo=None)])],
    "texto com maximo zero": [_acao(parametros=[_texto(maximo=0)])],
    "texto com maximo bool": [_acao(parametros=[_texto(maximo=True)])],
    "maximo fora de texto": [_acao(parametros=[Parametro("k", POS, "", maximo=3)])],
    "posicao em escopo ambiente": [
        _acao(escopo=Escopo.AMBIENTE, parametros=[Parametro("k", POS, "")])
    ],
    "posicao em escopo frente": [_acao(escopo=Escopo.FRENTE, parametros=[Parametro("k", POS, "")])],
    "duas posicoes": [_acao(parametros=[Parametro("j", POS, ""), Parametro("k", POS, "")])],
}


@pytest.mark.parametrize("defeito", DEFEITOS, ids=list(DEFEITOS))
def test_rn_ac_08_registro_invalido_na_construcao(defeito):
    with pytest.raises(CatalogoInvalido):
        _catalogo(DEFEITOS[defeito])


def test_rn_ac_08_o_defeito_quebra_mesmo_misturado_ao_registro_bom():
    defeituosa = dataclasses.replace(ACOES[0], nome="criar-frente")

    with pytest.raises(CatalogoInvalido):
        _catalogo((*ACOES, defeituosa))


def test_rn_ac_08_catalogo_invalido_e_erro_do_catalogo():
    assert issubclass(CatalogoInvalido, ErroDoCatalogo)


def test_rn_ac_08_o_que_e_valido_passa():
    """Os casos-limite que a verificacao NAO pode recusar: opcional no fim,
    uma posicao em escopo TAREFA, nomes com digito, acao sem parametro."""
    validas = [
        _acao("a1", parametros=[_texto("p1"), _texto("p2", obrigatorio=False)]),
        _acao("b_2_c", parametros=[Parametro("k", POS, "")]),
        _acao("sem_parametro", escopo=Escopo.AMBIENTE),
        _acao("so_usuario", chamadores={Chamador.USUARIO}),
        _acao("escolha", parametros=[Parametro("e", ESCOLHA, "", opcoes=("sim", "não"))]),
    ]

    assert _catalogo(validas).listar() == tuple(validas)
