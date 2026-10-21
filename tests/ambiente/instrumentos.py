"""Involucros das duas portas, para ver e perturbar o que o servico faz com elas.

Nao sao dubles do contrato - esses moram em tests/dobles e sao uma segunda
implementacao. Estes embrulham uma implementacao qualquer, delegam tudo, e no
caminho:
- anotam cada chamada num DIARIO compartilhado pelas duas portas, que e o que
  deixa verificar ordem entre banco e wiki (RN-A-14, RN-A-17);
- executam um gancho ANTES de delegar - e por ele que um "outro processo"
  grava no meio de uma operacao (RN-A-10, RN-A-11);
- injetam UMA falha, na n-esima chamada das duas portas juntas, antes ou
  depois de a chamada chegar a porta de verdade (PBT-U4-05). "Depois" e o
  caso traicoeiro: o disco mudou e mesmo assim quem chamou recebe erro;
- opcionalmente cedem o laco no meio da chamada, para o teste da trava
  (RN-A-06) enxergar intercalacao.
"""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable, Iterator
from typing import Any

from fishingrod.aplicacao.portas.persistencia import ErroDePersistencia
from fishingrod.aplicacao.portas.wiki import ArmazenamentoIndisponivel


class FalhaInjetadaNoBanco(ErroDePersistencia):
    """Uma falha de I/O qualquer da porta de persistencia, posta pelo teste."""


class FalhaInjetadaNaWiki(ArmazenamentoIndisponivel):
    """Idem, da porta de wiki - com o tipo que o adaptador real usaria."""


class Injecao:
    """Uma falha so, na n-esima chamada, contando as duas portas juntas."""

    def __init__(self, na_chamada: int, depois: bool) -> None:
        self.na_chamada = na_chamada
        self.depois = depois
        self.disparou = False
        self._contador = 0
        self._pausada = False

    def escolhida(self) -> bool:
        if self._pausada:
            return False
        self._contador += 1
        if self._contador == self.na_chamada:
            self.disparou = True
            return True
        return False

    @contextlib.contextmanager
    def pausada(self) -> Iterator[None]:
        """As leituras que a propria propriedade faz para verificar nao contam
        nem falham - senao a falha poderia cair na verificacao, e nao na
        operacao sob teste."""
        self._pausada = True
        try:
            yield
        finally:
            self._pausada = False


Gancho = Callable[[str], Awaitable[None]]


class _Espia:
    _falha: type[Exception]

    def __init__(
        self,
        interna: Any,
        diario: list[str] | None = None,
        *,
        injecao: Injecao | None = None,
        antes: Gancho | None = None,
        ceder: bool = False,
    ) -> None:
        self.interna = interna
        self.diario = [] if diario is None else diario
        self.injecao = injecao
        self.antes = antes
        self.ceder = ceder

    async def _chamar(self, nome: str, funcao: Callable[..., Awaitable[Any]], *args: Any) -> Any:
        self.diario.append(nome)
        escolhida = self.injecao is not None and self.injecao.escolhida()
        if escolhida and not self.injecao.depois:
            raise self._falha(f"falha injetada antes de {nome}")
        if self.antes is not None:
            await self.antes(nome)
        if self.ceder:
            await asyncio.sleep(0)
        resultado = await funcao(*args)
        if self.ceder:
            self.diario.append(f"{nome}:fim")
        if escolhida:
            raise self._falha(f"falha injetada depois de {nome}")
        return resultado


class PersistenciaEspia(_Espia):
    """As cinco operacoes de PortaPersistencia que U4 usa."""

    _falha = FalhaInjetadaNoBanco

    async def salvar_ambiente(self, ambiente):
        return await self._chamar("salvar_ambiente", self.interna.salvar_ambiente, ambiente)

    async def carregar_ambiente(self, id):
        return await self._chamar("carregar_ambiente", self.interna.carregar_ambiente, id)

    async def listar_ambientes(self):
        return await self._chamar("listar_ambientes", self.interna.listar_ambientes)

    async def apagar_ambiente(self, id):
        return await self._chamar("apagar_ambiente", self.interna.apagar_ambiente, id)

    async def anotar(self, id_ambiente, id_sessao, chave, anotacao):
        return await self._chamar(
            "anotar", self.interna.anotar, id_ambiente, id_sessao, chave, anotacao
        )


class WikiEspia(_Espia):
    """As cinco operacoes de PortaWiki."""

    _falha = FalhaInjetadaNaWiki

    async def listar(self, localizador, caminho):
        return await self._chamar("listar", self.interna.listar, localizador, caminho)

    async def ler(self, localizador, caminho_pagina):
        return await self._chamar("ler", self.interna.ler, localizador, caminho_pagina)

    async def escrever_proposta(self, localizador, proposta):
        return await self._chamar(
            "escrever_proposta", self.interna.escrever_proposta, localizador, proposta
        )

    async def renderizar_index(self, localizador, nome):
        return await self._chamar("renderizar_index", self.interna.renderizar_index, localizador, nome)

    async def apagar(self, localizador):
        return await self._chamar("apagar", self.interna.apagar, localizador)
