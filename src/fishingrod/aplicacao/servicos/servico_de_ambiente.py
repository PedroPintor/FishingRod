"""ServicoDeAmbiente: o caso de uso que coordena dominio, banco e wiki (U4).

Este e o unico arquivo de U4 que as outras unidades importam: U5 (ferramentas
de ambiente do orquestrador), U8 (o chat do bibliotecario) e U9 (as telas e o
composition root).

RN-A-01: so dominio e portas. Nenhum import de sqlite3, claude_agent_sdk,
textual, os, pathlib nem shutil - o servico nao sabe que existe disco. Quem
apaga a pasta da wiki e a porta (PortaWiki.apagar), nao este arquivo.

A leitura tem uma ordem: os erros, a conversao do esquema (pura), a busca de
alvo por identidade e, por fim, a classe. Dentro dela, os auxiliares vem antes
das onze operacoes, porque e neles que moram as regras de falha e de conflito -
num lugar so, em vez de repetidas onze vezes (business-logic-model.md 1).
"""

import asyncio
import dataclasses
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from fishingrod.aplicacao.esquema_wiki import EsquemaWiki
from fishingrod.aplicacao.portas.persistencia import (
    AmbienteInexistente,
    ConflitoDeVersao,
    PortaPersistencia,
    ResumoAmbiente,
)
from fishingrod.aplicacao.portas.wiki import (
    ErroDeWiki,
    PaginaProposta,
    PortaWiki,
    PropostaWiki,
)
from fishingrod.dominio import (
    Agente,
    AgenteInvalido,
    Ambiente,
    Anotacao,
    Chat,
    Etapa,
    ExecutorEtapa,
    Frente,
    Identidade,
    Sessao,
    Tarefa,
)

T = TypeVar("T")

# RN-A-11 (Q4=A). Conflito so vem de outro processo (RN-A-06), entao tres
# tentativas seguidas perdidas querem dizer disputa de verdade, nao azar.
MAXIMO_DE_TENTATIVAS = 3

# O NullHandler fica aqui, e nao no __init__ do pacote: servicos/ e
# compartilhado por U4, U7 e U8. Sem destino configurado, o aviso de RN-A-18
# nao pode vazar para a tela da TUI - quem decide o destino e U9.
_log = logging.getLogger("fishingrod.ambiente")
_log.addHandler(logging.NullHandler())


# --------------------------------------------------------------------------
# Erros (domain-entities.md 3.1)
# --------------------------------------------------------------------------
# Mensagens sem caminho de disco e sem detalhe de adaptador: carregam o id que
# faltou.


class ErroDeServicoDeAmbiente(Exception):
    """Raiz dos erros novos desta unidade (G5).

    Nao fica sob ErroDeDominio: nao achar um alvo nao e violacao de invariante -
    no dominio, isso e None (RN-14). Quem decide que o alvo era obrigatorio e o
    servico.
    """


class FrenteInexistente(ErroDeServicoDeAmbiente):
    """RN-A-08: id_frente nao existe neste ambiente."""


class TarefaInexistente(ErroDeServicoDeAmbiente):
    """RN-A-08: id_tarefa nao existe neste ambiente."""


class SessaoInexistente(ErroDeServicoDeAmbiente):
    """RN-A-08: id_sessao nao existe neste ambiente."""


class EtapaInexistente(ErroDeServicoDeAmbiente):
    """RN-A-08: id_etapa nao existe neste ambiente."""


class AgenteDesconhecido(ErroDeServicoDeAmbiente):
    """RN-A-22: nome fora da lista fechada de agentes de chat - inclusive o do
    orquestrador, que nunca esta nela (G3)."""


# --------------------------------------------------------------------------
# O esquema vira a primeira proposta (RN-A-13)
# --------------------------------------------------------------------------


def proposta_do_esquema(esquema: EsquemaWiki) -> PropostaWiki:
    """Uma entidade nova por EntidadeSemente e uma pagina por PropriedadeSemente,
    com a descricao da semente e conteudo vazio: o conteudo vem do trabalho
    real, nao de texto que o produto inventou (Q8 de U3).

    Esquema vazio da proposta vazia, e isso e valido - quem cria a raiz, nesse
    caso, e renderizar_index (RN-W-25).

    Nao valida nada: titulo e descricao sao verificados por escrever_proposta
    antes de tocar o disco (DP-W-10 de U3). Repetir aqui seria a segunda copia
    de uma regra que ja tem dono.
    """
    return PropostaWiki(
        entidades_novas=tuple(entidade.titulo for entidade in esquema.entidades),
        paginas=tuple(
            PaginaProposta(
                entidade=entidade.titulo,
                titulo=propriedade.titulo,
                descricao=propriedade.descricao,
                conteudo="",
            )
            for entidade in esquema.entidades
            for propriedade in entidade.propriedades
        ),
    )


