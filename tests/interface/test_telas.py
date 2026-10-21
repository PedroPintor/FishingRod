"""Card 001 - a primeira tela, dirigida pelo piloto de testes da Textual.

Cada teste segue um item de "Como testar" do card: abre o programa numa pasta
de dados temporaria, clica e digita como a pessoa faria, e olha o que ficou na
tela - e, quando importa, o que ficou no disco, abrindo o programa de novo.
"""

import asyncio

from textual.widgets import ContentSwitcher, Input, Label, ListView, Select, TabbedContent, Tabs, Tree

from fishingrod.interface.app import FishingRodApp
from fishingrod.interface.janelas import AVISO_SEM_NOME, JanelaDeAgente, JanelaDeApagar, JanelaDeNome
from fishingrod.interface.tela_de_inicio import ItemDeAmbiente, TelaDeInicio
from fishingrod.interface.tela_do_ambiente import PainelDaTarefa, TelaDoAmbiente

TAMANHO = (140, 45)


def rodar(pasta, roteiro):
    """Abre o programa sobre `pasta`, roda o roteiro e fecha."""

    async def principal():
        app = FishingRodApp(pasta)
        async with app.run_test(size=TAMANHO) as pilot:
            await pilot.pause()
            return await roteiro(app, pilot)

    return asyncio.run(principal())


async def digitar(pilot, texto: str) -> None:
    await pilot.press(*("space" if letra == " " else letra for letra in texto))


async def esperar(app, pilot) -> None:
    await app.workers.wait_for_complete()
    await pilot.pause()


async def criar_ambiente(app, pilot, nome: str) -> None:
    await pilot.click("#novo")
    await digitar(pilot, nome)
    await pilot.press("enter")
    await esperar(app, pilot)


def nomes_na_lista(app) -> list[str]:
    lista = app.screen.query_one("#ambientes", ListView)
    return [item.resumo.nome for item in lista.query(ItemDeAmbiente)]


async def entrar(app, pilot, nome: str) -> None:
    lista = app.screen.query_one("#ambientes", ListView)
    lista.index = nomes_na_lista(app).index(nome)
    await pilot.click("#entrar")
    await esperar(app, pilot)
    assert isinstance(app.screen, TelaDoAmbiente)


async def criar_frente(app, pilot, nome: str) -> None:
    await pilot.click("#nova-frente")
    await digitar(pilot, nome)
    await pilot.press("enter")
    await esperar(app, pilot)


async def criar_tarefa(app, pilot, nome: str) -> None:
    """Na frente que esta com o cursor na arvore."""
    await pilot.click("#nova-tarefa")
    await digitar(pilot, nome)
    await pilot.press("enter")
    await esperar(app, pilot)


def arvore(app) -> list[tuple[str, list[str]]]:
    raiz = app.screen.query_one("#arvore", Tree).root
    return [(str(f.label), [str(t.label) for t in f.children]) for f in raiz.children]


def painel_aberto(app) -> PainelDaTarefa:
    abertas = app.screen.query_one("#abertas", TabbedContent)
    return abertas.get_pane(abertas.active).query_one(PainelDaTarefa)


def abas_de_chat(painel: PainelDaTarefa) -> list[str]:
    return [str(tab.label) for tab in painel.query_one("#abas-de-chat", Tabs).query("Tab")]


def chat_ativo(painel: PainelDaTarefa) -> str:
    return str(painel.query_one("#abas-de-chat", Tabs).active_tab.label)


async def selecionar_no(app, pilot, id_arvore: str, rotulo: str) -> None:
    tree = app.screen.query_one(id_arvore, Tree)
    no = next(n for n in _todos(tree.root) if str(n.label) == rotulo)
    tree.move_cursor(no)
    tree.action_select_cursor()
    await esperar(app, pilot)


def _todos(no):
    for filho in no.children:
        yield filho
        yield from _todos(filho)


# --------------------------------------------------------------------------
# Tela de inicio
# --------------------------------------------------------------------------


def test_abro_o_programa_e_vejo_a_lista_vazia(tmp_path):
    async def roteiro(app, pilot):
        assert isinstance(app.screen, TelaDeInicio)
        return app.screen.query_one("#vazio", Label).display, nomes_na_lista(app)

    vazio_aparece, nomes = rodar(tmp_path, roteiro)

    assert vazio_aparece
    assert nomes == []


