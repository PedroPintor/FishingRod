"""Card 003, depois do retorno do Pedro - a janela do ambiente, aberta pelo
"⚙ ambiente" no pe da lateral."""

from textual.widgets import ContentSwitcher, Label, OptionList

from fishingrod.interface.ficha import FichaNaTela
from fishingrod.interface.janela_do_ambiente import AGENTES, INICIO, JanelaDoAmbiente
from fishingrod.interface.tela_do_ambiente import TelaDoAmbiente
from tests.interface.test_telas import criar_ambiente, criar_frente, criar_tarefa, entrar, esperar, rodar, selecionar_no


async def abrir_a_janela(app, pilot) -> JanelaDoAmbiente:
    await pilot.click("#configuracoes")
    await esperar(app, pilot)
    assert isinstance(app.screen, JanelaDoAmbiente)
    return app.screen


def test_o_botao_ambiente_abre_a_janela_com_o_nome_e_as_frentes(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        await selecionar_no(app, pilot, "#arvore", "Mídia")
        await criar_tarefa(app, pilot, "Leva de vídeos")
        await criar_frente(app, pilot, "Vendas")
        janela = await abrir_a_janela(app, pilot)
        secao = janela.query_one("#secoes", ContentSwitcher).current
        nome = str(janela.query_one("#nome-do-ambiente", Label).content)
        frentes = str(janela.query_one("#lista-de-frentes", Label).content)
        await pilot.press("escape")
        await esperar(app, pilot)
        return secao, nome, frentes, app.screen

    secao, nome, frentes, tela = rodar(tmp_path, roteiro)

    assert secao == INICIO
    assert nome == "Nexo"
    assert frentes == "Mídia (2 tarefas)\nVendas (0 tarefas)"
    assert isinstance(tela, TelaDoAmbiente)  # o Esc fecha a janela


def test_a_secao_agentes_lista_os_agentes_e_mostra_a_ficha_de_cada_um(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        janela = await abrir_a_janela(app, pilot)
        await pilot.click("#ir-secao-agentes")
        await esperar(app, pilot)
        secao = janela.query_one("#secoes", ContentSwitcher).current
        lista = janela.query_one("#agentes", OptionList)
        agentes = [str(lista.get_option_at_index(i).prompt) for i in range(lista.option_count)]
        primeira = janela.query_one(FichaNaTela).ficha.nome
        lista.highlighted = 1
        await esperar(app, pilot)
        segunda = janela.query_one(FichaNaTela).ficha
        await pilot.click("#fechar")
        await esperar(app, pilot)
        return secao, agentes, primeira, segunda, app.screen

    secao, agentes, primeira, segunda, tela = rodar(tmp_path, roteiro)

    assert secao == AGENTES
    assert agentes == ["orquestrador — abre cada sessão", "bibliotecario — pode ser chamado num chat"]
    assert primeira == "orquestrador"
    assert (segunda.nome, segunda.modelo) == ("bibliotecario", "sonnet")  # a ficha de verdade, como no painel
    assert isinstance(tela, TelaDoAmbiente)
