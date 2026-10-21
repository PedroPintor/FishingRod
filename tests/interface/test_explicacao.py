"""Card 003 - a interface em areas e a ficha do agente.

Cada teste segue um item de "Como testar" do card, dirigido pelo piloto da
Textual como em `test_telas.py`. Os da conversa usam o Claude roteirizado do
card 002, para nao gastar a assinatura.
"""

import asyncio

from claude_agent_sdk import TextBlock
from textual.css.query import NoMatches
from textual.widgets import Input, Label, Markdown, Static, TabbedContent, Tabs, Tree

from fishingrod.adaptadores.sessao.opcoes import montar_opcoes
from fishingrod.aplicacao.portas.wiki import PaginaProposta, PropostaWiki
from fishingrod.aplicacao.servicos.servico_de_conversa import EstadoDoChat
from fishingrod.dominio import Agente, Papel
from fishingrod.interface.app import FishingRodApp
from fishingrod.interface.explicacao import FICHA, LISTA_DA_WIKI, MEMORIA, PAGINA_DA_WIKI, WIKI, PainelDeExplicacao
from fishingrod.interface.ficha import ESFORCO_PADRAO, FichaNaTela, NENHUMA, SEM_INSTRUCOES, OpcoesDoClaude, montar_ficha
from fishingrod.interface.frases import MEMORIA_VAZIA
from fishingrod.interface.montagem import BIBLIOTECARIO, ORQUESTRADOR, montar, opcoes_do_claude
from fishingrod.interface.tela_do_ambiente import PainelDaTarefa
from tests.conversa.instrumentos import ate, com_roteiro
from tests.interface.test_chat import chat_visivel, faixa, mandar
from tests.interface.test_telas import (
    TAMANHO,
    abas_de_chat,
    chat_ativo,
    criar_ambiente,
    criar_frente,
    criar_tarefa,
    entrar,
    esperar,
    painel_aberto,
    rodar,
    selecionar_no,
)
from tests.sessao.cliente_roteirizado import FabricaRoteirizada, Mensagem, Parar, RoteiroDoTurno, assistente, resultado

SEIS_ACOES = ("criar_frente", "criar_tarefa", "criar_chat", "criar_etapa", "concluir_etapa", "anotar_memoria")


async def abrir_tarefa(app, pilot) -> PainelDaTarefa:
    await criar_ambiente(app, pilot, "Nexo")
    await entrar(app, pilot, "Nexo")
    await criar_frente(app, pilot, "Mídia")
    await criar_tarefa(app, pilot, "Campanha LP")
    return painel_aberto(app)


def explicacao(painel: PainelDaTarefa) -> PainelDeExplicacao:
    return painel.query_one("#explicacao", PainelDeExplicacao)


async def explicar(app, pilot, painel: PainelDaTarefa) -> None:
    await pilot.click(painel.query_one("#explicar"))
    await esperar(app, pilot)
    # O botao ignora um segundo clique enquanto ainda aparece apertado.
    await pilot.pause(0.25)


async def ir_para_a_aba(app, pilot, painel: PainelDaTarefa, aba: str) -> None:
    await pilot.click(explicacao(painel).query_one(f"#--content-tab-{aba}"))
    await esperar(app, pilot)


def aba_da_explicacao(painel: PainelDaTarefa) -> str:
    return explicacao(painel).query_one(TabbedContent).active


def ficha_na_tela(painel: PainelDaTarefa) -> dict[str, str]:
    """O que a aba "ficha" mostra, campo por campo."""
    painel_de_explicacao = explicacao(painel)

    def texto(seletor, tipo=Label) -> str:
        return str(painel_de_explicacao.query_one(seletor, tipo).content)

    campos = ("nome", "papel", "modelo", "esforco", "ferramentas", "ferramentas-da-maquina")
    na_tela = {campo: texto(f"#ficha-{campo}") for campo in campos}
    na_tela["instrucoes"] = texto("#ficha-instrucoes", Static)
    na_tela["do software"] = painel_de_explicacao.query_one("#ficha-marca", Label).display
    return na_tela