def test_crio_um_ambiente_e_ele_aparece_na_lista(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo Aquisição")
        return nomes_na_lista(app)

    assert rodar(tmp_path, roteiro) == ["Nexo Aquisição"]


def test_nome_vazio_mostra_o_aviso_e_nao_cria_nada(tmp_path):
    async def roteiro(app, pilot):
        await pilot.click("#novo")
        await digitar(pilot, "   ")
        await pilot.click("#criar")
        await pilot.pause()
        janela = app.screen
        aviso = str(janela.query_one("#aviso", Label).render())
        await pilot.press("escape")
        await pilot.pause()
        return isinstance(janela, JanelaDeNome), aviso, isinstance(app.screen, TelaDeInicio), nomes_na_lista(app)

    era_a_janela, aviso, voltou, nomes = rodar(tmp_path, roteiro)

    assert era_a_janela
    assert aviso == AVISO_SEM_NOME
    assert voltou and nomes == []


# --------------------------------------------------------------------------
# Tela do ambiente
# --------------------------------------------------------------------------


def test_entro_no_ambiente_crio_frente_e_tarefa_e_vejo_na_arvore(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        sem_frentes = app.screen.query_one("#sem-frentes", Label).display
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        painel = painel_aberto(app)
        sessao = painel.query_one("#sessao", Select)
        return sem_frentes, arvore(app), painel.tarefa.nome, sessao.value, abas_de_chat(painel)

    sem_frentes, nos, aberta, sessao, chats = rodar(tmp_path, roteiro)

    assert sem_frentes  # antes da primeira frente, a tela diz por onde comecar
    assert nos == [("Mídia", ["Campanha LP"])]
    assert aberta == "Campanha LP"  # a tarefa nova ja abre numa aba
    assert sessao is not Select.NULL
    assert chats == ["orquestrador"]


def test_crio_uma_sessao_nova_e_volto_para_a_primeira(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        painel = painel_aberto(app)
        await pilot.click("#nova-sessao")
        await esperar(app, pilot)
        painel = painel_aberto(app)
        tarefa = painel.tarefa
        na_segunda = painel.id_sessao == tarefa.sessoes[1].id
        chats_da_segunda = abas_de_chat(painel)
        painel.query_one("#sessao", Select).value = tarefa.sessoes[0].id.valor
        await esperar(app, pilot)
        return [s.nome for s in tarefa.sessoes], na_segunda, chats_da_segunda, painel.id_sessao == tarefa.sessoes[0].id

    nomes, na_segunda, chats, de_volta = rodar(tmp_path, roteiro)

    assert nomes == ["sessão 1", "sessão 2"]
    assert na_segunda and chats == ["orquestrador"]
    assert de_volta


def test_abro_um_chat_novo_com_um_agente_da_lista(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        await pilot.click("#novo-chat")
        await pilot.pause()
        janela = app.screen
        opcoes = [str(b.label) for b in janela.query(".agente")]
        await pilot.click("#agente-0")
        await esperar(app, pilot)
        painel = painel_aberto(app)
        conversa = painel.query_one("#conversas", ContentSwitcher).current
        id_do_novo = painel.tarefa.sessoes[0].chats[1].id.valor
        return isinstance(janela, JanelaDeAgente), opcoes, abas_de_chat(painel), chat_ativo(painel), conversa, id_do_novo

    async def reabrir(app, pilot):
        await entrar(app, pilot, "Nexo")
        await selecionar_no(app, pilot, "#arvore", "Campanha LP")
        return abas_de_chat(painel_aberto(app))

    era_a_janela, opcoes, abas, ativo, conversa, id_do_novo = rodar(tmp_path, roteiro)

    assert era_a_janela
    assert opcoes == ["bibliotecario"]  # o orquestrador nao: cada sessao so tem um
    assert abas == ["orquestrador", "bibliotecario"]
    assert ativo == "bibliotecario"  # o chat novo ja abre
    assert conversa == f"conversa-{id_do_novo}"
    assert rodar(tmp_path, reabrir) == ["orquestrador", "bibliotecario"]


def test_cancelar_a_escolha_do_agente_nao_abre_chat(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        await pilot.click("#novo-chat")
        await pilot.pause()
        await pilot.press("escape")
        await esperar(app, pilot)
        return abas_de_chat(painel_aberto(app))

    assert rodar(tmp_path, roteiro) == ["orquestrador"]


def test_abro_duas_tarefas_e_passo_de_uma_para_a_outra(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        await selecionar_no(app, pilot, "#arvore", "Mídia")
        await criar_tarefa(app, pilot, "Leva de vídeos")
        abertas = app.screen.query_one("#abertas", TabbedContent)
        await selecionar_no(app, pilot, "#arvore", "Campanha LP")
        return abertas.tab_count, painel_aberto(app).tarefa.nome

    abas, ativa = rodar(tmp_path, roteiro)

    assert abas == 2  # abrir de novo nao duplica a aba
    assert ativa == "Campanha LP"


def test_volto_para_a_lista_e_entro_em_outro_ambiente(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await criar_ambiente(app, pilot, "Faculdade")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await pilot.click("#voltar")
        await esperar(app, pilot)
        voltou = isinstance(app.screen, TelaDeInicio)
        await entrar(app, pilot, "Faculdade")
        return voltou, app.screen.ambiente.nome, arvore(app)

    voltou, nome, nos = rodar(tmp_path, roteiro)

    assert voltou
    assert nome == "Faculdade"
    assert nos == []  # dois ambientes nao se misturam


# --------------------------------------------------------------------------
# Fechar e abrir de novo
# --------------------------------------------------------------------------


def test_fecho_abro_de_novo_e_esta_tudo_la(tmp_path):
    async def trabalhar(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await entrar(app, pilot, "Nexo")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        await pilot.click("#nova-sessao")
        await esperar(app, pilot)

    async def reabrir(app, pilot):
        nomes = nomes_na_lista(app)
        await entrar(app, pilot, "Nexo")
        await selecionar_no(app, pilot, "#arvore", "Campanha LP")
        painel = painel_aberto(app)
        return nomes, arvore(app), [s.nome for s in painel.tarefa.sessoes]

    rodar(tmp_path, trabalhar)
    nomes, nos, sessoes = rodar(tmp_path, reabrir)

    assert nomes == ["Nexo"]
    assert nos == [("Mídia", ["Campanha LP"])]
    assert sessoes == ["sessão 1", "sessão 2"]


# --------------------------------------------------------------------------
# Apagar
# --------------------------------------------------------------------------


def test_apagar_avisa_em_maiusculas_e_cancelar_nao_muda_nada(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await pilot.click("#apagar")
        await pilot.pause()
        janela = app.screen
        aviso = str(janela.query_one("#aviso", Label).render())
        await pilot.click("#cancelar")
        await esperar(app, pilot)
        return isinstance(janela, JanelaDeApagar), aviso, nomes_na_lista(app)

    era_a_janela, aviso, nomes = rodar(tmp_path, roteiro)

    assert era_a_janela
    assert aviso.startswith("ATENÇÃO: APAGAR O AMBIENTE")
    assert "Nexo" in aviso and "ISSO NÃO TEM VOLTA" in aviso
    assert nomes == ["Nexo"]


def test_apagar_confirmado_tira_o_ambiente_da_lista_e_do_disco(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo")
        await criar_ambiente(app, pilot, "Faculdade")
        app.screen.query_one("#ambientes", ListView).index = nomes_na_lista(app).index("Nexo")
        await pilot.click("#apagar")
        await pilot.pause()
        await pilot.click("#apagar")  # o da janela
        await esperar(app, pilot)
        return nomes_na_lista(app)

    async def reabrir(app, pilot):
        return nomes_na_lista(app)

    assert rodar(tmp_path, roteiro) == ["Faculdade"]
    assert rodar(tmp_path, reabrir) == ["Faculdade"]
    assert len(list((tmp_path / "wikis").iterdir())) == 1  # so a wiki da Faculdade ficou


def test_o_nome_digitado_chega_inteiro(tmp_path):
    """O que a janela devolve e o que foi digitado, sem cortar espaco de dentro."""

    async def roteiro(app, pilot):
        await pilot.click("#novo")
        app.screen.query_one("#nome", Input).value = "Meus estudos  do semestre"
        await pilot.click("#criar")
        await esperar(app, pilot)
        return nomes_na_lista(app)

    assert rodar(tmp_path, roteiro) == ["Meus estudos  do semestre"]
