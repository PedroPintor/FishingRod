"""Porta de wiki: o contrato, os tipos de fronteira e os erros.

Este e o unico arquivo de U3 que as outras unidades importam. U4, U8 e o
composition root de U9 dependem daqui - nunca de `adaptadores/wiki` (DP-W-09).
A excecao nomeada e `aplicacao/caminho_wiki.py`, importavel por decisao
(DP-W-02): ele produz o caminho logico, que e vocabulario desta porta.

RN-W-36 / D-ARQ-08: nenhuma assinatura menciona Path, open, extensao de arquivo
ou erro do sistema operacional. Se mencionasse, a abstracao seria decorativa.
Por isso este modulo tambem nao importa `pathlib` nem `os`.
"""

from dataclasses import dataclass
from typing import Protocol


# --------------------------------------------------------------------------
# Erros (domain-entities.md 6)
# --------------------------------------------------------------------------
# Driver nao atravessa porta (R-FD3-7, NFR-W-13): nenhum OSError,
# PermissionError ou FileNotFoundError escapa do adaptador. Toda falha chega
# como uma destas sete.


class ErroDeWiki(Exception):
    """Raiz da hierarquia. Quem quiser tratar tudo captura esta."""


class LocalizadorNaoReconhecido(ErroDeWiki):
    """RN-W-09: o localizador usa um esquema que este adaptador nao atende.

    Nao e o mesmo que LocalizadorInvalido, de U1 (R-CG3-2). Aquele diz que o
    dominio montou o localizador errado; este diz que o localizador pode estar
    bem formado, mas fala de um lugar que este adaptador nao sabe abrir. Nao
    assume, nao adivinha.
    """


class CaminhoForaDaRaiz(ErroDeWiki):
    """RN-W-07, PBT-U3-01: o caminho nao designa um lugar dentro da wiki.

    Cobre a tentativa de escapar (`..`, symlink apontando para fora) e tambem o
    caminho que o modelo de dois niveis nao tem (RN-W-01): pedir um terceiro
    nivel e pedir um lugar que a wiki nao tem.
    """


class PaginaInexistente(ErroDeWiki):
    """`ler` de uma pagina que nao existe."""


class EntidadeInexistente(ErroDeWiki):
    """RN-W-28: escrever ou listar sob uma entidade que nao existe.

    Mesmo tipo de pre-condicao que AmbienteInexistente foi em U2 (RN-P-27) - la
    descoberta por um teste de propriedade durante a geracao de codigo, aqui
    desenhada antes.
    """


class DescricaoObrigatoria(ErroDeWiki):
    """RN-W-14: proposta com descricao vazia, recusada antes de tocar o disco.

    Vazia e tambem a que so tem espaco ou aspas: a regua e o valor depois de
    `caminho_wiki.normalizar_valor`, que e o que iria para o arquivo.
    """


class TituloInvalido(ErroDeWiki):
    """RN-W-05: titulo cujo slug sai vazio ou e reservado pelo sistema."""


class ArmazenamentoIndisponivel(ErroDeWiki):
    """Falha de I/O traduzida (NFR-W-13). Nunca o erro do sistema cru, e nunca
    com caminho absoluto na mensagem (NFR-W-17)."""


# --------------------------------------------------------------------------
# Tipos de fronteira (domain-entities.md 4)
# --------------------------------------------------------------------------
# Nao sao entidades de dominio: sao o vocabulario da porta. Vivem aqui porque o
# dominio nao sabe que existe disco.


@dataclass(frozen=True)
class ConteudoPagina:
    """O que `ler` devolve.

    Sem marca de proveniencia nem tamanho (Q10, versao enxuta): RNF-14 esta
    relaxada nesta iteracao, com risco aceito e condicao de reabertura em
    business-rules.md. O embrulho "isto e dado, nao instrucao" e de U8.
    """

    caminho: str  # logico, qualificado e canonico: "clientes/dr-marcelo" (R-CG3-3)
    titulo: str  # do frontmatter; "" quando ausente
    descricao: str  # do frontmatter; "" quando ausente
    conteudo: str  # o corpo, ja sem o bloco de frontmatter


