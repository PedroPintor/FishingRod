"""Card 002 - conversar com o agente na tela, dirigido pelo piloto da Textual.

O programa abre numa pasta temporaria, com o adaptador de sessao de verdade e
um Claude roteirizado no lugar do CLI. Cada teste segue um item de "Como
testar" do card.
"""

import asyncio

from claude_agent_sdk import TextBlock
from textual.widgets import Button, ContentSwitcher, Input, Label

from fishingrod.aplicacao.servicos.servico_de_conversa import EstadoDoChat
from fishingrod.interface.app import FishingRodApp
from fishingrod.interface.chat import ChatAberto
from fishingrod.interface.tela_de_inicio import TelaDeInicio
from fishingrod.interface.tela_do_ambiente import TelaDoAmbiente
from tests.conversa.instrumentos import ate, com_roteiro
from tests.interface.test_telas import (
    TAMANHO,
    criar_ambiente,
    criar_frente,
    criar_tarefa,
    digitar,
    entrar,
    esperar,
    painel_aberto,
    selecionar_no,
)
from tests.sessao.cliente_roteirizado import (
    FabricaRoteirizada,
    Mensagem,
    Parar,
    RoteiroDoTurno,
    assistente,
    inicio_de_mensagem,
    inicio_de_texto,
    resultado,
    trecho,
    turno_de_texto,
)


def rodar(pasta, fabrica, roteiro):
    async def principal():
        app = FishingRodApp(pasta, com_roteiro(fabrica))
        async with app.run_test(size=TAMANHO) as pilot:
            await pilot.pause()
            return await roteiro(app, pilot)

    return asyncio.run(principal())


async def abrir_um_chat(app, pilot) -> ChatAberto:
    """Ambiente, frente e tarefa novos: a tarefa abre com o chat do
    orquestrador."""
    await criar_ambiente(app, pilot, "loja")
    await entrar(app, pilot, "loja")
    await criar_frente(app, pilot, "vendas")
    await criar_tarefa(app, pilot, "site")
    return chat_visivel(app)


def chat_visivel(app) -> ChatAberto:
    conversas = painel_aberto(app).query_one("#conversas", ContentSwitcher)
    return conversas.query_one(f"#{conversas.current}", ChatAberto)


async def mandar(pilot, chat: ChatAberto, texto: str) -> None:
    chat.query_one("#campo", Input).focus()
    await digitar(pilot, texto)
    await pilot.press("enter")
    await pilot.pause()


async def ate_responder(pilot, chat: ChatAberto) -> None:
    await ate(lambda: chat.conversa.estado(chat.id_chat) is not EstadoDoChat.RESPONDENDO)
    await pilot.pause()


def mostrador(app) -> str:
    return str(app.screen.query_one("#conexoes", Label).content)


def faixa(chat: ChatAberto) -> str:
    return str(chat.query_one("#estado", Label).content)


def _em_pedacos(liberar: asyncio.Event, chegou: asyncio.Event) -> RoteiroDoTurno:
    return RoteiroDoTurno(
        [
            Mensagem(inicio_de_mensagem()),
            Mensagem(inicio_de_texto(0)),
            Mensagem(trecho(0, "Olá, ")),
            Parar(liberar, chegou),
            Mensagem(trecho(0, "tudo bem?")),
            Mensagem(assistente(TextBlock("Olá, tudo bem?"))),
            resultado(),
        ]
    )


def test_mando_oi_e_a_resposta_aparece_em_pedacos_com_o_mostrador_em_1(tmp_path):
    liberar, chegou = asyncio.Event(), asyncio.Event()
    fabrica = FabricaRoteirizada(turnos=[_em_pedacos(liberar, chegou)])

    async def roteiro(app, pilot):
        chat = await abrir_um_chat(app, pilot)
        antes = (mostrador(app), faixa(chat))
        await mandar(pilot, chat, "oi")
        await chegou.wait()
        await ate(lambda: "Olá," in chat.texto_da_conversa())
        app.screen.atualizar()
        no_meio = (chat.texto_da_conversa(), mostrador(app), faixa(chat))
        liberar.set()
        await ate_responder(pilot, chat)
        return antes, no_meio, chat.texto_da_conversa(), faixa(chat)

    antes, (meio, mostrador_no_meio, faixa_no_meio), fim, faixa_no_fim = rodar(tmp_path, fabrica, roteiro)

    assert antes == ("Claude: 0 conexões abertas", "○ pronto para conversar")
    assert "você: oi" in meio and "Olá," in meio and "tudo bem?" not in meio
    assert mostrador_no_meio == "Claude: 1 conexão aberta"
    assert faixa_no_meio == "● ligado · respondendo…"
    assert "orquestrador: Olá, tudo bem?" in fim
    assert faixa_no_fim == "● ligado"


