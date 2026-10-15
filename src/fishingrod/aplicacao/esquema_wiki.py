"""EsquemaWiki: a estrutura inicial da wiki, definida pelo dono (US-09).

E o que o formulario de criacao produz e o que ServicoDeAmbiente (U4)
materializa (US-08), convertendo-o na primeira PropostaWiki - nao existe
operacao de materializacao na porta (business-logic-model.md 6). A semente e
simplesmente a primeira proposta, ja aprovada por construcao.

Puro: nao toca disco e nao importa nada do projeto. Tambem nao valida titulo
nem descricao: a unica invariante que existia aqui ("ao menos uma entidade")
foi revogada na Parte B.3 do FD de U1, e o que resta (RN-W-05, RN-W-14) e
verificado por `escrever_proposta` antes de tocar o disco.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PropriedadeSemente:
    """Nasce com descricao e sem conteudo: a descricao e o que o indice usa para
    recuperacao, e o conteudo vem do trabalho real, nao de texto que o produto
    inventou (Q8, alternativa D)."""

    titulo: str
    descricao: str


@dataclass(frozen=True)
class EntidadeSemente:
    titulo: str
    propriedades: tuple[PropriedadeSemente, ...] = ()


@dataclass(frozen=True)
class EsquemaWiki:
    """Sem `nome` e sem `descricao` (C6): a wiki nao tem descricao, e o nome era o
    da maquete. `carregar_toml` saiu com as maquetes (Q8), com a assinatura
    preservada em component-methods.md 3.4."""

    entidades: tuple[EntidadeSemente, ...] = ()

    @staticmethod
    def vazio() -> "EsquemaWiki":
        """Estado valido (Parte B.3 de U1): a wiki nasce so com o indice, que
        diz que ainda nao tem nenhuma entidade (RN-W-19)."""
        return EsquemaWiki()

    @staticmethod
    def a_partir_do_formulario(dados: dict[str, Any]) -> "EsquemaWiki":
        """`dados` tem a forma

            {"entidades": [
                {"titulo": "Clientes",
                 "propriedades": [{"titulo": "Dr. Marcelo", "descricao": "..."}]},
                {"titulo": "Ofertas"},
            ]}

        "entidades" e "propriedades" ausentes valem lista vazia. O texto chega
        como o usuario digitou: nada e aparado nem reescrito aqui - quem decide
        o nome no disco e o slug, na escrita.
        """
        return EsquemaWiki(
            entidades=tuple(
                EntidadeSemente(
                    titulo=entidade["titulo"],
                    propriedades=tuple(
                        PropriedadeSemente(
                            titulo=propriedade["titulo"],
                            descricao=propriedade["descricao"],
                        )
                        for propriedade in entidade.get("propriedades", ())
                    ),
                )
                for entidade in dados.get("entidades", ())
            )
        )
