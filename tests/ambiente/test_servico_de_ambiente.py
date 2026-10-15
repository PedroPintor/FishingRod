"""U4 - ServicoDeAmbiente, por exemplo (PBT-10).

Cada teste fixa um comportamento concreto de uma regra RN-A-*, com o valor
esperado escrito. As propriedades gerais estao em test_propriedades.py; aqui
ficam os casos que um leitor precisa ver para entender a regra, e os que uma
propriedade nao alcanca bem (ordem exata das portas, a trava sob duas
corrotinas, o aviso no log, o cancelamento).

As portas sao o RepositorioEmMemoria (Q12=B de U2) e a WikiDeArquivos sobre
tmp_path (Q9=A de U3). Quando o teste precisa ver ou perturbar as chamadas,
elas vao embrulhadas pelos espias de instrumentos.py.
"""

import asyncio
import logging

import pytest

from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.persistencia import AmbienteInexistente, ConflitoDeVersao
from fishingrod.aplicacao.portas.wiki import PaginaProposta, PropostaWiki, TituloInvalido
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    AgenteDesconhecido,
    ErroDeServicoDeAmbiente,
    EtapaInexistente,
    FrenteInexistente,
    ServicoDeAmbiente,
    TarefaInexistente,
    proposta_do_esquema,
)
from fishingrod.dominio import (
    Agente,
    AgenteInvalido,
    Ambiente,
    ErroDeDominio,
    ExecutorEtapa,
    Identidade,
    NomeInvalido,
    Papel,
)
from tests.ambiente.estrategias import (
    BIBLIOTECARIO,
    ORQUESTRADOR,
    executar,
    novo_servico,
    semear,
)
from tests.ambiente.instrumentos import (
    FalhaInjetadaNaWiki,
    FalhaInjetadaNoBanco,
    PersistenciaEspia,
    WikiEspia,
)
from tests.dobles.repositorio_memoria import RepositorioEmMemoria

ESQUEMA = EsquemaWiki.a_partir_do_formulario(
    {
        "entidades": [
            {
                "titulo": "Clientes",
                "propriedades": [{"titulo": "Dr. Marcelo", "descricao": "dentista"}],
            },
            {"titulo": "Ofertas"},
        ]
    }
)


@pytest.fixture
def repo() -> RepositorioEmMemoria:
    return RepositorioEmMemoria()


@pytest.fixture
def dados(tmp_path):
    return tmp_path / "dados"


@pytest.fixture
def wiki(dados) -> WikiDeArquivos:
    return WikiDeArquivos(dados)


@pytest.fixture
def servico(repo, wiki) -> ServicoDeAmbiente:
    return novo_servico(repo, wiki)


def _pasta_da_wiki(dados, ambiente):
    return dados / "wikis" / ambiente.id.valor


async def _do_disco(repo, wiki, id_ambiente):
    """O que um serviço novo - outro processo, ou o mesmo depois de reabrir -
    carrega da mesma porta."""
    return await novo_servico(repo, wiki).carregar_ambiente(id_ambiente)


async def _com_tarefa(servico):
    ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
    frente = await servico.criar_frente(ambiente.id, "Aquisição")
    tarefa = await servico.criar_tarefa(ambiente.id, frente.id, "Prospectar dentistas")
    return ambiente, frente, tarefa


# --------------------------------------------------------------------------
# Construção (domain-entities.md 1.1, G3)
# --------------------------------------------------------------------------


def test_construcao_recusa_orquestrador_sem_papel_de_orquestrador(repo, wiki):
    with pytest.raises(AgenteInvalido):
        ServicoDeAmbiente(repo, wiki, BIBLIOTECARIO, ())


def test_g3_construcao_recusa_orquestrador_entre_os_agentes_de_chat(repo, wiki):
    with pytest.raises(AgenteInvalido):
        ServicoDeAmbiente(repo, wiki, ORQUESTRADOR, (BIBLIOTECARIO, ORQUESTRADOR))


