"""WikiDeArquivos: a implementacao real da porta de wiki, sobre uma pasta de
markdown.

A leitura deste arquivo tem uma ordem: primeiro os auxiliares de I/O -
traduzindo_erros (DP-W-04) e escrever_atomico (DP-W-05) -, depois a classe,
com a casca async em cima (DP-W-03) e o miolo sincrono embaixo. Nenhum metodo
monta Path por conta propria: todo caminho sai de caminhos.resolver_sob
(DP-W-01).

Toda operacao e UMA ida ao thread (NFR-W-03): o laco que le N cabecalhos roda
inteiro do lado de la, sem await no meio, e a TUI nao congela enquanto o
indice e renderizado.
"""

import asyncio
import contextlib
import logging
import os
import shutil
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

from fishingrod.adaptadores.wiki.caminhos import resolver_raiz, resolver_sob
from fishingrod.adaptadores.wiki.frontmatter import ler_cabecalho, ler_pagina, montar
from fishingrod.adaptadores.wiki.indice import montar_indice
from fishingrod.aplicacao.caminho_wiki import normalizar_valor, slug, slug_valido
from fishingrod.aplicacao.portas.wiki import (
    ArmazenamentoIndisponivel,
    CaminhoForaDaRaiz,
    ConteudoPagina,
    DescricaoObrigatoria,
    EntidadeInexistente,
    PaginaInexistente,
    PropostaWiki,
    TituloInvalido,
)

EXTENSAO = ".md"
NOME_DO_INDICE = "index"

# NFR-W-16. O NullHandler e instalado em adaptadores/wiki/__init__.py; destino
# nenhum e configurado aqui - isso e do composition root de U9.
_log = logging.getLogger("fishingrod.wiki")


# --------------------------------------------------------------------------
# Auxiliares de I/O (DP-W-04, DP-W-05)
# --------------------------------------------------------------------------


@contextlib.contextmanager
def traduzindo_erros(acao: str, logico: str = "") -> Iterator[None]:
    """O unico lugar do adaptador que conhece OSError e UnicodeError (DP-W-04).

    O que atravessa sai como ArmazenamentoIndisponivel, com o caminho LOGICO na
    mensagem e nunca o absoluto (NFR-W-17): o str() de um OSError traz o caminho
    do sistema, entao a mensagem usa so o motivo. O erro original segue como
    __cause__, para quem depurar.

    ErroDeWiki levantado dentro do bloco passa intocado - e por isso que os
    blocos podem se aninhar.
    """
    alvo = f" [{logico}]" if logico else ""
    try:
        yield
    except UnicodeError as erro:
        # NFR-W-10: travar visivel em vez de deformar em silencio. Na leitura, e
        # o arquivo que nao e UTF-8; na escrita, o texto que nao cabe nele.
        raise ArmazenamentoIndisponivel(
            f"nao foi possivel {acao}{alvo}: o texto nao e UTF-8 valido"
        ) from erro
    except OSError as erro:
        motivo = erro.strerror or type(erro).__name__
        raise ArmazenamentoIndisponivel(f"nao foi possivel {acao}{alvo}: {motivo}") from erro


def escrever_atomico(caminho: Path, texto: str) -> None:
    """Temporario na mesma pasta + os.replace (DP-W-05, NFR-W-11): quem abrir o
    arquivo ve o anterior inteiro ou o novo inteiro, nunca meio.

    Mesma pasta porque os.replace so e atomico dentro do mesmo volume. Sem
    fsync, de proposito: hoje o unico chamador e o index.md, que e projecao
    pura (RN-W-17) - se uma queda de energia o deixar vazio, a proxima
    renderizacao o refaz. Um chamador que nao seja projecao precisa repensar
    isso antes de usar este auxiliar.
    """
    descritor, nome = tempfile.mkstemp(
        dir=caminho.parent, prefix=f".{caminho.name}.", suffix=".tmp"
    )
    temporario = Path(nome)
    try:
        with open(descritor, "w", encoding="utf-8", newline="\n") as saida:
            saida.write(texto)
        _restringir_arquivo(temporario)
        os.replace(temporario, caminho)
    except BaseException:
        with contextlib.suppress(OSError):
            temporario.unlink()
        raise


