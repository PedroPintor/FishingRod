"""CatalogoDeAcoes: o registro e o unico ponto de execucao das acoes (U5).

Toda acao passa pelo mesmo caminho, venha da barra, do botao ou do agente
(business-logic-model.md 1). E isso que torna RF-F17 uma propriedade da
arquitetura, e nao uma convencao: a politica de confirmacao e consultada aqui,
uma vez, para toda acao (RN-AC-27), e a traducao de excecao para Resultado
tambem (G1).

RN-AC-01: so dominio, ServicoDeAmbiente e PortaDeConfirmacao. Nenhum import de
sqlite3, claude_agent_sdk, textual, os ou pathlib, nem de adaptador. Os erros
de persistencia e de wiki entram so como TIPOS, para o mapeamento.

A leitura tem uma ordem: comando e nome, a verificacao do registro, a tabela de
mapeamento e, por fim, a classe com o caminho de RN-AC-38.
"""

import logging
import re
from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType

from fishingrod.aplicacao.catalogo.argumentos import (
    ArgumentoRecusado,
    converter,
    repartir,
    sem_maiuscula_nem_acento,
)
from fishingrod.aplicacao.catalogo.parser import ComandoDigitado
from fishingrod.aplicacao.catalogo.registro import ACOES, achar_frente, achar_sessao, achar_tarefa
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    Acionamento,
    Alvo,
    CatalogoInvalido,
    Escopo,
    EtapaNaPosicao,
    MotivoFalha,
    PedidoDeConfirmacao,
    Referencias,
    Resultado,
    TipoParametro,
)
from fishingrod.aplicacao.portas.confirmacao import PortaDeConfirmacao
from fishingrod.aplicacao.portas.persistencia import (
    AmbienteInexistente,
    ConflitoDeVersao,
    ErroDePersistencia,
)
from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    AgenteDesconhecido,
    EtapaInexistente,
    FrenteInexistente,
    ServicoDeAmbiente,
    SessaoInexistente,
    TarefaInexistente,
)
from fishingrod.dominio import Chamador, ErroDeDominio, exige_aprovacao

# RN-AC-37. O NullHandler fica aqui pelo mesmo motivo de U2-U4: sem destino
# configurado, nada vaza para a tela da TUI - quem decide o destino e U9.
_log = logging.getLogger("fishingrod.acoes")
_log.addHandler(logging.NullHandler())

# snake_case ASCII minusculo, sem sublinhado duplo nem nas pontas. E o que
# torna a troca de `_` por `-` bijetiva (RN-AC-07): nenhum nome tem `-`, e
# nenhum comando valido tem `_`.
_NOME = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")

# Nome desconhecido volta no detalhe, cortado: e texto de quem acionou.
_ECO_MAXIMO = 100


# --------------------------------------------------------------------------
# Um nome, dois jeitos de escrever (RN-AC-07, G7)
# --------------------------------------------------------------------------


def comando_de(nome_da_acao: str) -> str:
    """`criar_tarefa` -> `criar-tarefa` (Q6=A). Sem a barra: a barra e do
    parser."""
    return nome_da_acao.replace("_", "-")


def nome_de(comando: str) -> str | None:
    """A inversa de comando_de. Comando com `_` nao e forma de comando (G7):
    `/criar_tarefa` e acao desconhecida, e nao um segundo jeito de escrever
    `/criar-tarefa`."""
    if "_" in comando:
        return None
    return comando.replace("-", "_")


# --------------------------------------------------------------------------
# Verificacao do registro (RN-AC-08, R-CG5-3)
# --------------------------------------------------------------------------


def _verificar(acoes: Sequence[Acao]) -> None:
    """Erro de montagem, e nao de uso: levanta CatalogoInvalido dizendo qual
    acao e o que esta errado."""
    vistos: set[str] = set()
    for acao in acoes:
        if not isinstance(acao, Acao):
            raise CatalogoInvalido(f"o registro tem um item que nao e Acao: {acao!r}")
        if not isinstance(acao.nome, str) or not _NOME.fullmatch(acao.nome):
            raise CatalogoInvalido(f"nome de acao fora do padrao snake_case: {acao.nome!r}")
        if acao.nome in vistos:
            raise CatalogoInvalido(f"acao [{acao.nome}] repetida no registro")
        vistos.add(acao.nome)
        if not acao.chamadores or not all(isinstance(c, Chamador) for c in acao.chamadores):
            raise CatalogoInvalido(f"acao [{acao.nome}] sem chamadores validos")
        _verificar_parametros(acao)