def test_construcao_recusa_nomes_repetidos_na_lista(repo, wiki):
    gemeo = Agente(nome=BIBLIOTECARIO.nome, papel=Papel.SUB_AGENTE, modelo="outro-modelo")

    with pytest.raises(AgenteInvalido):
        ServicoDeAmbiente(repo, wiki, ORQUESTRADOR, (BIBLIOTECARIO, gemeo))


def test_g5_os_erros_novos_tem_raiz_propria_fora_do_dominio():
    for erro in (FrenteInexistente, TarefaInexistente, EtapaInexistente, AgenteDesconhecido):
        assert issubclass(erro, ErroDeServicoDeAmbiente)
        assert not issubclass(erro, ErroDeDominio)


def test_rn_a_24_nao_ha_reabrir_etapa_nesta_iteracao():
    assert not hasattr(ServicoDeAmbiente, "reabrir_etapa")


# --------------------------------------------------------------------------
# Criar ambiente (RN-A-13..16, critério 1, US-08, US-09)
# --------------------------------------------------------------------------


def test_rn_a_13_o_esquema_vira_a_primeira_proposta():
    assert proposta_do_esquema(ESQUEMA) == PropostaWiki(
        entidades_novas=("Clientes", "Ofertas"),
        paginas=(PaginaProposta("Clientes", "Dr. Marcelo", "dentista", conteudo=""),),
    )
    assert proposta_do_esquema(EsquemaWiki.vazio()) == PropostaWiki()


def test_rn_a_14_criar_ambiente_escreve_a_wiki_antes_do_banco(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), WikiEspia(wiki, diario))

    executar(servico.criar_ambiente("Nexo", ESQUEMA))

    assert diario == ["escrever_proposta", "renderizar_index", "salvar_ambiente"]


def test_us_08_us_09_criar_ambiente_materializa_a_wiki_do_esquema(servico, repo, wiki, dados):
    """Critério 1: a wiki nasce do esquema e o índice é renderizado, numa
    operação só. A página nasce com a descrição da semente e corpo vazio."""

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", ESQUEMA)
        localizador = ambiente.raiz_wiki.localizador

        assert await wiki.listar(localizador, "") == ["clientes", "ofertas"]
        pagina = await wiki.ler(localizador, "clientes/dr-marcelo")
        assert (pagina.titulo, pagina.descricao, pagina.conteudo) == ("Dr. Marcelo", "dentista", "")
        assert (_pasta_da_wiki(dados, ambiente) / "index.md").is_file()

        assert ambiente.versao == 1
        assert ambiente.frentes == []  # RN-A-15: nasce sem frente
        assert await _do_disco(repo, wiki, ambiente.id) == ambiente

    executar(cenario())


def test_us_08_esquema_vazio_nasce_so_com_o_indice(servico, wiki, dados):
    ambiente = executar(servico.criar_ambiente("Nexo", EsquemaWiki.vazio()))

    assert executar(wiki.listar(ambiente.raiz_wiki.localizador, "")) == []
    assert [item.name for item in _pasta_da_wiki(dados, ambiente).iterdir()] == ["index.md"]


def test_rn_a_02_nome_invalido_nao_toca_porta_nenhuma(repo, wiki, dados):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), WikiEspia(wiki, diario))

    with pytest.raises(NomeInvalido):
        executar(servico.criar_ambiente("   ", ESQUEMA))

    assert diario == []
    assert not dados.exists()


def test_rn_a_16_esquema_recusado_pela_wiki_nao_grava_nada(servico, repo, dados):
    """A wiki valida a proposta inteira antes de escrever (DP-W-10 de U3): nem
    pasta, nem banco."""
    esquema = EsquemaWiki.a_partir_do_formulario({"entidades": [{"titulo": "Clientes"}, {"titulo": "..."}]})

    with pytest.raises(TituloInvalido):
        executar(servico.criar_ambiente("Nexo", esquema))

    assert executar(repo.listar_ambientes()) == []
    assert not dados.exists()


