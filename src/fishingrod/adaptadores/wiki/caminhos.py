"""O arquivo de seguranca da unidade: onde o caminho logico vira Path.

DP-W-01: `resolver_sob` e o UNICO produtor de Path do adaptador. Nenhum metodo
monta caminho por conta propria - para violar o confinamento seria preciso
escrever `raiz / algo` a mao em outro arquivo, o que salta aos olhos em
revisao. E o mesmo raciocinio que fez U2 ligar o PRAGMA uma vez, na abertura:
nao deixar preambulo para esquecer.

RN-W-07 em tres etapas, e as tres juntas e que satisfazem PBT-U3-01 - nenhuma
sozinha:
    1. slug, que ja elimina "/", "\\" e ".." - aplicado por quem chama, com
       caminho_wiki; aqui so se confere;
    2. montagem sob a raiz;
    3. resolve() dos dois lados - que atravessa symlink - e comparacao por
       componente com a raiz resolvida (NFR-W-05, TS-W-01).

Nada aqui cria diretorio (NFR-W-06): resolve() nao exige que o caminho exista.
Enquanto a raiz nao existe, a garantia e de prefixo; o que aparece depois, como
um symlink plantado dentro da wiki, e pego no caminho de cada arquivo (Q2=B).
"""

from pathlib import Path

from fishingrod.aplicacao.caminho_wiki import slug_valido
from fishingrod.aplicacao.portas.wiki import CaminhoForaDaRaiz, LocalizadorNaoReconhecido
from fishingrod.dominio.raiz_wiki import ESQUEMA_PADRAO


def resolver_raiz(raiz_de_dados: Path, localizador: str) -> Path:
    """A raiz da wiki de um ambiente, a partir de "dados:wikis/<id>".

    O adaptador nao constroi RaizWiki (R-CG3-2): interpreta o texto. Esquema
    diferente de `dados` levanta LocalizadorNaoReconhecido (RN-W-09) - nao
    assume, nao adivinha. O resto do localizador passa pelo mesmo confinamento
    de qualquer caminho, agora contra a raiz de dados: um localizador
    adulterado no banco nao leva a wiki para fora dela.
    """
    esquema, separador, relativo = localizador.partition(":")
    if not separador or esquema != ESQUEMA_PADRAO:
        raise LocalizadorNaoReconhecido(
            f"o localizador [{localizador}] nao usa o esquema [{ESQUEMA_PADRAO}:]"
        )
    try:
        return resolver_sob(raiz_de_dados.resolve(), relativo)
    except CaminhoForaDaRaiz as erro:
        raise CaminhoForaDaRaiz(
            f"o localizador [{localizador}] nao aponta para dentro da pasta de dados"
        ) from erro


def resolver_sob(raiz: Path, caminho_logico: str, sufixo: str = "") -> Path:
    """O Path de `caminho_logico` sob `raiz`, ja resolvido - ou CaminhoForaDaRaiz.

    `caminho_logico` sao segmentos separados por "/", cada um um slug valido.
    `sufixo` e constante do adaptador (".md" para pagina e indice, "" para
    pasta), nunca entrada externa.

    `raiz` chega JA RESOLVIDA - e o que resolver_raiz devolve. Os dois lados
    passam por resolve() (NFR-W-05), mas a raiz passa uma vez por operacao, e
    nao uma vez por arquivo: no Windows cada resolve() abre o caminho duas
    vezes, e resolver a raiz a cada pagina dobrava o custo da renderizacao
    (medido em Code Generation, contra NFR-W-02). Uma raiz passada sem resolver
    nao abre brecha: caminho resolvido nunca fica "dentro" de um caminho com
    symlink, com ".." ou relativo - o erro possivel e recusar demais, nunca
    aceitar o que sai.

    Devolve o caminho RESOLVIDO: quem escreve, escreve no lugar que foi
    verificado - e nao num nome que um symlink poderia redirecionar.
    """
    segmentos = caminho_logico.split("/")

    # Etapa 1, conferida: slug valido nao tem "/", "\", ".." nem nome
    # reservado. Segmento vazio ("a//b", "/a", "") tambem cai aqui.
    if not all(slug_valido(segmento) for segmento in segmentos):
        raise CaminhoForaDaRaiz(
            f"o caminho [{caminho_logico}] nao designa um lugar dentro da wiki"
        )

    # Etapa 2: montagem sob a raiz.
    candidato = raiz.joinpath(*segmentos[:-1], segmentos[-1] + sufixo)

    # Etapa 3, a que fecha o buraco. Sanitizar o nome nao alcanca symlink: o
    # titulo pode ser inocente e o link ja existir no disco, apontando para
    # fora. is_relative_to compara componentes, nao prefixo de texto - nao
    # confunde /dados/wiki2 com /dados/wiki.
    resolvido = candidato.resolve()
    if resolvido == raiz or not resolvido.is_relative_to(raiz):
        raise CaminhoForaDaRaiz(f"o caminho [{caminho_logico}] sai da wiki")
    return resolvido
