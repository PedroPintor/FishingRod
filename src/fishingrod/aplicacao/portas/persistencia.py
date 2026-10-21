"""Porta de persistencia: o contrato, os tipos de fronteira e os erros.

Este e o unico arquivo de U2 que as outras unidades importam. U4, U7, U8 e o
composition root de U9 dependem daqui - nunca de `adaptadores/persistencia`
(DP-P-11).

RN-P-16 / D-ARQ-04: nenhuma assinatura menciona sqlite3, cursor, conexao, SQL ou
nome de tabela. Se mencionasse, a abstracao seria decorativa. Por isso este
modulo tambem nao importa `sqlite3` nem `json`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fishingrod.dominio import Ambiente, Anotacao, Identidade


# --------------------------------------------------------------------------
# Erros (DP-P-11)
# --------------------------------------------------------------------------
# Moram aqui, ao lado do Protocol, e nao em dominio/erros.py: NomeInvalido diz
# que o usuario digitou algo invalido; ConflitoDeVersao diz que dois processos
# escreveram ao mesmo tempo. So um dos dois e assunto do dominio.


class ErroDePersistencia(Exception):
    """Raiz da hierarquia. Quem quiser tratar tudo captura esta."""


class ConflitoDeVersao(ErroDePersistencia):
    """RN-P-05: a versao em disco avancou desde a leitura.

    Quem chamou recarrega, reaplica a mudanca e salva de novo. O adaptador NAO
    faz isso por conta propria: ele tem o Ambiente que lhe entregaram, nao a
    intencao de quem o modificou (DP-P-13).
    """


class EsquemaIncompativel(ErroDePersistencia):
    """DP-P-07: versao maior que a suportada, no esquema fisico ou no documento.

    Nunca "tenta assim mesmo" - interpretar campos que nao se entende e como a
    corrupcao silenciosa comeca.
    """


class BancoIlegivel(ErroDePersistencia):
    """NFR-P-07: arquivo corrompido ou inacessivel.

    Levantada na abertura, antes de qualquer tela subir (DP-P-01).
    """


class AmbienteInexistente(ErroDePersistencia):
    """anotar ou inserir_mensagem sobre um ambiente que nao existe.

    [Emenda 2026-08-27 / Code Generation] Nao estava no desenho: apareceu quando
    PBT-U2-04 tentou inserir mensagem num ambiente nunca salvo e o adaptador
    real deixou sqlite3.IntegrityError vazar pela porta - a chave estrangeira
    que existe para a cascata de RN-P-20 tambem torna o ambiente uma
    pre-condicao. Sem este erro, o vocabulario da porta seria furado (NFR-P-16)
    e as duas implementacoes discordariam (RN-P-26).
    """


class MensagemInexistente(ErroDePersistencia):
    """atualizar_mensagem sobre um id que nao existe.

    Aqui a ausencia E defeito, ao contrario de carregar_ambiente (RN-P-04): so
    se atualiza a mensagem que se acabou de inserir.
    """


# --------------------------------------------------------------------------
# Tipos de fronteira (domain-entities.md 6)
# --------------------------------------------------------------------------
# Nao sao entidades de dominio: sao o vocabulario da porta. Vivem aqui porque o
# dominio nao sabe que existe disco.


@dataclass(frozen=True)
class UsoDeFerramenta:
    """Uma chamada de ferramenta feita dentro de uma mensagem.

    Sem `resultado_resumo` [emenda 2026-08-26 / NFR Q6]: no stream do SDK o
    resultado nao existe no instante do evento de uso, e nenhuma unidade tem
    desenhada a correlacao chamada-resultado. A coluna era nao-preenchivel.
    """

    tool: str
    args_resumo: str
    criado_em: datetime


@dataclass(frozen=True)
class MensagemPersistida:
    """Uma linha da transcricao, com os usos de ferramenta que pertencem a ela."""

    id: Identidade
    id_chat: Identidade
    papel: str
    texto: str
    em_andamento: bool
    criada_em: datetime
    usos_de_ferramenta: tuple[UsoDeFerramenta, ...] = ()


@dataclass(frozen=True)
class ResumoAmbiente:
    """O que a tela inicial precisa para deixar escolher qual ambiente abrir.

    RN-P-24: listar nao desserializa documento algum - e uma tela de escolha,
    nao uma carga.
    """

    id: Identidade
    nome: str
    atualizado_em: datetime


# --------------------------------------------------------------------------
# O contrato
# --------------------------------------------------------------------------


class PortaPersistencia(Protocol):
    """As nove operacoes. Semantica completa em business-logic-model.md 2."""

    # --- ambiente (documento) ---

    async def salvar_ambiente(self, ambiente: Ambiente) -> None:
        """Grava o documento se a versao em disco for a que o ambiente carrega.

        Sucesso incrementa a versao no disco E no objeto (RN-P-06). Divergencia
        levanta ConflitoDeVersao e nada e gravado (RN-P-05).

        NAO escreve nem apaga anotacao alguma (RN-P-08): memoria entra pela
        porta de anotar e sai pela carga.
        """
        ...

    async def carregar_ambiente(self, id: Identidade) -> Ambiente | None:
        """Reconstitui o ambiente inteiro, com toda a memoria de todas as
        sessoes (RN-P-11).

        Id inexistente devolve None, nao levanta (RN-P-04): ausencia e
        resultado, nao erro.
        """
        ...

    async def listar_ambientes(self) -> list[ResumoAmbiente]:
        """Do mais recentemente atualizado para o mais antigo (RN-P-24)."""
        ...

    async def apagar_ambiente(self, id: Identidade) -> None:
        """Remove o ambiente e tudo que pende dele, sem deixar orfao (RN-P-20).

        NAO toca no disco da wiki (RN-P-21) e nao pergunta nada (RN-P-23). Id
        inexistente e operacao vazia bem-sucedida (RN-P-22).
        """
        ...

    # --- memoria (tabela, append-only) ---

    async def anotar(
        self,
        id_ambiente: Identidade,
        id_sessao: Identidade,
        chave: str,
        anotacao: Anotacao,
    ) -> None:
        """Acrescenta uma anotacao. Nunca levanta ConflitoDeVersao e nunca altera
        Ambiente.versao (RN-P-07).

        Duas anotacoes concorrentes na mesma sessao sobrevivem ambas. E o ponto
        da decisao de tirar a memoria do documento.
        """
        ...

    # --- transcricao (tabela) ---

    async def inserir_mensagem(
        self,
        id_ambiente: Identidade,
        id_chat: Identidade,
        papel: str,
        texto: str,
        em_andamento: bool,
    ) -> Identidade:
        """Insere e devolve a identidade gerada - que e tambem a posicao
        cronologica (RN-P-12).

        E esse id que U7 guarda para chamar atualizar_mensagem durante o
        streaming.
        """
        ...

    async def atualizar_mensagem(
        self, id_mensagem: Identidade, texto: str, em_andamento: bool
    ) -> None:
        """Altera apenas texto e em_andamento (RN-P-18).

        Nao muda id, id_chat, papel nem criada_em - o que preserva a ordem da
        transcricao durante o streaming. Id inexistente levanta
        MensagemInexistente.
        """
        ...

    async def registrar_uso_ferramenta(
        self, id_mensagem: Identidade, tool: str, args_resumo: str
    ) -> None:
        """Varias por mensagem sao normais (RN-P-19)."""
        ...

    async def listar_mensagens(
        self,
        id_chat: Identidade,
        limite: int,
        antes_de: Identidade | None = None,
    ) -> list[MensagemPersistida]:
        """As `limite` mais recentes, em ordem crescente (RN-P-13).

        Com `antes_de`, as `limite` imediatamente anteriores aquele id
        (RN-P-14). A mais antiga da pagina e o cursor da pagina seguinte; como
        UUIDv7 e unico e ordenavel, paginar nao repete nem pula.
        """
        ...
