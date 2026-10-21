"""U5 - CatalogoDeAcoes, por exemplos (PBT-10): os criterios de pronto, um
exemplo por motivo de falha, a confirmacao, o log e o cancelamento.

Sempre contra o ServicoDeAmbiente real sobre o RepositorioEmMemoria; os
instrumentos so embrulham. As propriedades geradas estao em
test_propriedades.py.
"""

import asyncio
import logging

import pytest

from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.parser import ParserDeComando
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    Acionamento,
    Alvo,
    Escopo,
    EtapaNaPosicao,
    MotivoFalha,
    Resultado,
)
from fishingrod.aplicacao.portas.persistencia import BancoIlegivel, ConflitoDeVersao
from fishingrod.aplicacao.portas.wiki import ArmazenamentoIndisponivel
from fishingrod.dominio import (
    Ambiente,
    Anotacao,
    Chamador,
    Chat,
    ExecutorEtapa,
    Frente,
    OrquestradorDuplicado,
    Tarefa,
)
from tests.acoes.estrategias import (
    BIBLIOTECARIO,
    INEXISTENTE,
    ORQUESTRADOR,
    executar,
    montar,
)
from tests.acoes.instrumentos import (
    ConfirmacaoFixa,
    ConfirmacaoProibida,
    ConfirmacaoQueEspera,
    ConfirmacaoQueLevanta,
    ServicoEspiao,
    ServicoSabotado,
)
from tests.acoes.modelo import forma

parser = ParserDeComando()
AGENTE = Acionamento.agente(ORQUESTRADOR.nome)
USUARIO = Acionamento.usuario()


def _ambiente() -> tuple[Ambiente, Frente, Tarefa]:
    """Duas frentes; a tarefa do chat e "Campanha", com duas etapas."""
    ambiente = Ambiente("Nexo")
    frente = ambiente.criar_frente("Comercial")
    ambiente.criar_frente("Operação")
    tarefa = frente.criar_tarefa("Campanha", ORQUESTRADOR)
    tarefa.criar_etapa("ler o material", ExecutorEtapa.USUARIO)
    tarefa.criar_etapa("resumir", ExecutorEtapa.AGENTE)
    return ambiente, frente, tarefa


def _alvo(ambiente: Ambiente, frente: Frente, tarefa: Tarefa) -> Alvo:
    return Alvo(ambiente.id, frente.id, tarefa.id, tarefa.sessoes[0].id)


def _falha(resultado: Resultado) -> tuple:
    return resultado.motivo, dict(resultado.detalhe)


def _cenario(tmp_path, porta, corpo, *, instrumento=ServicoEspiao, acoes=None):
    """Monta sobre o ambiente de exemplo e roda `corpo(montagem, ambiente,
    frente, tarefa)` num laco so."""
    ambiente, frente, tarefa = _ambiente()

    async def rodar():
        extras = {} if acoes is None else {"acoes": acoes}
        montagem = await montar(tmp_path, ambiente, porta, instrumento=instrumento, **extras)
        return await corpo(montagem, ambiente, frente, tarefa)

    return executar(rodar())


# --------------------------------------------------------------------------
# Criterio 1 (TD-11) e criterio 3 (G1)
# --------------------------------------------------------------------------


def test_criterio_1_criar_tarefa_campanha_de_verao(tmp_path):
    """O argumento inteiro chega como nome - era isso que TD-11 quebrava."""

    async def corpo(m, ambiente, frente, tarefa):
        comando = parser.interpretar("/criar-tarefa campanha de verao")
        resultado = await m.catalogo.executar_comando(comando, Alvo(ambiente.id, frente.id))
        aberto = await m.aberto(ambiente.id)
        return resultado, [t.nome for t in aberto.buscar_frente(frente.id).tarefas]

    resultado, nomes = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert resultado.sucesso
    assert resultado.dado.nome == "campanha de verao"
    assert nomes == ["Campanha", "campanha de verao"]