def nome_na_ficha(app) -> str | None:
    """O nome na ficha do painel da tarefa aberta, ou None enquanto ele monta."""
    try:
        return explicacao(painel_aberto(app)).query_one(FichaNaTela).ficha.nome
    except (NoMatches, AttributeError, ValueError):
        return None


def memoria_na_tela(painel: PainelDaTarefa) -> str:
    return explicacao(painel).query_one("#memoria", Markdown).source


# --------------------------------------------------------------------------
# Nova lateral e area de trabalho
# --------------------------------------------------------------------------


def test_a_lateral_mostra_so_frentes_e_tarefas(tmp_path):
    async def roteiro(app, pilot):
        await abrir_tarefa(app, pilot)
        lateral = app.screen.query_one("#lateral")
        arvores = [arvore.id for arvore in lateral.query(Tree)]
        titulos = [str(titulo.content) for titulo in lateral.query(".titulo-lateral")]
        return arvores, titulos, bool(app.screen.query("#agentes"))

    arvores, titulos, tem_agentes = rodar(tmp_path, roteiro)

    assert arvores == ["arvore"]  # a wiki saiu da lateral
    assert titulos == ["FRENTES E TAREFAS"]
    assert not tem_agentes


# --------------------------------------------------------------------------
# Painel de explicacao
# --------------------------------------------------------------------------


def test_o_botao_explicar_mostra_e_esconde_o_painel(tmp_path):
    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        antes = explicacao(painel).display
        await explicar(app, pilot, painel)
        aberto = (explicacao(painel).display, aba_da_explicacao(painel), painel.query_one("#explicar").has_class("-ligado"))
        await explicar(app, pilot, painel)
        return antes, aberto, explicacao(painel).display, bool(painel.query("#mostrar-memoria"))

    antes, aberto, depois, botao_antigo = rodar(tmp_path, roteiro)

    assert antes is False
    assert aberto == (True, FICHA, True)  # abre na aba "ficha"
    assert depois is False
    assert not botao_antigo  # o "explicar" tomou o lugar do botao "memória"


def test_a_aba_memoria_mostra_as_anotacoes_da_sessao_escolhida(tmp_path):
    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        primeira = painel.tarefa.sessoes[0]
        await explicar(app, pilot, painel)
        await ir_para_a_aba(app, pilot, painel, MEMORIA)
        vazia = memoria_na_tela(painel)
        # Ninguem anota pela tela: quem anota e o agente, no chat - e o painel
        # aberto mostra a anotacao nova sem precisar fechar e abrir.
        await app.programa.servico.anotar_memoria(
            app.screen.ambiente.id, primeira.id, "icp", "dentistas", "orquestrador"
        )
        await app.screen.atualizar_explicacoes()
        await esperar(app, pilot)
        da_primeira = memoria_na_tela(painel)
        titulo = str(explicacao(painel).query_one("#titulo-da-memoria", Label).content)
        await pilot.click("#nova-sessao")
        await esperar(app, pilot)
        painel = painel_aberto(app)
        return vazia, da_primeira, titulo, aba_da_explicacao(painel), memoria_na_tela(painel)

    vazia, da_primeira, titulo, aba, da_segunda = rodar(tmp_path, roteiro)

    assert vazia == MEMORIA_VAZIA
    assert "### icp" in da_primeira and "dentistas" in da_primeira and "orquestrador" in da_primeira
    assert titulo == "MEMÓRIA DA SESSÃO 1"
    assert aba == MEMORIA  # trocar de sessao mantem o painel como estava
    assert da_segunda == MEMORIA_VAZIA  # sessao nova, memoria limpa (D21)


