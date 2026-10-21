"""RepositorioEmMemoria: um segundo enunciado do contrato (DP-P-10, Q4=A).

Escrito a mao, com dicionarios e listas. NAO usa sqlite3 em `:memory:`, e a
diferenca importa: se duble e real fossem o mesmo codigo, PBT-U2-08 passaria por
construcao e nao detectaria nada. Duas implementacoes independentes que
discordam revelam que o CONTRATO estava ambiguo - e e isso que se quer descobrir
antes de U4, U7 e U8 comecarem a depender dele.

Custo assumido: ~100 linhas a mais, e este arquivo pode ter bugs proprios. Um
bug aqui falha o teste de contrato, que e precisamente o trabalho dele.

RN-P-26: o falso e falso so no armazenamento. Ele TAMBEM levanta
ConflitoDeVersao, TAMBEM devolve None para id ausente e TAMBEM preserva
em_andamento. Duble que so faz o caminho feliz e duble que faz o teste mentir.
"""

import copy
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fishingrod.aplicacao.portas.persistencia import (
    AmbienteInexistente,
    ConflitoDeVersao,
    MensagemInexistente,
    MensagemPersistida,
    ResumoAmbiente,
    UsoDeFerramenta,
)
from fishingrod.dominio import Ambiente, Anotacao, Identidade


def _novo_id() -> str:
    return str(uuid.uuid7())


@dataclass
class _LinhaAmbiente:
    ambiente: Ambiente  # copia propria, com as memorias esvaziadas
    versao: int
    criado_em: datetime
    atualizado_em: datetime


@dataclass
class _LinhaAnotacao:
    id: str
    id_ambiente: str
    id_sessao: str
    chave: str
    anotacao: Anotacao


@dataclass
class _LinhaMensagem:
    id: str
    id_ambiente: str
    id_chat: str
    papel: str
    texto: str
    em_andamento: bool
    criada_em: datetime


@dataclass
class _LinhaUso:
    id: str
    id_mensagem: str
    tool: str
    args_resumo: str
    criado_em: datetime


