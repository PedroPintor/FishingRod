"""O que so o adaptador real tem: PRAGMAs, versoes, permissao, cascata, tempo.

Estes testes olham para dentro do armazenamento - contam linhas em tabela, leem
PRAGMA, verificam bits de permissao. E por isso que eles NAO estao em
test_contrato.py: la, tudo precisa valer para o duble tambem.
"""

import json
import os
import sqlite3
import stat
import time
import uuid
from datetime import UTC, datetime

import pytest

from fishingrod.adaptadores.persistencia import abrir_repositorio
from fishingrod.adaptadores.persistencia import esquema as esq
from fishingrod.adaptadores.persistencia.localizacao import caminho_do_banco, pasta_de_dados
from fishingrod.aplicacao.portas.persistencia import BancoIlegivel, EsquemaIncompativel
from fishingrod.dominio import Agente, Ambiente, Identidade, Papel
from tests.persistencia.estrategias import executar

ORQUESTRADOR = Agente(nome="orquestrador", papel=Papel.ORQUESTRADOR, modelo="claude-opus-5")


def _abrir(tmp_path, nome="fishingrod.db"):
    return executar(abrir_repositorio(tmp_path / nome))


def _ambiente_com_tarefa() -> Ambiente:
    ambiente = Ambiente(nome="ambiente")
    frente = ambiente.criar_frente("frente")
    frente.criar_tarefa("tarefa", ORQUESTRADOR)
    return ambiente


# --------------------------------------------------------------------------
# PRAGMAs (NFR-P-05, NFR-P-06, NFR-P-10)
# --------------------------------------------------------------------------


def test_nfr_p_05_e_06_os_pragmas_valem_na_conexao(tmp_path):
    """foreign_keys e o mais importante: o SQLite o mantem desligado por padrao,
    e sem ele a cascata de RN-P-20 nao acontece."""
    repositorio = _abrir(tmp_path)
    try:
        ler = lambda p: repositorio._conexao.execute(f"PRAGMA {p}").fetchone()[0]

        assert str(ler("journal_mode")).lower() == "wal"
        assert int(ler("synchronous")) == 1  # NORMAL
        assert int(ler("foreign_keys")) == 1
        assert int(ler("busy_timeout")) == 5000
    finally:
        executar(repositorio.fechar())


def test_nfr_p_20_apagar_nao_deixa_linha_em_tabela_nenhuma(tmp_path):
    """A versao observavel disto esta em PBT-U2-07. Esta aqui olha as tabelas."""
    repositorio = _abrir(tmp_path)
    try:
        ambiente = _ambiente_com_tarefa()
        tarefa = ambiente.frentes[0].tarefas[0]

        async def cenario():
            await repositorio.salvar_ambiente(ambiente)
            sessao = tarefa.sessoes[0]
            anotacao = sessao.memoria.anotar("achado", "algo", "agente")
            await repositorio.anotar(ambiente.id, sessao.id, "achado", anotacao)
            id_mensagem = await repositorio.inserir_mensagem(
                ambiente.id, Identidade.nova(), "agente", "oi", False
            )
            await repositorio.registrar_uso_ferramenta(id_mensagem, "ler", "{}")

        executar(cenario())

        contar = lambda t: repositorio._conexao.execute(
            f"SELECT count(*) FROM {t}"  # noqa: S608 - nome vem de literal deste teste
        ).fetchone()[0]
        assert (contar("anotacao"), contar("mensagem"), contar("uso_ferramenta")) == (1, 1, 1)

        executar(repositorio.apagar_ambiente(ambiente.id))

        assert contar("ambiente") == 0
        assert contar("anotacao") == 0
        assert contar("mensagem") == 0
        assert contar("uso_ferramenta") == 0
    finally:
        executar(repositorio.fechar())


# --------------------------------------------------------------------------
# As duas versoes (DP-P-07)
# --------------------------------------------------------------------------


def test_dp_p_07_banco_novo_recebe_a_versao_fisica(tmp_path):
    repositorio = _abrir(tmp_path)
    try:
        versao = repositorio._conexao.execute("PRAGMA user_version").fetchone()[0]
        assert versao == esq.VERSAO_ESQUEMA_FISICO
    finally:
        executar(repositorio.fechar())


def test_nfr_p_19_abrir_duas_vezes_e_inofensivo(tmp_path):
    """CREATE TABLE IF NOT EXISTS: reabrir nao recria nem perde nada."""
    primeiro = _abrir(tmp_path)
    ambiente = _ambiente_com_tarefa()
    executar(primeiro.salvar_ambiente(ambiente))
    executar(primeiro.fechar())

    segundo = _abrir(tmp_path)
    try:
        carregado = executar(segundo.carregar_ambiente(ambiente.id))
        assert carregado == ambiente  # CS-01: fechar e reabrir reconstitui
    finally:
        executar(segundo.fechar())


def test_dp_p_07_esquema_fisico_futuro_recusa_a_abertura(tmp_path):
    caminho = tmp_path / "fishingrod.db"
    executar(_abrir(tmp_path).fechar())

    bruta = sqlite3.connect(caminho)
    bruta.execute(f"PRAGMA user_version = {esq.VERSAO_ESQUEMA_FISICO + 1}")
    bruta.close()

    with pytest.raises(EsquemaIncompativel):
        executar(abrir_repositorio(caminho))


def test_rn_p_02_documento_futuro_recusa_a_carga(tmp_path):
    """A coluna versiona o documento; o PRAGMA versiona a tabela. Sao
    independentes, e este teste so mexe na primeira."""
    repositorio = _abrir(tmp_path)
    try:
        ambiente = _ambiente_com_tarefa()
        executar(repositorio.salvar_ambiente(ambiente))

        repositorio._conexao.execute(
            "UPDATE ambiente SET versao_esquema = ? WHERE id = ?",
            (esq.VERSAO_DOCUMENTO + 1, ambiente.id.valor),
        )

        with pytest.raises(EsquemaIncompativel):
            executar(repositorio.carregar_ambiente(ambiente.id))
    finally:
        executar(repositorio.fechar())


