"""As propriedades de U4: PBT-U4-01 a PBT-U4-06 (plano, secao 4).

PBT-06: as que tem estado rodam SEQUENCIAS de comandos - de zero a quinze - e
verificam depois de CADA comando, nao so no fim. O oraculo e o
ModeloDeAmbientes (PBT-05), escrito do jeito mais ingenuo possivel.

Cada exemplo gerado tem portas proprias: um RepositorioEmMemoria novo e uma
pasta de dados nova. O ambiente de partida vem de `ambientes`, de U2, gravado
direto nas portas (`semear`) - assim a sequencia ja comeca com frentes,
tarefas e etapas para mirar, em vez de sempre do vazio.
"""

from pathlib import Path

from hypothesis import event, given, settings
from hypothesis import strategies as st

from fishingrod.aplicacao.caminho_wiki import normalizar_valor, slug, slug_valido
from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.persistencia import AmbienteInexistente
from fishingrod.aplicacao.portas.wiki import DescricaoObrigatoria, ErroDeWiki, TituloInvalido
from tests.ambiente import estrategias as est
from tests.ambiente.estrategias import executar
from tests.ambiente.instrumentos import Injecao, PersistenciaEspia, WikiEspia
from tests.ambiente.modelo import ModeloDeAmbientes, chamar, projetar, resolver
from tests.dobles.repositorio_memoria import RepositorioEmMemoria
from tests.persistencia.estrategias import tarefas_de


def _tipo(erro: Exception | None) -> type[Exception] | None:
    return None if erro is None else type(erro)


async def _do_disco(repo, wiki, id_ambiente):
    """Um servico NOVO sobre a mesma porta: o que outro processo - ou este,
    depois de fechar e reabrir - carregaria."""
    return await est.novo_servico(repo, wiki).carregar_ambiente(id_ambiente)


def _fotografar(pasta: Path) -> dict[str, bytes]:
    return {
        item.relative_to(pasta).as_posix(): item.read_bytes()
        for item in pasta.rglob("*")
        if item.is_file()
    }


# --------------------------------------------------------------------------
# PBT-U4-01 - memoria igual ao disco, e igual ao modelo (fecha US-05)
# --------------------------------------------------------------------------


@settings(max_examples=60)
@given(ambiente=est.ambientes_de_partida(), comandos=st.lists(est.comandos(criar=True), max_size=15))
def test_pbt_u4_01_memoria_igual_ao_disco_e_ao_modelo(tmp_path, ambiente, comandos):
    """Para qualquer sequencia das 10 operacoes, com alvos validos e invalidos,
    depois de cada passo: (a) o ambiente aberto e igual ao que um servico novo
    carrega da mesma porta (RN-A-03, RN-A-07, RN-A-09); (b) ele tem a forma que
    o modelo diz que deveria ter; (c) o erro, quando ha, e o que o modelo
    previu. (a) e o round-trip de US-05: fechar e reabrir nao perde nada."""
    repo = RepositorioEmMemoria()
    wiki, _ = est.nova_wiki(tmp_path)
    servico = est.novo_servico(repo, wiki)
    modelo = ModeloDeAmbientes()

    async def cenario():
        await est.semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        modelo.acrescentar(ambiente)
        conhecidos = [ambiente.id]

        for comando in comandos:
            chamada = resolver(comando, conhecidos, modelo.ambientes)
            esperado = modelo.prever(chamada)
            devolvido, erro = await chamar(servico, chamada)

            assert _tipo(erro) is esperado, f"{chamada}: {erro!r}"
            # Nas estatisticas do Hypothesis (--hypothesis-show-statistics): a
            # prova de que cada operacao foi exercitada no sucesso e no erro.
            event(f"{chamada.operacao} -> {'ok' if erro is None else type(erro).__name__}")
            if erro is None:
                modelo.aplicar(chamada, devolvido)
                if chamada.operacao == "criar_ambiente":
                    conhecidos.append(devolvido.id)
                if chamada.operacao == "listar_ambientes":
                    assert {resumo.id for resumo in devolvido} == set(modelo.ambientes)

            for id_ambiente in conhecidos:
                if id_ambiente not in modelo.ambientes:
                    for leitor in (servico, est.novo_servico(repo, wiki)):
                        try:
                            await leitor.carregar_ambiente(id_ambiente)
                        except AmbienteInexistente:
                            continue
                        raise AssertionError(f"[{id_ambiente}] devia ter sido apagado")
                    continue
                aberto = await servico.carregar_ambiente(id_ambiente)
                assert aberto == await _do_disco(repo, wiki, id_ambiente)
                assert projetar(aberto) == modelo.ambientes[id_ambiente]

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U4-02 - conflito nao perde mudanca
# --------------------------------------------------------------------------

