"""Argumentos: do texto da barra para nomes, e dos nomes para valores
conferidos (U5, passo 4 do caminho de RN-AC-38).

Duas funcoes puras, uma para cada pedaco:
- `repartir` so existe para a barra: reparte o texto pelos parametros, na
  ordem, e o ultimo leva o resto (Q7=A, RN-AC-16) - e o que mata TD-11;
- `converter` e comum as duas entradas: confere presenca, tipo, opcao e
  tamanho (RN-AC-17..19) e devolve os valores prontos para `efetivar`.

So a FORMA e conferida aqui (RN-AC-03). Nome vazio no dominio, agente fora da
lista fechada e segundo orquestrador continuam sendo recusados por U1 e U4.

Nao importa nada do projeto alem de tipos.py.
"""

import re
import unicodedata
from collections.abc import Mapping, Sequence

from fishingrod.aplicacao.catalogo.tipos import Parametro, TipoParametro

# Os valores de `problema` no detalhe de ARGUMENTO_INVALIDO (domain-entities.md
# 5.2). FORA_DA_LISTA nao aparece aqui: quem a descobre e U4 (AgenteDesconhecido),
# e o catalogo so a traduz.
AUSENTE = "ausente"
DESCONHECIDO = "desconhecido"
TIPO = "tipo"
OPCAO = "opcao"
LONGO_DEMAIS = "longo_demais"
SOBRANDO = "sobrando"  # R-CG5-1

# Posicao e um numero de 1 a 999.999.999, venha como int ou como texto. O
# texto aceita so digitos ASCII: int("٢") vale 2 em Python, e nao e isso que
# se quer aceitar. O teto de nove digitos vale tambem para o int, para que a
# mesma posicao seja aceita ou recusada igual nas duas formas.
_DIGITOS = re.compile(r"[0-9]{1,9}")
MAIOR_POSICAO = 999_999_999

# Um nome desconhecido volta no detalhe para quem acionou poder corrigir. O
# corte evita devolver ao agente, inteira, uma chave de tamanho qualquer.
_ECO_MAXIMO = 100


class ArgumentoRecusado(Exception):
    """Interno do catalogo: o motivo de ARGUMENTO_INVALIDO, com o detalhe.

    Nao sai do catalogo - ele a captura no passo 4 e devolve Resultado.
    `parametro` e None so em SOBRANDO, que nao e de parametro nenhum.
    """

    def __init__(self, parametro: str | None, problema: str, maximo: int | None = None) -> None:
        super().__init__(parametro, problema)
        self.parametro = parametro
        self.problema = problema
        self.maximo = maximo

    def detalhe(self) -> dict[str, object]:
        detalhe: dict[str, object] = {"problema": self.problema}
        if self.parametro is not None:
            detalhe["parametro"] = self.parametro
        if self.maximo is not None:
            detalhe["maximo"] = self.maximo
        return detalhe


# --------------------------------------------------------------------------
# A barra: texto -> argumentos por nome
# --------------------------------------------------------------------------


def repartir(parametros: Sequence[Parametro], texto: str) -> dict[str, str]:
    """Cada parametro, menos o ultimo, pega uma palavra (ate o proximo espaco);
    o ultimo pega o resto, com os espacos de dentro INTACTOS (RN-AC-16).
    Acabou o texto, os parametros restantes ficam ausentes - e quem decide se
    isso e erro e `converter`.

    `str.split(maxsplit=1)` faz exatamente o corte de uma palavra: tira os
    espacos da frente, corta no primeiro espaco e devolve o resto sem mexer
    nele.

    Acao sem parametro e texto sobrando da SOBRANDO (R-CG5-1). Nenhuma das 6
    acoes cai nisso - o ultimo parametro sempre leva o resto -, mas a gramatica
    precisa ser total para qualquer registro.
    """
    restante = texto.strip()
    if not parametros:
        if restante:
            raise ArgumentoRecusado(None, SOBRANDO)
        return {}
    *primeiros, ultimo = parametros
    argumentos: dict[str, str] = {}
    for parametro in primeiros:
        if not restante:
            return argumentos
        palavra, *resto = restante.split(maxsplit=1)
        argumentos[parametro.nome] = palavra
        restante = resto[0] if resto else ""
    if restante:
        argumentos[ultimo.nome] = restante
    return argumentos


