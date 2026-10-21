"""O modelo simplificado que PBT-06 pede, e o interprete dos comandos gerados.

`ModeloDeAmbientes` e o que deveria estar no disco, escrito do jeito mais
ingenuo possivel: listas na ordem de criacao, sem versao, sem carimbo de tempo
e sem identidade de chat. Ele PREVE o resultado de cada chamada - sucesso ou o
tipo do erro - e, no sucesso, aplica o efeito. `projetar` poe um Ambiente de
verdade na mesma forma, e a propriedade compara os dois depois de cada passo.

A previsao segue a ordem em que o servico verifica: o ambiente primeiro
(abrir), depois o agente (resolvido dentro da intencao, antes do alvo), depois
o alvo, e por ultimo o dominio (nome).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from fishingrod.aplicacao.portas.persistencia import AmbienteInexistente, ErroDePersistencia
from fishingrod.aplicacao.portas.wiki import ErroDeWiki
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    AgenteDesconhecido,
    EtapaInexistente,
    ErroDeServicoDeAmbiente,
    FrenteInexistente,
    ServicoDeAmbiente,
    SessaoInexistente,
    TarefaInexistente,
)
from fishingrod.dominio import Ambiente, ErroDeDominio, ExecutorEtapa, Identidade, NomeInvalido
from tests.ambiente.estrategias import BIBLIOTECARIO, ORQUESTRADOR

# --------------------------------------------------------------------------
# A forma simplificada
# --------------------------------------------------------------------------


@dataclass
class EtapaModelo:
    id: Identidade
    descricao: str
    executor: ExecutorEtapa
    concluida: bool = False


@dataclass
class SessaoModelo:
    id: Identidade
    nome: str
    chats: list[tuple[str, str]] = field(default_factory=list)  # (agente, nome do chat)
    anotacoes: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # chave -> (autor, valor)


@dataclass
class TarefaModelo:
    id: Identidade
    nome: str
    sessoes: list[SessaoModelo] = field(default_factory=list)
    etapas: list[EtapaModelo] = field(default_factory=list)


@dataclass
class FrenteModelo:
    id: Identidade
    nome: str
    tarefas: list[TarefaModelo] = field(default_factory=list)


@dataclass
class AmbienteModelo:
    id: Identidade
    nome: str
    frentes: list[FrenteModelo] = field(default_factory=list)

    def tarefas(self) -> list[TarefaModelo]:
        return [tarefa for frente in self.frentes for tarefa in frente.tarefas]

    def sessoes(self) -> list[SessaoModelo]:
        return [sessao for tarefa in self.tarefas() for sessao in tarefa.sessoes]

    def etapas(self) -> list[EtapaModelo]:
        return [etapa for tarefa in self.tarefas() for etapa in tarefa.etapas]


def projetar(ambiente: Ambiente) -> AmbienteModelo:
    """Um Ambiente de verdade na forma do modelo."""
    return AmbienteModelo(
        id=ambiente.id,
        nome=ambiente.nome,
        frentes=[
            FrenteModelo(
                id=frente.id,
                nome=frente.nome,
                tarefas=[
                    TarefaModelo(
                        id=tarefa.id,
                        nome=tarefa.nome,
                        sessoes=[
                            SessaoModelo(
                                id=sessao.id,
                                nome=sessao.nome,
                                chats=[(chat.agente.nome, chat.nome) for chat in sessao.chats],
                                anotacoes={
                                    chave: [(anotacao.autor, anotacao.valor) for anotacao in lista]
                                    for chave, lista in sessao.memoria.anotacoes.items()
                                },
                            )
                            for sessao in tarefa.sessoes
                        ],
                        etapas=[
                            EtapaModelo(etapa.id, etapa.descricao, etapa.executor, etapa.concluida)
                            for etapa in tarefa.etapas
                        ],
                    )
                    for tarefa in frente.tarefas
                ],
            )
            for frente in ambiente.frentes
        ],
    )


def _nome_valido(texto: str) -> bool:
    return bool(texto.strip())  # RN-02 de U1, como exigir_texto


# --------------------------------------------------------------------------
# Do comando gerado a chamada concreta
# --------------------------------------------------------------------------

# Que tipo de alvo cada operacao recebe.
_ALVO = {
    "criar_tarefa": "frente",
    "criar_sessao": "tarefa",
    "criar_chat": "sessao",
    "criar_etapa": "tarefa",
    "anotar_memoria": "sessao",
    "concluir_etapa": "etapa",
}


@dataclass(frozen=True)
class Chamada:
    operacao: str
    id_ambiente: Identidade | None
    id_alvo: Identidade | None
    argumentos: tuple


def _escolher(ids: list[Identidade], seletor: int | None) -> Identidade:
    if seletor is None or not ids:
        return Identidade.nova()  # um id que nao existe em lugar nenhum
    return ids[seletor % len(ids)]


def resolver(
    comando: tuple, ambientes: list[Identidade], vistas: Mapping[Identidade, AmbienteModelo]
) -> Chamada:
    """Traduz os seletores em ids.

    `ambientes` sao os ids que o teste conhece (inclusive os ja apagados, que
    devem dar AmbienteInexistente). `vistas` e o que QUEM CHAMA enxerga de cada
    ambiente - e dela que saem os alvos (R-CG4-3). Ambiente sem vista nao
    existe para quem chama: todo alvo nele vira um id novo.
    """
    operacao, seletor_ambiente, seletor_alvo, *argumentos = comando
    id_ambiente = None if operacao in ("criar_ambiente", "listar_ambientes") else _escolher(
        ambientes, seletor_ambiente
    )
    id_alvo = None
    tipo = _ALVO.get(operacao)
    if tipo is not None:
        vista = vistas.get(id_ambiente)
        if vista is None:
            candidatos = []
        elif tipo == "frente":
            candidatos = [frente.id for frente in vista.frentes]
        elif tipo == "tarefa":
            candidatos = [tarefa.id for tarefa in vista.tarefas()]
        elif tipo == "sessao":
            candidatos = [sessao.id for sessao in vista.sessoes()]
        else:
            candidatos = [etapa.id for etapa in vista.etapas()]
        id_alvo = _escolher(candidatos, seletor_alvo)
    return Chamada(operacao, id_ambiente, id_alvo, tuple(argumentos))


_OPERACOES = {
    "criar_ambiente": lambda s, c: s.criar_ambiente(*c.argumentos),
    "carregar_ambiente": lambda s, c: s.carregar_ambiente(c.id_ambiente),
    "listar_ambientes": lambda s, c: s.listar_ambientes(),
    "apagar_ambiente": lambda s, c: s.apagar_ambiente(c.id_ambiente),
    "criar_frente": lambda s, c: s.criar_frente(c.id_ambiente, *c.argumentos),
    "criar_tarefa": lambda s, c: s.criar_tarefa(c.id_ambiente, c.id_alvo, *c.argumentos),
    "criar_sessao": lambda s, c: s.criar_sessao(c.id_ambiente, c.id_alvo, *c.argumentos),
    "criar_chat": lambda s, c: s.criar_chat(c.id_ambiente, c.id_alvo, *c.argumentos),
    "criar_etapa": lambda s, c: s.criar_etapa(c.id_ambiente, c.id_alvo, *c.argumentos),
    "concluir_etapa": lambda s, c: s.concluir_etapa(c.id_ambiente, c.id_alvo),
    "anotar_memoria": lambda s, c: s.anotar_memoria(c.id_ambiente, c.id_alvo, *c.argumentos),
}

# O que pode sair do servico como resposta. Qualquer outra excecao - TypeError,
# KeyError, AttributeError - e defeito, e deve derrubar o teste.
ERROS_ESPERAVEIS = (ErroDeDominio, ErroDeServicoDeAmbiente, ErroDePersistencia, ErroDeWiki)


async def chamar(servico: ServicoDeAmbiente, chamada: Chamada) -> tuple[Any, Exception | None]:
    try:
        return await _OPERACOES[chamada.operacao](servico, chamada), None
    except ERROS_ESPERAVEIS as erro:
        return None, erro


# --------------------------------------------------------------------------
# O modelo
# --------------------------------------------------------------------------


@dataclass
class ModeloDeAmbientes:
    """Os ambientes que deveriam existir no disco, por id."""

    ambientes: dict[Identidade, AmbienteModelo] = field(default_factory=dict)

    def acrescentar(self, ambiente: Ambiente) -> None:
        self.ambientes[ambiente.id] = projetar(ambiente)

    # --- previsao -------------------------------------------------------

    def prever(self, chamada: Chamada) -> type[Exception] | None:
        """O tipo do erro que o servico deve levantar, ou None para sucesso."""
        operacao, argumentos = chamada.operacao, chamada.argumentos

        if operacao == "criar_ambiente":
            # Os comandos so geram esquemas validos; o caso hostil e de PBT-U4-03.
            return None if _nome_valido(argumentos[0]) else NomeInvalido
        if operacao == "listar_ambientes":
            return None

        ambiente = self.ambientes.get(chamada.id_ambiente)
        if ambiente is None:
            return AmbienteInexistente
        if operacao in ("carregar_ambiente", "apagar_ambiente"):
            return None
        if operacao == "criar_frente":
            return None if _nome_valido(argumentos[0]) else NomeInvalido

        if operacao == "criar_chat" and argumentos[0] != BIBLIOTECARIO.nome:
            return AgenteDesconhecido

        if operacao == "criar_tarefa":
            if self._frente(ambiente, chamada.id_alvo) is None:
                return FrenteInexistente
            return None if _nome_valido(argumentos[0]) else NomeInvalido
        if operacao == "concluir_etapa":
            return None if self._etapa(ambiente, chamada.id_alvo) is not None else EtapaInexistente

        if operacao in ("criar_chat", "anotar_memoria"):
            if self._sessao(ambiente, chamada.id_alvo) is None:
                return SessaoInexistente
            if operacao == "criar_chat":
                nome = argumentos[1]
                return None if nome == "" or _nome_valido(nome) else NomeInvalido
            chave, _, autor = argumentos
            return None if _nome_valido(chave) and _nome_valido(autor) else NomeInvalido

        if self._tarefa(ambiente, chamada.id_alvo) is None:
            return TarefaInexistente
        if operacao == "criar_sessao":
            nome = argumentos[0]
            return None if nome == "" or _nome_valido(nome) else NomeInvalido
        if operacao == "criar_etapa":
            return None if _nome_valido(argumentos[0]) else NomeInvalido
        raise AssertionError(f"operacao sem previsao: {operacao}")

    # --- efeito ---------------------------------------------------------

    def aplicar(self, chamada: Chamada, devolvido: Any) -> None:
        """O efeito de uma chamada que deu certo. Os ids vem do objeto que o
        servico devolveu: o modelo nao tem como sabe-los antes."""
        operacao, argumentos = chamada.operacao, chamada.argumentos

        if operacao == "criar_ambiente":
            self.ambientes[devolvido.id] = AmbienteModelo(devolvido.id, argumentos[0])
            return
        if operacao in ("carregar_ambiente", "listar_ambientes"):
            return
        if operacao == "apagar_ambiente":
            del self.ambientes[chamada.id_ambiente]
            return

        ambiente = self.ambientes[chamada.id_ambiente]
        if operacao == "criar_frente":
            ambiente.frentes.append(FrenteModelo(devolvido.id, argumentos[0]))
        elif operacao == "criar_tarefa":
            self._frente(ambiente, chamada.id_alvo).tarefas.append(
                TarefaModelo(
                    devolvido.id,
                    argumentos[0],
                    sessoes=[
                        SessaoModelo(
                            devolvido.sessoes[0].id,
                            "sessão 1",
                            chats=[(ORQUESTRADOR.nome, ORQUESTRADOR.nome)],  # RN-A-21
                        )
                    ],
                )
            )
        elif operacao == "criar_sessao":
            tarefa = self._tarefa(ambiente, chamada.id_alvo)
            nome = argumentos[0] or f"sessão {len(tarefa.sessoes) + 1}"
            tarefa.sessoes.append(
                SessaoModelo(devolvido.id, nome, chats=[(ORQUESTRADOR.nome, ORQUESTRADOR.nome)])
            )
        elif operacao == "criar_chat":
            nome = argumentos[1] or BIBLIOTECARIO.nome
            self._sessao(ambiente, chamada.id_alvo).chats.append((BIBLIOTECARIO.nome, nome))
        elif operacao == "criar_etapa":
            self._tarefa(ambiente, chamada.id_alvo).etapas.append(
                EtapaModelo(devolvido.id, argumentos[0], argumentos[1])
            )
        elif operacao == "concluir_etapa":
            self._etapa(ambiente, chamada.id_alvo).concluida = True
        elif operacao == "anotar_memoria":
            chave, valor, autor = argumentos
            self._sessao(ambiente, chamada.id_alvo).anotacoes.setdefault(chave, []).append(
                (autor, valor)
            )
        else:
            raise AssertionError(f"operacao sem efeito: {operacao}")

    # --- busca ----------------------------------------------------------

    @staticmethod
    def _frente(ambiente: AmbienteModelo, id: Identidade | None) -> FrenteModelo | None:
        return next((f for f in ambiente.frentes if f.id == id), None)

    @staticmethod
    def _tarefa(ambiente: AmbienteModelo, id: Identidade | None) -> TarefaModelo | None:
        return next((t for t in ambiente.tarefas() if t.id == id), None)

    @staticmethod
    def _sessao(ambiente: AmbienteModelo, id: Identidade | None) -> SessaoModelo | None:
        return next((s for s in ambiente.sessoes() if s.id == id), None)

    @staticmethod
    def _etapa(ambiente: AmbienteModelo, id: Identidade | None) -> EtapaModelo | None:
        return next((e for e in ambiente.etapas() if e.id == id), None)