def test_o_painel_e_de_cada_tarefa(tmp_path):
    async def roteiro(app, pilot):
        await abrir_tarefa(app, pilot)
        await selecionar_no(app, pilot, "#arvore", "Mídia")
        await criar_tarefa(app, pilot, "Leva de vídeos")
        segunda = painel_aberto(app)
        await explicar(app, pilot, segunda)
        await ir_para_a_aba(app, pilot, segunda, WIKI)
        await selecionar_no(app, pilot, "#arvore", "Campanha LP")
        primeira = painel_aberto(app)
        return primeira.tarefa.nome, explicacao(primeira).display, aba_da_explicacao(primeira), explicacao(segunda).display

    nome, aberto_na_primeira, aba_na_primeira, aberto_na_segunda = rodar(tmp_path, roteiro)

    assert nome == "Campanha LP"
    assert aberto_na_primeira is False and aba_na_primeira == FICHA  # a outra continua como estava
    assert aberto_na_segunda is True


# --------------------------------------------------------------------------
# Wiki no painel
# --------------------------------------------------------------------------


def test_abrir_uma_pagina_da_wiki_nao_cria_aba_de_tarefa(tmp_path):
    async def roteiro(app, pilot):
        await criar_ambiente(app, pilot, "Nexo Aquisição")
        await entrar(app, pilot, "Nexo Aquisição")
        pagina = PaginaProposta(entidade="Clientes", titulo="Dr. Marcelo", descricao="dentista", conteudo="Atende em Pinheiros.")
        localizador = app.screen.ambiente.raiz_wiki.localizador
        await app.programa.wiki.escrever_proposta(localizador, PropostaWiki(("Clientes",), (pagina,)))
        await app.programa.wiki.renderizar_index(localizador, "Nexo Aquisição")
        await criar_frente(app, pilot, "Mídia")
        await criar_tarefa(app, pilot, "Campanha LP")
        painel = painel_aberto(app)
        await explicar(app, pilot, painel)
        await ir_para_a_aba(app, pilot, painel, WIKI)
        texto = explicacao(painel).query_one("#texto-da-pagina", Markdown)
        explicacao(painel).query_one("#wiki", Tree).root.expand_all()
        await pilot.pause()
        await selecionar_no(app, pilot, "#wiki", "index")
        do_index = texto.source
        await selecionar_no(app, pilot, "#wiki", "dr-marcelo")
        abertas = app.screen.query_one("#abertas", TabbedContent)
        return do_index, texto.source, abertas.tab_count, abertas.active

    do_index, da_pagina, abas, ativa = rodar(tmp_path, roteiro)

    assert "Nexo Aquisição" in do_index and "dr-marcelo" in do_index
    assert "# Dr. Marcelo" in da_pagina and "Atende em Pinheiros." in da_pagina
    assert abas == 1  # so a tarefa: a pagina abriu no painel
    assert ativa.startswith("tarefa-")


# --------------------------------------------------------------------------
# Ficha do agente
# --------------------------------------------------------------------------


def test_cada_campo_da_ficha_sai_do_agente_do_catalogo_e_das_opcoes(tmp_path):
    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        await explicar(app, pilot, painel)
        return ficha_na_tela(painel)

    ficha = rodar(tmp_path, roteiro)

    assert ficha == {
        "nome": "orquestrador",
        "do software": True,
        "papel": "abre cada sessão",
        "modelo": ORQUESTRADOR.modelo,
        "esforco": ESFORCO_PADRAO,
        "ferramentas": " · ".join(SEIS_ACOES),  # sem criar_sessao: e so do usuario
        "ferramentas-da-maquina": NENHUMA,  # D16
        "instrucoes": SEM_INSTRUCOES,
    }
    assert ORQUESTRADOR.modelo == "opus"


def test_a_ficha_le_as_mesmas_opcoes_que_vao_para_o_claude():
    """A ficha nao tem texto escrito a mao: o que ela mostra das opcoes e o que
    `montar_opcoes`, a funcao que liga o chat, entrega ao Claude."""
    agente = Agente("revisor", Papel.SUB_AGENTE, "haiku", regras=("Seja breve.", "Cite a fonte."))
    opcoes = montar_opcoes(
        agente=agente, cli=None, pasta_de_trabalho=None, servidores={}, permitidos=(), conversa="x", retomar=False
    )

    lido = opcoes_do_claude(agente)

    assert lido.esforco == opcoes.effort
    assert lido.ferramentas_da_maquina == tuple(opcoes.tools) == ()
    assert lido.instrucoes == opcoes.system_prompt == "Seja breve.\n\nCite a fonte."