# --------------------------------------------------------------------------
# Abertura (NFR-P-07, DP-P-01)
# --------------------------------------------------------------------------


def test_nfr_p_07_arquivo_corrompido_levanta_na_abertura(tmp_path):
    """E na ABERTURA, nao tres telas adiante: com abertura preguicosa, o erro
    apareceria depois da TUI ja ter subido."""
    caminho = tmp_path / "fishingrod.db"
    caminho.write_bytes(b"isto nao e um banco de dados, e um arquivo qualquer")

    with pytest.raises(BancoIlegivel):
        executar(abrir_repositorio(caminho))


def test_dp_p_01_a_fabrica_cria_o_diretorio_que_falta(tmp_path):
    fundo = tmp_path / "a" / "b" / "c"
    repositorio = executar(abrir_repositorio(fundo / "fishingrod.db"))
    try:
        assert (fundo / "fishingrod.db").exists()
    finally:
        executar(repositorio.fechar())


@pytest.mark.skipif(os.name == "nt", reason="chmod no Windows so mexe no bit de leitura")
def test_nfr_p_14_permissoes_restritas(tmp_path):
    """DP-P-08: 0o700 no diretorio, 0o600 no arquivo. Os -wal e -shm nao recebem
    chmod de proposito - quem os protege e o diretorio."""
    pasta = tmp_path / "dados"
    caminho = pasta / "fishingrod.db"
    repositorio = executar(abrir_repositorio(caminho))
    try:
        assert stat.S_IMODE(os.stat(pasta).st_mode) == 0o700
        assert stat.S_IMODE(os.stat(caminho).st_mode) == 0o600
    finally:
        executar(repositorio.fechar())


# --------------------------------------------------------------------------
# Localizacao (DP-P-05)
# --------------------------------------------------------------------------


def test_dp_p_05_localizacao_nao_toca_disco(monkeypatch, tmp_path):
    """Funcao pura: resolve caminho e nao cria nada."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr("sys.platform", "linux")

    assert pasta_de_dados() == tmp_path / "xdg" / "fishingrod"
    assert caminho_do_banco().name == "fishingrod.db"
    assert not (tmp_path / "xdg").exists()


@pytest.mark.parametrize(
    "plataforma,esperado",
    [("win32", "FishingRod"), ("darwin", "FishingRod"), ("linux", "fishingrod")],
)
def test_dp_p_05_uma_raiz_por_sistema(monkeypatch, plataforma, esperado):
    monkeypatch.setattr("sys.platform", plataforma)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    assert pasta_de_dados().name == esperado


# --------------------------------------------------------------------------
# Desempenho (NFR-P-01, NFR-P-04)
# --------------------------------------------------------------------------


def test_nfr_p_01_carga_de_cinco_mil_anotacoes(tmp_path):
    """Alvo: ~1s. A margem generosa existe porque o numero que interessa e a
    ordem de grandeza - se a carga virar dezenas de segundos, o desenho quebrou.

    A carga do cenario e feita direto na conexao de proposito: 5.000 chamadas de
    anotar mediriam o custo da transacao por anotacao, que nao e o que NFR-P-01
    pergunta.
    """
    repositorio = _abrir(tmp_path)
    try:
        ambiente = _ambiente_com_tarefa()
        sessao = ambiente.frentes[0].tarefas[0].sessoes[0]
        executar(repositorio.salvar_ambiente(ambiente))

        agora = datetime.now(UTC).isoformat()
        linhas = [
            (
                str(uuid.uuid7()),
                ambiente.id.valor,
                sessao.id.valor,
                f"chave-{i % 20}",
                "agente",
                f"anotacao numero {i}",
                agora,
            )
            for i in range(5000)
        ]
        repositorio._conexao.execute("BEGIN IMMEDIATE")
        repositorio._conexao.executemany(
            "INSERT INTO anotacao "
            "(id, id_ambiente, id_sessao, chave, autor, valor, criada_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            linhas,
        )
        repositorio._conexao.execute("COMMIT")

        inicio = time.perf_counter()
        carregado = executar(repositorio.carregar_ambiente(ambiente.id))
        decorrido = time.perf_counter() - inicio

        assert carregado.frentes[0].tarefas[0].sessoes[0].memoria.total_de_anotacoes() == 5000
        assert decorrido < 5.0, f"carga levou {decorrido:.2f}s"
    finally:
        executar(repositorio.fechar())


# --------------------------------------------------------------------------
# NFR-P-02: listar nao desserializa documento
# --------------------------------------------------------------------------


def test_nfr_p_02_listar_nao_le_a_coluna_documento(tmp_path):
    """RN-P-24: e uma tela de escolha, nao uma carga.

    Prova pelo unico jeito que nao depende de instrumentar o driver: com o
    documento corrompido, listar continua funcionando e carregar quebra.
    """
    repositorio = _abrir(tmp_path)
    try:
        ambiente = _ambiente_com_tarefa()
        executar(repositorio.salvar_ambiente(ambiente))

        repositorio._conexao.execute(
            "UPDATE ambiente SET documento = ? WHERE id = ?",
            ("{isto nao e json", ambiente.id.valor),
        )

        [resumo] = executar(repositorio.listar_ambientes())
        assert resumo.id == ambiente.id
        assert resumo.nome == ambiente.nome

        with pytest.raises(json.JSONDecodeError):
            executar(repositorio.carregar_ambiente(ambiente.id))
    finally:
        executar(repositorio.fechar())