# `carregar` raro: com metade dos passos sendo leitura - como estava na
# primeira versao -, nenhum dos 40 exemplos chegou a ter conflito (medido com
# --hypothesis-show-statistics), e a propriedade passava sem testar nada.
_PASSOS_DE_DOIS_PROCESSOS = st.lists(
    st.tuples(
        st.sampled_from(["A", "B"]),
        est.ponderado(
            (6, est.comandos_de_estrutura),
            (1, st.tuples(st.just("carregar_ambiente"), st.just(0), st.none())),
        ),
    ),
    max_size=15,
)


@settings(max_examples=40)
@given(ambiente=est.ambientes_de_partida(), passos=_PASSOS_DE_DOIS_PROCESSOS)
def test_pbt_u4_02_conflito_nao_perde_mudanca(tmp_path, ambiente, passos):
    """Dois servicos sobre a mesma porta - "dois processos" - revezando. Quase
    toda operacao de um encontra a memoria velha, porque o outro gravou no
    meio, e passa por conflito, recarga e reaplicacao (RN-A-10, RN-A-11).

    Depois de cada passo, o DISCO e igual ao modelo: toda operacao que deu
    certo, de qualquer dos dois, esta la. A memoria de quem nao agiu fica velha
    ate a proxima recarga, e isso e RN-A-26, nao defeito - por isso nao se
    compara memoria aqui (R-CG4-3).

    Os alvos de cada um saem da memoria DELE: quem chama so conhece os ids do
    proprio processo (R-CG4-3)."""
    repo = RepositorioEmMemoria()
    wiki, _ = est.nova_wiki(tmp_path)
    diario: list[str] = []  # so para contar as gravacoes
    servicos = {
        "A": est.novo_servico(PersistenciaEspia(repo, diario), wiki),
        "B": est.novo_servico(PersistenciaEspia(repo, diario), wiki),
    }
    modelo = ModeloDeAmbientes()

    async def cenario():
        await est.semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        modelo.acrescentar(ambiente)
        # Os dois abrem a mesma versao ANTES de qualquer escrita, como duas
        # janelas abertas no mesmo ambiente. Sem isso, a primeira escrita de
        # cada um sempre partia de memoria fresca, e conflito so aparecia no
        # padrao X-Y-X.
        for servico in servicos.values():
            await servico.carregar_ambiente(ambiente.id)
        gravacoes_com_sucesso = 0

        for ator, comando in passos:
            servico = servicos[ator]
            vista = projetar(await servico.carregar_ambiente(ambiente.id))
            chamada = resolver(comando, [ambiente.id], {ambiente.id: vista})
            esperado = modelo.prever(chamada)
            devolvido, erro = await chamar(servico, chamada)

            assert _tipo(erro) is esperado, f"{ator} {chamada}: {erro!r}"
            if erro is None:
                modelo.aplicar(chamada, devolvido)
                if chamada.operacao not in ("carregar_ambiente", "anotar_memoria"):
                    gravacoes_com_sucesso += 1
            disco = await _do_disco(repo, wiki, ambiente.id)
            assert projetar(disco) == modelo.ambientes[ambiente.id]

        # Toda gravacao a mais que as que deram certo foi um conflito.
        conflitos = diario.count("salvar_ambiente") - gravacoes_com_sucesso
        event("com conflito" if conflitos else "sem conflito")

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U4-03 - a wiki nasce igual ao esquema
# --------------------------------------------------------------------------


def _recusa_prevista(esquema: EsquemaWiki) -> type[ErroDeWiki] | None:
    """O oraculo da validacao de U3, na ordem dela (DP-W-10): todos os titulos
    primeiro, depois as descricoes."""
    titulos = [entidade.titulo for entidade in esquema.entidades] + [
        titulo
        for entidade in esquema.entidades
        for propriedade in entidade.propriedades
        for titulo in (entidade.titulo, propriedade.titulo)
    ]
    if not all(slug_valido(slug(titulo)) for titulo in titulos):
        return TituloInvalido
    descricoes = [p.descricao for e in esquema.entidades for p in e.propriedades]
    if not all(normalizar_valor(descricao) for descricao in descricoes):
        return DescricaoObrigatoria
    return None