def test_a_ficha_muda_quando_a_configuracao_muda(tmp_path):
    """Trocar o agente, o catalogo ou as opcoes troca a ficha: nenhum valor e fixo."""

    async def principal():
        programa = await montar(tmp_path)
        try:
            agente = Agente(
                "revisor",
                Papel.SUB_AGENTE,
                "haiku",
                ferramentas=("anotar_memoria", "criar_sessao", "nao_existe"),
                regras=("Seja breve.",),
            )
            opcoes = OpcoesDoClaude(esforco="high", ferramentas_da_maquina=("Read", "Bash"), instrucoes="Seja breve.")
            return montar_ficha(agente, programa.catalogo, opcoes, do_software=False)
        finally:
            await programa.fechar()

    ficha = asyncio.run(principal())

    assert (ficha.nome, ficha.do_software, ficha.papel, ficha.modelo) == ("revisor", False, "pode ser chamado num chat", "haiku")
    assert ficha.esforco == "high"
    # Conferidas no catalogo: criar_sessao nao e de agente, e a inventada nao existe.
    assert ficha.ferramentas == ("anotar_memoria",)
    assert ficha.ferramentas_da_maquina == ("Read", "Bash")
    assert ficha.instrucoes == "Seja breve."


def test_a_ficha_segue_o_chat_ativo(tmp_path):
    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        await explicar(app, pilot, painel)
        await pilot.click("#novo-chat")
        await pilot.pause()
        await pilot.click("#agente-0")
        # O chat novo redesenha a tarefa fora de um worker: espera o painel novo
        # mostrar a ficha antes de clicar de novo.
        await ate(lambda: nome_na_ficha(app) == "bibliotecario")
        await esperar(app, pilot)
        painel = painel_aberto(app)
        do_bibliotecario = (chat_ativo(painel), ficha_na_tela(painel), explicacao(painel).display)
        id_do_orquestrador = painel.tarefa.sessoes[0].chats[0].id.valor
        # Ativar a aba e o que o clique faz; clicar logo depois do redesenho
        # da tarefa as vezes se perde no piloto de testes.
        painel.query_one("#abas-de-chat", Tabs).active = f"chat-{id_do_orquestrador}"
        await esperar(app, pilot)
        return do_bibliotecario, abas_de_chat(painel), ficha_na_tela(painel)["nome"]

    (ativo, ficha, aberto), abas, depois = rodar(tmp_path, roteiro)

    assert ativo == "bibliotecario" and aberto  # o painel continua aberto com o chat novo
    assert ficha["nome"] == "bibliotecario" and ficha["do software"]
    assert ficha["papel"] == "pode ser chamado num chat"
    assert ficha["modelo"] == BIBLIOTECARIO.modelo == "sonnet"
    assert ficha["ferramentas"] == NENHUMA and ficha["instrucoes"] == SEM_INSTRUCOES
    assert abas == ["orquestrador", "bibliotecario"]
    assert depois == "orquestrador"


# --------------------------------------------------------------------------
# Nada trava, e o foco nao pula sozinho
# --------------------------------------------------------------------------


