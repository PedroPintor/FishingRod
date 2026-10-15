"""O caminho logico da wiki: slug, caminho qualificado e normalizacao de valor.

Mora na aplicacao, e nao no adaptador (DP-W-02): o caminho logico e
vocabulario da porta - e o que aparece dentro de `[[...]]` no indice, o que o
agente passa a `ler`, e o que U8 vai precisar prever para validar um link.
Qualquer unidade que precise dele importa daqui.

Nao importa `pathlib` nem `os`, de proposito: isto manipula texto de caminho
logico, nao caminho de sistema. No dia em que importar, a fronteira tera
vazado.
"""

import re
import unicodedata

# RN-W-05: nomes que o Windows reserva para dispositivo. `nul.md` e um arquivo
# que o sistema se recusa a criar - a falha apareceria como OSError no meio de
# uma aprovacao, longe da causa.
NOMES_RESERVADOS = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{numero}" for numero in range(1, 10)}
    | {f"lpt{numero}" for numero in range(1, 10)}
)

# Tabela pre-slug: uma entrada, a que RN-W-04 exige ("Dr. Marcelo & Cia" ->
# "dr-marcelo-e-cia"). Uma tabela maior seria invencao sem regra que a peca.
_SUBSTITUICOES = (("&", " e "),)

_FORA_DO_SLUG = re.compile(r"[^a-z0-9]+")
_QUEBRAS = re.compile(r"\r\n|[\r\n\t]")
_ASPAS = ('"', "'")


def slug(titulo: str) -> str:
    """RN-W-04: minusculas, sem acento, tudo que nao for a-z0-9 vira hifen,
    hifens consecutivos colapsam, hifens das bordas sao aparados.

    Funcao total: nunca levanta. Titulo so de simbolos devolve "" - quem decide
    o que isso significa e quem chama, porque escrever recusa com
    TituloInvalido e ler/listar recusam com CaminhoForaDaRaiz.

    Idempotente (PBT-U3-05): a saida so tem a-z, 0-9 e hifens isolados no meio,
    e nenhuma etapa altera um texto assim. E por isso que passar o slug onde se
    espera o titulo da o mesmo resultado.
    """
    # NFKD primeiro: separa o acento da letra E reduz as formas de
    # compatibilidade (U+FF11 -> "1", U+FF0F -> "/", U+FF06 -> "&"), que assim
    # caem na mesma peneira que o caractere comum - inclusive a tabela abaixo.
    texto = unicodedata.normalize("NFKD", titulo)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for de, para in _SUBSTITUICOES:
        texto = texto.replace(de, para)
    return _FORA_DO_SLUG.sub("-", texto.lower()).strip("-")


def slug_valido(nome: str) -> bool:
    """O nome pode existir no disco: e o proprio slug, nao e vazio e nao e
    reservado (RN-W-04, RN-W-05).

    Serve tambem de peneira para o que se encontra no disco (RN-W-02, RN-W-03):
    pasta ou arquivo cujo nome nao passa aqui nao foi escrito pelo app, e nao
    entra na wiki - nem no indice, nem em `listar`.
    """
    return bool(nome) and nome not in NOMES_RESERVADOS and slug(nome) == nome


def caminho(entidade: str, propriedade: str) -> str:
    """O caminho logico qualificado, "entidade/propriedade" (RN-W-33).

    Aceita titulo ou slug, indiferentemente: o resultado e sempre o canonico
    (R-CG3-3, PBT-U3-05).
    """
    return f"{slug(entidade)}/{slug(propriedade)}"


def normalizar_valor(valor: str) -> str:
    """O valor que vai para uma linha `chave: valor` do frontmatter.

    Quebra de linha e tabulacao viram espaco - senao o valor partiria o bloco.
    Depois apara as bordas e tira aspas externas balanceadas ate nao sobrar
    par - senao o leitor, que tira um par (RN-W-15), devolveria outra coisa.

    E o que faz o round-trip (PBT-U3-03) valer para qualquer entrada: o que volta
    da leitura e exatamente normalizar_valor(o que foi proposto). Idempotente:
    normalizar_valor(normalizar_valor(x)) == normalizar_valor(x).

    [Correcao 2026-10-01 / Code Generation] O plano dizia "remove UM par". Com
    um so, '""x""' sairia '"x"', o leitor devolveria 'x', e cairiam juntos o
    round-trip e a idempotencia que o proprio plano exige. O mesmo vale para
    '" x "': tirado o par, sobra espaco na borda. Por isso o laco aparar/tirar
    par vai ate o ponto fixo.
    """
    texto = _QUEBRAS.sub(" ", valor)
    while True:
        texto = texto.strip()
        if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in _ASPAS:
            texto = texto[1:-1]
            continue
        return texto