def test_rn_a_16_falha_de_io_na_wiki_nao_grava_no_banco(repo, wiki):
    async def falhar(nome):
        if nome == "renderizar_index":
            raise FalhaInjetadaNaWiki("disco cheio")

    servico = novo_servico(repo, WikiEspia(wiki, antes=falhar))

    with pytest.raises(FalhaInjetadaNaWiki):
        executar(servico.criar_ambiente("Nexo", ESQUEMA))

    assert executar(repo.listar_ambientes()) == []


def test_rn_a_16_falha_no_banco_deixa_so_uma_wiki_orfa(repo, wiki, dados):
    """O inverso não acontece: nunca existe ambiente apontando para wiki que
    não existe."""

    async def falhar(nome):
        if nome == "salvar_ambiente":
            raise FalhaInjetadaNoBanco("banco travado")

    servico = novo_servico(PersistenciaEspia(repo, antes=falhar), wiki)

    with pytest.raises(FalhaInjetadaNoBanco):
        executar(servico.criar_ambiente("Nexo", ESQUEMA))

    assert executar(repo.listar_ambientes()) == []
    [orfa] = list((dados / "wikis").iterdir())
    assert (orfa / "index.md").is_file()


def test_rn_a_19_nome_de_ambiente_repetido_e_permitido(servico):
    async def cenario():
        primeiro = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        segundo = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())

        assert primeiro.id != segundo.id
        assert primeiro.raiz_wiki != segundo.raiz_wiki
        resumos = await servico.listar_ambientes()
        assert {r.id for r in resumos} == {primeiro.id, segundo.id}
        assert {r.nome for r in resumos} == {"Nexo"}

    executar(cenario())


def test_criterio_4_cada_ambiente_e_a_sua_raiz(servico, repo, wiki):
    """Vários ambientes na mesma instalação (Q10=B): carregar(id) devolve o
    certo, e a wiki de um não enxerga a do outro."""

    async def cenario():
        um = await servico.criar_ambiente("Um", ESQUEMA)
        outro = await servico.criar_ambiente("Outro", EsquemaWiki.vazio())

        servico_novo = novo_servico(repo, wiki)
        assert (await servico_novo.carregar_ambiente(um.id)).nome == "Um"
        assert (await servico_novo.carregar_ambiente(outro.id)).nome == "Outro"
        assert await wiki.listar(um.raiz_wiki.localizador, "") == ["clientes", "ofertas"]
        assert await wiki.listar(outro.raiz_wiki.localizador, "") == []

    executar(cenario())


# --------------------------------------------------------------------------
# Carregar, listar e apagar (RN-A-03..05, RN-A-17, RN-A-18, RN-A-20, critério 6)
# --------------------------------------------------------------------------