@pytest.mark.parametrize(
    ("linha", "tipo"),
    [
        ("/criar-frente comercial e ticket", Frente),
        ("/criar-tarefa campanha de verao", Tarefa),
        ("/criar-chat bibliotecario pesquisa de ICP", Chat),
        ("/criar-etapa usuario assistir a aula 3", EtapaNaPosicao),
        ("/concluir-etapa 2", EtapaNaPosicao),
        ("/anotar-memoria travado-por esperando o cliente", Anotacao),
    ],
)
def test_criterio_3_g1_toda_acao_devolve_resultado_com_o_objeto(tmp_path, linha, tipo):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar_comando(
            parser.interpretar(linha), _alvo(ambiente, frente, tarefa)
        )

    resultado = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert isinstance(resultado, Resultado)
    assert resultado.sucesso and resultado.motivo is None and dict(resultado.detalhe) == {}
    assert isinstance(resultado.dado, tipo)


def test_g5_criar_etapa_e_concluir_etapa_devolvem_a_posicao(tmp_path):
    """O dado e o objeto VIVO do ambiente aberto, como em U4: por isso o
    estado da etapa criada e lido antes de concluir."""

    async def corpo(m, ambiente, frente, tarefa):
        alvo = _alvo(ambiente, frente, tarefa)
        criada = await m.catalogo.executar_comando(parser.interpretar("/criar-etapa agente revisar"), alvo)
        ao_criar = (criada.dado.posicao, criada.dado.etapa.descricao, criada.dado.etapa.concluida)
        concluida = await m.catalogo.executar_comando(parser.interpretar("/concluir-etapa 3"), alvo)
        return ao_criar, criada.dado, concluida.dado

    ao_criar, criada, concluida = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert ao_criar == (3, "revisar", False)
    assert (concluida.posicao, concluida.etapa.concluida) == (3, True)
    assert concluida.etapa is criada.etapa


def test_rn_ac_10_identidades_alem_das_exigidas_sao_ignoradas(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        frente_nova = await m.catalogo.executar(
            "criar_frente", Alvo(ambiente.id, INEXISTENTE, INEXISTENTE), {"nome": "x"}, USUARIO
        )
        etapa = await m.catalogo.executar(
            "concluir_etapa", Alvo(ambiente.id, None, tarefa.id), {"posicao": 1}, USUARIO
        )
        return frente_nova, etapa

    frente_nova, etapa = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert frente_nova.sucesso and etapa.sucesso


# --------------------------------------------------------------------------
# Um exemplo por MotivoFalha (Q10=A)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("nome", "como_veio"),
    [("enviar_mensagem", "enviar_mensagem"), ("criar-tarefa", "criar-tarefa"), ("", "")],
)
def test_acao_desconhecida_por_nome(tmp_path, nome, como_veio):
    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar(nome, _alvo(ambiente, frente, tarefa), {}, AGENTE)
        return resultado, m.visto.chamadas

    resultado, chamadas = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert _falha(resultado) == (MotivoFalha.ACAO_DESCONHECIDA, {"acao": como_veio})
    assert chamadas == []


@pytest.mark.parametrize(
    ("linha", "como_veio"),
    [("/criar_tarefa x", "criar_tarefa"), ("/", ""), ("/ajuda", "ajuda"), ("/Criar-Tarefa x", "Criar-Tarefa")],
)
def test_acao_desconhecida_pela_barra_g7(tmp_path, linha, como_veio):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar_comando(parser.interpretar(linha), _alvo(ambiente, frente, tarefa))

    resultado = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert _falha(resultado) == (MotivoFalha.ACAO_DESCONHECIDA, {"acao": como_veio})


def test_nao_permitida_rn_ac_06_antes_de_qualquer_outra_verificacao(tmp_path):
    """Um registro de teste com uma acao so do usuario. O agente recebe
    NAO_PERMITIDA mesmo com o alvo incompleto e os argumentos errados: a
    autorizacao e conferida no catalogo, e antes de tudo."""
    executadas = []

    async def efetivar(*argumentos):
        executadas.append(argumentos)
        return "feito"

    so_usuario = Acao(
        "so_usuario", "teste", Escopo.TAREFA, (), frozenset({Chamador.USUARIO}), efetivar
    )

    async def corpo(m, ambiente, frente, tarefa):
        do_agente = await m.catalogo.executar("so_usuario", Alvo(ambiente.id), {"lixo": 1}, AGENTE)
        do_usuario = await m.catalogo.executar(
            "so_usuario", _alvo(ambiente, frente, tarefa), {}, USUARIO
        )
        return do_agente, do_usuario

    do_agente, do_usuario = _cenario(tmp_path, ConfirmacaoProibida(), corpo, acoes=(so_usuario,))

    assert _falha(do_agente) == (
        MotivoFalha.NAO_PERMITIDA,
        {"acao": "so_usuario", "chamador": "agente"},
    )
    assert do_usuario.sucesso and do_usuario.dado == "feito"
    assert len(executadas) == 1