def test_esc_interrompe_a_resposta_e_devolve_a_fila_ao_campo(tmp_path):
    chegou = asyncio.Event()
    fabrica = FabricaRoteirizada(
        turnos=[RoteiroDoTurno([Mensagem(assistente(TextBlock("começando"))), Parar(chegou=chegou), resultado()])]
    )

    async def roteiro(app, pilot):
        chat = await abrir_um_chat(app, pilot)
        await mandar(pilot, chat, "um")
        await chegou.wait()
        await ate(lambda: "começando" in chat.texto_da_conversa())
        await mandar(pilot, chat, "dois")
        na_fila = faixa(chat)
        await pilot.press("escape")
        await ate_responder(pilot, chat)
        return na_fila, chat.texto_da_conversa(), chat.query_one("#campo", Input).value, app.screen

    na_fila, texto, campo, tela = rodar(tmp_path, fabrica, roteiro)

    assert na_fila == "● ligado · respondendo… · 1 na fila"
    assert "orquestrador: começando (interrompida)" in texto
    assert "você: dois" not in texto
    assert campo == "dois"
    assert isinstance(tela, TelaDoAmbiente)  # o Esc interrompeu, e nao saiu do ambiente


def test_desligar_volta_a_pronto_e_a_mensagem_seguinte_liga_de_novo(tmp_path):
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("primeira"), turno_de_texto("segunda")])

    async def roteiro(app, pilot):
        chat = await abrir_um_chat(app, pilot)
        await mandar(pilot, chat, "um")
        await ate_responder(pilot, chat)
        ligado = (faixa(chat), chat.query_one("#desligar", Button).display)
        await pilot.click(chat.query_one("#desligar", Button))
        await pilot.pause()
        app.screen.atualizar()
        desligado = (faixa(chat), chat.query_one("#desligar", Button).display, mostrador(app), fabrica.vivos)
        await mandar(pilot, chat, "dois")
        await ate_responder(pilot, chat)
        app.screen.atualizar()
        return ligado, desligado, (faixa(chat), mostrador(app)), chat.texto_da_conversa()

    ligado, desligado, religado, texto = rodar(tmp_path, fabrica, roteiro)

    assert ligado == ("● ligado", True)
    assert desligado == ("○ pronto para conversar", False, "Claude: 0 conexões abertas", 0)
    assert religado == ("● ligado", "Claude: 1 conexão aberta")
    assert "orquestrador: segunda" in texto
    assert len(fabrica.clientes) == 2


def test_saio_do_ambiente_com_chats_ligados_e_o_mostrador_vai_a_zero(tmp_path):
    fabrica = FabricaRoteirizada()

    async def roteiro(app, pilot):
        chat = await abrir_um_chat(app, pilot)
        await mandar(pilot, chat, "oi")
        await ate_responder(pilot, chat)
        antes = app.programa.conversa.conexoes_abertas()
        await pilot.click("#voltar")
        await esperar(app, pilot)
        return antes, app.programa.conversa.conexoes_abertas(), fabrica.vivos, app.screen

    antes, depois, vivos, tela = rodar(tmp_path, fabrica, roteiro)

    assert antes == 1
    assert (depois, vivos) == (0, 0)
    assert isinstance(tela, TelaDeInicio)


def test_fecho_o_programa_abro_de_novo_e_as_mensagens_estao_la(tmp_path):
    fabrica = FabricaRoteirizada(turnos=[turno_de_texto("até amanhã")])

    async def primeira_vez(app, pilot):
        chat = await abrir_um_chat(app, pilot)
        await mandar(pilot, chat, "boa noite")
        await ate_responder(pilot, chat)

    async def segunda_vez(app, pilot):
        await entrar(app, pilot, "loja")
        await selecionar_no(app, pilot, "#arvore", "site")
        await ate(lambda: bool(app.screen.query(ChatAberto)))  # a aba da tarefa termina de montar
        chat = chat_visivel(app)
        await ate(lambda: "boa noite" in chat.texto_da_conversa())
        return chat.texto_da_conversa(), faixa(chat)

    rodar(tmp_path, fabrica, primeira_vez)
    texto, estado = rodar(tmp_path, fabrica, segunda_vez)

    assert "você: boa noite" in texto and "orquestrador: até amanhã" in texto
    assert estado == "○ pronto para conversar"
    assert fabrica.vivos == 0
