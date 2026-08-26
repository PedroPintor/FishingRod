"""U1 - Tarefa e Frente (RN-04, RN-05, RN-06, RN-08, RN-14)."""

import pytest

from fishingrod.dominio import (
    Agente,
    AgenteInvalido,
    ExecutorEtapa,
    Frente,
    Identidade,
    OrquestradorDuplicado,
    Papel,
    Tarefa,
)

ORQUESTRADOR = Agente(nome="orquestrador", papel=Papel.ORQUESTRADOR, modelo="claude")
BIBLIOTECARIO = Agente(nome="bibliotecario", papel=Papel.SUB_AGENTE, modelo="claude")


def test_rn_05_tarefa_nasce_com_um_chat_de_orquestrador():
    frente = Frente(nome="campanha de verao")

    tarefa = frente.criar_tarefa("mapear publico", ORQUESTRADOR)

    assert len(tarefa.chats) == 1
    assert tarefa.chats[0].agente is ORQUESTRADOR
    assert tarefa.contar_orquestradores() == 1


def test_rn_05_criar_tarefa_com_sub_agente_levanta():
    """O agente vem por parametro (Q4=A); passar um sub-agente e erro de
    dominio, nao um chat de sub-agente na posicao do orquestrador."""
    frente = Frente(nome="frente")

    with pytest.raises(AgenteInvalido):
        frente.criar_tarefa("tarefa", BIBLIOTECARIO)


def test_rn_06_segundo_orquestrador_levanta():
    frente = Frente(nome="frente")
    tarefa = frente.criar_tarefa("tarefa", ORQUESTRADOR)

    with pytest.raises(OrquestradorDuplicado):
        tarefa.criar_chat(ORQUESTRADOR)


def test_rn_06_sub_agente_sempre_pode_ganhar_chat():
    """E assim que o chat do bibliotecario nasce quando o orquestrador delega
    (Q14=X)."""
    frente = Frente(nome="frente")
    tarefa = frente.criar_tarefa("tarefa", ORQUESTRADOR)

    chat = tarefa.criar_chat(BIBLIOTECARIO)
    tarefa.criar_chat(BIBLIOTECARIO)

    assert chat.nome == "bibliotecario"
    assert len(tarefa.chats) == 3
    assert tarefa.contar_orquestradores() == 1


def test_rn_04_nome_duplicado_de_tarefa_e_permitido():
    frente = Frente(nome="frente")

    primeira = frente.criar_tarefa("mesma coisa", ORQUESTRADOR)
    segunda = frente.criar_tarefa("mesma coisa", ORQUESTRADOR)

    assert primeira.id != segunda.id
    assert len(frente.tarefas) == 2


def test_rn_14_buscar_tarefa_inexistente_devolve_none():
    frente = Frente(nome="frente")
    frente.criar_tarefa("tarefa", ORQUESTRADOR)

    assert frente.buscar_tarefa(Identidade.nova()) is None


def test_rn_14_buscar_tarefa_por_identidade_devolve_a_mesma():
    frente = Frente(nome="frente")
    tarefa = frente.criar_tarefa("tarefa", ORQUESTRADOR)

    assert frente.buscar_tarefa(tarefa.id) is tarefa


def test_rn_08_etapas_sao_anexadas_ao_fim_e_nao_tem_dependencia():
    tarefa = Tarefa(nome="tarefa")

    primeira = tarefa.criar_etapa("primeira", ExecutorEtapa.USUARIO)
    segunda = tarefa.criar_etapa("segunda", ExecutorEtapa.AGENTE)

    assert tarefa.etapas == [primeira, segunda]

    # Concluir a segunda com a primeira pendente e permitido (Q5b=A).
    segunda.concluir()
    assert segunda.concluida is True
    assert primeira.concluida is False
