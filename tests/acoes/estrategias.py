"""Geradores de Hypothesis para U5, e o que todo teste da unidade monta igual.

Reaproveita U4 (`ambientes_de_partida`, `novo_servico`, ORQUESTRADOR,
BIBLIOTECARIO, `executar`, `ponderado`) em vez de redefinir (PBT-07): o
ambiente de onde as propriedades partem e o mesmo que ja exercitou o servico.

O catalogo e sempre testado contra o ServicoDeAmbiente REAL, sobre o
RepositorioEmMemoria. A wiki e a de arquivos, numa pasta que nunca chega a
existir: nenhuma das 7 acoes toca a wiki (o ciclo de vida do ambiente ficou
fora, Q1=A), entao o ambiente de partida e semeado so no repositorio.
"""

import copy
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hypothesis import strategies as st

from fishingrod.adaptadores.wiki import WikiDeArquivos
from fishingrod.aplicacao.catalogo.argumentos import (
    AUSENTE,
    DESCONHECIDO,
    LONGO_DEMAIS,
    MAIOR_POSICAO,
    OPCAO,
    TIPO,
    sem_maiuscula_nem_acento,
)
from fishingrod.aplicacao.catalogo.catalogo import CatalogoDeAcoes, comando_de
from fishingrod.aplicacao.catalogo.registro import ACOES
from fishingrod.aplicacao.catalogo.parser import ParserDeComando
from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    Acionamento,
    Alvo,
    MotivoFalha,
    Parametro,
    Resultado,
    TipoParametro,
)
from fishingrod.aplicacao.portas.persistencia import (
    AmbienteInexistente,
    BancoIlegivel,
    ConflitoDeVersao,
    EsquemaIncompativel,
)
from fishingrod.aplicacao.portas.wiki import ArmazenamentoIndisponivel, PaginaInexistente
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    AgenteDesconhecido,
    EtapaInexistente,
    FrenteInexistente,
    ServicoDeAmbiente,
    SessaoInexistente,
    TarefaInexistente,
)
from fishingrod.dominio import (
    AgenteInvalido,
    Chamador,
    Ambiente,
    Frente,
    Identidade,
    NomeInvalido,
    OrquestradorDuplicado,
    Tarefa,
)
from tests.ambiente.estrategias import (
    BIBLIOTECARIO,
    ORQUESTRADOR,
    ambientes_de_partida,
    executar,
    executores,
    novo_servico,
    pasta_de_dados,
    ponderado,
)
from tests.ambiente.instrumentos import FalhaInjetadaNoBanco
from tests.dobles.repositorio_memoria import RepositorioEmMemoria

REGISTRO: dict[str, Acao] = {acao.nome: acao for acao in ACOES}
NOMES_DAS_ACOES = tuple(REGISTRO)
# As que o agente pode acionar: criar_sessao e so do usuario (D21).
NOMES_DAS_ACOES_DO_AGENTE = tuple(acao.nome for acao in ACOES if Chamador.AGENTE in acao.chamadores)

# Um id que nao existe em ambiente nenhum. Constante, e nao Identidade.nova():
# o exemplo encolhido precisa ser o mesmo na reexecucao.
INEXISTENTE = Identidade("00000000-0000-0000-0000-000000000000")


# --------------------------------------------------------------------------
# A montagem
# --------------------------------------------------------------------------


@dataclass
class Montagem:
    catalogo: CatalogoDeAcoes
    servico: ServicoDeAmbiente  # o real
    repositorio: RepositorioEmMemoria
    visto: Any  # o que o catalogo recebeu: o servico real ou um instrumento dele

    async def aberto(self, id_ambiente: Identidade) -> Ambiente:
        return await self.servico.carregar_ambiente(id_ambiente)


async def montar(
    tmp_path: Path,
    ambiente: Ambiente | None,
    confirmacao: Any,
    *,
    instrumento: Any = None,
    acoes: tuple[Acao, ...] = ACOES,
) -> Montagem:
    """O catalogo como U9 vai monta-lo, sobre um ambiente que ja existe - como
    se outra sessao o tivesse criado. `instrumento` embrulha o servico real
    (ServicoEspiao, ServicoSabotado) antes de o catalogo recebe-lo.

    Semeia uma COPIA, com versao zero: o mesmo ambiente gerado pode semear dois
    repositorios (PBT-U5-07), e o objeto do teste fica intocado para servir de
    referencia."""
    repositorio = RepositorioEmMemoria()
    if ambiente is not None:
        semente = copy.deepcopy(ambiente)
        semente.versao = 0
        await repositorio.salvar_ambiente(semente)
    servico = novo_servico(repositorio, WikiDeArquivos(pasta_de_dados(tmp_path)))
    visto = servico if instrumento is None else instrumento(servico)
    return Montagem(CatalogoDeAcoes(visto, confirmacao, acoes), servico, repositorio, visto)


