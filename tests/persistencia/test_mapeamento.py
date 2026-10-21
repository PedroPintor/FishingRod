"""Ambiente <-> documento JSON, por exemplo (DP-P-06).

As propriedades geradas estao em test_contrato.py. Aqui fica o exemplo legivel:
quando o round-trip quebrar, este teste mostra qual campo sumiu, em vez de um
contra-exemplo de vinte linhas.
"""

import json

from fishingrod.adaptadores.persistencia import mapeamento
from fishingrod.dominio import Agente, Ambiente, ExecutorEtapa, Papel


def _ambiente_completo() -> Ambiente:
    ambiente = Ambiente(nome="Campanha de verao")

    pesquisa = ambiente.criar_frente("pesquisa")
    tarefa = pesquisa.criar_tarefa(
        "mapear concorrentes",
        Agente(
            nome="orquestrador",
            papel=Papel.ORQUESTRADOR,
            modelo="claude-opus-5",
            ferramentas=("criar_etapa", "anotar"),
            regras=("nunca apagar anotacao",),
        ),
    )
    tarefa.sessoes[0].criar_chat(
        Agente(nome="bibliotecario", papel=Papel.SUB_AGENTE, modelo="claude-sonnet-5"),
        nome="wiki",
    )
    tarefa.criar_sessao(
        Agente(nome="orquestrador", papel=Papel.ORQUESTRADOR, modelo="claude-opus-5"),
        nome="revisao",
    )
    tarefa.criar_etapa("levantar lista", ExecutorEtapa.AGENTE).concluir()
    tarefa.criar_etapa("revisar", ExecutorEtapa.USUARIO)

    ambiente.criar_frente("execucao")
    return ambiente


def test_round_trip_do_documento_preserva_tudo():
    original = _ambiente_completo()

    documento = mapeamento.documento_de(original)
    voltou = mapeamento.ambiente_de(json.loads(json.dumps(documento)), versao=7)

    assert voltou.versao == 7
    original.versao = 7  # a versao vem da coluna, nao do JSON
    assert voltou == original


def test_o_documento_nao_carrega_versao_nem_memoria():
    """R-CG-5: versao e versao_esquema sao colunas.

    E o que permite listar_ambientes responder sem desserializar (RN-P-24), e o
    que mantem a memoria fora do documento (RN-P-08).
    """
    documento = mapeamento.documento_de(_ambiente_completo())
    texto = json.dumps(documento)

    assert set(documento) == {"id", "nome", "raiz_wiki", "frentes"}
    assert "versao_esquema" not in texto
    assert "memoria" not in texto
    assert "anotacoes" not in texto


def test_o_localizador_da_wiki_sobrevive():
    """RN-P-15: a unica referencia a wiki e o localizador, e ele e logico."""
    original = _ambiente_completo()
    voltou = mapeamento.ambiente_de(mapeamento.documento_de(original), versao=1)

    assert voltou.raiz_wiki == original.raiz_wiki
    assert voltou.raiz_wiki.localizador == f"dados:wikis/{original.id.valor}"