def _escrever_pagina(arquivo: Path, texto: str) -> None:
    """Direto, sem temporario (NFR-W-12): a pagina e escrita inteira (RN-W-26),
    e a nao-atomicidade da proposta foi aceita em Q7=A. A assimetria com o
    indice e deliberada - o argumento de Q7=A depende de o indice estar
    inteiro.

    newline LF explicito (RN-W-31, NFR-W-14): o padrao do Windows traduziria
    para CRLF, e o corpo nao voltaria byte a byte.
    """
    with open(arquivo, "w", encoding="utf-8", newline="\n") as saida:
        saida.write(texto)
    _restringir_arquivo(arquivo)


def _criar_diretorio(pasta: Path) -> None:
    """Cria a pasta e os ancestrais que faltarem. Pasta que ja existe e no-op
    (RN-W-06); um arquivo no lugar dela e FileExistsError, que quem chama
    traduz."""
    if pasta.is_dir():
        return
    if pasta.parent != pasta and not pasta.parent.exists():
        _criar_diretorio(pasta.parent)
    pasta.mkdir()
    _restringir_diretorio(pasta)


def _restringir_diretorio(pasta: Path) -> None:
    """NFR-W-07, identico a NFR-P-14 de U2: mesma pasta de dados, mesma
    politica (R-CG3-5). No Windows o chmod do Python so mexe no bit de
    somente-leitura e nao expressa nada disso; a raiz %LOCALAPPDATA% ja e
    privada ao usuario."""
    if os.name == "posix":
        os.chmod(pasta, 0o700)


def _restringir_arquivo(arquivo: Path) -> None:
    if os.name == "posix":
        os.chmod(arquivo, 0o600)


# --------------------------------------------------------------------------
# Nomes que chegam de fora (RN-W-03, RN-W-05, RN-W-07 etapa 1)
# --------------------------------------------------------------------------


def _nome_de_titulo(titulo: str) -> str:
    """Escrita: o nome no disco e o slug do titulo, gerado aqui e nunca
    recalculado (RN-W-03). Titulo que nao da nome valido e recusado antes de
    tocar o disco (RN-W-05)."""
    nome = slug(titulo)
    if not slug_valido(nome):
        raise TituloInvalido(f"o titulo [{titulo}] nao produz um nome valido para a wiki")
    return nome


def _caminho_de_fora(caminho: str, niveis: int, o_que: str) -> str:
    """Leitura: cada segmento vira slug, e o resultado e o caminho canonico
    (R-CG3-3) - "Clientes/Dr. Marcelo" e "clientes/dr-marcelo" levam a mesma
    pagina. Numero de segmentos diferente de `niveis`, ou segmento que nao
    sobra como nome valido, e um lugar que a wiki nao tem (RN-W-01)."""
    segmentos = [slug(segmento) for segmento in caminho.split("/")]
    if len(segmentos) != niveis or not all(slug_valido(s) for s in segmentos):
        raise CaminhoForaDaRaiz(f"[{caminho}] nao designa {o_que} da wiki")
    return "/".join(segmentos)


