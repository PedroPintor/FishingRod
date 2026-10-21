"""Ambiente <-> documento JSON (DP-P-06, Q8=A).

A conversao mora aqui, no adaptador. U1 nao e tocado por esta unidade: o dominio
nao ganha to_dict, nao ganha from_dict e nao ganha import novo. O dominio nao
sabe que existe disco.

O risco assumido e concreto: alguem acrescenta um campo ao dominio e esquece
este arquivo. Quem cobre e PBT-U2-01 (round-trip para todo Ambiente gerado), que
falha porque o campo novo nao sobrevive a salvar-e-carregar. O esquecimento e
detectado, nao confiado a memoria de quem revisa.

Ausencias deliberadas (domain-entities.md 4):
- `versao` e `versao_esquema` sao COLUNAS, nao campos do JSON (R-CG-5). E o que
  permite listar_ambientes responder sem desserializar nada.
- Memoria e mensagem nao estao aqui: sao tabelas.
"""

from typing import Any

from fishingrod.dominio import (
    Agente,
    Ambiente,
    Chat,
    Etapa,
    ExecutorEtapa,
    Frente,
    Identidade,
    Papel,
    RaizWiki,
    Sessao,
    Tarefa,
)


def documento_de(ambiente: Ambiente) -> dict[str, Any]:
    """Serializa a estrutura do ambiente. Nao inclui memoria nem transcricao."""
    return {
        "id": ambiente.id.valor,
        "nome": ambiente.nome,
        "raiz_wiki": ambiente.raiz_wiki.localizador if ambiente.raiz_wiki else None,
        "frentes": [_frente_para_dict(f) for f in ambiente.frentes],
    }


def ambiente_de(documento: dict[str, Any], versao: int) -> Ambiente:
    """Reconstitui o ambiente. `versao` vem da coluna, nunca do JSON.

    A reconstrucao passa pelos construtores de dominio, entao um documento
    corrompido levanta erro de dominio em vez de virar entidade invalida.
    Sessao.memoria fica vazia aqui: quem a preenche e o repositorio, lendo a
    tabela `anotacao` (RN-P-08, RN-P-11).
    """
    return Ambiente(
        nome=documento["nome"],
        frentes=[_frente_de_dict(d) for d in documento["frentes"]],
        id=Identidade(documento["id"]),
        raiz_wiki=RaizWiki(documento["raiz_wiki"]) if documento["raiz_wiki"] else None,
        versao=versao,
    )


# --------------------------------------------------------------------------
# Frente
# --------------------------------------------------------------------------


def _frente_para_dict(frente: Frente) -> dict[str, Any]:
    return {
        "id": frente.id.valor,
        "nome": frente.nome,
        "tarefas": [_tarefa_para_dict(t) for t in frente.tarefas],
    }


def _frente_de_dict(d: dict[str, Any]) -> Frente:
    return Frente(
        nome=d["nome"],
        tarefas=[_tarefa_de_dict(t) for t in d["tarefas"]],
        id=Identidade(d["id"]),
    )


# --------------------------------------------------------------------------
# Tarefa
# --------------------------------------------------------------------------


def _tarefa_para_dict(tarefa: Tarefa) -> dict[str, Any]:
    return {
        "id": tarefa.id.valor,
        "nome": tarefa.nome,
        "sessoes": [_sessao_para_dict(s) for s in tarefa.sessoes],
        "etapas": [_etapa_para_dict(e) for e in tarefa.etapas],
    }


def _tarefa_de_dict(d: dict[str, Any]) -> Tarefa:
    return Tarefa(
        nome=d["nome"],
        sessoes=[_sessao_de_dict(s) for s in d["sessoes"]],
        etapas=[_etapa_de_dict(e) for e in d["etapas"]],
        id=Identidade(d["id"]),
    )


# --------------------------------------------------------------------------
# Sessao
# --------------------------------------------------------------------------


def _sessao_para_dict(sessao: Sessao) -> dict[str, Any]:
    return {
        "id": sessao.id.valor,
        "nome": sessao.nome,
        "chats": [_chat_para_dict(c) for c in sessao.chats],
    }


def _sessao_de_dict(d: dict[str, Any]) -> Sessao:
    return Sessao(
        nome=d["nome"],
        chats=[_chat_de_dict(c) for c in d["chats"]],
        id=Identidade(d["id"]),
    )


# --------------------------------------------------------------------------
# Chat e Agente
# --------------------------------------------------------------------------


def _chat_para_dict(chat: Chat) -> dict[str, Any]:
    return {
        "id": chat.id.valor,
        "nome": chat.nome,
        "agente": _agente_para_dict(chat.agente),
    }


def _chat_de_dict(d: dict[str, Any]) -> Chat:
    return Chat(
        agente=_agente_de_dict(d["agente"]),
        nome=d["nome"],
        id=Identidade(d["id"]),
    )


def _agente_para_dict(agente: Agente) -> dict[str, Any]:
    return {
        "nome": agente.nome,
        "papel": agente.papel.value,
        "modelo": agente.modelo,
        "ferramentas": list(agente.ferramentas),
        "regras": list(agente.regras),
    }


def _agente_de_dict(d: dict[str, Any]) -> Agente:
    return Agente(
        nome=d["nome"],
        papel=Papel(d["papel"]),
        modelo=d["modelo"],
        ferramentas=tuple(d["ferramentas"]),
        regras=tuple(d["regras"]),
    )


# --------------------------------------------------------------------------
# Etapa
# --------------------------------------------------------------------------


def _etapa_para_dict(etapa: Etapa) -> dict[str, Any]:
    return {
        "id": etapa.id.valor,
        "descricao": etapa.descricao,
        "executor": etapa.executor.value,
        "concluida": etapa.concluida,
    }


def _etapa_de_dict(d: dict[str, Any]) -> Etapa:
    return Etapa(
        descricao=d["descricao"],
        executor=ExecutorEtapa(d["executor"]),
        concluida=d["concluida"],
        id=Identidade(d["id"]),
    )