def test_mexer_no_painel_nao_interrompe_a_conversa_nem_tira_o_foco(tmp_path):
    liberar, chegou = asyncio.Event(), asyncio.Event()
    fabrica = FabricaRoteirizada(
        turnos=[
            RoteiroDoTurno(
                [Mensagem(assistente(TextBlock("Olá, "))), Parar(liberar, chegou), Mensagem(assistente(TextBlock("tudo bem?"))), resultado()]
            )
        ]
    )

    async def principal():
        app = FishingRodApp(tmp_path, com_roteiro(fabrica))
        async with app.run_test(size=TAMANHO) as pilot:
            await pilot.pause()
            painel = await abrir_tarefa(app, pilot)
            chat = chat_visivel(app)
            campo = chat.query_one("#campo", Input)
            await mandar(pilot, chat, "oi")
            await chegou.wait()
            await digitar_sem_mandar(pilot, "e")
            focos = []
            for passo in (
                lambda: explicar(app, pilot, painel),
                lambda: ir_para_a_aba(app, pilot, painel, MEMORIA),
                lambda: ir_para_a_aba(app, pilot, painel, WIKI),
                lambda: ir_para_a_aba(app, pilot, painel, FICHA),
                lambda: explicar(app, pilot, painel),
            ):
                await passo()
                focos.append(app.focused is campo)
            no_meio = chat.conversa.estado(chat.id_chat)
            liberar.set()
            await ate(lambda: chat.conversa.estado(chat.id_chat) is not EstadoDoChat.RESPONDENDO)
            await pilot.pause()
            return focos, no_meio, campo.value, chat.texto_da_conversa(), faixa(chat), chat_visivel(app) is chat

    focos, no_meio, campo, texto, estado, mesmo_chat = asyncio.run(principal())

    assert focos == [True] * 5
    assert no_meio is EstadoDoChat.RESPONDENDO
    assert campo == "e"  # o que estava sendo escrito continua no campo
    assert "tudo bem?" in texto and "(interrompida)" not in texto
    assert estado == "● ligado"
    assert mesmo_chat  # o chat nao foi redesenhado


async def digitar_sem_mandar(pilot, texto: str) -> None:
    await pilot.press(*texto)


async def clicar_na_wiki(app, pilot, painel: PainelDaTarefa, rotulo: str) -> None:
    """Clica no no da arvore da wiki, como a pessoa faz."""
    arvore = explicacao(painel).query_one("#wiki", Tree)
    no = next(n for n in arvore.root.children if str(n.label) == rotulo)
    await pilot.click(arvore, offset=(4, no.line))
    await esperar(app, pilot)


def tela_da_wiki(painel: PainelDaTarefa) -> str:
    return explicacao(painel).query_one("#telas-da-wiki").current


def test_depois_de_abrir_o_index_as_outras_abas_ainda_abrem(tmp_path):
    """O retorno do Pedro: abrir o index prendia o painel na aba "wiki" -
    clicar em "memória" ou "ficha" voltava para ela."""

    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        campo = chat_visivel(app).query_one("#campo", Input)
        campo.focus()
        await explicar(app, pilot, painel)
        await ir_para_a_aba(app, pilot, painel, WIKI)
        await clicar_na_wiki(app, pilot, painel, "index")
        com_o_index = (tela_da_wiki(painel), "Nexo" in explicacao(painel).query_one("#texto-da-pagina", Markdown).source)
        abas = []
        for aba in (MEMORIA, FICHA, WIKI):
            await ir_para_a_aba(app, pilot, painel, aba)
            await pilot.pause(0.3)
            abas.append(aba_da_explicacao(painel))
        return com_o_index, abas, app.focused is campo

    com_o_index, abas, foco_no_campo = rodar(tmp_path, roteiro)

    assert com_o_index == (PAGINA_DA_WIKI, True)
    assert abas == [MEMORIA, FICHA, WIKI]
    assert foco_no_campo  # nada no painel pegou o foco


def test_voltar_na_wiki_mostra_a_lista_de_novo(tmp_path):
    async def roteiro(app, pilot):
        painel = await abrir_tarefa(app, pilot)
        await explicar(app, pilot, painel)
        await ir_para_a_aba(app, pilot, painel, WIKI)
        no_comeco = tela_da_wiki(painel)
        await clicar_na_wiki(app, pilot, painel, "index")
        aberta = tela_da_wiki(painel)
        await pilot.click(explicacao(painel).query_one("#voltar-a-lista"))
        await esperar(app, pilot)
        return no_comeco, aberta, tela_da_wiki(painel), painel.explicacao.pagina

    no_comeco, aberta, depois, lembrada = rodar(tmp_path, roteiro)

    assert (no_comeco, aberta, depois) == (LISTA_DA_WIKI, PAGINA_DA_WIKI, LISTA_DA_WIKI)
    assert lembrada is None  # redesenhar a tarefa nao reabre a pagina