def _verificar_parametros(acao: Acao) -> None:
    nomes: set[str] = set()
    opcional_visto = False
    posicoes = 0
    for parametro in acao.parametros:
        onde = f"acao [{acao.nome}], parametro [{parametro.nome}]"
        if not isinstance(parametro.nome, str) or not _NOME.fullmatch(parametro.nome):
            raise CatalogoInvalido(f"{onde}: nome fora do padrao snake_case")
        if parametro.nome in nomes:
            raise CatalogoInvalido(f"{onde}: nome repetido na acao")
        nomes.add(parametro.nome)
        # Obrigatorios antes dos opcionais: e o que deixa a barra posicional
        # (Q7=A) sem ambiguidade.
        if parametro.obrigatorio and opcional_visto:
            raise CatalogoInvalido(f"{onde}: obrigatorio depois de um opcional")
        opcional_visto = opcional_visto or not parametro.obrigatorio

        e_escolha = parametro.tipo is TipoParametro.ESCOLHA
        if e_escolha and not parametro.opcoes:
            raise CatalogoInvalido(f"{onde}: ESCOLHA sem opcoes")
        if not e_escolha and parametro.opcoes:
            raise CatalogoInvalido(f"{onde}: opcoes so existem em ESCOLHA")
        # G4 compara sem maiuscula e sem acento: duas opcoes que so diferem
        # nisso seriam a mesma escolha.
        normalizadas = [sem_maiuscula_nem_acento(opcao) for opcao in parametro.opcoes]
        if len(set(normalizadas)) != len(normalizadas):
            raise CatalogoInvalido(f"{onde}: opcoes que so diferem em maiuscula ou acento")

        e_texto = parametro.tipo is TipoParametro.TEXTO
        maximo_valido = (
            isinstance(parametro.maximo, int)
            and not isinstance(parametro.maximo, bool)
            and parametro.maximo >= 1
        )
        if e_texto and not maximo_valido:
            raise CatalogoInvalido(f"{onde}: TEXTO sem maximo de caracteres (G10)")
        if not e_texto and parametro.maximo is not None:
            raise CatalogoInvalido(f"{onde}: maximo so existe em TEXTO")

        # R-CG5-3: a posicao aponta uma etapa da tarefa-alvo. Sem tarefa no
        # escopo nao ha lista para apontar; com duas posicoes, nao se saberia
        # qual etapa a confirmacao mostra.
        if parametro.tipo is TipoParametro.POSICAO:
            posicoes += 1
            if acao.escopo is not Escopo.TAREFA:
                raise CatalogoInvalido(f"{onde}: POSICAO so em acao de escopo TAREFA")
            if posicoes > 1:
                raise CatalogoInvalido(f"{onde}: no maximo uma POSICAO por acao")


# --------------------------------------------------------------------------
# De excecao para Resultado (domain-entities.md 5.3, RN-AC-36)
# --------------------------------------------------------------------------


class _PosicaoAlemDoFim(Exception):
    """Interno: a posicao pedida passa do numero de etapas da tarefa. Vira
    ALVO_INEXISTENTE pelo mesmo caminho dos outros alvos que nao existem."""

    def __init__(self, posicao: int, total: int) -> None:
        super().__init__(posicao, total)
        self.posicao = posicao
        self.total = total


def _traduzir(erro: Exception) -> Resultado | None:
    """Do mais especifico para o mais geral: AmbienteInexistente e
    ConflitoDeVersao herdam de ErroDePersistencia, e por isso vem antes da
    linha geral. None quer dizer defeito - quem chamou registra no log.

    `erro` no detalhe e so o NOME do tipo: nunca a mensagem, que pode trazer
    caminho de disco ou conteudo (RN-AC-35).
    """
    match erro:
        case _PosicaoAlemDoFim(posicao=posicao, total=total):
            return Resultado.falha(
                MotivoFalha.ALVO_INEXISTENTE, alvo="etapa", posicao=posicao, total=total
            )
        case AmbienteInexistente():
            return Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="ambiente")
        case FrenteInexistente():
            return Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="frente")
        case TarefaInexistente():
            return Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="tarefa")
        case SessaoInexistente():
            return Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="sessao")
        case EtapaInexistente():
            return Resultado.falha(MotivoFalha.ALVO_INEXISTENTE, alvo="etapa")
        case AgenteDesconhecido():
            return Resultado.falha(
                MotivoFalha.ARGUMENTO_INVALIDO, parametro="agente", problema="fora_da_lista"
            )
        case ConflitoDeVersao():
            return Resultado.falha(MotivoFalha.CONFLITO)
        case ErroDePersistencia() | ErroDeWiki():
            return Resultado.falha(MotivoFalha.FALHA_DE_ARMAZENAMENTO, erro=type(erro).__name__)
        case ErroDeDominio():
            return Resultado.falha(MotivoFalha.REGRA_VIOLADA, erro=type(erro).__name__)
    return None