def _wiki_esperada(esquema: EsquemaWiki) -> dict[str, dict[str, tuple[str, str]]]:
    """slug da entidade -> slug da pagina -> (titulo, descricao) normalizados.
    Titulos que colidem no slug caem no mesmo lugar, e a ultima escrita vence -
    e a ordem em que a proposta e escrita (RN-A-13)."""
    esperada: dict[str, dict[str, tuple[str, str]]] = {}
    for entidade in esquema.entidades:
        paginas = esperada.setdefault(slug(entidade.titulo), {})
        for propriedade in entidade.propriedades:
            paginas[slug(propriedade.titulo)] = (
                normalizar_valor(propriedade.titulo),
                normalizar_valor(propriedade.descricao),
            )
    return esperada


@settings(max_examples=40)
@given(nome=est.texto_nao_vazio, esquema=est.esquemas_quaisquer)
def test_pbt_u4_03_a_wiki_nasce_igual_ao_esquema(tmp_path, nome, esquema):
    """US-08, US-09, RN-A-13, RN-A-14. Para qualquer esquema: ou ele e aceito e
    a wiki tem exatamente as entidades e paginas dele - descricao da semente,
    corpo vazio, indice presente mesmo com esquema vazio -, ou e recusado com o
    erro que a validacao de U3 preve, e nem o banco nem o disco ganharam nada."""
    repo = RepositorioEmMemoria()
    wiki, dados = est.nova_wiki(tmp_path)
    servico = est.novo_servico(repo, wiki)
    recusa = _recusa_prevista(esquema)

    async def cenario():
        try:
            ambiente = await servico.criar_ambiente(nome, esquema)
        except ErroDeWiki as erro:
            event(f"recusado: {type(erro).__name__}")
            assert type(erro) is recusa, repr(erro)
            assert await repo.listar_ambientes() == []
            assert not dados.exists()
            return
        event("aceito, vazio" if not esquema.entidades else "aceito")
        assert recusa is None

        localizador = ambiente.raiz_wiki.localizador
        esperada = _wiki_esperada(esquema)
        assert await wiki.listar(localizador, "") == sorted(esperada)
        for entidade, paginas in esperada.items():
            assert await wiki.listar(localizador, entidade) == sorted(paginas)
            for pagina, (titulo, descricao) in paginas.items():
                lida = await wiki.ler(localizador, f"{entidade}/{pagina}")
                assert (lida.titulo, lida.descricao, lida.conteudo) == (titulo, descricao, "")
        assert (dados / "wikis" / ambiente.id.valor / "index.md").is_file()
        assert [resumo.id for resumo in await repo.listar_ambientes()] == [ambiente.id]

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U4-04 - isolamento entre ambientes (criterio 4)
# --------------------------------------------------------------------------


@settings(max_examples=30)
@given(
    ambiente=est.ambientes_de_partida(),
    vizinho=est.ambientes_de_partida(),
    esquema=est.esquemas_validos,
    esquema_do_vizinho=est.esquemas_validos,
    comandos=st.lists(est.comandos(), max_size=15),
)
def test_pbt_u4_04_isolamento_entre_ambientes(
    tmp_path, ambiente, vizinho, esquema, esquema_do_vizinho, comandos
):
    """Qualquer sequencia de comandos num ambiente - inclusive apaga-lo - nao
    muda o vizinho: nem o que esta no banco, nem um byte da wiki dele
    (RN-A-06, RN-A-08)."""
    repo = RepositorioEmMemoria()
    wiki, dados = est.nova_wiki(tmp_path)
    servico = est.novo_servico(repo, wiki)
    modelo = ModeloDeAmbientes()

    async def cenario():
        await est.semear(repo, wiki, ambiente, esquema)
        await est.semear(repo, wiki, vizinho, esquema_do_vizinho)
        modelo.acrescentar(ambiente)
        foto = await _do_disco(repo, wiki, vizinho.id)
        pasta_do_vizinho = dados / "wikis" / vizinho.id.valor
        arquivos = _fotografar(pasta_do_vizinho)

        for comando in comandos:
            chamada = resolver(comando, [ambiente.id], modelo.ambientes)
            esperado = modelo.prever(chamada)
            devolvido, erro = await chamar(servico, chamada)

            assert _tipo(erro) is esperado, f"{chamada}: {erro!r}"
            if erro is None:
                modelo.aplicar(chamada, devolvido)
            assert await _do_disco(repo, wiki, vizinho.id) == foto
            assert _fotografar(pasta_do_vizinho) == arquivos

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U4-05 - falha nao deixa rastro
# --------------------------------------------------------------------------


