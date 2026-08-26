"""Erros de dominio de U1.

Q7=A: violacao de invariante levanta excecao tipada. Busca que nao encontra
devolve None (RN-14) - nao achar nao e violacao de regra, e resultado.
"""


class ErroDeDominio(Exception):
    """Base de toda violacao de invariante do dominio."""


class NomeInvalido(ErroDeDominio):
    """Nome ou descricao vazia, ou composta so de espacos (RN-02)."""


class OrquestradorDuplicado(ErroDeDominio):
    """Tentativa de por um segundo orquestrador na mesma tarefa (RN-06)."""


class AgenteInvalido(ErroDeDominio):
    """Papel do agente incompativel com a operacao (RN-05)."""


def exigir_texto(valor: str, campo: str) -> str:
    """Devolve o texto se for valido; levanta NomeInvalido caso contrario.

    RN-02: vazio e "" e tambem qualquer texto cujo strip() seja vazio.
    O texto valido NAO e normalizado - o dominio recusa o invalido, mas nao
    reescreve o que o usuario digitou.
    """
    if not isinstance(valor, str) or not valor.strip():
        raise NomeInvalido(f"{campo} nao pode ser vazio")
    return valor