def test_rn_a_03_carregar_devolve_o_mesmo_objeto_sem_reler_o_disco(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        diario.clear()

        assert await servico.carregar_ambiente(ambiente.id) is ambiente
        assert await servico.carregar_ambiente(ambiente.id) is ambiente
        assert diario == []

    executar(cenario())


def test_rn_a_04_operacao_abre_o_ambiente_sem_carregar_antes(repo, wiki):
    async def cenario():
        ambiente = Ambiente(nome="criado por outra sessão")
        await semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        servico = novo_servico(repo, wiki)

        frente = await servico.criar_frente(ambiente.id, "Aquisição")

        aberto = await servico.carregar_ambiente(ambiente.id)
        assert aberto.frentes == [frente]
        assert aberto.frentes[0] is frente

    executar(cenario())


@pytest.mark.parametrize(
    "operacao",
    [
        lambda s, id: s.carregar_ambiente(id),
        lambda s, id: s.apagar_ambiente(id),
        lambda s, id: s.criar_frente(id, "f"),
        lambda s, id: s.criar_tarefa(id, Identidade.nova(), "t"),
        lambda s, id: s.criar_chat(id, Identidade.nova(), BIBLIOTECARIO.nome),
        lambda s, id: s.criar_etapa(id, Identidade.nova(), "e", ExecutorEtapa.USUARIO),
        lambda s, id: s.concluir_etapa(id, Identidade.nova()),
        lambda s, id: s.anotar_memoria(id, Identidade.nova(), "k", "v", "autor"),
    ],
    ids=[
        "carregar",
        "apagar",
        "criar_frente",
        "criar_tarefa",
        "criar_chat",
        "criar_etapa",
        "concluir_etapa",
        "anotar_memoria",
    ],
)
def test_rn_a_05_ambiente_que_nao_existe_e_erro_tipado(servico, operacao):
    """Q12=B: nunca None. O ambiente é verificado antes de qualquer alvo."""
    with pytest.raises(AmbienteInexistente):
        executar(operacao(servico, Identidade.nova()))


def test_rn_a_20_listar_nao_abre_nenhum_ambiente(repo, wiki):
    async def cenario():
        um, outro = Ambiente(nome="Um"), Ambiente(nome="Outro")
        for ambiente in (um, outro):
            await semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        diario: list[str] = []
        servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

        resumos = await servico.listar_ambientes()

        assert {r.id for r in resumos} == {um.id, outro.id}
        assert diario == ["listar_ambientes"]

    executar(cenario())


def test_rn_a_17_apagar_e_banco_antes_da_wiki(repo, wiki, dados):
    """Critério 6. Nada é perguntado (RN-P-23): a confirmação é da tela."""
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), WikiEspia(wiki, diario))

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", ESQUEMA)
        diario.clear()

        await servico.apagar_ambiente(ambiente.id)

        assert diario == ["apagar_ambiente", "apagar"]
        assert await repo.listar_ambientes() == []
        assert not _pasta_da_wiki(dados, ambiente).exists()
        with pytest.raises(AmbienteInexistente):
            await servico.carregar_ambiente(ambiente.id)

    executar(cenario())


def test_rn_a_17_falha_no_banco_ao_apagar_nao_toca_a_wiki(repo, wiki, dados):
    async def falhar(nome):
        if nome == "apagar_ambiente":
            raise FalhaInjetadaNoBanco("banco travado")

    servico = novo_servico(PersistenciaEspia(repo, antes=falhar), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", ESQUEMA)

        with pytest.raises(FalhaInjetadaNoBanco):
            await servico.apagar_ambiente(ambiente.id)

        assert (_pasta_da_wiki(dados, ambiente) / "index.md").is_file()
        assert await servico.carregar_ambiente(ambiente.id) is ambiente

    executar(cenario())


def test_rn_a_18_falha_ao_apagar_a_wiki_vira_warning_e_nao_erro(repo, wiki, dados, caplog):
    """G1: o ambiente já não existe, que era o pedido. O aviso traz o id e o
    tipo do erro - nunca o texto dele, que poderia ter caminho de disco."""

    async def falhar(nome):
        if nome == "apagar":
            raise FalhaInjetadaNaWiki("arquivo em uso: C:\\Users\\alguem\\segredo")

    servico = novo_servico(repo, WikiEspia(wiki, antes=falhar))
    caplog.set_level(logging.WARNING, logger="fishingrod.ambiente")

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", ESQUEMA)

        await servico.apagar_ambiente(ambiente.id)  # não levanta

        assert await repo.listar_ambientes() == []
        assert _pasta_da_wiki(dados, ambiente).is_dir()  # órfã, inofensiva
        return ambiente

    ambiente = executar(cenario())

    [aviso] = [r for r in caplog.records if r.name == "fishingrod.ambiente"]
    assert aviso.levelno == logging.WARNING
    assert ambiente.id.valor in aviso.getMessage()
    assert "FalhaInjetadaNaWiki" in aviso.getMessage()
    assert "Users" not in aviso.getMessage()


# --------------------------------------------------------------------------
# Estrutura (RN-A-02, RN-A-07, RN-A-08, RN-A-21..23, US-15..17, US-19)
# --------------------------------------------------------------------------


def test_us_15_us_16_frente_e_tarefa_com_o_orquestrador_do_construtor(servico, repo, wiki):
    """RN-A-21: quem chama criar_tarefa não escolhe nem conhece o agente."""

    async def cenario():
        ambiente, frente, tarefa = await _com_tarefa(servico)

        assert [c.agente for c in tarefa.chats] == [ORQUESTRADOR]
        assert ambiente.frentes == [frente] and frente.tarefas == [tarefa]
        assert await _do_disco(repo, wiki, ambiente.id) == ambiente

    executar(cenario())


def test_rn_a_22_criar_chat_so_com_agente_da_lista_fechada(servico):
    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)

        chat = await servico.criar_chat(ambiente.id, tarefa.id, BIBLIOTECARIO.nome)
        assert chat.agente is BIBLIOTECARIO
        assert chat.nome == BIBLIOTECARIO.nome  # nome vazio vira o do agente

        versao = ambiente.versao
        for nome in (ORQUESTRADOR.nome, "Bibliotecario", "qualquer um"):
            with pytest.raises(AgenteDesconhecido):
                await servico.criar_chat(ambiente.id, tarefa.id, nome)
        assert ambiente.versao == versao  # nada gravado
        assert len(tarefa.chats) == 2

    executar(cenario())