class WikiDeArquivos:
    """Implementa PortaWiki sobre uma pasta de markdown.

    Recebe a raiz de DADOS, nao a raiz da wiki (DP-W-08): a raiz da wiki depende
    do ambiente e chega em cada chamada pelo localizador. Um adaptador serve
    todos os ambientes. Quem chama pasta_de_dados() e o composition root de U9 -
    este adaptador nao importa nada de adaptadores/persistencia (R-FD3-1).
    """

    def __init__(self, raiz_de_dados: Path) -> None:
        self._raiz_de_dados = Path(raiz_de_dados)

    # ----------------------------------------------------------------------
    # A casca async (DP-W-03): uma ida ao thread por operacao, e so
    # ----------------------------------------------------------------------

    async def listar(self, localizador: str, caminho: str) -> list[str]:
        return await asyncio.to_thread(self._listar, localizador, caminho)

    async def ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina:
        return await asyncio.to_thread(self._ler, localizador, caminho_pagina)

    async def escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None:
        await asyncio.to_thread(self._escrever_proposta, localizador, proposta)

    async def renderizar_index(self, localizador: str, nome: str) -> None:
        await asyncio.to_thread(self._renderizar_index, localizador, nome)

    async def apagar(self, localizador: str) -> None:
        await asyncio.to_thread(self._apagar, localizador)

    # ----------------------------------------------------------------------
    # listar e ler (business-logic-model.md 2 e 3)
    # ----------------------------------------------------------------------

    def _listar(self, localizador: str, caminho: str) -> list[str]:
        """Nomes, e so (RN-W-37). Nao cria nada (NFR-W-06)."""
        with traduzindo_erros("listar", caminho):
            raiz = resolver_raiz(self._raiz_de_dados, localizador)
            if caminho == "":
                if not raiz.is_dir():
                    return []  # a wiki ainda nao foi renderizada, e isso nao e erro
                return [nome for nome, _ in self._entidades(raiz)]

            entidade = _caminho_de_fora(caminho, 1, "uma entidade")
            pasta = resolver_sob(raiz, entidade)
            if not pasta.is_dir():
                raise EntidadeInexistente(f"nao existe a entidade [{entidade}]")
            return [nome for nome, _ in self._paginas(raiz, entidade, pasta)]

    def _ler(self, localizador: str, caminho_pagina: str) -> ConteudoPagina:
        with traduzindo_erros("ler a pagina", caminho_pagina):
            raiz = resolver_raiz(self._raiz_de_dados, localizador)
            logico = _caminho_de_fora(caminho_pagina, 2, "uma pagina")
            arquivo = resolver_sob(raiz, logico, EXTENSAO)
            if not arquivo.is_file():
                raise PaginaInexistente(f"nao existe a pagina [{logico}]")
            # Sem limite de tamanho (RN-W-32), UTF-8 estrito (NFR-W-10) e sem
            # traducao de quebra de linha: o corpo volta como esta no disco.
            with open(arquivo, encoding="utf-8", newline="\n") as entrada:
                texto = entrada.read()

        titulo, descricao, conteudo = ler_pagina(texto)
        return ConteudoPagina(
            caminho=logico, titulo=titulo, descricao=descricao, conteudo=conteudo
        )

    # ----------------------------------------------------------------------
    # escrever_proposta (business-logic-model.md 4)
    # ----------------------------------------------------------------------

    def _escrever_proposta(self, localizador: str, proposta: PropostaWiki) -> None:
        with traduzindo_erros("validar a proposta"):
            raiz = resolver_raiz(self._raiz_de_dados, localizador)
            entidades, paginas = self._validar(raiz, proposta)

        # RN-W-29: entidades primeiro, paginas depois. Nao e atomica: o que
        # falhar daqui em diante e I/O real, e o que ja foi escrito fica.
        for nome, pasta in entidades:
            with traduzindo_erros("criar a entidade", nome):
                _criar_diretorio(pasta)
        for logico, arquivo, texto in paginas:
            with traduzindo_erros("escrever a pagina", logico):
                _escrever_pagina(arquivo, texto)

    def _validar(
        self, raiz: Path, proposta: PropostaWiki
    ) -> tuple[list[tuple[str, Path]], list[tuple[str, Path, str]]]:
        """DP-W-10: as verificacoes sobre a proposta INTEIRA, antes de qualquer
        escrita. E o que torna a nao-atomicidade de RN-W-29 suportavel: tudo que
        se verifica sem escrever e verificado antes.

        A ordem segue business-logic-model.md 4, com uma troca: o confinamento
        vem antes da existencia da entidade, para que nem a consulta de
        existencia olhe um caminho fora da raiz.
        """
        # 1. todo titulo produz nome valido (RN-W-05)
        novas = list(dict.fromkeys(_nome_de_titulo(t) for t in proposta.entidades_novas))
        rascunhos = []
        for pagina in proposta.paginas:
            entidade = _nome_de_titulo(pagina.entidade)
            logico = f"{entidade}/{_nome_de_titulo(pagina.titulo)}"
            rascunhos.append((entidade, logico, pagina))

        # 2. toda pagina tem descricao nao vazia (RN-W-14)
        for _, logico, pagina in rascunhos:
            if not normalizar_valor(pagina.descricao):
                raise DescricaoObrigatoria(f"a pagina [{logico}] precisa de descricao")

        # 3. todo caminho resolvido cai sob a raiz (RN-W-07)
        entidades = [(nome, resolver_sob(raiz, nome)) for nome in novas]
        paginas = []
        for _, logico, pagina in rascunhos:
            texto = montar(
                normalizar_valor(pagina.titulo),
                normalizar_valor(pagina.descricao),
                pagina.conteudo,
            )
            # Surrogate isolado - que um JSON com escape de surrogate produz -
            # nao existe em UTF-8. Descoberto aqui, a falha acontece antes de
            # abrir o arquivo; aberto para escrita, ele ja estaria truncado.
            with traduzindo_erros("preparar a pagina", logico):
                texto.encode("utf-8")
            paginas.append((logico, resolver_sob(raiz, logico, EXTENSAO), texto))

        # 4. toda entidade referida existe ou nasce nesta proposta (RN-W-28)
        criadas = set(novas)
        for entidade in dict.fromkeys(entidade for entidade, _, _ in rascunhos):
            if entidade not in criadas and not resolver_sob(raiz, entidade).is_dir():
                raise EntidadeInexistente(
                    f"a entidade [{entidade}] nao existe e nao esta entre as "
                    "entidades novas da proposta"
                )

        return entidades, paginas

    # ----------------------------------------------------------------------
    # renderizar_index (business-logic-model.md 5)
    # ----------------------------------------------------------------------

    def _renderizar_index(self, localizador: str, nome: str) -> None:
        """Projecao pura do disco (RN-W-17): nunca le o index.md anterior - ele
        e saida, nunca entrada. Renderizar duas vezes da os mesmos bytes
        (PBT-U3-02)."""
        inicio = time.perf_counter()
        with traduzindo_erros("renderizar o indice"):
            raiz = resolver_raiz(self._raiz_de_dados, localizador)
            indice = resolver_sob(raiz, NOME_DO_INDICE, EXTENSAO)
            _criar_diretorio(raiz)  # RN-W-25: e o que faz a wiki nascer vazia

            entidades: dict[str, dict[str, str]] = {}
            for entidade, pasta in self._entidades(raiz):
                entidades[entidade] = {}
                for pagina, arquivo in self._paginas(raiz, entidade, pasta):
                    descricao = self._descricao_para_o_indice(f"{entidade}/{pagina}", arquivo)
                    if descricao:
                        entidades[entidade][pagina] = descricao

            escrever_atomico(indice, montar_indice(nome, entidades))

        _log.debug(
            "indice renderizado: %d paginas em %d entidades, %.1f ms",
            sum(len(paginas) for paginas in entidades.values()),
            len(entidades),
            (time.perf_counter() - inicio) * 1000,
        )

    def _descricao_para_o_indice(self, logico: str, arquivo: Path) -> str:
        """RN-W-20 e NFR-W-10: pagina sem descricao legivel fica fora do indice,
        e o arquivo NAO e tocado - nem para consertar.

        E o unico evento silencioso por desenho, e por isso o WARNING
        (NFR-W-16): sem ele, "escrevi a pagina e ela nao aparece" vira depuracao
        por leitura de codigo.
        """
        try:
            with traduzindo_erros("ler o cabecalho", logico):
                with open(arquivo, encoding="utf-8", newline="\n") as entrada:
                    _, descricao = ler_cabecalho(entrada)  # NFR-W-01: para no fechamento
        except ArmazenamentoIndisponivel as erro:
            _log.warning("pagina [%s] fora do indice: %s", logico, erro)
            return ""
        if not descricao:
            _log.warning("pagina [%s] fora do indice: sem descricao no frontmatter", logico)
        return descricao

    # ----------------------------------------------------------------------
    # apagar (acrescentada por U4, Q6=A; domain-entities.md 5 de U4)
    # ----------------------------------------------------------------------

    def _apagar(self, localizador: str) -> None:
        """Remove a raiz inteira. Quem chama e so o ServicoDeAmbiente, depois de
        o ambiente ter saido do banco.

        A raiz sai de resolver_raiz ja resolvida: o que se remove e o lugar que
        foi verificado, e nao um nome que um link poderia redirecionar. Dentro
        dela, shutil.rmtree nao segue link - symlink e junction sao removidos
        como entrada, e o que eles apontam fica intacto (verificado no codigo
        do 3.14: os.walk com _walk_symlinks_as_files).
        """
        with traduzindo_erros("apagar a wiki"):
            raiz = resolver_raiz(self._raiz_de_dados, localizador)
            if not raiz.exists():
                return  # mesma regra de apagar_ambiente em U2 (RN-P-22)

            # R-CG4-2: o confinamento garante "dentro da pasta de dados", nao
            # "uma wiki so". Um localizador adulterado como "dados:wikis" passa
            # por ele e levaria a wiki de todos os ambientes. Toda wiki criada
            # pelo app tem indice (RN-A-14 de U4), entao a falta dele quer dizer
            # que isto nao e uma wiki.
            if not resolver_sob(raiz, NOME_DO_INDICE, EXTENSAO).is_file():
                raise CaminhoForaDaRaiz(
                    f"o localizador [{localizador}] nao aponta para uma wiki: falta o indice"
                )
            shutil.rmtree(raiz)

    # ----------------------------------------------------------------------
    # O que conta como wiki no disco (RN-W-02)
    # ----------------------------------------------------------------------

    # os.scandir, e nao Path.iterdir + is_dir: o tipo da entrada ja vem na
    # listagem, e cada is_dir de Path seria mais um stat por pagina - o custo
    # que NFR-W-02 mede. Da entrada so se usa o nome; o caminho que se abre
    # continua saindo de resolver_sob (DP-W-01).

    def _entidades(self, raiz: Path) -> list[tuple[str, Path]]:
        """So pasta na raiz e entidade - e so se o nome for slug valido (RN-W-03:
        o nome no disco e o slug) e se ela resolver dentro da raiz. index.md,
        arquivo solto e pasta de outro programa ficam de fora, sem aviso."""
        encontradas = []
        with os.scandir(raiz) as entradas:
            for entrada in entradas:
                if slug_valido(entrada.name) and entrada.is_dir():
                    pasta = self._dentro_da_raiz(raiz, entrada.name)
                    if pasta is not None:
                        encontradas.append((entrada.name, pasta))
        return sorted(encontradas)  # RN-W-21: nunca a ordem do sistema de arquivos

    def _paginas(self, raiz: Path, entidade: str, pasta: Path) -> list[tuple[str, Path]]:
        """So .md dentro de entidade e propriedade, com o mesmo filtro de nome.
        Subpasta dentro de entidade seria o nivel 3, que nao existe (RN-W-01)."""
        encontradas = []
        with os.scandir(pasta) as entradas:
            for entrada in entradas:
                nome = entrada.name.removesuffix(EXTENSAO)
                if entrada.name.endswith(EXTENSAO) and slug_valido(nome) and entrada.is_file():
                    arquivo = self._dentro_da_raiz(raiz, f"{entidade}/{nome}", EXTENSAO)
                    if arquivo is not None:
                        encontradas.append((nome, arquivo))
        return sorted(encontradas)

    @staticmethod
    def _dentro_da_raiz(raiz: Path, logico: str, sufixo: str = "") -> Path | None:
        """Entrada do disco que resolve fora da raiz - um symlink plantado - e
        ignorada, nao seguida. Vai para o log porque ninguem planta isso por
        acaso."""
        try:
            return resolver_sob(raiz, logico, sufixo)
        except CaminhoForaDaRaiz:
            _log.warning("entrada [%s] ignorada: resolve fora da raiz da wiki", logico)
            return None