# --------------------------------------------------------------------------
# Alvo por identidade, dentro do ambiente (RN-A-08)
# --------------------------------------------------------------------------
# O None do dominio vira erro tipado aqui (Q12=B), antes de qualquer mudanca.


def _achar_frente(ambiente: Ambiente, id_frente: Identidade) -> Frente:
    frente = ambiente.buscar_frente(id_frente)
    if frente is None:
        raise FrenteInexistente(f"nao existe a frente [{id_frente}] neste ambiente")
    return frente


def _achar_tarefa(ambiente: Ambiente, id_tarefa: Identidade) -> Tarefa:
    for frente in ambiente.frentes:
        tarefa = frente.buscar_tarefa(id_tarefa)
        if tarefa is not None:
            return tarefa
    raise TarefaInexistente(f"nao existe a tarefa [{id_tarefa}] neste ambiente")


def _achar_sessao(ambiente: Ambiente, id_sessao: Identidade) -> Sessao:
    for frente in ambiente.frentes:
        for tarefa in frente.tarefas:
            sessao = tarefa.buscar_sessao(id_sessao)
            if sessao is not None:
                return sessao
    raise SessaoInexistente(f"nao existe a sessao [{id_sessao}] neste ambiente")


def _achar_etapa(ambiente: Ambiente, id_etapa: Identidade) -> Etapa:
    for frente in ambiente.frentes:
        for tarefa in frente.tarefas:
            etapa = tarefa.buscar_etapa(id_etapa)
            if etapa is not None:
                return etapa
    raise EtapaInexistente(f"nao existe a etapa [{id_etapa}] neste ambiente")


def _localizador(ambiente: Ambiente) -> str:
    # raiz_wiki so e None antes do __post_init__ de Ambiente, que a monta a
    # partir do id (Q9=A de U1). Um Ambiente que chegou aqui sempre a tem.
    return ambiente.raiz_wiki.localizador


# --------------------------------------------------------------------------
# O servico
# --------------------------------------------------------------------------