def test_rn_a_22_agente_desconhecido_vem_antes_do_alvo(servico):
    """O agente é resolvido dentro da intenção, antes de procurar a tarefa."""

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        with pytest.raises(AgenteDesconhecido):
            await servico.criar_chat(ambiente.id, Identidade.nova(), "ninguém")

    executar(cenario())


def test_us_17_etapas_anexam_ao_fim_e_us_19_concluir(servico, repo, wiki):
    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)

        primeira = await servico.criar_etapa(ambiente.id, tarefa.id, "listar", ExecutorEtapa.AGENTE)
        segunda = await servico.criar_etapa(ambiente.id, tarefa.id, "ligar", ExecutorEtapa.USUARIO)
        concluida = await servico.concluir_etapa(ambiente.id, segunda.id)

        assert concluida is segunda and segunda.concluida
        assert tarefa.etapas == [primeira, segunda]
        assert not primeira.concluida  # sem dependência entre etapas
        assert await _do_disco(repo, wiki, ambiente.id) == ambiente

    executar(cenario())


def test_rn_a_23_concluir_duas_vezes_grava_de_novo_e_nao_e_erro(servico):
    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)
        etapa = await servico.criar_etapa(ambiente.id, tarefa.id, "ligar", ExecutorEtapa.USUARIO)

        await servico.concluir_etapa(ambiente.id, etapa.id)
        versao = ambiente.versao
        await servico.concluir_etapa(ambiente.id, etapa.id)

        assert etapa.concluida
        assert ambiente.versao == versao + 1

    executar(cenario())