def tarefas_de(ambiente: Ambiente) -> list[tuple[Frente, Tarefa]]:
    return [(frente, tarefa) for frente in ambiente.frentes for tarefa in frente.tarefas]


def alvo_da_tarefa(ambiente: Ambiente, frente: Frente, tarefa: Tarefa) -> Alvo:
    """O alvo que U9 amarra a um chat: o ambiente, a frente da tarefa, a
    tarefa e a sessao do chat - aqui, a primeira (RN-AC-11)."""
    return Alvo(ambiente.id, frente.id, tarefa.id, tarefa.sessoes[0].id)


def tarefa_com_etapas(ambiente: Ambiente) -> tuple[Frente, Tarefa]:
    """`ambientes_de_partida` garante que existe."""
    return next((f, t) for f, t in tarefas_de(ambiente) if t.etapas)


@st.composite
def ambientes_de_uma_tarefa(draw: Any, minimo: int = 0, maximo: int = 6) -> Ambiente:
    """Uma frente, uma tarefa e de `minimo` a `maximo` etapas, parte delas ja
    concluida - para as propriedades de posicao (PBT-U5-08, PBT-U5-09)."""
    ambiente = Ambiente("Nexo")
    tarefa = ambiente.criar_frente("Comercial").criar_tarefa("Campanha", ORQUESTRADOR)
    for _ in range(draw(st.integers(min_value=minimo, max_value=maximo))):
        etapa = tarefa.criar_etapa(draw(palavras), draw(executores))
        if draw(st.booleans()):
            etapa.concluir()
    return ambiente


# --------------------------------------------------------------------------
# Texto e espaco (R-CG5-6)
# --------------------------------------------------------------------------

# Todo caractere que str.isspace() diz que e espaco - os mesmos que strip() e
# split() cortam. Inclui tabulacao, espaco nao separavel, os separadores de
# informacao (\x1c-\x1f) e o separador de linha Unicode.
ESPACOS = tuple(c for c in map(chr, range(sys.maxunicode + 1)) if c.isspace())

separadores = st.text(st.sampled_from(ESPACOS), min_size=1, max_size=3)

# Sem surrogate e sem controle, como em U2; e sem nenhum espaco, porque e uma
# palavra.
_SEM_ESPACO = st.characters(
    exclude_categories=("Cs", "Cc", "Zs", "Zl", "Zp"), exclude_characters=ESPACOS
)

palavras = st.text(_SEM_ESPACO, min_size=1, max_size=12)


@st.composite
def textos_livres(draw: Any, max_palavras: int = 5) -> str:
    """Sem espaco nas pontas e com espacos variados por dentro: o texto que
    TD-11 quebrava."""
    pedacos = draw(st.lists(palavras, min_size=1, max_size=max_palavras))
    texto = pedacos[0]
    for pedaco in pedacos[1:]:
        texto += draw(separadores) + pedaco
    return texto


# Nome de comando como o parser o entrega: sem espaco, possivelmente vazio, com
# barra, hifen, sublinhado, acento e Unicode - os primeiros com peso, para nao
# dependerem da sorte.
nomes_de_comando = st.text(st.sampled_from("/-_aáÇz9") | _SEM_ESPACO, max_size=15)

_ACENTOS = {"a": "áàâãä", "e": "éêè", "i": "íî", "o": "óôõ", "u": "úü"}


@st.composite
def escritas_de(draw: Any, opcao: str) -> str:
    """A opcao com maiuscula e acento sorteados letra a letra (G4)."""
    letras = []
    for letra in opcao:
        variante = draw(st.sampled_from(letra + _ACENTOS.get(letra, "")))
        letras.append(variante.upper() if draw(st.booleans()) else variante)
    return "".join(letras)


# --------------------------------------------------------------------------
# Quem aciona
# --------------------------------------------------------------------------