# --------------------------------------------------------------------------
# As duas entradas: argumentos por nome -> valores conferidos
# --------------------------------------------------------------------------


def converter(parametros: Sequence[Parametro], argumentos: Mapping[object, object]) -> dict[str, object]:
    """Confere os argumentos contra os parametros e devolve os valores prontos.

    A ordem e fixa, para a mesma entrada dar sempre o mesmo `parametro` e o
    mesmo `problema`: primeiro as chaves desconhecidas, em ordem alfabetica
    (RN-AC-17); depois cada parametro, na ordem do registro, com ausente ->
    tipo -> opcao -> tamanho.

    Ausente e: chave que nao veio, `None` (o `null` do JSON do agente) ou texto
    so de espacos (G3, R-CG5-4). Obrigatorio ausente e recusado; opcional
    ausente e OMITIDO do resultado - o padrao e do `efetivar` da acao.
    """
    nomes = {parametro.nome for parametro in parametros}
    desconhecidas = sorted((chave for chave in argumentos if chave not in nomes), key=str)
    if desconhecidas:
        raise ArgumentoRecusado(str(desconhecidas[0])[:_ECO_MAXIMO], DESCONHECIDO)

    convertidos: dict[str, object] = {}
    for parametro in parametros:
        valor = argumentos.get(parametro.nome)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            if parametro.obrigatorio:
                raise ArgumentoRecusado(parametro.nome, AUSENTE)
            continue
        convertidos[parametro.nome] = _converter_um(parametro, valor)
    return convertidos


def _converter_um(parametro: Parametro, valor: object) -> object:
    match parametro.tipo:
        case TipoParametro.TEXTO:
            if not isinstance(valor, str):
                raise ArgumentoRecusado(parametro.nome, TIPO)
            if parametro.maximo is not None and len(valor) > parametro.maximo:
                raise ArgumentoRecusado(parametro.nome, LONGO_DEMAIS, parametro.maximo)
            # O texto valido nao e normalizado: o dominio tambem nao reescreve
            # o que foi digitado (RN-02 de U1).
            return valor
        case TipoParametro.ESCOLHA:
            if not isinstance(valor, str):
                raise ArgumentoRecusado(parametro.nome, TIPO)
            procurado = sem_maiuscula_nem_acento(valor)
            for opcao in parametro.opcoes:
                if sem_maiuscula_nem_acento(opcao) == procurado:
                    return opcao  # a forma canonica, a do registro
            raise ArgumentoRecusado(parametro.nome, OPCAO)
        case TipoParametro.POSICAO:
            posicao = _posicao(valor)
            if posicao is None:
                raise ArgumentoRecusado(parametro.nome, TIPO)
            return posicao
    raise AssertionError(f"tipo de parametro sem conversao: {parametro.tipo}")


def _posicao(valor: object) -> int | None:
    """RN-AC-23: inteiro de 1 em diante, ou texto so de digitos. bool e int em
    Python, mas `True` nao e a posicao 1; fracao nao e posicao."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        posicao = valor
    elif isinstance(valor, str) and _DIGITOS.fullmatch(valor):
        posicao = int(valor)
    else:
        return None
    return posicao if 1 <= posicao <= MAIOR_POSICAO else None


def sem_maiuscula_nem_acento(texto: str) -> str:
    """G4: `Usuário`, `USUARIO` e `usuario` sao a mesma escolha. NFKD separa a
    letra da marca de acento; as marcas saem; casefold e o minusculo que vale
    para qualquer alfabeto."""
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).casefold()