def test_rn_a_08_alvo_inexistente_e_erro_tipado_e_nada_e_gravado(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

    async def cenario():
        ambiente, _, _ = await _com_tarefa(servico)
        versao = ambiente.versao
        diario.clear()
        fantasma = Identidade.nova()

        with pytest.raises(FrenteInexistente):
            await servico.criar_tarefa(ambiente.id, fantasma, "t")
        for operacao in (
            servico.criar_chat(ambiente.id, fantasma, BIBLIOTECARIO.nome),
            servico.criar_etapa(ambiente.id, fantasma, "e", ExecutorEtapa.AGENTE),
            servico.anotar_memoria(ambiente.id, fantasma, "k", "v", "autor"),
        ):
            with pytest.raises(TarefaInexistente):
                await operacao
        with pytest.raises(EtapaInexistente):
            await servico.concluir_etapa(ambiente.id, fantasma)

        assert diario == []
        assert ambiente.versao == versao

    executar(cenario())


def test_rn_a_08_alvo_de_outro_ambiente_nao_existe_neste(servico):
    """Critério 4, por identidade: a tarefa existe - em outro ambiente."""

    async def cenario():
        _, _, tarefa_de_outro = await _com_tarefa(servico)
        ambiente = await servico.criar_ambiente("Outro", EsquemaWiki.vazio())

        with pytest.raises(TarefaInexistente):
            await servico.criar_etapa(ambiente.id, tarefa_de_outro.id, "e", ExecutorEtapa.AGENTE)

    executar(cenario())


def test_rn_a_02_erro_do_dominio_chega_antes_de_gravar(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)
        versao = ambiente.versao
        diario.clear()

        with pytest.raises(NomeInvalido):
            await servico.criar_frente(ambiente.id, "  ")
        with pytest.raises(NomeInvalido):
            await servico.criar_etapa(ambiente.id, tarefa.id, "", ExecutorEtapa.AGENTE)
        with pytest.raises(NomeInvalido):
            await servico.anotar_memoria(ambiente.id, tarefa.id, " ", "v", "autor")

        assert diario == []
        assert ambiente.versao == versao
        assert len(ambiente.frentes) == 1

    executar(cenario())


def test_rn_a_07_uma_gravacao_por_operacao(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        frente = await servico.criar_frente(ambiente.id, "f")
        tarefa = await servico.criar_tarefa(ambiente.id, frente.id, "t")
        await servico.criar_chat(ambiente.id, tarefa.id, BIBLIOTECARIO.nome)
        etapa = await servico.criar_etapa(ambiente.id, tarefa.id, "e", ExecutorEtapa.AGENTE)
        await servico.concluir_etapa(ambiente.id, etapa.id)

        assert diario == ["salvar_ambiente"] * 6
        assert ambiente.versao == 6

    executar(cenario())


# --------------------------------------------------------------------------
# Memória (RN-A-25, US-04)
# --------------------------------------------------------------------------


def test_rn_a_25_anotar_nao_grava_o_documento_e_acumula(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario), wiki)

    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)
        versao = ambiente.versao
        diario.clear()

        primeira = await servico.anotar_memoria(ambiente.id, tarefa.id, "icp", "dentistas", "orquestrador")
        segunda = await servico.anotar_memoria(ambiente.id, tarefa.id, "icp", "clínicas", "usuário")

        assert diario == ["anotar", "anotar"]
        assert ambiente.versao == versao
        assert tarefa.memoria.anotacoes["icp"] == [primeira, segunda]  # US-04: não substitui
        assert await _do_disco(repo, wiki, ambiente.id) == ambiente

    executar(cenario())


