"""U1 - Tarefa, Sessao e Frente (RN-04, RN-05, RN-06, RN-08, RN-14, D21)."""

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


def test_rn_05_tarefa_nasce_com_uma_sessao_e_nela_um_chat_de_orquestrador():
    frente = Frente(nome="campanha de verao")

    tarefa = frente.criar_tarefa("mapear publico", ORQUESTRADOR)

    assert len(tarefa.sessoes) == 1
    sessao = tarefa.sessoes[0]
    assert len(sessao.chats) == 1
    assert sessao.chats[0].agente is ORQUESTRADOR
    assert sessao.contar_orquestradores() == 1


def test_d21_sessao_nova_tambem_nasce_com_o_orquestrador():
    tarefa = Frente(nome="frente").criar_tarefa("tarefa", ORQUESTRADOR)

    segunda = tarefa.criar_sessao(ORQUESTRADOR)

    assert len(tarefa.sessoes) == 2
    assert [c.agente for c in segunda.chats] == [ORQUESTRADOR]
    assert tarefa.buscar_sessao(segunda.id) is segunda


def test_d21_sessao_sem_nome_leva_o_numero_dela():
    tarefa = Frente(nome="frente").criar_tarefa("tarefa", ORQUESTRADOR)

    tarefa.criar_sessao(ORQUESTRADOR)
    nomeada = tarefa.criar_sessao(ORQUESTRADOR, "revisao")

    assert [s.nome for s in tarefa.sessoes] == ["sessão 1", "sessão 2", "revisao"]
    assert nomeada.nome == "revisao"


def test_d21_sessao_com_sub_agente_levanta_e_nao_entra_na_tarefa():
    tarefa = Frente(nome="frente").criar_tarefa("tarefa", ORQUESTRADOR)

    with pytest.raises(AgenteInvalido):
        tarefa.criar_sessao(BIBLIOTECARIO)

    assert len(tarefa.sessoes) == 1


def test_d21_memorias_de_sessoes_diferentes_nao_se_misturam():
    tarefa = Frente(nome="frente").criar_tarefa("tarefa", ORQUESTRADOR)
    primeira = tarefa.sessoes[0]
    segunda = tarefa.criar_sessao(ORQUESTRADOR)

    primeira.memoria.anotar("plano", "so da primeira", "usuario")

    assert segunda.memoria.total_de_anotacoes() == 0


def test_rn_05_criar_tarefa_com_sub_agente_levanta():
    """O agente vem por parametro (Q4=A); passar um sub-agente e erro de
    dominio, nao um chat de sub-agente na posicao do orquestrador."""
    frente = Frente(nome="frente")

    with pytest.raises(AgenteInvalido):
        frente.criar_tarefa("tarefa", BIBLIOTECARIO)

    assert frente.tarefas == []


def test_rn_06_segundo_orquestrador_levanta():
    frente = Frente(nome="frente")
    sessao = frente.criar_tarefa("tarefa", ORQUESTRADOR).sessoes[0]

    with pytest.raises(OrquestradorDuplicado):
        sessao.criar_chat(ORQUESTRADOR)


def test_rn_06_sub_agente_sempre_pode_ganhar_chat():
    """E assim que o chat do bibliotecario nasce quando o orquestrador delega
    (Q14=X)."""
    frente = Frente(nome="frente")
    sessao = frente.criar_tarefa("tarefa", ORQUESTRADOR).sessoes[0]

    chat = sessao.criar_chat(BIBLIOTECARIO)
    sessao.criar_chat(BIBLIOTECARIO)

    assert chat.nome == "bibliotecario"
    assert len(sessao.chats) == 3
    assert sessao.contar_orquestradores() == 1


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
