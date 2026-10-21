"""As acoes do catalogo como ferramentas do agente (U6, RN-S-46..51).

E o UNICO modulo de U6 que importa o catalogo de U5, e so o composition root
(U9) o importa (DP-S-23): `aplicacao/ferramentas/__init__.py` nao o reexporta.
Por isso U7 continua sem conhecer o catalogo.

Cada entrada tem uma fabrica que, na abertura da sessao, amarra o alvo (do
contexto) e quem aciona (do Agente) - o modelo nao tem onde passar id nem autor
(RN-S-48) - e devolve uma Ferramenta cuja funcao chama
`CatalogoDeAcoes.executar`, o unico caminho de U5 (RN-S-49). Politica,
validacao e confirmacao continuam la dentro.
"""

import json
import logging
from collections.abc import Mapping, Sequence

from fishingrod.aplicacao.catalogo.argumentos import MAIOR_POSICAO
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    Acionamento,
    Alvo,
    EtapaNaPosicao,
    Parametro,
    Resultado,
    TipoParametro,
)
from fishingrod.aplicacao.ferramentas.tipos import EntradaDoRegistro, Ferramenta, RespostaDaFerramenta
from fishingrod.aplicacao.portas.sessao import ContextoDaSessao, Familia
from fishingrod.dominio import Agente, Anotacao, Chamador, Chat, Frente, Sessao, Tarefa

# R-ND6-14: o aviso de `dado` desconhecido (G12). O NullHandler fica aqui pelo
# mesmo motivo de U2-U5: sem destino configurado, nada vaza para a tela.
_log = logging.getLogger("fishingrod.sessao.ferramentas")
_log.addHandler(logging.NullHandler())


def entradas_de_acoes(catalogo: CatalogoDeAcoes) -> tuple[EntradaDoRegistro, ...]:
    """Uma entrada por acao que aceita o chamador AGENTE (RN-S-46; hoje, as 6),
    na ordem do registro de U5, na familia AMBIENTE, com o nome da acao."""
    return tuple(_entrada(catalogo, acao) for acao in catalogo.listar(chamador=Chamador.AGENTE))


def _entrada(catalogo: CatalogoDeAcoes, acao: Acao) -> EntradaDoRegistro:
    esquema = esquema_de(acao.parametros)

    def fabricar(contexto: ContextoDaSessao, agente: Agente) -> Ferramenta:
        alvo = Alvo(
            contexto.id_ambiente, contexto.id_frente, contexto.id_tarefa, contexto.id_sessao
        )
        acionamento = Acionamento.agente(agente.nome)

        async def executar(argumentos: Mapping[str, object]) -> RespostaDaFerramenta:
            resultado = await catalogo.executar(acao.nome, alvo, argumentos, acionamento)
            return RespostaDaFerramenta(texto_do_resultado(resultado), erro=not resultado.sucesso)

        return Ferramenta(acao.nome, acao.descricao, esquema, executar)

    return EntradaDoRegistro(acao.nome, Familia.AMBIENTE, fabricar)


# --------------------------------------------------------------------------
# O esquema (RN-S-47, G14)
# --------------------------------------------------------------------------


def esquema_de(parametros: Sequence[Parametro]) -> dict[str, object]:
    """Um objeto com uma propriedade por parametro, `required` com os
    obrigatorios e nada alem deles.

    O esquema orienta o modelo e o SDK o confere antes de chamar a ferramenta
    (A16, R-CG6-1); quem decide continua sendo o catalogo. Por isso ele nunca e
    mais frouxo que a conferencia de forma do catalogo (PBT-U6-06, R-CG6-4):
    TEXTO obrigatorio leva `pattern: "\\S"` (so espacos e ausente para U5) e
    POSICAO leva o teto de U5 (`MAIOR_POSICAO`), alem do minimo 1. A lista
    fechada de agentes de U4 nao cabe no esquema: e regra do dominio, e o
    agente le `fora_da_lista`.
    """
    propriedades: dict[str, object] = {}
    obrigatorios: list[str] = []
    for parametro in parametros:
        propriedades[parametro.nome] = _propriedade(parametro)
        if parametro.obrigatorio:
            obrigatorios.append(parametro.nome)
    return {
        "type": "object",
        "properties": propriedades,
        "required": obrigatorios,
        "additionalProperties": False,
    }


def _propriedade(parametro: Parametro) -> dict[str, object]:
    match parametro.tipo:
        case TipoParametro.TEXTO:
            propriedade: dict[str, object] = {
                "type": "string",
                "description": parametro.descricao,
                "maxLength": parametro.maximo,
            }
            if parametro.obrigatorio:
                # Texto so de espacos o catalogo trata como ausente (R-CG5-6).
                # O `\S` do `re` do Python e o complemento de str.isspace().
                propriedade["minLength"] = 1
                propriedade["pattern"] = r"\S"
            return propriedade
        case TipoParametro.ESCOLHA:
            return {"type": "string", "description": parametro.descricao, "enum": list(parametro.opcoes)}
        case TipoParametro.POSICAO:
            return {
                "type": "integer",
                "description": parametro.descricao,
                "minimum": 1,
                "maximum": MAIOR_POSICAO,
            }
    raise AssertionError(f"tipo de parametro sem esquema: {parametro.tipo}")


# --------------------------------------------------------------------------
# O texto que o agente le (RN-S-50, RN-S-51, G12)
# --------------------------------------------------------------------------


def texto_do_resultado(resultado: Resultado) -> str:
    """JSON compacto, com acento como acento. A projecao NAO tem id (G12): o
    agente nunca usa id (Q3=A de U5), e um id no texto seria conteudo do
    ambiente vazando para o historico do provedor.

    Falha: `{"ok": false, "motivo": ..., "detalhe": {...}}`. O `detalhe` de U5
    so tem categorias e numeros.
    """
    if resultado.sucesso:
        corpo: dict[str, object] = {"ok": True}
        corpo.update(_projecao(resultado.dado))
    else:
        corpo = {"ok": False, "motivo": resultado.motivo.value, "detalhe": dict(resultado.detalhe)}
    return json.dumps(corpo, ensure_ascii=False, separators=(",", ":"))


def _projecao(dado: object) -> dict[str, object]:
    match dado:
        case Frente():
            return {"frente": {"nome": dado.nome}}
        case Tarefa():
            return {"tarefa": {"nome": dado.nome}}
        case Sessao():
            return {"sessao": {"nome": dado.nome}}
        case Chat():
            return {"chat": {"nome": dado.nome, "agente": dado.agente.nome}}
        case EtapaNaPosicao(etapa=etapa, posicao=posicao):
            return {
                "etapa": {
                    "posicao": posicao,
                    "descricao": etapa.descricao,
                    "executor": etapa.executor.value,
                    "concluida": etapa.concluida,
                }
            }
        case Anotacao():
            # O valor nao volta: o agente acabou de escreve-lo, e repetir ate
            # 20.000 caracteres so gastaria contexto (G12).
            return {"anotacao": {"autor": dado.autor}}
    _log.warning("acao devolveu um dado de tipo desconhecido (%s)", type(dado).__name__)
    return {}