@settings(max_examples=40)
@given(
    ambiente=est.ambientes_de_partida(),
    comandos=st.lists(est.comandos(criar=True), max_size=12),
    # Cada comando faz uma ou duas chamadas; com um teto de 25, tres em cada
    # quatro exemplos terminavam sem a falha disparar (medido).
    na_chamada=st.integers(min_value=1, max_value=8),
    depois=st.booleans(),
)
def test_pbt_u4_05_falha_nao_deixa_rastro(tmp_path, ambiente, comandos, na_chamada, depois):
    """Uma falha, na n-esima chamada das duas portas juntas, antes ou depois de
    a chamada chegar a porta de verdade. Depois de cada comando, para todo
    ambiente que o banco lista: o aberto e igual ao do disco (RN-A-09), e a
    wiki dele existe (RN-A-16: nunca ha ambiente apontando para wiki que nao
    existe).

    Nao ha previsao de resultado aqui - a falha pode cair em qualquer lugar.
    O que se verifica e o rastro que ela deixa."""
    repo = RepositorioEmMemoria()
    wiki, dados = est.nova_wiki(tmp_path)
    injecao = Injecao(na_chamada, depois)
    servico = est.novo_servico(
        PersistenciaEspia(repo, injecao=injecao), WikiEspia(wiki, injecao=injecao)
    )

    async def cenario():
        await est.semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        conhecidos = [ambiente.id]

        for comando in comandos:
            vistas = {
                resumo.id: projetar(await _do_disco(repo, wiki, resumo.id))
                for resumo in await repo.listar_ambientes()
            }
            chamada = resolver(comando, conhecidos, vistas)
            devolvido, erro = await chamar(servico, chamada)
            if erro is None and chamada.operacao == "criar_ambiente":
                conhecidos.append(devolvido.id)

            with injecao.pausada():
                for resumo in await repo.listar_ambientes():
                    if resumo.id not in conhecidos:
                        conhecidos.append(resumo.id)  # criado, mas a resposta se perdeu
                    aberto = await servico.carregar_ambiente(resumo.id)
                    assert aberto == await _do_disco(repo, wiki, resumo.id), chamada
                    assert (dados / "wikis" / resumo.id.valor / "index.md").is_file()

        event(f"falha {'disparou' if injecao.disparou else 'nao disparou'}, {'depois' if depois else 'antes'}")

    executar(cenario())


# --------------------------------------------------------------------------
# PBT-U4-06 - concluir_etapa e idempotente (R-CG4-4)
# --------------------------------------------------------------------------


@settings(max_examples=30)
@given(
    ambiente=est.ambientes_de_partida(),
    escolha=st.integers(min_value=0, max_value=50),
    vezes=st.integers(min_value=1, max_value=3),
)
def test_pbt_u4_06_concluir_etapa_e_idempotente(tmp_path, ambiente, escolha, vezes):
    """PBT-04, para RN-A-23: concluir k vezes a mais deixa o mesmo estado que
    concluir uma - fora `versao`, que sobe a cada vez, porque concluir de novo
    grava de novo."""
    etapas = [etapa for tarefa in tarefas_de(ambiente) for etapa in tarefa.etapas]
    alvo = etapas[escolha % len(etapas)]  # ambientes_de_partida garante pelo menos uma
    repo = RepositorioEmMemoria()
    wiki, _ = est.nova_wiki(tmp_path)
    servico = est.novo_servico(repo, wiki)

    async def cenario():
        await est.semear(repo, wiki, ambiente, EsquemaWiki.vazio())
        await servico.concluir_etapa(ambiente.id, alvo.id)
        aberto = await servico.carregar_ambiente(ambiente.id)
        uma_vez, versao = projetar(aberto), aberto.versao

        for _ in range(vezes):
            await servico.concluir_etapa(ambiente.id, alvo.id)

        assert projetar(aberto) == uma_vez
        assert aberto.versao == versao + vezes
        assert projetar(await _do_disco(repo, wiki, ambiente.id)) == uma_vez

    executar(cenario())