acionamentos_de_agente = st.sampled_from([ORQUESTRADOR.nome, BIBLIOTECARIO.nome]).map(
    Acionamento.agente
)
acionamentos = st.one_of(st.just(Acionamento.usuario()), acionamentos_de_agente)

# O bibliotecario e o unico agente de chat; os outros caem na lista fechada de
# U4 (fora_da_lista), no passo 7.
nomes_de_agente = ponderado(
    (4, st.just(BIBLIOTECARIO.nome)), (1, st.just(ORQUESTRADOR.nome)), (1, palavras)
)


# --------------------------------------------------------------------------
# Argumentos
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Entrada:
    """Os argumentos de uma acao como quem aciona os escreve, e como o servico
    deve recebe-los depois de convertidos."""

    acao: str
    escritos: dict[str, object]
    esperados: dict[str, object]


@st.composite
def entradas_validas(
    draw: Any,
    acao: Acao,
    etapas: int = 9,
    agentes: st.SearchStrategy[str] = st.just(BIBLIOTECARIO.nome),
) -> Entrada:
    """Uma palavra para cada parametro que nao e o ultimo, texto livre para o
    ultimo, a opcao com maiuscula e acento sorteados, e uma posicao de 1 a
    `etapas` - como int ou como texto. O opcional pode faltar."""
    escritos: dict[str, object] = {}
    esperados: dict[str, object] = {}
    ultimo = acao.parametros[-1]
    for parametro in acao.parametros:
        if not parametro.obrigatorio and draw(st.booleans()):
            break  # opcional ausente: o padrao e do efetivar (R-CG5-4)
        if parametro.tipo is TipoParametro.ESCOLHA:
            canonica = draw(st.sampled_from(parametro.opcoes))
            escrito, esperado = draw(escritas_de(canonica)), canonica
        elif parametro.tipo is TipoParametro.POSICAO:
            esperado = draw(st.integers(min_value=1, max_value=max(etapas, 1)))
            escrito = str(esperado) if draw(st.booleans()) else esperado
        elif parametro.nome == "agente":
            escrito = esperado = draw(agentes)
        elif parametro is ultimo:
            escrito = esperado = draw(textos_livres())
        else:
            escrito = esperado = draw(palavras)
        escritos[parametro.nome] = escrito
        esperados[parametro.nome] = esperado
    return Entrada(acao.nome, escritos, esperados)


def valores_da_barra(acao: Acao, argumentos: dict[str, object]) -> list[str] | None:
    """Os argumentos como palavras da barra, na ordem - ou None quando a barra
    nao consegue escreve-los: chave desconhecida, buraco no meio, valor que
    nao e texto, so espacos, ou espaco dentro de quem nao e o ultimo."""
    if set(argumentos) - {parametro.nome for parametro in acao.parametros}:
        return None
    valores: list[str] = []
    for indice, parametro in enumerate(acao.parametros):
        if parametro.nome not in argumentos:
            depois = acao.parametros[indice + 1 :]
            return None if any(p.nome in argumentos for p in depois) else valores
        valor = argumentos[parametro.nome]
        if parametro.tipo is TipoParametro.POSICAO and type(valor) in (int, bool, float):
            valor = str(valor)
        if not isinstance(valor, str) or not valor.strip() or valor != valor.strip():
            return None
        if parametro is not acao.parametros[-1] and any(c.isspace() for c in valor):
            return None
        valores.append(valor)
    return valores


@st.composite
def linhas(draw: Any, comando: str, valores: list[str]) -> str:
    """`/comando` e os valores com 1 a 3 espacos quaisquer entre eles, e as
    vezes espaco sobrando no fim."""
    linha = "/" + comando
    for valor in valores:
        linha += draw(separadores) + valor
    if draw(st.booleans()):
        linha += draw(separadores)
    return linha


def linhas_de(entrada: Entrada) -> st.SearchStrategy[str]:
    valores = valores_da_barra(REGISTRO[entrada.acao], entrada.escritos)
    assert valores is not None, "entrada valida sempre cabe na barra"
    return linhas(comando_de(entrada.acao), valores)


# --- uma violacao (PBT-U5-10) ------------------------------------------------

