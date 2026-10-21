"""Card 002 - os itens de "Como testar" que precisam do Claude de verdade.

Fora da suite padrao: gastam a assinatura (`uv run pytest -m sdk_real`). O
programa e montado como na tela, com o adaptador real; so o agente que
conversa e trocado pelo apelido `haiku`, o mais barato - o que se confere e a
conversa, nao a qualidade da resposta.
"""

import asyncio

import pytest

from fishingrod.aplicacao.servicos.servico_de_conversa import AGENTE, AVISO, USUARIO
from fishingrod.dominio import Agente, Papel
from fishingrod.interface.montagem import montar
from tests.conversa.instrumentos import ate_responder, preparar, textos
from tests.sessao.test_sdk_real import descendentes, esperar

pytestmark = pytest.mark.sdk_real

BARATO = Agente("bibliotecario", Papel.SUB_AGENTE, "haiku", regras=("Responda em portugues, numa frase curta.",))
PRAZO = 180


def rodar(coro):
    async def com_prazo():
        async with asyncio.timeout(PRAZO + 60):
            return await coro

    return asyncio.run(com_prazo())


def test_sdk_real_mando_oi_e_a_resposta_chega_com_uma_conexao(tmp_path):
    async def cenario():
        programa = await montar(tmp_path)
        try:
            _, chat, _ = await preparar(programa, agente=BARATO)
            programa.conversa.enviar(chat.id, "Responda apenas: oi.")
            await ate_responder(programa.conversa, chat, prazo=PRAZO)
            return textos(programa.conversa, chat), programa.conversa.conexoes_abertas(), len(descendentes())
        finally:
            await programa.fechar()

    linhas, abertas, processos = rodar(cenario())

    assert linhas[0] == (USUARIO, "Responda apenas: oi.")
    assert linhas[1][0] == AGENTE and linhas[1][1].strip()
    assert (abertas, processos) == (1, 1)


def test_sdk_real_fecho_o_programa_e_nenhum_processo_fica(tmp_path):
    async def cenario():
        programa = await montar(tmp_path)
        _, um, outro = await preparar(programa, agente=BARATO)
        programa.conversa.enviar(um.id, "Responda apenas: um.")
        programa.conversa.enviar(outro.id, "Responda apenas: dois.")
        await ate_responder(programa.conversa, um, outro, prazo=PRAZO)
        antes = len(descendentes())
        await programa.fechar()
        await esperar(lambda: not descendentes(), prazo=10)
        return antes, descendentes()

    antes, depois = rodar(cenario())

    assert antes == 2
    assert depois == []


def test_sdk_real_o_agente_lembra_do_numero_depois_de_reabrir(tmp_path):
    async def cenario():
        programa = await montar(tmp_path)
        _, chat, _ = await preparar(programa, agente=BARATO)
        programa.conversa.enviar(chat.id, "Meu numero da sorte e 42. Responda apenas: anotado.")
        await ate_responder(programa.conversa, chat, prazo=PRAZO)
        await programa.fechar()

        de_novo = await montar(tmp_path)
        try:
            await de_novo.conversa.abrir(chat.contexto, BARATO)
            de_novo.conversa.enviar(chat.id, "Qual e o meu numero da sorte? Responda so o numero.")
            await ate_responder(de_novo.conversa, chat, prazo=PRAZO)
            return textos(de_novo.conversa, chat)
        finally:
            await de_novo.fechar()

    linhas = rodar(cenario())

    assert AVISO not in [papel for papel, _ in linhas]
    assert linhas[-1][0] == AGENTE and "42" in linhas[-1][1]
