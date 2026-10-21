"""RepositorioSQLite: a implementacao real da porta de persistencia.

A leitura deste arquivo tem uma ordem: primeiro a fabrica (DP-P-01), depois os
dois auxiliares de transacao (DP-P-03), e so entao as nove operacoes. Nenhuma
operacao abre transacao por conta propria - todas recebem um cursor de um dos
auxiliares e nao sabem o que e Lock, thread ou COMMIT. E isso que torna RN-P-03
estrutura em vez de disciplina.
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from fishingrod.adaptadores.persistencia import esquema as esq
from fishingrod.adaptadores.persistencia import mapeamento
from fishingrod.aplicacao.portas.persistencia import (
    AmbienteInexistente,
    BancoIlegivel,
    ConflitoDeVersao,
    EsquemaIncompativel,
    MensagemInexistente,
    MensagemPersistida,
    ResumoAmbiente,
    UsoDeFerramenta,
)
from fishingrod.dominio import Ambiente, Anotacao, Identidade

T = TypeVar("T")

# DP-P-09: destino nenhum e configurado aqui - isso e do composition root de U9.
_log = logging.getLogger("fishingrod.persistencia")
_log.addHandler(logging.NullHandler())


# --------------------------------------------------------------------------
# Fabrica (DP-P-01)
# --------------------------------------------------------------------------


async def abrir_repositorio(caminho: Path) -> "RepositorioSQLite":
    """A unica forma legitima de obter um repositorio.

    Quem instanciar RepositorioSQLite a mao sem passar por aqui recebe um objeto
    que nao funciona, e descobre isso na primeira chamada - nao tres telas
    adiante.

    E este passo que faz NFR-P-07 acontecer na INICIALIZACAO: com abertura
    preguicosa, um banco corrompido so apareceria depois da TUI ja ter subido, e
    a unica resposta possivel seria uma caixa de dialogo dizendo que o programa
    nao devia ter aberto.
    """
    return await asyncio.to_thread(_abrir_sync, caminho)


def _abrir_sync(caminho: Path) -> "RepositorioSQLite":
    caminho = Path(caminho)
    _preparar_diretorio(caminho.parent)

    try:
        conexao = sqlite3.connect(
            caminho,
            check_same_thread=False,  # o acesso e serializado pelo Lock (NFR-P-09)
            isolation_level=None,  # DP-P-02: nenhuma transacao implicita
        )
    except sqlite3.Error as erro:
        raise BancoIlegivel(f"nao foi possivel abrir [{caminho}]: {erro}") from erro

    try:
        _restringir_permissao(caminho)
        esq.aplicar_pragmas(conexao)
        esq.criar_esquema(conexao)
        esq.verificar_versao_fisica(conexao)
    except EsquemaIncompativel:
        conexao.close()
        raise
    except sqlite3.Error as erro:
        conexao.close()
        raise BancoIlegivel(f"o arquivo [{caminho}] nao e um banco valido: {erro}") from erro
    except Exception:
        conexao.close()
        raise

    return RepositorioSQLite(conexao)


def _preparar_diretorio(diretorio: Path) -> None:
    """DP-P-08: o diretorio e a protecao real."""
    diretorio.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(diretorio, 0o700)


def _restringir_permissao(caminho: Path) -> None:
    """DP-P-08: confirmacao no arquivo do banco.

    Os arquivos -wal e -shm NAO recebem chmod: eles nascem e morrem durante a
    execucao, entao qualquer garantia dada numa abertura nao vale na seguinte.
    Quem os protege e o diretorio 0o700.

    Em Windows o chmod do Python so mexe no bit de somente-leitura e nao
    expressa nada disso; a raiz %LOCALAPPDATA% ja e privada ao usuario.
    """
    if os.name != "nt":
        os.chmod(caminho, 0o600)


# --------------------------------------------------------------------------
# Auxiliares de tempo
# --------------------------------------------------------------------------


def _agora() -> str:
    return datetime.now(UTC).isoformat()


def _data(texto: str) -> datetime:
    return datetime.fromisoformat(texto)


def _novo_id() -> str:
    """UUIDv7: a identidade E a ordem cronologica (ESC-14, RN-P-12)."""
    return str(uuid.uuid7())


class RepositorioSQLite:
    """Implementa PortaPersistencia sobre uma conexao ja aberta e ja pragmada."""

    def __init__(self, conexao: sqlite3.Connection) -> None:
        self._conexao = conexao
        # NFR-P-09: uma conexao, um Lock. Serializa as corrotinas do processo
        # antes que elas cheguem ao driver.
        self._lock = asyncio.Lock()

    async def fechar(self) -> None:
        """Fecha a conexao. Sem __del__ e sem finalizador: quem abre e fecha e o
        composition root de U9, e e a unica coisa que faz isso."""
        async with self._lock:
            await asyncio.to_thread(self._conexao.close)

    # ----------------------------------------------------------------------
    # Transacao (DP-P-02, DP-P-03, DP-P-04)
    # ----------------------------------------------------------------------

    async def _ler(self, fn: Callable[[sqlite3.Cursor], T]) -> T:
        """BEGIN diferido. Leitura nao disputa trava de escrita."""
        async with self._lock:
            return await asyncio.to_thread(self._em_transacao, fn, "BEGIN")

    async def _escrever(self, fn: Callable[[sqlite3.Cursor], T]) -> T:
        """BEGIN IMMEDIATE - e aqui que NFR-P-10 encontra NFR-P-11.

        Em WAL, uma transacao aberta com BEGIN simples que le primeiro e escreve
        depois nao consegue subir para escritora se outro processo ja segurou a
        trava nesse meio-tempo: o SQLite devolve SQLITE_BUSY na hora, SEM
        consultar o busy_timeout, porque esperar ali seria arriscar impasse com
        o instantaneo de leitura ja fixado. salvar_ambiente e exatamente esse
        formato.

        IMMEDIATE pede a trava de escrita na abertura, onde o tempo de espera E
        respeitado. Sem esta linha, a segunda instancia do FishingRod falharia
        na cara do usuario em vez de esperar meio segundo.
        """
        async with self._lock:
            try:
                return await asyncio.to_thread(self._em_transacao, fn, "BEGIN IMMEDIATE")
            except ConflitoDeVersao as erro:
                # DP-P-09: esperado, U4 reabsorve recarregando e repetindo.
                _log.warning("conflito de versao ao gravar: %s", erro)
                raise
            except Exception:
                _log.exception("falha ao gravar")
                raise

    def _em_transacao(self, fn: Callable[[sqlite3.Cursor], T], inicio: str) -> T:
        """Tudo daqui para baixo e sincrono: a transacao comeca e termina dentro
        de um unico to_thread, sem ponto de await no meio onde outra corrotina
        pudesse intercalar (NFR-P-08).

        `inicio` e sempre uma constante deste modulo, nunca entrada externa.
        """
        cursor = self._conexao.cursor()
        cursor.execute(inicio)
        try:
            resultado = fn(cursor)
        except Exception:
            # DP-P-04: o caminho do erro e o mesmo caminho da transacao. E daqui
            # que sai a segunda metade de RN-P-05 - "e nada e gravado".
            if self._conexao.in_transaction:
                cursor.execute("ROLLBACK")
            raise
        cursor.execute("COMMIT")
        return resultado

    # ----------------------------------------------------------------------
    # Ambiente
    # ----------------------------------------------------------------------

    async def salvar_ambiente(self, ambiente: Ambiente) -> None:
        nova_versao = await self._escrever(lambda cur: self._salvar_sync(cur, ambiente))
        # RN-P-06: so depois do COMMIT. A instancia em memoria fica pronta para
        # a proxima gravacao sem recarregar.
        ambiente.versao = nova_versao

    def _salvar_sync(self, cursor: sqlite3.Cursor, ambiente: Ambiente) -> int:
        linha = cursor.execute(
            "SELECT versao FROM ambiente WHERE id = ?", (ambiente.id.valor,)
        ).fetchone()

        documento = json.dumps(mapeamento.documento_de(ambiente), ensure_ascii=False)
        agora = _agora()

        if linha is None:
            if ambiente.versao != 0:
                # Carregado e depois apagado por outra instancia. Inserir aqui
                # ressuscitaria um ambiente que alguem removeu de proposito.
                raise ConflitoDeVersao(
                    f"o ambiente [{ambiente.id.valor}] nao existe mais em disco "
                    f"(o objeto carrega versao {ambiente.versao})"
                )
            cursor.execute(
                "INSERT INTO ambiente "
                "(id, nome, versao, versao_esquema, documento, criado_em, atualizado_em) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    ambiente.id.valor,
                    ambiente.nome,
                    1,
                    esq.VERSAO_DOCUMENTO,
                    documento,
                    agora,
                    agora,
                ),
            )
            return 1

        versao_em_disco = int(linha[0])
        if versao_em_disco != ambiente.versao:
            raise ConflitoDeVersao(
                f"a versao em disco do ambiente [{ambiente.id.valor}] e "
                f"{versao_em_disco}; o objeto carrega {ambiente.versao}"
            )

        nova_versao = versao_em_disco + 1
        cursor.execute(
            "UPDATE ambiente SET nome = ?, versao = ?, versao_esquema = ?, "
            "documento = ?, atualizado_em = ? WHERE id = ?",
            (
                ambiente.nome,
                nova_versao,
                esq.VERSAO_DOCUMENTO,
                documento,
                agora,
                ambiente.id.valor,
            ),
        )
        return nova_versao

    async def carregar_ambiente(self, id: Identidade) -> Ambiente | None:
        return await self._ler(lambda cur: self._carregar_sync(cur, id))

    def _carregar_sync(self, cursor: sqlite3.Cursor, id: Identidade) -> Ambiente | None:
        linha = cursor.execute(
            "SELECT documento, versao, versao_esquema FROM ambiente WHERE id = ?",
            (id.valor,),
        ).fetchone()

        if linha is None:
            return None  # RN-P-04: ausencia e resultado, nao erro.

        documento, versao, versao_esquema = linha[0], int(linha[1]), int(linha[2])

        if versao_esquema > esq.VERSAO_DOCUMENTO:
            raise EsquemaIncompativel(
                f"o documento do ambiente [{id.valor}] esta na versao "
                f"{versao_esquema}; esta versao entende ate {esq.VERSAO_DOCUMENTO}"
            )

        ambiente = mapeamento.ambiente_de(json.loads(documento), versao)
        self._preencher_memoria(cursor, ambiente)
        return ambiente

    def _preencher_memoria(self, cursor: sqlite3.Cursor, ambiente: Ambiente) -> None:
        """RN-P-10 e RN-P-11: toda a memoria de todas as sessoes, na ordem em que
        foi escrita, e Memoria.versao igual ao total carregado.

        Uma consulta so para o ambiente inteiro - e por isso que o indice comeca
        em id_ambiente (R-CG-1). Nao existe memoria parcial: um agente que le o
        blackboard leu o blackboard inteiro.
        """
        sessoes = {
            sessao.id.valor: sessao
            for frente in ambiente.frentes
            for tarefa in frente.tarefas
            for sessao in tarefa.sessoes
        }
        if not sessoes:
            return

        linhas = cursor.execute(
            "SELECT id_sessao, chave, autor, valor, criada_em FROM anotacao "
            "WHERE id_ambiente = ? ORDER BY id",
            (ambiente.id.valor,),
        ).fetchall()

        for id_sessao, chave, autor, valor, criada_em in linhas:
            sessao = sessoes.get(id_sessao)
            if sessao is None:
                # Anotacao de uma sessao que saiu do documento. Nao ha para onde
                # devolve-la; a linha continua no banco (RN-P-09, append-only).
                continue
            memoria = sessao.memoria
            memoria.anotacoes.setdefault(chave, []).append(
                Anotacao(autor=autor, valor=valor, criada_em=_data(criada_em))
            )
            memoria.versao += 1

    async def listar_ambientes(self) -> list[ResumoAmbiente]:
        return await self._ler(self._listar_ambientes_sync)

    def _listar_ambientes_sync(self, cursor: sqlite3.Cursor) -> list[ResumoAmbiente]:
        """RN-P-24: colunas nomeadas, nunca `documento`. E uma tela de escolha,
        nao uma carga (NFR-P-02).

        `id DESC` no desempate deixa a ordem determinista quando dois ambientes
        sao gravados dentro do mesmo instante - o que acontece em teste gerado.
        """
        linhas = cursor.execute(
            "SELECT id, nome, atualizado_em FROM ambiente "
            "ORDER BY atualizado_em DESC, id DESC"
        ).fetchall()
        return [
            ResumoAmbiente(id=Identidade(id), nome=nome, atualizado_em=_data(atualizado))
            for id, nome, atualizado in linhas
        ]

    async def apagar_ambiente(self, id: Identidade) -> None:
        await self._escrever(lambda cur: self._apagar_sync(cur, id))

    def _apagar_sync(self, cursor: sqlite3.Cursor, id: Identidade) -> None:
        """RN-P-20: anotacoes, mensagens e usos vao junto por cascata - o que so
        acontece porque foreign_keys esta ON (esquema.aplicar_pragmas).

        RN-P-22: id inexistente e operacao vazia bem-sucedida.
        RN-P-21: nada no disco da wiki e tocado - isso e do servico de U4.
        """
        cursor.execute("DELETE FROM ambiente WHERE id = ?", (id.valor,))

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
        await self._escrever(
            lambda cur: self._anotar_sync(cur, id_ambiente, id_sessao, chave, anotacao)
        )

    def _anotar_sync(
        self,
        cursor: sqlite3.Cursor,
        id_ambiente: Identidade,
        id_sessao: Identidade,
        chave: str,
        anotacao: Anotacao,
    ) -> None:
        """Um INSERT. Nada e lido, nada e comparado (RN-P-07).

        E por isso que duas anotacoes simultaneas na mesma sessao vencem as
        duas. Se a memoria voltasse para dentro do documento, esta regra
        passaria a ser impossivel de cumprir.

        A unica leitura e a da pre-condicao: a anotacao pende de um ambiente que
        precisa existir. Verificar aqui e o que faz a falha chegar como
        AmbienteInexistente em vez de sqlite3.IntegrityError.
        """
        self._exigir_ambiente(cursor, id_ambiente)
        cursor.execute(
            "INSERT INTO anotacao "
            "(id, id_ambiente, id_sessao, chave, autor, valor, criada_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _novo_id(),
                id_ambiente.valor,
                id_sessao.valor,
                chave,
                anotacao.autor,
                anotacao.valor,
                anotacao.criada_em.isoformat(),
            ),
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
        id_mensagem = Identidade(_novo_id())
        await self._escrever(
            lambda cur: self._inserir_mensagem_sync(
                cur, id_mensagem, id_ambiente, id_chat, papel, texto, em_andamento
            )
        )
        return id_mensagem

    def _inserir_mensagem_sync(
        self,
        cursor: sqlite3.Cursor,
        id_mensagem: Identidade,
        id_ambiente: Identidade,
        id_chat: Identidade,
        papel: str,
        texto: str,
        em_andamento: bool,
    ) -> None:
        self._exigir_ambiente(cursor, id_ambiente)
        cursor.execute(
            "INSERT INTO mensagem "
            "(id, id_ambiente, id_chat, papel, texto, em_andamento, criada_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                id_mensagem.valor,
                id_ambiente.valor,
                id_chat.valor,
                papel,
                texto,
                int(em_andamento),
                _agora(),
            ),
        )

    @staticmethod
    def _exigir_ambiente(cursor: sqlite3.Cursor, id_ambiente: Identidade) -> None:
        """A chave estrangeira ja recusaria - mas recusaria com
        sqlite3.IntegrityError, que e vocabulario do driver e nao da porta."""
        existe = cursor.execute(
            "SELECT 1 FROM ambiente WHERE id = ?", (id_ambiente.valor,)
        ).fetchone()
        if existe is None:
            raise AmbienteInexistente(f"nao existe ambiente [{id_ambiente.valor}]")

    async def atualizar_mensagem(
        self, id_mensagem: Identidade, texto: str, em_andamento: bool
    ) -> None:
        await self._escrever(
            lambda cur: self._atualizar_mensagem_sync(cur, id_mensagem, texto, em_andamento)
        )

    def _atualizar_mensagem_sync(
        self,
        cursor: sqlite3.Cursor,
        id_mensagem: Identidade,
        texto: str,
        em_andamento: bool,
    ) -> None:
        """RN-P-18: apenas texto e em_andamento. Nao muda id, id_chat, papel nem
        criada_em - e o que preserva a ordem da transcricao durante o streaming.
        """
        cursor.execute(
            "UPDATE mensagem SET texto = ?, em_andamento = ? WHERE id = ?",
            (texto, int(em_andamento), id_mensagem.valor),
        )
        if cursor.rowcount == 0:
            raise MensagemInexistente(f"nao existe mensagem [{id_mensagem.valor}]")

    async def registrar_uso_ferramenta(
        self, id_mensagem: Identidade, tool: str, args_resumo: str
    ) -> None:
        await self._escrever(
            lambda cur: self._registrar_uso_sync(cur, id_mensagem, tool, args_resumo)
        )

    def _registrar_uso_sync(
        self,
        cursor: sqlite3.Cursor,
        id_mensagem: Identidade,
        tool: str,
        args_resumo: str,
    ) -> None:
        """A verificacao de existencia e explicita, e nao deixada para a chave
        estrangeira: assim a falha chega como MensagemInexistente, do vocabulario
        da porta, e o duble e o real erram igual (RN-P-26).
        """
        existe = cursor.execute(
            "SELECT 1 FROM mensagem WHERE id = ?", (id_mensagem.valor,)
        ).fetchone()
        if existe is None:
            raise MensagemInexistente(f"nao existe mensagem [{id_mensagem.valor}]")

        cursor.execute(
            "INSERT INTO uso_ferramenta (id, id_mensagem, tool, args_resumo, criado_em) "
            "VALUES (?, ?, ?, ?, ?)",
            (_novo_id(), id_mensagem.valor, tool, args_resumo, _agora()),
        )

    async def listar_mensagens(
        self,
        id_chat: Identidade,
        limite: int,
        antes_de: Identidade | None = None,
    ) -> list[MensagemPersistida]:
        return await self._ler(
            lambda cur: self._listar_mensagens_sync(cur, id_chat, limite, antes_de)
        )

    def _listar_mensagens_sync(
        self,
        cursor: sqlite3.Cursor,
        id_chat: Identidade,
        limite: int,
        antes_de: Identidade | None,
    ) -> list[MensagemPersistida]:
        """RN-P-13 e RN-P-14: as mais recentes por id DESC, devolvidas crescentes.

        idx_mensagem_chat(id_chat, id) e o que faz o custo ser funcao de
        `limite`, nao do tamanho do chat (NFR-P-04).
        """
        if antes_de is None:
            linhas = cursor.execute(
                "SELECT id, id_chat, papel, texto, em_andamento, criada_em FROM mensagem "
                "WHERE id_chat = ? ORDER BY id DESC LIMIT ?",
                (id_chat.valor, limite),
            ).fetchall()
        else:
            linhas = cursor.execute(
                "SELECT id, id_chat, papel, texto, em_andamento, criada_em FROM mensagem "
                "WHERE id_chat = ? AND id < ? ORDER BY id DESC LIMIT ?",
                (id_chat.valor, antes_de.valor, limite),
            ).fetchall()

        linhas.reverse()  # a mais antiga primeiro
        if not linhas:
            return []

        usos = self._usos_por_mensagem(cursor, [linha[0] for linha in linhas])

        return [
            MensagemPersistida(
                id=Identidade(id),
                id_chat=Identidade(chat),
                papel=papel,
                texto=texto,
                em_andamento=bool(em_andamento),
                criada_em=_data(criada_em),
                usos_de_ferramenta=tuple(usos.get(id, ())),
            )
            for id, chat, papel, texto, em_andamento, criada_em in linhas
        ]

    def _usos_por_mensagem(
        self, cursor: sqlite3.Cursor, ids: list[str]
    ) -> dict[str, list[UsoDeFerramenta]]:
        """Uma consulta para a pagina inteira, em vez de uma por mensagem.

        NFR-P-13: os `?` sao gerados em numero, nunca em conteudo - nenhum valor
        entra na string da consulta. Todos continuam vinculados como parametro.
        """
        marcadores = ",".join("?" * len(ids))
        linhas = cursor.execute(
            "SELECT id_mensagem, tool, args_resumo, criado_em FROM uso_ferramenta "
            f"WHERE id_mensagem IN ({marcadores}) ORDER BY id",
            ids,
        ).fetchall()

        agrupados: dict[str, list[UsoDeFerramenta]] = {}
        for id_mensagem, tool, args_resumo, criado_em in linhas:
            agrupados.setdefault(id_mensagem, []).append(
                UsoDeFerramenta(
                    tool=tool, args_resumo=args_resumo, criado_em=_data(criado_em)
                )
            )
        return agrupados