def test_argumento_invalido(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar_comando(
            parser.interpretar("/criar-tarefa"), Alvo(ambiente.id, frente.id)
        )

    resultado = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert _falha(resultado) == (
        MotivoFalha.ARGUMENTO_INVALIDO,
        {"parametro": "nome", "problema": "ausente"},
    )


@pytest.mark.parametrize(
    ("linha", "falta"),
    [
        ("/criar-tarefa x", "frente"),
        ("/criar-tarefa", "frente"),
        ("/concluir-etapa dois", "tarefa"),
        ("/criar-sessao", "tarefa"),
        ("/anotar-memoria k", "sessao"),
    ],
)
def test_alvo_ausente_antes_dos_argumentos_e_sem_ler_nada(tmp_path, linha, falta):
    """R-CG5-2: o texto so e repartido no passo 4, entao o alvo incompleto
    aparece antes do argumento ruim. E nada foi lido (passos 1 a 4)."""

    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar_comando(parser.interpretar(linha), Alvo(ambiente.id))
        return resultado, m.visto.chamadas

    resultado, chamadas = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert _falha(resultado) == (MotivoFalha.ALVO_AUSENTE, {"falta": falta})
    assert chamadas == []


def test_alvo_inexistente(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        executar_ = m.catalogo.executar
        return (
            await executar_("criar_frente", Alvo(INEXISTENTE), {"nome": "x"}, USUARIO),
            await executar_("criar_tarefa", Alvo(ambiente.id, INEXISTENTE), {"nome": "x"}, USUARIO),
            await executar_(
                "criar_etapa",
                Alvo(ambiente.id, frente.id, INEXISTENTE),
                {"executor": "agente", "descricao": "x"},
                USUARIO,
            ),
            await executar_(
                "anotar_memoria",
                Alvo(ambiente.id, frente.id, tarefa.id, INEXISTENTE),
                {"chave": "k", "valor": "v"},
                USUARIO,
            ),
            await executar_("concluir_etapa", _alvo(ambiente, frente, tarefa), {"posicao": 3}, USUARIO),
            m.visto.mudancas(),
        )

    *resultados, mudancas = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert [_falha(r) for r in resultados] == [
        (MotivoFalha.ALVO_INEXISTENTE, {"alvo": "ambiente"}),
        (MotivoFalha.ALVO_INEXISTENTE, {"alvo": "frente"}),
        (MotivoFalha.ALVO_INEXISTENTE, {"alvo": "tarefa"}),
        (MotivoFalha.ALVO_INEXISTENTE, {"alvo": "sessao"}),
        (MotivoFalha.ALVO_INEXISTENTE, {"alvo": "etapa", "posicao": "3", "total": "2"}),
    ]
    assert mudancas == []


def test_regra_violada_vinda_do_dominio(tmp_path):
    """Um Acionamento montado com nome vazio (defeito de U9): o dominio recusa
    o autor da anotacao, e o catalogo so traduz - com o NOME do tipo do erro,
    nunca a mensagem."""

    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar(
            "anotar_memoria",
            _alvo(ambiente, frente, tarefa),
            {"chave": "k", "valor": "v"},
            Acionamento.agente("   "),
        )

    resultado = _cenario(tmp_path, ConfirmacaoFixa(True), corpo)

    assert _falha(resultado) == (MotivoFalha.REGRA_VIOLADA, {"erro": "NomeInvalido"})


@pytest.mark.parametrize(
    ("erro", "onde", "falha"),
    [
        (ConflitoDeVersao, "operacao", (MotivoFalha.CONFLITO, {})),
        (BancoIlegivel, "leitura", (MotivoFalha.FALHA_DE_ARMAZENAMENTO, {"erro": "BancoIlegivel"})),
        (
            ArmazenamentoIndisponivel,
            "operacao",
            (MotivoFalha.FALHA_DE_ARMAZENAMENTO, {"erro": "ArmazenamentoIndisponivel"}),
        ),
        (OrquestradorDuplicado, "operacao", (MotivoFalha.REGRA_VIOLADA, {"erro": "OrquestradorDuplicado"})),
    ],
)
def test_conflito_armazenamento_e_regra_pelo_servico(tmp_path, erro, onde, falha):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar_comando(
            parser.interpretar("/criar-etapa agente revisar"), _alvo(ambiente, frente, tarefa)
        )

    resultado = _cenario(
        tmp_path,
        ConfirmacaoProibida(),
        corpo,
        instrumento=lambda servico: ServicoSabotado(servico, lambda: erro("C:/dados/segredo"), onde),
    )

    assert _falha(resultado) == falha
    assert "segredo" not in repr(resultado)  # RN-AC-35: nada de caminho de disco


def test_recusada_rn_ac_33_nada_e_escrito(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        antes = forma(await m.aberto(ambiente.id))
        resultado = await m.catalogo.executar(
            "criar_frente", Alvo(ambiente.id), {"nome": "Nova"}, AGENTE
        )
        aberto = await m.aberto(ambiente.id)
        return resultado, antes, forma(aberto), m.visto.mudancas()

    porta = ConfirmacaoFixa(False)
    resultado, antes, depois, mudancas = _cenario(tmp_path, porta, corpo)

    assert _falha(resultado) == (MotivoFalha.RECUSADA, {})
    assert len(porta.pedidos) == 1
    assert (depois, mudancas) == (antes, [])


def test_falha_inesperada_rn_ac_37_vai_para_o_log_sem_os_argumentos(tmp_path, caplog):
    caplog.set_level(logging.ERROR, logger="fishingrod.acoes")

    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar(
            "anotar_memoria",
            _alvo(ambiente, frente, tarefa),
            {"chave": "cliente-sigiloso", "valor": "telefone 99999-0000"},
            USUARIO,
        )

    resultado = _cenario(
        tmp_path,
        ConfirmacaoProibida(),
        corpo,
        instrumento=lambda servico: ServicoSabotado(servico, lambda: RuntimeError("defeito"), "operacao"),
    )

    assert _falha(resultado) == (MotivoFalha.FALHA_INESPERADA, {})
    [registro] = caplog.records
    assert registro.levelno == logging.ERROR and registro.name == "fishingrod.acoes"
    assert "anotar_memoria" in registro.getMessage()
    assert "usuario" in registro.getMessage()
    assert "RuntimeError" in registro.getMessage()
    assert registro.exc_info is not None  # a pilha vai junto
    assert "cliente-sigiloso" not in caplog.text and "99999" not in caplog.text


def test_resultado_nao_traz_frase_nem_mensagem_do_erro(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar(
            "criar_chat", _alvo(ambiente, frente, tarefa), {"agente": "fulano"}, USUARIO
        )

    resultado = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    # A mensagem de AgenteDesconhecido lista os agentes; o Resultado, nao.
    assert _falha(resultado) == (
        MotivoFalha.ARGUMENTO_INVALIDO,
        {"parametro": "agente", "problema": "fora_da_lista"},
    )


# --------------------------------------------------------------------------
# Criterio 6: a lista fechada de agentes (cumprida por U4, traduzida aqui)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("agente", "sucesso"),
    [(BIBLIOTECARIO.nome, True), (ORQUESTRADOR.nome, False), ("fulano", False), ("Bibliotecario", False)],
)
def test_criterio_6_criar_chat_so_com_agente_da_lista(tmp_path, agente, sucesso):
    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar_comando(
            parser.interpretar(f"/criar-chat {agente}"), _alvo(ambiente, frente, tarefa)
        )
        aberto = await m.aberto(ambiente.id)
        depois = aberto.frentes[0].tarefas[0]
        return resultado, [(c.agente.nome, c.nome) for c in depois.sessoes[0].chats]

    resultado, chats = _cenario(tmp_path, ConfirmacaoProibida(), corpo)

    assert resultado.sucesso is sucesso
    if sucesso:
        # nome ausente -> o nome do agente (R-CG5-4 e o Chat de U1)
        assert chats == [(ORQUESTRADOR.nome, ORQUESTRADOR.nome), (agente, agente)]
    else:
        assert resultado.detalhe["problema"] == "fora_da_lista"
        assert chats == [(ORQUESTRADOR.nome, ORQUESTRADOR.nome)]


# --------------------------------------------------------------------------
# Quem aciona (RN-AC-11..15)
# --------------------------------------------------------------------------


def test_rn_ac_14_c1_a_a_tarefa_do_agente_nasce_na_frente_da_tarefa_do_chat(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar(
            "criar_tarefa", _alvo(ambiente, frente, tarefa), {"nome": "follow-up"}, AGENTE
        )
        aberto = await m.aberto(ambiente.id)
        return resultado, [[t.nome for t in f.tarefas] for f in aberto.frentes]

    resultado, tarefas = _cenario(tmp_path, ConfirmacaoFixa(True), corpo)

    assert resultado.sucesso
    assert tarefas == [["Campanha", "follow-up"], []]


def test_rn_ac_13_o_autor_e_quem_acionou(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        alvo = _alvo(ambiente, frente, tarefa)
        pelo_usuario = await m.catalogo.executar_comando(
            parser.interpretar("/anotar-memoria icp dentistas"), alvo
        )
        pelo_agente = await m.catalogo.executar(
            "anotar_memoria", alvo, {"chave": "icp", "valor": "clínicas pequenas"}, AGENTE
        )
        com_autor = await m.catalogo.executar(
            "anotar_memoria", alvo, {"chave": "icp", "valor": "x", "autor": "usuario"}, AGENTE
        )
        aberto = await m.aberto(ambiente.id)
        anotacoes = aberto.frentes[0].tarefas[0].sessoes[0].memoria.anotacoes["icp"]
        return pelo_usuario, pelo_agente, com_autor, [(a.autor, a.valor) for a in anotacoes]

    porta = ConfirmacaoFixa(True)
    pelo_usuario, pelo_agente, com_autor, anotacoes = _cenario(tmp_path, porta, corpo)

    assert pelo_usuario.dado.autor == "usuario"
    assert pelo_agente.dado.autor == ORQUESTRADOR.nome
    assert _falha(com_autor) == (
        MotivoFalha.ARGUMENTO_INVALIDO,
        {"parametro": "autor", "problema": "desconhecido"},
    )
    assert anotacoes == [("usuario", "dentistas"), (ORQUESTRADOR.nome, "clínicas pequenas")]
    assert len(porta.pedidos) == 1  # o argumento ruim nao perguntou (RN-AC-21)


def test_rn_ac_15_a_barra_aciona_como_usuario_e_nao_pergunta(tmp_path):
    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar_comando(
            parser.interpretar("/anotar-memoria travado-por esperando o cliente"),
            _alvo(ambiente, frente, tarefa),
        )

    porta = ConfirmacaoProibida()
    resultado = _cenario(tmp_path, porta, corpo)

    assert resultado.sucesso and resultado.dado.autor == "usuario"
    assert not porta.perguntou


@pytest.mark.parametrize(
    ("nome", "alvo_de", "argumentos", "motivo"),
    [
        ("criar_etapa", "tarefa", {"executor": "talvez", "descricao": "x"}, MotivoFalha.ARGUMENTO_INVALIDO),
        ("criar_tarefa", "ambiente", {"nome": "x"}, MotivoFalha.ALVO_AUSENTE),
        ("criar_tarefa", "frente_inexistente", {"nome": "x"}, MotivoFalha.ALVO_INEXISTENTE),
        ("concluir_etapa", "tarefa", {"posicao": 9}, MotivoFalha.ALVO_INEXISTENTE),
        ("criar_frente", "ambiente_inexistente", {"nome": "x"}, MotivoFalha.ALVO_INEXISTENTE),
    ],
)
def test_rn_ac_21_o_que_nao_executaria_nunca_e_perguntado(tmp_path, nome, alvo_de, argumentos, motivo):
    async def corpo(m, ambiente, frente, tarefa):
        alvo = {
            "tarefa": _alvo(ambiente, frente, tarefa),
            "ambiente": Alvo(ambiente.id),
            "frente_inexistente": Alvo(ambiente.id, INEXISTENTE),
            "ambiente_inexistente": Alvo(INEXISTENTE),
        }[alvo_de]
        resultado = await m.catalogo.executar(nome, alvo, argumentos, AGENTE)
        return resultado, m.visto.mudancas()

    porta = ConfirmacaoProibida()
    resultado, mudancas = _cenario(tmp_path, porta, corpo)

    assert resultado.motivo is motivo
    assert not porta.perguntou and mudancas == []


# --------------------------------------------------------------------------
# A confirmacao (RN-AC-27..33, criterio 5)
# --------------------------------------------------------------------------


def test_criterio_5_a_acao_do_agente_so_executa_depois_do_sim(tmp_path):
    porta = ConfirmacaoQueEspera(True)

    async def corpo(m, ambiente, frente, tarefa):
        pedido = asyncio.create_task(
            m.catalogo.executar(
                "criar_etapa",
                _alvo(ambiente, frente, tarefa),
                {"executor": "usuario", "descricao": "ler o material"},
                AGENTE,
            )
        )
        await porta.chegou.wait()
        antes_do_sim = list(m.visto.mudancas())
        porta.liberada.set()
        resultado = await pedido
        return antes_do_sim, resultado, m.visto.mudancas()

    antes_do_sim, resultado, depois = _cenario(tmp_path, porta, corpo)

    assert antes_do_sim == []
    assert resultado.sucesso and resultado.dado.posicao == 3
    assert [operacao for operacao, _ in depois] == ["criar_etapa"]


def test_d_q2_2_o_pedido_mostra_nomes_posicao_e_descricao(tmp_path):
    """G2: as referencias ja achadas. Em concluir_etapa, a posicao E a
    descricao, para uma posicao errada ficar visivel antes do sim."""

    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar(
            "concluir_etapa", _alvo(ambiente, frente, tarefa), {"posicao": "2"}, AGENTE
        )

    porta = ConfirmacaoFixa(True)
    resultado = _cenario(tmp_path, porta, corpo)

    [pedido] = porta.pedidos
    assert pedido.acao == "concluir_etapa"
    assert pedido.acionamento == AGENTE
    assert dict(pedido.argumentos) == {"posicao": 2}
    assert pedido.referencias.frente.nome == "Comercial"
    assert pedido.referencias.tarefa.nome == "Campanha"
    assert (pedido.referencias.etapa.posicao, pedido.referencias.etapa.etapa.descricao) == (2, "resumir")
    assert resultado.sucesso and resultado.dado.etapa.id == pedido.referencias.etapa.etapa.id


def test_rn_ac_31_o_pedido_e_somente_leitura(tmp_path):
    class PortaQueEdita:
        async def confirmar(self, pedido):
            pedido.argumentos["descricao"] = "outra coisa"
            return True

    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar(
            "criar_etapa", _alvo(ambiente, frente, tarefa), {"executor": "agente", "descricao": "x"}, AGENTE
        )
        return resultado, m.visto.mudancas()

    resultado, mudancas = _cenario(tmp_path, PortaQueEdita(), corpo)

    # Tentar editar levanta dentro da porta: falha inesperada, e nada executa.
    assert resultado.motivo is MotivoFalha.FALHA_INESPERADA
    assert mudancas == []


def test_rn_ac_31_executa_o_que_foi_mostrado_mesmo_se_quem_chamou_mexer_depois(tmp_path):
    porta = ConfirmacaoQueEspera(True)

    async def corpo(m, ambiente, frente, tarefa):
        argumentos = {"executor": "agente", "descricao": "o que foi mostrado"}
        pedido = asyncio.create_task(
            m.catalogo.executar("criar_etapa", _alvo(ambiente, frente, tarefa), argumentos, AGENTE)
        )
        await porta.chegou.wait()
        argumentos["descricao"] = "trocado durante a espera"
        porta.liberada.set()
        return await pedido, porta.pedidos[0]

    resultado, mostrado = _cenario(tmp_path, porta, corpo)

    assert mostrado.argumentos["descricao"] == "o que foi mostrado"
    assert resultado.dado.etapa.descricao == "o que foi mostrado"


@pytest.mark.parametrize("resposta", [False, None, 0, 1, "sim", "True", [], [True]])
def test_rn_ac_30_so_true_confirma(tmp_path, resposta):
    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar(
            "criar_frente", Alvo(ambiente.id), {"nome": "Nova"}, AGENTE
        )
        return resultado, m.visto.mudancas()

    resultado, mudancas = _cenario(tmp_path, ConfirmacaoFixa(resposta), corpo)

    assert _falha(resultado) == (MotivoFalha.RECUSADA, {})
    assert mudancas == []


@pytest.mark.parametrize("erro", [RuntimeError, BancoIlegivel, ConflitoDeVersao, ArmazenamentoIndisponivel])
def test_rn_ac_30_r_cg5_5_porta_que_levanta_e_falha_inesperada(tmp_path, caplog, erro):
    """Qualquer erro da porta e falha inesperada - um ErroDePersistencia vindo
    da tela nao e falha de armazenamento desta acao. Vai para o log, sem os
    argumentos, e nada executa."""
    caplog.set_level(logging.ERROR, logger="fishingrod.acoes")

    async def corpo(m, ambiente, frente, tarefa):
        resultado = await m.catalogo.executar(
            "anotar_memoria",
            _alvo(ambiente, frente, tarefa),
            {"chave": "conta", "valor": "senha-do-cliente-123"},
            AGENTE,
        )
        return resultado, m.visto.mudancas()

    resultado, mudancas = _cenario(tmp_path, ConfirmacaoQueLevanta(lambda: erro("tela")), corpo)

    assert _falha(resultado) == (MotivoFalha.FALHA_INESPERADA, {})
    assert mudancas == []
    [registro] = caplog.records
    assert erro.__name__ in registro.getMessage() and "agente" in registro.getMessage()
    assert "senha-do-cliente-123" not in caplog.text


def test_rn_ac_30_cancelar_a_espera_cancela_e_nada_executa(tmp_path):
    porta = ConfirmacaoQueEspera(True)

    async def corpo(m, ambiente, frente, tarefa):
        antes = forma(await m.aberto(ambiente.id))
        pedido = asyncio.create_task(
            m.catalogo.executar("criar_frente", Alvo(ambiente.id), {"nome": "Nova"}, AGENTE)
        )
        await porta.chegou.wait()
        pedido.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pedido
        porta.liberada.set()  # tarde demais: nao ha mais quem execute
        await asyncio.sleep(0)
        return antes, forma(await m.aberto(ambiente.id)), m.visto.mudancas()

    antes, depois, mudancas = _cenario(tmp_path, porta, corpo)

    assert (depois, mudancas) == (antes, [])


def test_rn_ac_32_pedido_pendente_nao_bloqueia_uma_acao_sua_no_mesmo_ambiente(tmp_path):
    """O agente pede uma etapa e espera voce; enquanto isso, voce cria outra
    pela barra. A sua termina sem esperar - nenhuma trava ficou presa -, e a
    do agente, confirmada depois, cai na posicao certa."""
    porta = ConfirmacaoQueEspera(True)

    async def corpo(m, ambiente, frente, tarefa):
        alvo = _alvo(ambiente, frente, tarefa)
        do_agente = asyncio.create_task(
            m.catalogo.executar(
                "criar_etapa", alvo, {"executor": "agente", "descricao": "do agente"}, AGENTE
            )
        )
        await porta.chegou.wait()
        sua = await asyncio.wait_for(
            m.catalogo.executar_comando(parser.interpretar("/criar-etapa usuario sua"), alvo),
            timeout=5,
        )
        porta.liberada.set()
        return sua, await do_agente

    sua, do_agente = _cenario(tmp_path, porta, corpo)

    assert sua.sucesso and sua.dado.posicao == 3
    assert do_agente.sucesso and do_agente.dado.posicao == 4


def test_usuario_executa_direto_pelo_botao_tambem(tmp_path):
    """RN-AC-29: pelo botao (executar, com o Acionamento do usuario), nao
    pela barra."""

    async def corpo(m, ambiente, frente, tarefa):
        return await m.catalogo.executar("criar_frente", Alvo(ambiente.id), {"nome": "Nova"}, USUARIO)

    porta = ConfirmacaoProibida()
    resultado = _cenario(tmp_path, porta, corpo)

    assert resultado.sucesso and not porta.perguntou


def test_catalogo_sem_estado_entre_execucoes(tmp_path):
    """Dois catalogos sobre o mesmo servico enxergam o mesmo ambiente: o
    catalogo nao guarda nada alem do registro e das duas referencias."""

    async def corpo(m, ambiente, frente, tarefa):
        outro = CatalogoDeAcoes(m.servico, ConfirmacaoProibida())
        await m.catalogo.executar("criar_frente", Alvo(ambiente.id), {"nome": "Uma"}, USUARIO)
        await outro.executar("criar_frente", Alvo(ambiente.id), {"nome": "Outra"}, USUARIO)
        return [f.nome for f in (await m.aberto(ambiente.id)).frentes]

    assert _cenario(tmp_path, ConfirmacaoProibida(), corpo) == ["Comercial", "Operação", "Uma", "Outra"]