@dataclass
class RepositorioEmMemoria:
    """Implementa PortaPersistencia sem disco nenhum."""

    _ambientes: dict[str, _LinhaAmbiente] = field(default_factory=dict)
    _anotacoes: list[_LinhaAnotacao] = field(default_factory=list)
    _mensagens: list[_LinhaMensagem] = field(default_factory=list)
    _usos: list[_LinhaUso] = field(default_factory=list)

    async def fechar(self) -> None:
        """Existe para que o composition root trate os dois iguais."""

    def _exigir_ambiente(self, id_ambiente: Identidade) -> None:
        """O equivalente a chave estrangeira do real (emenda 2026-08-27)."""
        if id_ambiente.valor not in self._ambientes:
            raise AmbienteInexistente(f"nao existe ambiente [{id_ambiente.valor}]")

    # ----------------------------------------------------------------------
    # Ambiente
    # ----------------------------------------------------------------------

    async def salvar_ambiente(self, ambiente: Ambiente) -> None:
        linha = self._ambientes.get(ambiente.id.valor)
        agora = datetime.now(UTC)

        if linha is None:
            if ambiente.versao != 0:
                raise ConflitoDeVersao(
                    f"o ambiente [{ambiente.id.valor}] nao existe mais em memoria "
                    f"(o objeto carrega versao {ambiente.versao})"
                )
            self._ambientes[ambiente.id.valor] = _LinhaAmbiente(
                ambiente=self._copia_sem_memoria(ambiente),
                versao=1,
                criado_em=agora,
                atualizado_em=agora,
            )
            ambiente.versao = 1
            return

        if linha.versao != ambiente.versao:
            raise ConflitoDeVersao(
                f"a versao em memoria do ambiente [{ambiente.id.valor}] e "
                f"{linha.versao}; o objeto carrega {ambiente.versao}"
            )

        linha.ambiente = self._copia_sem_memoria(ambiente)
        linha.versao += 1
        linha.atualizado_em = agora
        ambiente.versao = linha.versao

    @staticmethod
    def _copia_sem_memoria(ambiente: Ambiente) -> Ambiente:
        """RN-P-08: salvar_ambiente nao escreve nem apaga anotacao alguma.

        A copia e o equivalente da serializacao do adaptador real: sem ela, o
        objeto do chamador e o "disco" seriam o mesmo objeto, e o duble
        esconderia justamente os erros que PBT-U2-01 procura.
        """
        copia = copy.deepcopy(ambiente)
        for frente in copia.frentes:
            for tarefa in frente.tarefas:
                for sessao in tarefa.sessoes:
                    sessao.memoria.anotacoes = {}
                    sessao.memoria.versao = 0
        return copia

    async def carregar_ambiente(self, id: Identidade) -> Ambiente | None:
        linha = self._ambientes.get(id.valor)
        if linha is None:
            return None  # RN-P-04

        ambiente = copy.deepcopy(linha.ambiente)
        ambiente.versao = linha.versao

        sessoes = {
            sessao.id.valor: sessao
            for frente in ambiente.frentes
            for tarefa in frente.tarefas
            for sessao in tarefa.sessoes
        }
        # RN-P-10: a lista esta na ordem de escrita, e e essa a ordem que volta.
        for anotada in self._anotacoes:
            if anotada.id_ambiente != id.valor:
                continue
            sessao = sessoes.get(anotada.id_sessao)
            if sessao is None:
                continue
            sessao.memoria.anotacoes.setdefault(anotada.chave, []).append(
                anotada.anotacao
            )
            sessao.memoria.versao += 1

        return ambiente

    async def listar_ambientes(self) -> list[ResumoAmbiente]:
        linhas = sorted(
            self._ambientes.values(),
            key=lambda linha: (linha.atualizado_em, linha.ambiente.id.valor),
            reverse=True,
        )
        return [
            ResumoAmbiente(
                id=linha.ambiente.id,
                nome=linha.ambiente.nome,
                atualizado_em=linha.atualizado_em,
            )
            for linha in linhas
        ]

    async def apagar_ambiente(self, id: Identidade) -> None:
        # RN-P-22: id inexistente e operacao vazia bem-sucedida.
        self._ambientes.pop(id.valor, None)

        # A cascata, feita a mao - o que o real recebe de graca do
        # ON DELETE CASCADE com foreign_keys = ON.
        self._anotacoes = [a for a in self._anotacoes if a.id_ambiente != id.valor]
        apagadas = {m.id for m in self._mensagens if m.id_ambiente == id.valor}
        self._mensagens = [m for m in self._mensagens if m.id_ambiente != id.valor]
        self._usos = [u for u in self._usos if u.id_mensagem not in apagadas]

    # ----------------------------------------------------------------------
    # Memoria
    # ----------------------------------------------------------------------

    async def anotar(
        self,
        id_ambiente: Identidade,
        id_sessao: Identidade,
        chave: str,
        anotacao: Anotacao,
    ) -> None:
        # RN-P-07: nao compara versao e nao levanta ConflitoDeVersao. A unica
        # leitura e a pre-condicao do ambiente, que no real vem da chave
        # estrangeira.
        self._exigir_ambiente(id_ambiente)
        self._anotacoes.append(
            _LinhaAnotacao(
                id=_novo_id(),
                id_ambiente=id_ambiente.valor,
                id_sessao=id_sessao.valor,
                chave=chave,
                anotacao=anotacao,
            )
        )

    # ----------------------------------------------------------------------
    # Transcricao
    # ----------------------------------------------------------------------

    async def inserir_mensagem(
        self,
        id_ambiente: Identidade,
        id_chat: Identidade,
        papel: str,
        texto: str,
        em_andamento: bool,
    ) -> Identidade:
        self._exigir_ambiente(id_ambiente)
        id_mensagem = _novo_id()
        self._mensagens.append(
            _LinhaMensagem(
                id=id_mensagem,
                id_ambiente=id_ambiente.valor,
                id_chat=id_chat.valor,
                papel=papel,
                texto=texto,
                em_andamento=em_andamento,
                criada_em=datetime.now(UTC),
            )
        )
        return Identidade(id_mensagem)

    async def atualizar_mensagem(
        self, id_mensagem: Identidade, texto: str, em_andamento: bool
    ) -> None:
        for mensagem in self._mensagens:
            if mensagem.id == id_mensagem.valor:
                # RN-P-18: so estes dois campos.
                mensagem.texto = texto
                mensagem.em_andamento = em_andamento
                return
        raise MensagemInexistente(f"nao existe mensagem [{id_mensagem.valor}]")

    async def registrar_uso_ferramenta(
        self, id_mensagem: Identidade, tool: str, args_resumo: str
    ) -> None:
        if not any(m.id == id_mensagem.valor for m in self._mensagens):
            raise MensagemInexistente(f"nao existe mensagem [{id_mensagem.valor}]")
        self._usos.append(
            _LinhaUso(
                id=_novo_id(),
                id_mensagem=id_mensagem.valor,
                tool=tool,
                args_resumo=args_resumo,
                criado_em=datetime.now(UTC),
            )
        )

    async def listar_mensagens(
        self,
        id_chat: Identidade,
        limite: int,
        antes_de: Identidade | None = None,
    ) -> list[MensagemPersistida]:
        # UUIDv7 em texto canonico ordena lexicograficamente na mesma ordem em
        # que ordena cronologicamente - e a mesma comparacao que o SQLite faz
        # com `id < ?` sobre TEXT.
        candidatas = sorted(
            (m for m in self._mensagens if m.id_chat == id_chat.valor),
            key=lambda m: m.id,
        )
        if antes_de is not None:
            candidatas = [m for m in candidatas if m.id < antes_de.valor]

        pagina = candidatas[-limite:] if limite > 0 else []

        return [
            MensagemPersistida(
                id=Identidade(m.id),
                id_chat=Identidade(m.id_chat),
                papel=m.papel,
                texto=m.texto,
                em_andamento=m.em_andamento,
                criada_em=m.criada_em,
                usos_de_ferramenta=tuple(
                    UsoDeFerramenta(
                        tool=u.tool, args_resumo=u.args_resumo, criado_em=u.criado_em
                    )
                    for u in sorted(
                        (u for u in self._usos if u.id_mensagem == m.id),
                        key=lambda u: u.id,
                    )
                ),
            )
            for m in pagina
        ]
