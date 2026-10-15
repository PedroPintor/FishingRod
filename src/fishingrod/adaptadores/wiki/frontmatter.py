"""Frontmatter: como a pagina e montada, e as duas leituras dela (DP-W-06).

A gramatica (RN-W-11, RN-W-15, RN-W-16) - escrita uma vez, aqui. As tres
funcoes abaixo seguem esta e nenhuma outra:

    pagina       := [frontmatter] corpo
    frontmatter  := ABRE linha* FECHA
    ABRE         := a PRIMEIRA linha do texto, se for "---"
    FECHA        := a primeira linha seguinte que for "---"
                    ("---" admite espaco em branco depois - inclusive o CR de
                    um arquivo salvo com CRLF -, mas nao antes)
    linha        := chave ":" valor        partida no PRIMEIRO ":"
                  | qualquer outra coisa   ignorada
    chave        := "titulo" | "descricao", com as bordas aparadas. Chave
                    desconhecida e ignorada; repetida, vale a ultima
    valor        := o resto da linha, com as bordas aparadas e UM par de
                    aspas externas ("..." ou '...') removido
    corpo        := tudo depois de FECHA, menos a primeira linha se ela for
                    vazia - a linha em branco que `montar` poe entre os dois

    Linha termina em LF, e so em LF: quem le abre o arquivo com newline igual
    a LF, sem traducao, para que o corpo volte byte a byte (PBT-U3-03,
    PBT-U3-07).

    Sem ABRE, ou com ABRE e sem FECHA: titulo e descricao vazios, corpo = o
    texto inteiro, e nada levanta (RN-W-15).

So o PRIMEIRO bloco, comecando na primeira linha, e frontmatter (RN-W-16). O
corpo e markdown escrito por agente, e `---` e regua horizontal - vai aparecer.

As duas leituras sao independentes por decisao (Q5=B do NFR Design): o
cabecalho para no fechamento e tem teto (NFR-W-01); a pagina le tudo e nao tem
teto. Cada uma pode se otimizar e verificar do seu jeito. O que as obriga a
concordar e um teste, nao uma funcao compartilhada: a propriedade de
concordancia de tests/wiki/test_frontmatter.py (NFR-W-20). Se a gramatica
mudar, as duas mudam juntas - e o teste diz se uma ficou para tras.

Nada aqui abre arquivo: e manipulacao de texto. Quem abre e
wiki_de_arquivos.py, dentro de traduzindo_erros (DP-W-04).
"""

from collections.abc import Iterable
from itertools import islice

DELIMITADOR = "---"
CHAVE_TITULO = "titulo"
CHAVE_DESCRICAO = "descricao"

# NFR-W-01: passou disto sem fechar, nao ha frontmatter. Conta a linha que abre
# e a que fecha; a pagina que o app escreve usa quatro.
TETO_DO_CABECALHO = 64

_ASPAS = ('"', "'")


def montar(titulo: str, descricao: str, conteudo: str) -> str:
    """A pagina inteira, pronta para gravar (RN-W-13).

    `titulo` e `descricao` chegam ja normalizados (caminho_wiki.normalizar_valor,
    aplicado por quem chama): um valor com quebra de linha partiria o bloco. O
    `conteudo` vai como veio, byte a byte - inclusive `---`, CR e linhas em
    branco no comeco (PBT-U3-07).
    """
    return (
        f"{DELIMITADOR}\n"
        f"{CHAVE_TITULO}: {titulo}\n"
        f"{CHAVE_DESCRICAO}: {descricao}\n"
        f"{DELIMITADOR}\n"
        "\n"
        f"{conteudo}"
    )


def ler_cabecalho(linhas: Iterable[str]) -> tuple[str, str]:
    """(titulo, descricao), consumindo so as linhas do bloco - e no maximo
    TETO_DO_CABECALHO delas (NFR-W-01).

    `linhas` e o proprio arquivo aberto: o iterador e preguicoso, e o laco para
    no fechamento. O custo da renderizacao passa a depender do NUMERO de
    paginas, nunca do tamanho delas - a pagina de 2 MB que Q11=A permite nao
    pesa mais que uma vazia.

    Severa por oficio: quem chama e o indice, e a pergunta e "esta pagina
    entra, e com que descricao?". Bloco que nao fecha dentro do teto nao e
    bloco.
    """
    titulo = descricao = ""
    for numero, linha in enumerate(islice(linhas, TETO_DO_CABECALHO), start=1):
        delimitador = linha.rstrip() == DELIMITADOR
        if numero == 1:
            if not delimitador:
                return "", ""
            continue
        if delimitador:
            return titulo, descricao

        chave, separador, valor = linha.partition(":")
        if not separador:
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in _ASPAS:
            valor = valor[1:-1]
        chave = chave.strip()
        if chave == CHAVE_TITULO:
            titulo = valor
        elif chave == CHAVE_DESCRICAO:
            descricao = valor

    return "", ""


def ler_pagina(texto: str) -> tuple[str, str, str]:
    """(titulo, descricao, corpo), sobre o texto inteiro e sem teto (Q11=A).

    Tolerante por oficio (RN-W-15): quem chama e `ler`, e a pergunta e "me de
    o conteudo". Sem bloco, ou com bloco que nao fecha, devolve titulo e
    descricao vazios e o texto inteiro como corpo - recusar uma pagina legivel
    por metadado faltando trocaria um defeito visivel por um inacessivel.
    """
    # split, e nao splitlines: splitlines parte tambem em VT, FF, NEL e
    # U+2028, e o cabecalho - que itera o arquivo aberto com newline LF - nao.
    # Seria a primeira divergencia entre as duas leituras.
    linhas = texto.split("\n")
    if linhas[0].rstrip() != DELIMITADOR:
        return "", "", texto

    titulo = descricao = ""
    for indice in range(1, len(linhas)):
        linha = linhas[indice]
        if linha.rstrip() == DELIMITADOR:
            resto = linhas[indice + 1 :]
            if resto and resto[0].rstrip("\r") == "":
                resto = resto[1:]
            return titulo, descricao, "\n".join(resto)

        chave, separador, valor = linha.partition(":")
        if not separador:
            continue
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in _ASPAS:
            valor = valor[1:-1]
        chave = chave.strip()
        if chave == CHAVE_TITULO:
            titulo = valor
        elif chave == CHAVE_DESCRICAO:
            descricao = valor

    return "", "", texto