_TIPO_ERRADO_TEXTO = st.one_of(
    st.integers(),
    st.floats(),
    st.booleans(),
    st.lists(st.text(max_size=3), max_size=2),
    st.binary(max_size=3),
)
_TIPO_ERRADO_POSICAO = st.one_of(
    st.booleans(),
    st.floats(),
    st.integers(max_value=0),
    st.integers(min_value=MAIOR_POSICAO + 1),
    st.sampled_from(["dois", "1.5", "-1", "0", "00", "٢", "1e3", " 2", "1234567890", "+3"]),
)


@dataclass(frozen=True)
class Violacao:
    """Argumentos com exatamente uma violacao, e o detalhe que ela deve dar."""

    argumentos: dict[str, object]
    detalhe: dict[str, str]


def casos_de_violacao(acao: Acao) -> list[tuple[str, Parametro | None]]:
    """Toda violacao que cabe nesta acao, uma por (tipo, parametro)."""
    obrigatorios = [p for p in acao.parametros if p.obrigatorio]
    casos: list[tuple[str, Parametro | None]] = [("ausente", p) for p in obrigatorios]
    casos += [("nulo", p) for p in obrigatorios]
    casos += [("espacos", p) for p in obrigatorios]
    casos += [("desconhecida", None)]
    casos += [("tipo", p) for p in acao.parametros]
    casos += [("opcao", p) for p in acao.parametros if p.tipo is TipoParametro.ESCOLHA]
    casos += [("longo", p) for p in acao.parametros if p.tipo is TipoParametro.TEXTO]
    return casos


TIPOS_DE_VIOLACAO = ("ausente", "nulo", "espacos", "desconhecida", "tipo", "opcao", "longo")