@dataclass(frozen=True)
class PaginaProposta:
    """Uma pagina dentro de uma proposta.

    `entidade` e `titulo` sao titulos; o nome no disco e o slug deles, gerado
    uma vez e nunca recalculado (RN-W-03). Passar o slug no lugar do titulo da
    o mesmo resultado, porque slug(slug(x)) == slug(x) (PBT-U3-05) - e e isso
    que deixa o agente usar o caminho que leu no indice.

    `conteudo` e a pagina INTEIRA (C4=A, RN-W-26), nao um fragmento. Nem o
    agente nem U8 escrevem o bloco `---`: quem monta o frontmatter e o
    adaptador (RN-W-13).
    """

    entidade: str
    titulo: str
    descricao: str  # obrigatoria, nao vazia (RN-W-14)
    conteudo: str


@dataclass(frozen=True)
class PropostaWiki:
    """Um conjunto coerente de escritas, aprovado de uma vez - `aprovar` e um ato
    por promocao (component-methods.md 3.3).

    `entidades_novas` existe para a entidade que nasce vazia. Pedir de novo uma
    entidade que ja existe e no-op (RN-W-06).
    """

    entidades_novas: tuple[str, ...] = ()
    paginas: tuple[PaginaProposta, ...] = ()


# --------------------------------------------------------------------------
# O contrato
# --------------------------------------------------------------------------


class PortaWiki(Protocol):
    """As cinco operacoes. Semantica completa em business-logic-model.md 2-5;
    `apagar` foi acrescentada por U4 (Q6=A) e esta em
    construction/ambiente/functional-design/domain-entities.md 5.

    `localizador` e o texto de RaizWiki ("dados:wikis/<id>"), e os caminhos sao
    logicos ("clientes/dr-marcelo", sem extensao) - nunca caminho de sistema
    (RN-W-08).
    """

    async def listar(self, localizador: str, caminho: str) -> list[str]:
        """`caminho` vazio lista as entidades; o nome de uma entidade lista as
        paginas dela, sem extensao. Devolve nomes em ordem alfabetica, e so
        nomes (RN-W-37).

        Raiz que ainda nao existe devolve lista vazia, sem criar nada
        (NFR-W-06): a wiki ainda nao foi renderizada, e isso nao e erro.
        """
        ...

    async def ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina:
        """`caminho_pagina` tem exatamente dois segmentos, "entidade/pagina".
        Um, ou tres ou mais, e CaminhoForaDaRaiz: nao existe nivel 3 (RN-W-01).

        Frontmatter ausente devolve titulo e descricao vazios, e a leitura NAO
        falha (RN-W-15). Sem limite de tamanho (RN-W-32).
        """
        ...

    async def escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None:
        """Valida a proposta inteira antes de tocar o disco (DP-W-10), depois
        cria as entidades e por fim escreve as paginas (RN-W-29).

        Nao e atomica: falha de I/O no meio deixa o que ja foi escrito, e o
        indice renderizado em seguida mostra exatamente o que aterrissou. A
        porta nao compara com o que havia - a rede e a aprovacao humana
        (RN-W-27).

        Quem chama: ServicoBibliotecario.aprovar (U8), depois da aprovacao, e
        ServicoDeAmbiente (U4), com a semente do esquema.
        """
        ...

    async def renderizar_index(self, localizador: str, nome: str) -> None:
        """Reescreve o index.md por inteiro a partir do disco (RN-W-17), sem LLM
        (RN-W-23) e sem ler o indice anterior. Cria a raiz se ela nao existir
        (RN-W-25) - e o que faz a wiki nascer mesmo com esquema vazio.

        `nome` e o nome do ambiente, para o cabecalho (RN-W-24).
        """
        ...

    async def apagar(self, localizador: str) -> None:
        """Remove a raiz da wiki inteira, com tudo que ha dentro.

        Raiz que nao existe e operacao vazia bem-sucedida, como apagar_ambiente
        em U2 (RN-P-22) - por isso apagar duas vezes e o mesmo que apagar uma
        (PBT-U3-08). Nada fora da raiz e removido, nem atraves de link.

        Raiz que existe mas nao tem index.md e recusada com CaminhoForaDaRaiz
        (R-CG4-2): toda wiki que o app cria tem indice, e um localizador
        adulterado que apontasse para uma pasta acima, como "dados:wikis", nao
        pode levar as wikis de todos os ambientes junto.

        Quem chama: so ServicoDeAmbiente.apagar_ambiente (U4), depois de o
        ambiente ter saido do banco.
        """
        ...
