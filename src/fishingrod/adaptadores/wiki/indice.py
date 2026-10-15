"""O index.md como funcao pura (DP-W-07): recebe o que ja foi lido, devolve
texto. Nao abre arquivo, nao lista pasta, nao escreve.

E o que deixa a gramatica de RN-W-18 e a ordem de RN-W-21 testaveis sem disco,
e o que faz PBT-U3-02 (bytes identicos) depender so daqui: a funcao ordena por
conta propria, entao a ordem em que o sistema de arquivos devolve as entradas
nao chega ate a saida. Nenhum LLM no laco (RN-W-23).
"""

from collections.abc import Mapping

# RN-W-19, letra por letra - o travessao e o U+2014.
VAZIO = "(vazio — ainda não tem nenhuma entidade)"
SEM_PROPRIEDADES = "(sem propriedades)"


def montar_indice(nome: str, entidades: Mapping[str, Mapping[str, str]]) -> str:
    """O texto inteiro do index.md, em LF e terminado por uma quebra de linha.

    `entidades` e {slug da entidade: {slug da pagina: descricao}}, ja so com as
    paginas que entram (RN-W-20 e aplicada por quem leu o disco). Entidade sem
    pagina mostra SEM_PROPRIEDADES: o agente precisa distinguir "entidade
    vazia" de "entidade quebrada", e um cabecalho seguido de nada nao distingue.
    """
    linhas = [f"# Wiki — {_uma_linha(nome)}", "", "## Entidades", ""]
    if not entidades:
        linhas.append(VAZIO)

    for posicao, entidade in enumerate(sorted(entidades)):
        if posicao:
            linhas.append("")
        linhas += [f"### [[{entidade}]]", ""]
        paginas = entidades[entidade]
        if not paginas:
            linhas.append(SEM_PROPRIEDADES)
        for pagina in sorted(paginas):
            # Link sempre qualificado (RN-W-33): o agente passa o caminho direto
            # a `ler`, sem monta-lo.
            linhas.append(f"- [[{entidade}/{pagina}]]: {_uma_linha(paginas[pagina])}")

    return "\n".join(linhas) + "\n"


def _uma_linha(texto: str) -> str:
    """A gramatica e de linha (RN-W-18): um nome de ambiente com quebra partiria
    o cabecalho em dois. As descricoes ja chegam numa linha so - o leitor de
    cabecalho parte em LF -, mas a funcao e pura e nao depende de quem chama."""
    return texto.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