def _registrar_inesperada(acao: str, acionamento: Acionamento, erro: Exception) -> None:
    """RN-AC-37: nome da acao, tipo de quem acionou, tipo do erro e a pilha.
    Os ARGUMENTOS nao entram - podem trazer conteudo do usuario, como um valor
    de memoria. O nome da acao e sempre um nome do registro, nunca o que foi
    digitado."""
    chamador = getattr(getattr(acionamento, "chamador", None), "value", "?")
    _log.error(
        "acao [%s] acionada por %s falhou de forma inesperada (%s)",
        acao,
        chamador,
        type(erro).__name__,
        exc_info=erro,
    )


# --------------------------------------------------------------------------
# O catalogo
# --------------------------------------------------------------------------

# O passo 4 e diferente para as duas entradas (R-CG5-2): `executar` converte
# argumentos por nome; `executar_comando` reparte o texto antes. Todo o resto e
# o mesmo caminho.
_Argumentos = Callable[[Acao], dict[str, object]]


class CatalogoDeAcoes:
    """O registro e o unico ponto de execucao (domain-entities.md 6.1).

    Nao guarda estado alem do registro e das duas referencias do construtor:
    duas execucoes concorrentes nao se veem, e quem serializa o acesso ao
    ambiente e a trava de U4.

    Fora a montagem (CatalogoInvalido), `executar` e `executar_comando` nunca
    levantam (RN-AC-34): toda falha vira Resultado. So o cancelamento e a
    interrupcao do processo passam, porque nao sao Exception.
    """

    def __init__(
        self,
        servico: ServicoDeAmbiente,
        confirmacao: PortaDeConfirmacao,
        acoes: Sequence[Acao] = ACOES,
    ) -> None:
        """`acoes` e parametro para teste - uma acao so de usuario, por exemplo,
        e o que exercita NAO_PERMITIDA. Em producao, e o registro."""
        acoes = tuple(acoes)
        _verificar(acoes)
        self._servico = servico
        self._confirmacao = confirmacao
        self._acoes = acoes
        self._por_nome = {acao.nome: acao for acao in acoes}

    # ----------------------------------------------------------------------
    # O registro
    # ----------------------------------------------------------------------

    def listar(self, escopo: Escopo | None = None, chamador: Chamador | None = None) -> tuple[Acao, ...]:
        """RN-AC-09: na ordem do registro. E daqui que a paleta tira a lista do
        usuario e U9 tira as ferramentas do orquestrador."""
        return tuple(
            acao
            for acao in self._acoes
            if (escopo is None or acao.escopo is escopo)
            and (chamador is None or chamador in acao.chamadores)
        )

    def buscar(self, nome: str) -> Acao | None:
        """Pelo nome da acao (snake_case), nao pelo comando."""
        return self._por_nome.get(nome)

    # ----------------------------------------------------------------------
    # As duas entradas
    # ----------------------------------------------------------------------

    async def executar(
        self,
        nome: str,
        alvo: Alvo,
        argumentos: Mapping[str, object],
        acionamento: Acionamento,
    ) -> Resultado:
        """Botao e agente: argumentos por nome (RN-AC-17)."""
        return await self._executar(
            nome, nome, alvo, acionamento, lambda acao: converter(acao.parametros, argumentos)
        )

    async def executar_comando(self, comando: ComandoDigitado, alvo: Alvo) -> Resultado:
        """A barra `/`. Sempre do usuario (RN-AC-15, G8): o agente nao digita
        nela, e por isso nao ha Acionamento para receber.

        O texto so e repartido no passo 4 (R-CG5-2): um erro de texto nunca
        aparece antes de NAO_PERMITIDA ou de ALVO_AUSENTE.
        """
        return await self._executar(
            nome_de(comando.nome),
            comando.nome,
            alvo,
            Acionamento.usuario(),
            lambda acao: converter(acao.parametros, repartir(acao.parametros, comando.texto)),
        )

    # ----------------------------------------------------------------------
    # O caminho (RN-AC-38)
    # ----------------------------------------------------------------------

    async def _executar(
        self,
        nome: object,
        como_chegou: object,
        alvo: Alvo,
        acionamento: Acionamento,
        argumentos_de: _Argumentos,
    ) -> Resultado:
        """A primeira verificacao que falha decide o motivo, e nada depois dela
        acontece. Os passos 1 a 4 nao leem nada: argumento ruim nao toca o
        banco, nao pergunta a ninguem e nao chama o servico (RN-AC-21).

        `como_chegou` e o nome como quem acionou o escreveu - o que volta no
        detalhe de ACAO_DESCONHECIDA. Pela barra, e o comando com hifen.
        """
        acao: Acao | None = None
        try:
            # 1. a acao existe
            acao = self._por_nome.get(nome) if isinstance(nome, str) else None
            if acao is None:
                return Resultado.falha(
                    MotivoFalha.ACAO_DESCONHECIDA, acao=str(como_chegou)[:_ECO_MAXIMO]
                )
            # 2. quem aciona pode (RN-AC-06): antes de qualquer outra coisa, e
            #    aqui, mesmo que a tela ja nao ofereca a acao
            if acionamento.chamador not in acao.chamadores:
                return Resultado.falha(
                    MotivoFalha.NAO_PERMITIDA, acao=acao.nome, chamador=acionamento.chamador.value
                )
            # 3. o alvo tem o que o escopo exige (RN-AC-10)
            falta = _falta_no_alvo(acao.escopo, alvo)
            if falta is not None:
                return Resultado.falha(MotivoFalha.ALVO_AUSENTE, falta=falta)
            # 4. os argumentos (RN-AC-16..20)
            try:
                convertidos = MappingProxyType(argumentos_de(acao))
            except ArgumentoRecusado as recusa:
                return Resultado.falha(MotivoFalha.ARGUMENTO_INVALIDO, **recusa.detalhe())
            # 5. as referencias existem (G2): le o ambiente aberto, nao muda nada
            referencias = await self._achar_referencias(acao, alvo, convertidos)
            # 6. a confirmacao, se a politica exigir (RN-AC-27, RN-AC-28)
            if exige_aprovacao(acionamento.chamador):
                pedido = PedidoDeConfirmacao(acao.nome, acionamento, alvo, convertidos, referencias)
                try:
                    resposta = await self._confirmacao.confirmar(pedido)
                except Exception as erro:
                    # R-CG5-5: a porta tem tratamento proprio. QUALQUER erro
                    # dela e falha inesperada - um ErroDePersistencia vindo da
                    # tela nao e falha de armazenamento desta acao.
                    _registrar_inesperada(acao.nome, acionamento, erro)
                    return Resultado.falha(MotivoFalha.FALHA_INESPERADA)
                if resposta is not True:  # so True confirma (RN-AC-30)
                    return Resultado.falha(MotivoFalha.RECUSADA)  # nada foi escrito (RN-AC-33)
                convertidos = pedido.argumentos  # o que executa e o que foi mostrado
            # 7. a execucao
            dado = await acao.efetivar(self._servico, alvo, convertidos, referencias, acionamento)
            return Resultado.ok(dado)
        except Exception as erro:
            resultado = _traduzir(erro)
            if resultado is None:
                _registrar_inesperada(acao.nome if acao else "?", acionamento, erro)
                resultado = Resultado.falha(MotivoFalha.FALHA_INESPERADA)
            return resultado
        # Cancelamento (CancelledError) e interrupcao nao sao Exception: passam
        # sem ser tocados, e nada depois do ponto em que chegaram executa.

    async def _achar_referencias(
        self, acao: Acao, alvo: Alvo, argumentos: Mapping[str, object]
    ) -> Referencias:
        """Passo 5. O servico devolve o mesmo objeto aberto (RN-A-03), e a trava
        de U4 e pega e solta dentro desta leitura: na espera da confirmacao,
        nenhuma trava esta presa (RN-AC-32).

        Inexistente levanta o erro de U4, e a tabela o traduz - um caminho so
        para o passo 5 e o passo 7.
        """
        ambiente = await self._servico.carregar_ambiente(alvo.id_ambiente)
        if acao.escopo is Escopo.AMBIENTE:
            return Referencias()
        if acao.escopo is Escopo.FRENTE:
            return Referencias(frente=achar_frente(ambiente, alvo.id_frente))
        if acao.escopo is Escopo.SESSAO:
            frente, tarefa, sessao = achar_sessao(ambiente, alvo.id_sessao)
            return Referencias(frente=frente, tarefa=tarefa, sessao=sessao)
        frente, tarefa = achar_tarefa(ambiente, alvo.id_tarefa)
        etapa = None
        for parametro in acao.parametros:
            if parametro.tipo is TipoParametro.POSICAO and parametro.nome in argumentos:
                posicao = argumentos[parametro.nome]
                if posicao > len(tarefa.etapas):
                    raise _PosicaoAlemDoFim(posicao, len(tarefa.etapas))
                etapa = EtapaNaPosicao(tarefa.etapas[posicao - 1], posicao)
        return Referencias(frente=frente, tarefa=tarefa, etapa=etapa)


def _falta_no_alvo(escopo: Escopo, alvo: Alvo) -> str | None:
    """RN-AC-10: o que o escopo exige e nao veio. Identidades alem das exigidas
    sao ignoradas."""
    if alvo.id_ambiente is None:
        return "ambiente"
    if escopo is Escopo.FRENTE and alvo.id_frente is None:
        return "frente"
    if escopo is Escopo.TAREFA and alvo.id_tarefa is None:
        return "tarefa"
    if escopo is Escopo.SESSAO and alvo.id_sessao is None:
        return "sessao"
    return None