# --------------------------------------------------------------------------
# Falha e conflito (RN-A-09..12, R-CG4-1, R-CG4-5, critério 5)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("depois", [False, True], ids=["antes-de-gravar", "depois-de-gravar"])
def test_rn_a_09_falha_na_gravacao_deixa_a_memoria_igual_ao_disco(repo, wiki, depois):
    """"Depois" é a porta que grava e mesmo assim responde erro: a mudança
    está no disco, e a memória precisa ficar com ela. Nos dois casos, o objeto
    continua o mesmo (G2)."""
    falhar = {"ligado": False}

    async def gancho(nome):
        if falhar["ligado"] and nome == "salvar_ambiente" and not depois:
            raise FalhaInjetadaNoBanco("banco travado")

    class Espia(PersistenciaEspia):
        async def salvar_ambiente(self, ambiente):
            await super().salvar_ambiente(ambiente)
            if falhar["ligado"] and depois:
                raise FalhaInjetadaNoBanco("a resposta se perdeu")

    servico = novo_servico(Espia(repo, antes=gancho), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        falhar["ligado"] = True

        with pytest.raises(FalhaInjetadaNoBanco):
            await servico.criar_frente(ambiente.id, "Aquisição")

        assert await servico.carregar_ambiente(ambiente.id) is ambiente
        assert ambiente == await _do_disco(repo, wiki, ambiente.id)
        assert [f.nome for f in ambiente.frentes] == (["Aquisição"] if depois else [])

    executar(cenario())


def test_rn_a_09_falha_ao_anotar_some_da_memoria(repo, wiki):
    falhar = {"ligado": False}

    async def gancho(nome):
        if falhar["ligado"] and nome == "anotar":
            raise FalhaInjetadaNoBanco("banco travado")

    servico = novo_servico(PersistenciaEspia(repo, antes=gancho), wiki)

    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(servico)
        falhar["ligado"] = True

        with pytest.raises(FalhaInjetadaNoBanco):
            await servico.anotar_memoria(ambiente.id, tarefa.id, "icp", "dentistas", "eu")

        aberto = await servico.carregar_ambiente(ambiente.id)
        assert aberto is ambiente
        assert aberto == await _do_disco(repo, wiki, ambiente.id)
        assert aberto.frentes[0].tarefas[0].memoria.total_de_anotacoes() == 0

    executar(cenario())


def test_r_cg4_1_recarga_que_falha_vira_nota_e_fecha_o_ambiente(repo, wiki):
    """Sobe o erro da gravação - o motivo de a operação ter falhado -, com a
    falha da recarga anotada nele. Nada é engolido, e o ambiente é fechado: a
    próxima operação o lê de novo do disco."""
    falhar = {"ligado": False}

    async def gancho(nome):
        if falhar["ligado"] and nome in ("salvar_ambiente", "carregar_ambiente"):
            raise FalhaInjetadaNoBanco(f"{nome} falhou")

    servico = novo_servico(PersistenciaEspia(repo, antes=gancho), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        falhar["ligado"] = True

        with pytest.raises(FalhaInjetadaNoBanco) as erro:
            await servico.criar_frente(ambiente.id, "Aquisição")

        assert str(erro.value) == "salvar_ambiente falhou"
        assert any("recarga" in nota for nota in erro.value.__notes__)

        falhar["ligado"] = False
        reaberto = await servico.carregar_ambiente(ambiente.id)
        assert reaberto is not ambiente
        assert reaberto.frentes == []

    executar(cenario())


def test_rn_a_10_conflito_recarrega_e_reaplica_no_mesmo_objeto(repo, wiki):
    """Critério 5. O outro processo gravou entre a leitura e a escrita deste:
    a operação dá certo mesmo assim, o efeito dos dois fica no disco, e quem
    segurava a referência ao Ambiente vê tudo (G2)."""
    diario: list[str] = []
    este = novo_servico(PersistenciaEspia(repo, diario), wiki)
    outro = novo_servico(repo, wiki)

    async def cenario():
        ambiente = await este.criar_ambiente("Nexo", EsquemaWiki.vazio())
        await outro.criar_frente(ambiente.id, "do outro")
        diario.clear()

        frente = await este.criar_frente(ambiente.id, "deste")

        assert diario == ["salvar_ambiente", "carregar_ambiente", "salvar_ambiente"]
        assert await este.carregar_ambiente(ambiente.id) is ambiente
        assert [f.nome for f in ambiente.frentes] == ["do outro", "deste"]
        assert ambiente.frentes[1] is frente
        assert ambiente == await _do_disco(repo, wiki, ambiente.id)

    executar(cenario())


def test_rn_a_11_tres_conflitos_seguidos_desiste_com_a_memoria_igual_ao_disco(repo, wiki):
    """O outro processo grava antes de CADA tentativa deste. Na terceira, o
    serviço desiste com ConflitoDeVersao - e o que fica na memória é o disco,
    sem a mudança que não entrou."""
    diario: list[str] = []
    outro = novo_servico(repo, wiki)

    async def outro_grava_antes(nome):
        if nome == "salvar_ambiente" and intrometer["ligado"]:
            await outro.criar_frente(id_ambiente["valor"], "intrusa")

    intrometer = {"ligado": False}
    id_ambiente = {}
    este = novo_servico(PersistenciaEspia(repo, diario, antes=outro_grava_antes), wiki)

    async def cenario():
        ambiente = await este.criar_ambiente("Nexo", EsquemaWiki.vazio())
        id_ambiente["valor"] = ambiente.id
        intrometer["ligado"] = True
        diario.clear()

        with pytest.raises(ConflitoDeVersao):
            await este.criar_frente(ambiente.id, "deste")

        assert diario.count("salvar_ambiente") == 3
        assert diario.count("carregar_ambiente") == 3
        assert [f.nome for f in ambiente.frentes] == ["intrusa"] * 3
        assert ambiente == await _do_disco(repo, wiki, ambiente.id)

    executar(cenario())


def test_rn_a_12_ambiente_apagado_por_outro_processo(repo, wiki):
    este = novo_servico(repo, wiki)
    outro = novo_servico(repo, wiki)

    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(este)
        await outro.apagar_ambiente(ambiente.id)

        with pytest.raises(AmbienteInexistente):
            await este.criar_frente(ambiente.id, "tarde demais")
        with pytest.raises(AmbienteInexistente):
            await este.carregar_ambiente(ambiente.id)  # foi fechado

    executar(cenario())


def test_rn_a_12_anotar_em_ambiente_apagado_por_outro_processo(repo, wiki):
    este = novo_servico(repo, wiki)
    outro = novo_servico(repo, wiki)

    async def cenario():
        ambiente, _, tarefa = await _com_tarefa(este)
        await outro.apagar_ambiente(ambiente.id)

        with pytest.raises(AmbienteInexistente):
            await este.anotar_memoria(ambiente.id, tarefa.id, "k", "v", "autor")
        with pytest.raises(AmbienteInexistente):
            await este.carregar_ambiente(ambiente.id)

    executar(cenario())


def test_r_cg4_5_cancelamento_no_meio_da_gravacao_fecha_o_ambiente(repo, wiki):
    """A TUI fechou no meio de um salvar_ambiente: não dá para saber se a
    gravação chegou ao disco. O ambiente sai dos abertos, e a próxima operação
    o lê de novo."""
    entrou = asyncio.Event()

    async def demorar(nome):
        if nome == "salvar_ambiente":
            entrou.set()
            await asyncio.sleep(3600)

    async def cenario():
        ambiente = Ambiente(nome="Nexo")
        await semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        servico = novo_servico(PersistenciaEspia(repo, antes=demorar), wiki)
        aberto = await servico.carregar_ambiente(ambiente.id)

        tarefa = asyncio.create_task(servico.criar_frente(ambiente.id, "nunca"))
        await entrou.wait()
        tarefa.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarefa

        reaberto = await servico.carregar_ambiente(ambiente.id)
        assert reaberto is not aberto
        assert reaberto.frentes == []

    executar(cenario())


# --------------------------------------------------------------------------
# A trava (RN-A-06)
# --------------------------------------------------------------------------


def test_rn_a_06_mesmo_ambiente_uma_operacao_por_vez(repo, wiki):
    """O espia cede o laço no meio do salvar_ambiente. Com a trava, a segunda
    operação só entra quando a primeira saiu."""
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario, ceder=True), wiki)

    async def cenario():
        ambiente = await servico.criar_ambiente("Nexo", EsquemaWiki.vazio())
        diario.clear()

        await asyncio.gather(
            servico.criar_frente(ambiente.id, "um"),
            servico.criar_frente(ambiente.id, "dois"),
        )

        assert diario == ["salvar_ambiente", "salvar_ambiente:fim"] * 2
        assert sorted(f.nome for f in ambiente.frentes) == ["dois", "um"]
        assert ambiente == await _do_disco(repo, wiki, ambiente.id)

    executar(cenario())


def test_rn_a_06_ambientes_diferentes_nao_esperam_um_pelo_outro(repo, wiki):
    diario: list[str] = []
    servico = novo_servico(PersistenciaEspia(repo, diario, ceder=True), wiki)

    async def cenario():
        um = await servico.criar_ambiente("Um", EsquemaWiki.vazio())
        outro = await servico.criar_ambiente("Outro", EsquemaWiki.vazio())
        diario.clear()

        await asyncio.gather(
            servico.criar_frente(um.id, "f"),
            servico.criar_frente(outro.id, "f"),
        )

        assert diario == ["salvar_ambiente"] * 2 + ["salvar_ambiente:fim"] * 2

    executar(cenario())