@st.composite
def violacoes(draw: Any, acao: Acao, tipo: str | None = None) -> Violacao:
    """Parte de argumentos validos e quebra UMA coisa: obrigatorio faltando,
    None, so espacos, chave a mais, tipo errado, fora das opcoes ou acima do
    maximo. Com `tipo`, so violacoes daquele tipo."""
    argumentos = dict(draw(entradas_validas(acao)).escritos)
    nomes = {parametro.nome for parametro in acao.parametros}
    casos = [caso for caso in casos_de_violacao(acao) if tipo is None or caso[0] == tipo]
    caso, parametro = draw(st.sampled_from(casos))

    if caso == "ausente":
        argumentos.pop(parametro.nome, None)
        return Violacao(argumentos, {"parametro": parametro.nome, "problema": AUSENTE})
    if caso == "nulo":
        argumentos[parametro.nome] = None
        return Violacao(argumentos, {"parametro": parametro.nome, "problema": AUSENTE})
    if caso == "espacos":
        argumentos[parametro.nome] = draw(separadores)
        return Violacao(argumentos, {"parametro": parametro.nome, "problema": AUSENTE})
    if caso == "desconhecida":
        chave = draw(
            st.sampled_from(["autor", "id_tarefa", "frente", "Nome", "posição"])
            | palavras.filter(lambda p: p not in nomes)
        )
        argumentos[chave] = draw(st.one_of(st.none(), palavras, st.integers()))
        return Violacao(argumentos, {"parametro": chave, "problema": DESCONHECIDO})
    if caso == "tipo":
        errado = _TIPO_ERRADO_POSICAO if parametro.tipo is TipoParametro.POSICAO else _TIPO_ERRADO_TEXTO
        argumentos[parametro.nome] = draw(errado)
        return Violacao(argumentos, {"parametro": parametro.nome, "problema": TIPO})
    if caso == "opcao":
        validas = {sem_maiuscula_nem_acento(opcao) for opcao in parametro.opcoes}
        argumentos[parametro.nome] = draw(
            palavras.filter(lambda p: sem_maiuscula_nem_acento(p) not in validas)
        )
        return Violacao(argumentos, {"parametro": parametro.nome, "problema": OPCAO})
    # longo: um caractere ou mais acima do maximo, sem espaco nenhum
    base = draw(palavras)
    excesso = draw(st.integers(min_value=1, max_value=30))
    tamanho = parametro.maximo + excesso
    argumentos[parametro.nome] = (base * (tamanho // len(base) + 1))[:tamanho]
    return Violacao(
        argumentos,
        {"parametro": parametro.nome, "problema": LONGO_DEMAIS, "maximo": str(parametro.maximo)},
    )


# --- qualquer coisa (PBT-U5-03) ----------------------------------------------

_NOMES_DE_PARAMETRO = sorted({p.nome for acao in ACOES for p in acao.parametros})

valores_quaisquer = st.one_of(
    st.text(max_size=30),
    st.integers(min_value=-5, max_value=12),
    st.booleans(),
    st.none(),
    st.floats(),
    st.lists(st.integers(), max_size=2),
)

argumentos_quaisquer = st.dictionaries(
    st.sampled_from([*_NOMES_DE_PARAMETRO, "autor", "id_tarefa"]) | st.text(max_size=8),
    valores_quaisquer,
    max_size=4,
)

nomes_quaisquer = ponderado(
    (6, st.sampled_from(NOMES_DAS_ACOES)),
    (1, st.sampled_from(["criar-tarefa", "enviar_mensagem", "criar_ambiente", "", "CRIAR_FRENTE"])),
    (1, st.text(max_size=12)),
)


def _ids(ids: list[Identidade]) -> st.SearchStrategy[Identidade | None]:
    if not ids:
        return ponderado((1, st.just(INEXISTENTE)), (1, st.none()))
    return ponderado((6, st.sampled_from(ids)), (1, st.just(INEXISTENTE)), (1, st.none()))


@st.composite
def alvos_quaisquer(draw: Any, ambiente: Ambiente) -> Alvo:
    """Identidades existentes na maior parte das vezes; inexistentes ou
    ausentes no resto."""
    pares = tarefas_de(ambiente)
    return Alvo(
        draw(ponderado((8, st.just(ambiente.id)), (1, st.just(INEXISTENTE)))),
        draw(_ids([frente.id for frente in ambiente.frentes])),
        draw(_ids([tarefa.id for _, tarefa in pares])),
        draw(_ids([sessao.id for _, tarefa in pares for sessao in tarefa.sessoes])),
    )


# A resposta da porta. So `True` confirma; os outros sao os que um `if
# resposta:` deixaria passar (1, "sim", "True") ou nao.
RESPOSTAS_QUE_NAO_CONFIRMAM = (False, None, 0, 1, "sim", "True", [], "nao")
respostas_que_nao_confirmam = st.sampled_from(RESPOSTAS_QUE_NAO_CONFIRMAM)
# As que nao confirmam vem primeiro: o Hypothesis favorece a primeira opcao.
respostas = ponderado((3, respostas_que_nao_confirmam), (2, st.just(True)))


# --------------------------------------------------------------------------
# Excecoes (domain-entities.md 5.3)
# --------------------------------------------------------------------------

# Toda linha da tabela, com o motivo que ela deve dar - mais tres defeitos
# quaisquer. As classes servem de fabrica: cada sabotagem levanta uma
# instancia nova.
ERROS_DA_TABELA: tuple[tuple[type[Exception], MotivoFalha], ...] = (
    (AmbienteInexistente, MotivoFalha.ALVO_INEXISTENTE),
    (FrenteInexistente, MotivoFalha.ALVO_INEXISTENTE),
    (TarefaInexistente, MotivoFalha.ALVO_INEXISTENTE),
    (SessaoInexistente, MotivoFalha.ALVO_INEXISTENTE),
    (EtapaInexistente, MotivoFalha.ALVO_INEXISTENTE),
    (AgenteDesconhecido, MotivoFalha.ARGUMENTO_INVALIDO),
    (ConflitoDeVersao, MotivoFalha.CONFLITO),
    (BancoIlegivel, MotivoFalha.FALHA_DE_ARMAZENAMENTO),
    (EsquemaIncompativel, MotivoFalha.FALHA_DE_ARMAZENAMENTO),
    (FalhaInjetadaNoBanco, MotivoFalha.FALHA_DE_ARMAZENAMENTO),
    (ArmazenamentoIndisponivel, MotivoFalha.FALHA_DE_ARMAZENAMENTO),
    (PaginaInexistente, MotivoFalha.FALHA_DE_ARMAZENAMENTO),
    (NomeInvalido, MotivoFalha.REGRA_VIOLADA),
    (OrquestradorDuplicado, MotivoFalha.REGRA_VIOLADA),
    (AgenteInvalido, MotivoFalha.REGRA_VIOLADA),
    (RuntimeError, MotivoFalha.FALHA_INESPERADA),
    (KeyError, MotivoFalha.FALHA_INESPERADA),
    (TypeError, MotivoFalha.FALHA_INESPERADA),
)

erros_da_tabela = st.sampled_from(ERROS_DA_TABELA)

# Onde a sabotagem acontece: na leitura do passo 5 ou na operacao do passo 7.
LEITURA = "leitura"
OPERACAO = "operacao"
lugares_de_sabotagem = st.sampled_from([LEITURA, OPERACAO])

# Texto qualquer para a barra: o que vem depois do nome.
textos_da_barra = st.one_of(st.just(""), textos_livres(), st.text(max_size=20))


# --------------------------------------------------------------------------
# Sequencias de comandos do usuario (PBT-U5-06)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Passo:
    """Um comando do usuario. `acao` e o nome no registro a que ele chega, ou
    None quando nao chega a nenhum; `como_chegou` e o nome como foi escrito
    (com hifen, pela barra). `linha` existe quando o comando vem pela barra.
    `violacao` e o detalhe que o passo 4 deve dar, quando ha uma."""

    acao: str | None
    como_chegou: str
    alvo: Alvo
    argumentos: dict[str, object]
    esperados: dict[str, object]
    linha: str | None
    violacao: dict[str, str] | None

    async def executar(self, catalogo: CatalogoDeAcoes) -> Resultado:
        if self.linha is not None:
            return await catalogo.executar_comando(ParserDeComando().interpretar(self.linha), self.alvo)
        return await catalogo.executar(self.como_chegou, self.alvo, self.argumentos, Acionamento.usuario())


# Nomes que nao chegam a acao nenhuma: G7 (sublinhado na barra, hifen fora
# dela), maiuscula, nome vazio, comando da tela e acao que nao existe.
_DESCONHECIDOS_NA_BARRA = ["criar_tarefa", "criar-projeto", "", "ajuda", "Criar-Frente", "criar--frente"]
_DESCONHECIDOS_POR_NOME = ["criar-tarefa", "criar_projeto", "", "enviar_mensagem", "CRIAR_FRENTE"]


@st.composite
def passos(draw: Any, vista: Any) -> Passo:
    """Um comando sobre o ambiente que `vista` (o AmbienteModelo de U4)
    descreve: pela barra ou por argumentos, com alvo existente, inexistente ou
    ausente, argumentos validos ou com uma violacao, posicao dentro ou fora.

    A violacao so vai pela barra quando a barra consegue escreve-la; senao, o
    mesmo passo vai por argumentos.
    """
    tarefas = vista.tarefas()
    alvo = Alvo(
        draw(ponderado((12, st.just(vista.id)), (1, st.just(INEXISTENTE)))),
        draw(_ids([frente.id for frente in vista.frentes])),
        draw(_ids([tarefa.id for tarefa in tarefas])),
        draw(_ids([sessao.id for sessao in vista.sessoes()])),
    )
    pela_barra = draw(st.booleans())
    if not draw(ponderado((12, st.just(True)), (1, st.just(False)))):
        nome = draw(st.sampled_from(_DESCONHECIDOS_NA_BARRA if pela_barra else _DESCONHECIDOS_POR_NOME))
        linha = draw(linhas(nome, [draw(palavras)])) if pela_barra else None
        return Passo(None, nome, alvo, {}, {}, linha, None)

    acao = REGISTRO[draw(st.sampled_from(NOMES_DAS_ACOES))]
    tarefa = next((t for t in tarefas if t.id == alvo.id_tarefa), None)
    etapas = len(tarefa.etapas) if tarefa is not None else 0
    # Ate duas posicoes alem do fim: ALVO_INEXISTENTE com posicao e total.
    entrada = draw(entradas_validas(acao, etapas=etapas + 2, agentes=nomes_de_agente))
    argumentos, violacao = entrada.escritos, None
    if draw(ponderado((4, st.just(False)), (1, st.just(True)))):
        quebrada = draw(violacoes(acao))
        argumentos, violacao = quebrada.argumentos, quebrada.detalhe

    linha = None
    if pela_barra:
        valores = valores_da_barra(acao, argumentos)
        if valores is not None:
            linha = draw(linhas(comando_de(acao.nome), valores))
    como_chegou = comando_de(acao.nome) if linha is not None else acao.nome
    return Passo(acao.nome, como_chegou, alvo, argumentos, entrada.esperados, linha, violacao)