class ServicoDeAmbiente:
    """Onze operacoes sobre ambientes, para a tela e para os agentes (C1=A).

    Guarda dois estados, e so (domain-entities.md 1.2):
    - os ambientes ABERTOS, um objeto por id no processo (Q1=A). A tela e os
      agentes enxergam o mesmo objeto; e por isso que uma recarga atualiza o
      objeto em vez de troca-lo (G2);
    - uma TRAVA por ambiente (Q10=A). Duas operacoes no mesmo ambiente nunca se
      intercalam; ambientes diferentes nao esperam um pelo outro.

    Nao guarda "ambiente ativo" (Q2=A): toda operacao, menos criar e listar,
    recebe o id do ambiente explicito.

    Devolve o objeto afetado ou levanta erro tipado - nunca Resultado, que e de
    U5 (Q3=A).
    """

    def __init__(
        self,
        persistencia: PortaPersistencia,
        wiki: PortaWiki,
        orquestrador: Agente,
        agentes_de_chat: tuple[Agente, ...],
    ) -> None:
        """Recebe as portas ja montadas pelo composition root: o servico nao
        constroi adaptador nem le configuracao (services.md 1, passo 3).

        As tres recusas sao erro de montagem, nao de uso, e por isso levantam
        AgenteInvalido, de U1.
        """
        if not orquestrador.e_orquestrador:
            raise AgenteInvalido(
                "o orquestrador do servico precisa ter papel orquestrador; "
                f"[{orquestrador.nome}] tem papel {orquestrador.papel.value}"
            )
        for agente in agentes_de_chat:
            if agente.e_orquestrador:
                # G3: toda sessao ja nasce com o seu orquestrador (RN-A-21).
                # Fora da lista, pedir um segundo cai em AgenteDesconhecido, sem
                # depender de o dominio pegar o caso depois.
                raise AgenteInvalido(
                    f"[{agente.nome}] e orquestrador e nao pode estar entre os agentes de chat"
                )
        nomes = [agente.nome for agente in agentes_de_chat]
        repetidos = sorted({nome for nome in nomes if nomes.count(nome) > 1})
        if repetidos:
            raise AgenteInvalido(f"nomes repetidos entre os agentes de chat: {repetidos}")

        self._persistencia = persistencia
        self._wiki = wiki
        self._orquestrador = orquestrador
        self._agentes_de_chat = {agente.nome: agente for agente in agentes_de_chat}
        self._abertos: dict[Identidade, Ambiente] = {}
        self._travas: dict[Identidade, asyncio.Lock] = {}

    # ----------------------------------------------------------------------
    # Auxiliares: estado, falha e conflito (business-logic-model.md 1)
    # ----------------------------------------------------------------------

    def _trava(self, id_ambiente: Identidade) -> asyncio.Lock:
        """RN-A-06. Criada sob demanda e nunca removida, nem ao apagar o
        ambiente: remover deixaria uma corrotina que esperava a trava antiga
        rodar junto com outra que pegou uma nova."""
        trava = self._travas.get(id_ambiente)
        if trava is None:
            trava = self._travas[id_ambiente] = asyncio.Lock()
        return trava

    def _fechar(self, id_ambiente: Identidade) -> None:
        self._abertos.pop(id_ambiente, None)

    async def _abrir(self, id_ambiente: Identidade) -> Ambiente:
        """RN-A-03 e RN-A-04: o aberto volta sem reler o disco; o que nao esta
        aberto e carregado e passa a estar. Chamado ja com a trava."""
        aberto = self._abertos.get(id_ambiente)
        if aberto is not None:
            return aberto
        ambiente = await self._persistencia.carregar_ambiente(id_ambiente)
        if ambiente is None:
            # RN-A-05: a porta devolve None (RN-P-04); quem converte e o servico.
            raise AmbienteInexistente(f"nao existe ambiente [{id_ambiente}]")
        self._abertos[id_ambiente] = ambiente
        return ambiente

    async def _recarregar(self, ambiente: Ambiente) -> None:
        """Le do disco e copia o estado lido para dentro do MESMO objeto (RN-A-03,
        G2). Trocar o objeto quebraria Q1=A no primeiro conflito: a tela ficaria
        segurando o antigo.

        Ambiente que sumiu do disco - apagado por outro processo - e fechado, e
        a resposta e AmbienteInexistente (RN-A-12). Se a leitura falhar, o
        ambiente tambem e fechado (RN-A-09): a proxima operacao o abre de novo,
        do disco.
        """
        try:
            lido = await self._persistencia.carregar_ambiente(ambiente.id)
        except BaseException:
            self._fechar(ambiente.id)
            raise
        if lido is None:
            self._fechar(ambiente.id)
            raise AmbienteInexistente(f"o ambiente [{ambiente.id}] nao existe mais")
        # Campo a campo, por dataclasses.fields: se Ambiente ganhar um campo, a
        # recarga continua completa sem ninguem lembrar de mexer aqui.
        for campo in dataclasses.fields(Ambiente):
            setattr(ambiente, campo.name, getattr(lido, campo.name))

    async def _gravar(self, ambiente: Ambiente, gravacao: Awaitable[None]) -> None:
        """RN-A-09: memoria nunca diverge do disco depois de uma falha.

        Gravacao que falhou deixou na memoria uma mudanca que o disco nao tem;
        recarregar faz ela sumir tambem daqui. Se a recarga tambem falhar, quem
        sobe e o erro da GRAVACAO - o motivo de a operacao ter falhado -, e a
        falha da recarga vai junto como nota (R-CG4-1), em vez de ser engolida.
        O ambiente, nesse caso, ja foi fechado por _recarregar.

        Cancelamento nao e falha (R-CG4-5): a gravacao pode ter chegado ao disco
        ou nao. O ambiente e fechado, sem esperar nada, e a proxima operacao o
        le de novo do disco.

        ConflitoDeVersao passa direto: quem o trata e _mutar (RN-A-10).
        """
        try:
            await gravacao
        except ConflitoDeVersao:
            raise
        except Exception as erro:
            try:
                await self._recarregar(ambiente)
            except Exception as erro_da_recarga:
                erro.add_note(
                    "a recarga depois da falha tambem falhou "
                    f"({type(erro_da_recarga).__name__}); o ambiente foi fechado"
                )
            raise
        except BaseException:
            self._fechar(ambiente.id)
            raise

    async def _mutar(self, id_ambiente: Identidade, intencao: Callable[[Ambiente], T]) -> T:
        """O caminho de toda operacao de estrutura.

        `intencao` acha o alvo, chama o dominio e devolve o objeto criado ou
        alterado - sem I/O. E guardada como funcao, e nao como objeto, porque
        e o que se reaplica ao estado novo depois de um conflito (RN-A-10).

        Ela roda ANTES da gravacao: um erro do dominio ou de alvo inexistente
        aparece antes de qualquer escrita (RN-A-02, RN-A-08), e, como o dominio
        valida antes de mudar o objeto, nao deixa mudanca pela metade.
        """
        async with self._trava(id_ambiente):
            ambiente = await self._abrir(id_ambiente)
            for tentativa in range(1, MAXIMO_DE_TENTATIVAS + 1):
                resultado = intencao(ambiente)
                try:
                    await self._gravar(ambiente, self._persistencia.salvar_ambiente(ambiente))
                except ConflitoDeVersao:
                    # A recarga aqui e fluxo normal, entao, se falhar, e o erro
                    # dela que sobe (R-CG4-1): AmbienteInexistente (RN-A-12) ou
                    # o erro de leitura.
                    await self._recarregar(ambiente)
                    if tentativa == MAXIMO_DE_TENTATIVAS:
                        raise  # RN-A-11, com a memoria ja igual ao disco
                else:
                    return resultado
        raise AssertionError("inalcancavel: a ultima tentativa devolve ou levanta")

    def _resolver_agente(self, nome_agente: str) -> Agente:
        agente = self._agentes_de_chat.get(nome_agente)
        if agente is None:
            raise AgenteDesconhecido(
                f"[{nome_agente}] nao esta entre os agentes com que se pode abrir chat: "
                f"{sorted(self._agentes_de_chat)}"
            )
        return agente

    # ----------------------------------------------------------------------
    # Ciclo do ambiente (business-logic-model.md 2)
    # ----------------------------------------------------------------------

    async def criar_ambiente(self, nome: str, esquema: EsquemaWiki) -> Ambiente:
        """US-08, US-09. RN-A-14: o dominio primeiro (valida o nome, gera id e
        raiz), depois a wiki, depois o banco.

        Wiki primeiro (Q5=A) porque o contrario deixaria, numa falha no meio, um
        ambiente apontando para wiki que nao existe. Assim, o pior caso e uma
        pasta orfa, inofensiva - e nao ha compensacao (RN-A-16).

        O ambiente nasce sem frente (RN-A-15): quem garante que o usuario tem
        onde trabalhar e a tela (U9).

        Sem trava: o id e novo e ninguem mais o conhece ate a ultima linha. Pelo
        mesmo motivo, ConflitoDeVersao aqui e impossivel.
        """
        ambiente = Ambiente(nome=nome)
        localizador = _localizador(ambiente)
        await self._wiki.escrever_proposta(localizador, proposta_do_esquema(esquema))
        await self._wiki.renderizar_index(localizador, ambiente.nome)
        await self._persistencia.salvar_ambiente(ambiente)
        self._abertos[ambiente.id] = ambiente
        return ambiente

    async def carregar_ambiente(self, id_ambiente: Identidade) -> Ambiente:
        """US-05. Aberto volta como o MESMO objeto, sem reler o disco (RN-A-03);
        id que nao existe e AmbienteInexistente (RN-A-05)."""
        async with self._trava(id_ambiente):
            return await self._abrir(id_ambiente)

    async def listar_ambientes(self) -> list[ResumoAmbiente]:
        """RN-A-20: repassa a porta, na ordem dela - mais recentemente atualizado
        primeiro -, sem trava e sem abrir nenhum ambiente."""
        return await self._persistencia.listar_ambientes()

    async def apagar_ambiente(self, id_ambiente: Identidade) -> None:
        """Criterio 6, RN-A-17: banco primeiro, wiki depois. Se travar no meio,
        sobra uma pasta orfa, e nunca um ambiente vivo sem wiki.

        Nao pergunta nada (RN-P-23): a confirmacao e da tela.
        """
        async with self._trava(id_ambiente):
            ambiente = await self._abrir(id_ambiente)
            await self._persistencia.apagar_ambiente(id_ambiente)
            self._fechar(id_ambiente)
            try:
                await self._wiki.apagar(_localizador(ambiente))
            except ErroDeWiki as erro:
                # RN-A-18 (G1), o unico erro que o servico nao propaga: o
                # ambiente ja nao existe, que era o pedido. Levantar faria a tela
                # dizer "nao foi possivel apagar" sobre algo que sumiu da lista.
                # So o tipo do erro, e nunca caminho de disco.
                _log.warning(
                    "ambiente [%s] apagado, mas a pasta da wiki ficou no disco (%s)",
                    id_ambiente,
                    type(erro).__name__,
                )

    # ----------------------------------------------------------------------
    # Estrutura, todas por _mutar (business-logic-model.md 3)
    # ----------------------------------------------------------------------

    async def criar_frente(self, id_ambiente: Identidade, nome: str) -> Frente:
        """US-15. Nome repetido e permitido (RN-04 de U1): a identidade
        distingue."""
        return await self._mutar(id_ambiente, lambda ambiente: ambiente.criar_frente(nome))

    async def criar_tarefa(self, id_ambiente: Identidade, id_frente: Identidade, nome: str) -> Tarefa:
        """US-16. A tarefa nasce com a primeira sessao, e nela o chat do
        orquestrador do construtor: quem chama nao escolhe nem conhece o agente
        (RN-A-21, D21)."""
        return await self._mutar(
            id_ambiente,
            lambda ambiente: _achar_frente(ambiente, id_frente).criar_tarefa(
                nome, self._orquestrador
            ),
        )

    async def criar_sessao(
        self, id_ambiente: Identidade, id_tarefa: Identidade, nome: str = ""
    ) -> Sessao:
        """D21. A sessao nasce com o chat do orquestrador, como a primeira.
        `nome` vazio vira "sessão N" (Tarefa, de U1)."""
        return await self._mutar(
            id_ambiente,
            lambda ambiente: _achar_tarefa(ambiente, id_tarefa).criar_sessao(
                self._orquestrador, nome
            ),
        )

    async def criar_chat(
        self, id_ambiente: Identidade, id_sessao: Identidade, nome_agente: str, nome: str = ""
    ) -> Chat:
        """Q14=X: e assim que o orquestrador delega ao bibliotecario. So abre chat
        com agente da lista fechada, achado pelo nome (RN-A-22) - quem chama, a
        tela ou um agente, nao consegue entregar um agente de fora.

        `nome` vazio vira o nome do agente (Chat, de U1).
        """

        def intencao(ambiente: Ambiente) -> Chat:
            # Resolvido dentro da intencao: nome desconhecido falha antes de
            # qualquer escrita, como os outros erros de validacao.
            agente = self._resolver_agente(nome_agente)
            return _achar_sessao(ambiente, id_sessao).criar_chat(agente, nome)

        return await self._mutar(id_ambiente, intencao)

    async def criar_etapa(
        self,
        id_ambiente: Identidade,
        id_tarefa: Identidade,
        descricao: str,
        executor: ExecutorEtapa,
    ) -> Etapa:
        """US-17, a parte de gravar (C1=A). Anexa ao fim: a posicao na lista e a
        ordem (RN-08 de U1)."""
        return await self._mutar(
            id_ambiente,
            lambda ambiente: _achar_tarefa(ambiente, id_tarefa).criar_etapa(descricao, executor),
        )

    async def concluir_etapa(self, id_ambiente: Identidade, id_etapa: Identidade) -> Etapa:
        """US-19. Idempotente: concluir o que ja esta concluido grava de novo e
        nao e erro (RN-A-23, PBT-U4-06).

        Sem id_tarefa (G4): a identidade da etapa ja e unica no ambiente.
        Reabrir nao existe nesta iteracao (RN-A-24).
        """

        def intencao(ambiente: Ambiente) -> Etapa:
            etapa = _achar_etapa(ambiente, id_etapa)
            etapa.concluir()
            return etapa

        return await self._mutar(id_ambiente, intencao)

    # ----------------------------------------------------------------------
    # Memoria (business-logic-model.md 4)
    # ----------------------------------------------------------------------

    async def anotar_memoria(
        self,
        id_ambiente: Identidade,
        id_sessao: Identidade,
        chave: str,
        valor: str,
        autor: str,
    ) -> Anotacao:
        """US-04. A memoria e da sessao (D21). Nao passa por _mutar porque nao grava o documento (RN-A-25):
        o dominio cria a Anotacao e o servico a entrega a porta de anotar.
        Nunca chama salvar_ambiente, nunca levanta ConflitoDeVersao e nao muda
        Ambiente.versao.

        Anotacao gravada por outro processo so aparece aqui quando o ambiente
        for recarregado (RN-A-26).
        """
        async with self._trava(id_ambiente):
            ambiente = await self._abrir(id_ambiente)
            sessao = _achar_sessao(ambiente, id_sessao)
            anotacao = sessao.memoria.anotar(chave, valor, autor)  # valida chave e autor
            await self._gravar(
                ambiente, self._persistencia.anotar(id_ambiente, id_sessao, chave, anotacao)
            )
            return anotacao
