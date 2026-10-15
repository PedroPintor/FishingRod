"""Esquema fisico, PRAGMAs e as duas versoes (DP-P-07).

Este modulo nao conhece dominio nem porta: so SQL e sqlite3. E testavel sozinho,
com uma conexao em memoria.
"""

import sqlite3

# DP-P-07 - duas versoes, dois escopos, independentes:
#
#   VERSAO_ESQUEMA_FISICO -> PRAGMA user_version. Tabelas, indices, chaves.
#                            Verificada na abertura.
#   VERSAO_DOCUMENTO      -> coluna versao_esquema. Formato do JSON.
#                            Verificada em carregar_ambiente (RN-P-02 emendada).
#
# Sao perguntas diferentes e vao mudar em momentos diferentes. Acrescentar uma
# coluna em `anotacao` nao muda o formato do documento; renomear um campo dentro
# do JSON nao muda tabela nenhuma.
VERSAO_ESQUEMA_FISICO = 1
VERSAO_DOCUMENTO = 1

DDL = """
CREATE TABLE IF NOT EXISTS ambiente (
    id             TEXT    PRIMARY KEY,
    nome           TEXT    NOT NULL,
    versao         INTEGER NOT NULL,
    versao_esquema INTEGER NOT NULL,
    documento      TEXT    NOT NULL,
    criado_em      TEXT    NOT NULL,
    atualizado_em  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS anotacao (
    id          TEXT NOT NULL PRIMARY KEY,
    id_ambiente TEXT NOT NULL REFERENCES ambiente(id) ON DELETE CASCADE,
    id_tarefa   TEXT NOT NULL,
    chave       TEXT NOT NULL,
    autor       TEXT NOT NULL,
    valor       TEXT NOT NULL,
    criada_em   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mensagem (
    id           TEXT    NOT NULL PRIMARY KEY,
    id_ambiente  TEXT    NOT NULL REFERENCES ambiente(id) ON DELETE CASCADE,
    id_chat      TEXT    NOT NULL,
    papel        TEXT    NOT NULL,
    texto        TEXT    NOT NULL,
    em_andamento INTEGER NOT NULL,
    criada_em    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS uso_ferramenta (
    id          TEXT NOT NULL PRIMARY KEY,
    id_mensagem TEXT NOT NULL REFERENCES mensagem(id) ON DELETE CASCADE,
    tool        TEXT NOT NULL,
    args_resumo TEXT NOT NULL,
    criado_em   TEXT NOT NULL
);

-- R-CG-1: o indice comeca em id_ambiente, e nao em id_tarefa, porque RN-P-11
-- diz que a carga traz a memoria de TODAS as tarefas de uma vez. O unico
-- caminho de leitura que existe filtra por ambiente.
CREATE INDEX IF NOT EXISTS idx_anotacao_ambiente
    ON anotacao(id_ambiente, id_tarefa, id);

-- NFR-P-04: e este indice que faz listar_mensagens ser funcao de `limite`, e
-- nao do tamanho do chat.
CREATE INDEX IF NOT EXISTS idx_mensagem_chat
    ON mensagem(id_chat, id);

CREATE INDEX IF NOT EXISTS idx_uso_mensagem
    ON uso_ferramenta(id_mensagem);
"""


def aplicar_pragmas(conexao: sqlite3.Connection) -> None:
    """Os quatro PRAGMAs que o desenho exige, aplicados uma vez por conexao.

    foreign_keys e o mais importante: o SQLite o mantem DESLIGADO por padrao, e
    sem ele a cascata de RN-P-20 simplesmente nao acontece - apagar_ambiente
    deixaria orfaos em silencio. PBT-U2-07 quebra se este pragma sumir.
    """
    conexao.execute("PRAGMA journal_mode = WAL")  # NFR-P-05
    conexao.execute("PRAGMA synchronous = NORMAL")  # NFR-P-05
    conexao.execute("PRAGMA foreign_keys = ON")  # NFR-P-06
    conexao.execute("PRAGMA busy_timeout = 5000")  # NFR-P-10


def criar_esquema(conexao: sqlite3.Connection) -> None:
    """NFR-P-19: idempotente. Abrir duas vezes o mesmo banco e inofensivo."""
    conexao.executescript(DDL)


def verificar_versao_fisica(conexao: sqlite3.Connection) -> int:
    """Le PRAGMA user_version; carimba 1 num banco novo; recusa versao futura.

    Devolve a versao encontrada. Levantar aqui e o que faz o programa nao subir
    sobre um banco que ele nao entende (NFR-P-20).
    """
    from fishingrod.aplicacao.portas.persistencia import EsquemaIncompativel

    encontrada = int(conexao.execute("PRAGMA user_version").fetchone()[0])

    if encontrada == 0:
        # Banco recem-criado (ou anterior ao carimbo): passa a valer a atual.
        # PRAGMA nao aceita parametro vinculado, e por isso o valor vem de uma
        # constante do modulo, nunca de entrada externa (NFR-P-13).
        conexao.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA_FISICO:d}")
        return VERSAO_ESQUEMA_FISICO

    if encontrada > VERSAO_ESQUEMA_FISICO:
        raise EsquemaIncompativel(
            f"o banco foi escrito por uma versao mais nova do FishingRod "
            f"(esquema fisico {encontrada}; esta versao entende ate "
            f"{VERSAO_ESQUEMA_FISICO})"
        )

    return encontrada
