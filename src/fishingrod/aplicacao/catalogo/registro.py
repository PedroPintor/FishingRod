"""O registro: as 7 acoes do ambiente, como dado (U5, RN-AC-05).

A paleta, os botoes e as ferramentas do orquestrador leem esta mesma tupla
(criterio 2). Ficam FORA (Q1=A): criar, carregar, listar e apagar ambiente, que
a tela de inicio chama direto no servico, e a navegacao da tela (`/ajuda`,
`/sair`, trocar de chat), que e de U9. Conversar nao e acao (RN-AC-04).

Cada `efetivar` chama UMA operacao de U4 e devolve o que ela devolveu, ou deixa
a excecao subir (G1). Nao valida, nao consulta politica e nao captura nada: o
catalogo ja fez tudo isso antes de chegar aqui, num ponto so.

As descricoes sao texto de produto - a paleta as mostra e o esquema da
ferramenta do agente as carrega (U6) -, e por isso tem acento.
"""

from collections.abc import Mapping

from fishingrod.aplicacao.catalogo.tipos import (
    Acao,
    Acionamento,
    Alvo,
    EtapaNaPosicao,
    Escopo,
    Parametro,
    Referencias,
    TipoParametro,
)
from fishingrod.aplicacao.servicos.servico_de_ambiente import (
    EtapaInexistente,
    FrenteInexistente,
    ServicoDeAmbiente,
    SessaoInexistente,
    TarefaInexistente,
)
from fishingrod.dominio import (
    Ambiente,
    Anotacao,
    Chamador,
    Chat,
    Etapa,
    ExecutorEtapa,
    Frente,
    Identidade,
    Sessao,
    Tarefa,
)

# Q2=B, D-Q2-1: nesta iteracao as 6 primeiras aceitam os dois. O agente sempre passa pela
# confirmacao - quem decide isso e a politica, consultada pelo catalogo.
_OS_DOIS = frozenset({Chamador.USUARIO, Chamador.AGENTE})

# G10: limites de tamanho, em caracteres, por SECURITY-05. Generosos de
# proposito; mudam so aqui.
MAXIMO_NOME = 200
MAXIMO_AGENTE = 100
MAXIMO_CHAVE = 100
MAXIMO_DESCRICAO = 1_000
MAXIMO_VALOR = 20_000


# --------------------------------------------------------------------------
# Busca por identidade dentro do ambiente aberto
# --------------------------------------------------------------------------
# A mesma travessia que U4 faz, de poucas linhas, em vez de U4 ganhar operacao
# publica nova (business-logic-model.md 2.1). Levanta os erros de U4, para a
# tabela de mapeamento do catalogo tratar o passo 5 e o passo 7 por um caminho
# so. Mora aqui, e nao em catalogo.py, porque as duas pontas a usam: o catalogo
# para achar as referencias, e as acoes de etapa para devolver a posicao.


def achar_frente(ambiente: Ambiente, id_frente: Identidade) -> Frente:
    frente = ambiente.buscar_frente(id_frente)
    if frente is None:
        raise FrenteInexistente(f"nao existe a frente [{id_frente}] neste ambiente")
    return frente


def achar_tarefa(ambiente: Ambiente, id_tarefa: Identidade) -> tuple[Frente, Tarefa]:
    """A tarefa e a frente dela: a confirmacao mostra as duas pelo nome."""
    for frente in ambiente.frentes:
        tarefa = frente.buscar_tarefa(id_tarefa)
        if tarefa is not None:
            return frente, tarefa
    raise TarefaInexistente(f"nao existe a tarefa [{id_tarefa}] neste ambiente")


def achar_sessao(ambiente: Ambiente, id_sessao: Identidade) -> tuple[Frente, Tarefa, Sessao]:
    """A sessao, a tarefa e a frente dela: a confirmacao mostra as tres pelo
    nome."""
    for frente in ambiente.frentes:
        for tarefa in frente.tarefas:
            sessao = tarefa.buscar_sessao(id_sessao)
            if sessao is not None:
                return frente, tarefa, sessao
    raise SessaoInexistente(f"nao existe a sessao [{id_sessao}] neste ambiente")


async def _na_posicao(servico: ServicoDeAmbiente, alvo: Alvo, etapa: Etapa) -> EtapaNaPosicao:
    """G5: a etapa com a posicao, para quem acionou poder aponta-la depois.

    Acha a tarefa de novo pelo id, no ambiente aberto, DEPOIS de executar:
    numa recarga por conflito os objetos de dentro do ambiente sao outros
    (RN-A-03), e a etapa que importa e a que esta na arvore agora.
    """
    ambiente = await servico.carregar_ambiente(alvo.id_ambiente)
    _, tarefa = achar_tarefa(ambiente, alvo.id_tarefa)
    for posicao, atual in enumerate(tarefa.etapas, start=1):
        if atual.id == etapa.id:
            return EtapaNaPosicao(atual, posicao)
    raise EtapaInexistente(f"nao existe a etapa [{etapa.id}] na tarefa [{alvo.id_tarefa}]")


# --------------------------------------------------------------------------
# As 7 acoes (domain-entities.md 2.5)
# --------------------------------------------------------------------------
# Escopo e parametros ja foram conferidos: a identidade que o escopo exige
# existe no Alvo, e todo obrigatorio esta em `argumentos`.


async def _criar_frente(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> Frente:
    return await servico.criar_frente(alvo.id_ambiente, argumentos["nome"])


async def _criar_tarefa(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> Tarefa:
    # Pelo agente, id_frente e a frente da tarefa do chat (C1=A, RN-AC-14):
    # quem amarra o Alvo e U9, nao o agente.
    return await servico.criar_tarefa(alvo.id_ambiente, alvo.id_frente, argumentos["nome"])


async def _criar_sessao(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> Sessao:
    # `nome` ausente vira "", que a Tarefa de U1 troca por "sessão N".
    return await servico.criar_sessao(alvo.id_ambiente, alvo.id_tarefa, argumentos.get("nome", ""))


async def _criar_chat(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> Chat:
    # R-CG5-4: `nome` opcional ausente nao chega aqui; "" e o padrao, que o
    # Chat de U1 troca pelo nome do agente. A lista fechada e de U4 (RN-A-22).
    return await servico.criar_chat(
        alvo.id_ambiente, alvo.id_sessao, argumentos["agente"], argumentos.get("nome", "")
    )


async def _criar_etapa(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> EtapaNaPosicao:
    etapa = await servico.criar_etapa(
        alvo.id_ambiente,
        alvo.id_tarefa,
        argumentos["descricao"],
        ExecutorEtapa(argumentos["executor"]),  # a opcao ja veio na forma canonica
    )
    return await _na_posicao(servico, alvo, etapa)


async def _concluir_etapa(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> EtapaNaPosicao:
    # RN-AC-22: a etapa ja foi achada pela posicao ANTES da confirmacao, e e
    # ela que se conclui - a posicao nao e relida. O servico recebe o id.
    etapa = await servico.concluir_etapa(alvo.id_ambiente, referencias.etapa.etapa.id)
    return await _na_posicao(servico, alvo, etapa)


async def _anotar_memoria(
    servico: ServicoDeAmbiente,
    alvo: Alvo,
    argumentos: Mapping[str, object],
    referencias: Referencias,
    acionamento: Acionamento,
) -> Anotacao:
    # RN-AC-13: o autor e quem acionou, dito pelo sistema. Nao existe
    # parametro `autor`.
    return await servico.anotar_memoria(
        alvo.id_ambiente,
        alvo.id_sessao,
        argumentos["chave"],
        argumentos["valor"],
        acionamento.autor,
    )


def _texto(nome: str, descricao: str, maximo: int, obrigatorio: bool = True) -> Parametro:
    return Parametro(nome, TipoParametro.TEXTO, descricao, obrigatorio=obrigatorio, maximo=maximo)


ACOES: tuple[Acao, ...] = (
    Acao(
        nome="criar_frente",
        descricao="Cria uma frente de trabalho no ambiente.",
        escopo=Escopo.AMBIENTE,
        parametros=(_texto("nome", "Nome da frente.", MAXIMO_NOME),),
        chamadores=_OS_DOIS,
        efetivar=_criar_frente,
    ),
    Acao(
        nome="criar_tarefa",
        descricao="Cria uma tarefa na frente, já com uma sessão e o chat do orquestrador.",
        escopo=Escopo.FRENTE,
        parametros=(_texto("nome", "Nome da tarefa.", MAXIMO_NOME),),
        chamadores=_OS_DOIS,
        efetivar=_criar_tarefa,
    ),
    # D21: so o usuario abre sessao. O agente vive dentro de uma sessao, e
    # abrir outra e decisao de quem esta trabalhando, nao dele.
    Acao(
        nome="criar_sessao",
        descricao="Abre uma sessão nova na tarefa, já com o chat do orquestrador.",
        escopo=Escopo.TAREFA,
        parametros=(
            _texto(
                "nome",
                "Nome da sessão. Sem ele, a sessão se chama \"sessão\" e o número dela.",
                MAXIMO_NOME,
                obrigatorio=False,
            ),
        ),
        chamadores=frozenset({Chamador.USUARIO}),
        efetivar=_criar_sessao,
    ),
    Acao(
        nome="criar_chat",
        descricao="Abre um chat na sessão com um dos agentes disponíveis.",
        escopo=Escopo.SESSAO,
        parametros=(
            _texto("agente", "Nome do agente do chat.", MAXIMO_AGENTE),
            _texto(
                "nome",
                "Nome do chat. Sem ele, o chat leva o nome do agente.",
                MAXIMO_NOME,
                obrigatorio=False,
            ),
        ),
        chamadores=_OS_DOIS,
        efetivar=_criar_chat,
    ),
    Acao(
        nome="criar_etapa",
        descricao="Acrescenta uma etapa ao fim da lista de etapas da tarefa.",
        escopo=Escopo.TAREFA,
        parametros=(
            Parametro(
                "executor",
                TipoParametro.ESCOLHA,
                "Quem executa a etapa: o agente ou o usuário.",
                opcoes=tuple(executor.value for executor in ExecutorEtapa),
            ),
            _texto("descricao", "O que a etapa pede.", MAXIMO_DESCRICAO),
        ),
        chamadores=_OS_DOIS,
        efetivar=_criar_etapa,
    ),
    Acao(
        nome="concluir_etapa",
        descricao="Marca como concluída a etapa na posição indicada da tarefa.",
        escopo=Escopo.TAREFA,
        parametros=(
            Parametro(
                "posicao",
                TipoParametro.POSICAO,
                "Posição da etapa na lista da tarefa: 1 é a primeira.",
            ),
        ),
        chamadores=_OS_DOIS,
        efetivar=_concluir_etapa,
    ),
    Acao(
        nome="anotar_memoria",
        descricao="Acrescenta uma anotação à memória da sessão, assinada por quem anotou.",
        escopo=Escopo.SESSAO,
        parametros=(
            _texto("chave", "Assunto da anotação. Pela barra, uma palavra só.", MAXIMO_CHAVE),
            _texto("valor", "O que anotar.", MAXIMO_VALOR),
        ),
        chamadores=_OS_DOIS,
        efetivar=_anotar_memoria,
    ),
)
