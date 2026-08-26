# Plano de Application Design — FishingRod, Iteração 1

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-20 · **Base:** `execution-plan.md` v2 (aprovado), `requirements.md` v2 (§9),
`stories.md` (linha fina, 14 histórias), artefatos de Reverse Engineering, notas retidas em
`aidlc-state.md`

> **Como usar este documento**: cada pergunta tem opções e uma tag `[Answer]:`. Responda com a
> letra depois da tag, no próprio arquivo. Onde eu tenho uma recomendação, ela está marcada com
> **(recomendo)** e o motivo está escrito acima das opções — inclusive o custo de escolher a minha
> recomendação. Se nenhuma opção servir, use a última (Other) e descreva.
>
> **Nada de desenho é gerado antes de todas as respostas existirem.** Application Design fecha as
> decisões que Requirements e Workflow Planning deixaram deliberadamente abertas; se eu adivinhar,
> a iteração inteira herda a adivinhação.

---

## 1. Escopo deste estágio

Application Design responde **quais componentes existem, o que cada um responde por, qual é a
assinatura de fronteira e quem depende de quem**. Não responde regra de negócio detalhada — isso é
Functional Design, por unidade, na fase de CONSTRUCTION.

### Decisões que este estágio precisa fechar

Vindas de `requirements.md` §6 e §9.8 e das notas retidas em `aidlc-state.md`:

| # | Decisão aberta | Por que ela é deste estágio |
|---|---|---|
| 1 | Forma da cadeia `Ambiente → Projeto → Sessao` | O usuário registrou dúvida explícita sobre ela olhando para o futuro do produto |
| 2 | Desenho da identidade (tipo, onde nasce, como atravessa serialização) | Decisão de maior alcance da iteração — atravessa domínio, banco, wiki e TUI |
| 3 | Fronteira da porta de persistência e o que é documento vs tabela | D-ARQ-04 exige porta em vocabulário de domínio; a divisão híbrida ainda não existe |
| 4 | Forma concreta da porta de sessão sobre o ciclo assíncrono do SDK | ESC-18 fixou o ciclo medido pelo spike; falta a assinatura e como o streaming chega à TUI |
| 5 | Critério do bibliotecário entre criar entidade e criar propriedade | **Risco número um do desenho da wiki**; sem regra, a wiki apodrece em semanas |
| 6 | Qual grafo manda na recuperação: hierarquia de pastas ou links `[[...]]` | Determina como o `index.md` é construído e mantido |
| 7 | Assinaturas das tools de wiki e escopo de permissão das ferramentas de arquivo | O spike mediu permissão de tool **MCP**; escopo de ferramenta de **arquivo** não foi medido |
| 8 | Ordem técnica das dívidas TD-01 a TD-04 | O usuário pediu que a correção venha **depois** de a arquitetura fechar |

### Fora deste estágio

Regras de negócio detalhadas, esquema SQL literal, prompts dos agentes, layout de tela,
decomposição em unidades (Units Generation), stack de teste e política de NFR (NFR Requirements).

---

## 2. Fatos verificados no código, que sustentam as perguntas

Levantados agora, não presumidos:

- `Ambiente/agente.py:6` importa `ClaudeAgentOptions` do SDK no núcleo — viola RF-F04 hoje.
- `AgenteClaude.responder()` (`agente.py:45-46`) retorna `None`.
- `AgenteDoSistema` (`agente.py:72-75`) é uma **lista de instâncias compartilhadas** no nível do
  módulo. `Chat(agente=OrquestradorTeste)` guarda referência à *mesma* instância em todos os
  chats de todos os ambientes. Qualquer estado de sessão colocado no agente vaza entre chats.
- `Sessao.enviar()` (`sessao.py:135-144`) é **síncrono** e chama `chat.agente.responder(mensagem)`
  direto. O ciclo do SDK é assíncrono. Esse é o ponto exato onde a porta de sessão entra.
- Endereçamento é posicional (`indice_ativo` em `Ambiente`, `Projeto` e `Sessao`) e nominal
  (`_buscar_sessao(nome)`, `buscar_projeto(nome)`), e `/nome-chat` renomeia chat em runtime
  (`sessao.py:94-98`) — por isso nome não serve como identidade.
- `Memoria.anotar()` (`memoria.py:16-19`) levanta `KeyError` na primeira escrita de chave nova.
- Roteamento de comando está **dentro do domínio**: cada andar tem `_detectar_comando_*` e
  `_acionar_comando`, e `enviar()` decide entre executar comando e delegar para o andar de baixo.
- Vocabulário: `Projeto` ≈ frente, `Sessao` ≈ tarefa, `Memoria` pende de `Sessao` (logo, memória
  por tarefa já é verdade estrutural).

---

## 3. Perguntas de decisão

### Categoria A — Identificação de componentes

#### Pergunta 1 — A cadeia `Ambiente → Projeto → Sessao`

Hoje cada andar faz três trabalhos ao mesmo tempo: guarda estado, roteia comando e delega
mensagem. Isso funciona no console porque só existe uma entrada (uma string). Com persistência,
TUI e agente com ferramentas, a mesma classe passaria a decidir também quando salvar e como tratar
falha do provedor — quatro responsabilidades numa classe.

O custo de mexer: é a mudança de maior superfície da iteração, toca os três arquivos do núcleo e a
TUI. O custo de **não** mexer: cada capacidade nova entra empilhando `if` em `enviar()`.

A) Manter a cadeia como está: estado, roteamento e delegação juntos em cada andar

B) **(recomendo)** Manter a hierarquia de dados (ambiente contém frentes, frente contém tarefas),
mas **tirar o roteamento e a delegação de dentro dela**: o domínio passa a ter estado e
invariantes; um serviço de aplicação recebe a mensagem, decide se é comando ou conversa, chama o
domínio e a porta de sessão, e salva

C) Achatar a hierarquia: um único agregado `Ambiente` com coleções indexadas por identidade, sem
os andares intermediários como objetos com comportamento

D) Other (please describe after [Answer]: tag below)

[Answer]: B - essa cadeia eu tinha feito inicialmente , mas ja percebi que era ruim depois de um tempo que eu estava implementando. temos que adaptar a cadeia para se adequar nas nossas necessidades do software.

#### Pergunta 2 — Organização dos pacotes dentro de `src/`

ESC-15 já fixou layout `src/` com pacote real. Falta a divisão interna. Note que o núcleo precisa
rodar **sem** `claude_agent_sdk` instalado (RF-F04), o que fica trivial de provar se a fronteira
for visível no nome do pacote.

A) **(recomendo)** Por camada: `dominio/`, `aplicacao/` (serviços + portas), `adaptadores/`
(SQLite, Claude, wiki), `interface/` (TUI). A regra "quem pode importar quem" é verificável por
inspeção do import

B) Por fatia vertical: `ambiente/`, `tarefa/`, `wiki/`, `agente/`, cada uma com seu domínio e seu
adaptador dentro

C) Manter a divisão atual traduzida (`ambiente/`, `model/`) e acrescentar pacotes novos conforme
necessário

D) Other (please describe after [Answer]: tag below)

[Answer]: A - vamos seguir com essa organizacao. eu gostei

#### Pergunta 3 — Fronteira do agregado para persistência

Isto decide o que é salvo atomicamente junto. Com um agregado só, cada mensagem nova reescreve o
documento do ambiente inteiro. Com agregados separados, salvar uma tarefa não toca as outras, mas
a integridade entre eles passa a ser responsabilidade do código.

A) Um agregado único `Ambiente` (frentes, tarefas, chats, memória tudo dentro) — salvo inteiro a
cada mudança

B) **(recomendo)** `Ambiente` guarda a estrutura (frentes, tarefas, chats: identidade, nome,
etapas, agente, memória) como documento; **transcrição de mensagens é tabela separada**,
apend-only, referenciada por identidade de chat. Salvar um turno de conversa escreve uma linha, e
não o documento todo

C) Cada tarefa é seu próprio agregado persistido, e o ambiente guarda só referências

D) Other (please describe after [Answer]: tag below)

[Answer]: B - vamos comprar a escrita constante, paralelismo e consultabilidade pagando com um mapeamento a mais e integridade referencial manual.

### Categoria B — Métodos e contratos de fronteira

#### Pergunta 4 — Desenho da identidade

RF-F16 e ESC-14 já fixaram identidade opaca e estável. Falta o tipo e o lugar onde ela nasce. Se a
identidade nascer no adaptador de persistência, o domínio fica com objeto sem identidade até ser
salvo — e a TUI precisa referenciar coisas que ainda não foram salvas.

A) `uuid.uuid4()` da stdlib, gerada no construtor da entidade de domínio

B) **(recomendo)** UUIDv7 (ordenável por tempo, `uuid.uuid7()` existe a partir do Python 3.14; no
3.13 é gerado por implementação própria de ~10 linhas ou dependência mínima), gerada no construtor
da entidade de domínio. Ordenável por tempo dá ordenação estável de transcrição e paginação sem
coluna extra

C) ULID via dependência externa, gerada no construtor da entidade de domínio

D) Identidade gerada pela persistência (autoincremento do SQLite), e o domínio só a recebe depois
de salvar

E) Other (please describe after [Answer]: tag below)

[Answer]: B - vamos seguir com a ordenabilidade e o tempo de criação da identidade.

#### Pergunta 5 — Forma da porta de sessão viva

O spike mediu o ciclo real: `async with ClaudeSDKClient(...)` → `query()` → `receive_response()` →
saída do contexto. O Textual roda em asyncio e `on_input_submitted` já é async. A pergunta é o que
a porta expõe para o serviço de aplicação.

A) Porta síncrona (`abrir`/`enviar`/`fechar` normais) e o adaptador esconde o asyncio internamente
(`asyncio.run` ou loop próprio em thread). Núcleo simples, mas paga ponte thread↔loop e perde
streaming natural

B) **(recomendo)** Porta assíncrona nativa: `abrir()` async retornando uma sessão, `enviar()` async
devolvendo um **iterador assíncrono de eventos** (pedaço de texto, uso de ferramenta, fim de
turno), `fechar()` async. Casa com o Textual sem ponte e entrega streaming de graça. Custo: o
serviço de aplicação que a usa também é async, e teste de domínio precisa de `pytest-asyncio`

C) Porta assíncrona que devolve a resposta **completa** de uma vez (sem iterador). Mais simples de
testar; sem streaming — o usuário espera a resposta inteira olhando para uma tela parada

D) Other (please describe after [Answer]: tag below)

[Answer]: B - vamos seguir com a porta assíncrona nativa.

#### Pergunta 6 — Agente vs sessão viva (o problema da instância compartilhada)

`AgenteDoSistema` são instâncias compartilhadas entre todos os chats. Se a sessão do SDK morar
dentro do objeto agente, dois chats abertos com o mesmo agente compartilham histórico — que é
exatamente o risco 7 do plano ("misturar histórico entre chats").

A) **(recomendo)** `Agente` vira **configuração imutável** (nome, papel, modelo, ferramentas,
regras) e pode continuar compartilhada; a **sessão viva** é um objeto separado, criado por chat,
cujo dono é o chat/serviço. `Agente.responder()` deixa de existir

B) Cada chat recebe uma **cópia** do agente, e a sessão viva mora dentro da cópia

C) Manter `Agente.responder()` como método, e o agente resolve internamente qual sessão usar a
partir de um identificador de chat recebido como parâmetro

D) Other (please describe after [Answer]: tag below)

[Answer]: A - vamos seguir com a configuração imutável e a sessão viva separada.

### Categoria C — Camada de serviço

#### Pergunta 7 — Onde mora o roteamento de comando (`/frentes`, `/nova-tarefa`, `/nome-chat`)

Hoje mora no domínio. O mockup do usuário mantém paleta acionada por `/`, então o vocabulário de
comando sobrevive. RF-F17 exige que "a regra que a TUI aciona é a mesma que um comando aciona".

A) Manter no domínio, como hoje (`_detectar_comando` + `_acionar_comando` por andar)

B) **(recomendo)** Um serviço de comandos na camada de aplicação: traduz a string em uma chamada
de serviço e devolve mensagem de sistema. Domínio não conhece a sintaxe `/`, e a TUI ganha os
mesmos comandos sem duplicar regra

C) Na interface (TUI), que traduz o comando e chama os serviços diretamente

D) Other (please describe after [Answer]: tag below)

[Answer]: B - omandos não são um recurso da interface de texto — são o vocabulário de ações do ambiente. A sintaxe / é uma de várias formas de acionar esse vocabulário, ao lado de botões, atalhos e, futuramente, do próprio agente. Portanto o catálogo de ações pertence à camada de aplicação, o parser / é um adaptador de entrada descartável, e o domínio permanece sem conhecimento de qualquer sintaxe. Isso torna o RF-F17 uma propriedade da arquitetura em vez de uma convenção a ser mantida manualmente.

Ou seja: B, com a ressalva de que "serviço de comandos" deve ser lido como "catálogo de ações + parser separado", não como uma função que recebe string.

1. Ação como objeto de primeira classe na camada de aplicação.

Cada ação carrega o que precisa para ser executada e o que precisa para ser exibida:



python
@dataclass(frozen=True)
class Acao:
    nome: str                  # "nova-tarefa"
    descricao: str             # para a paleta e o tooltip do botão
    parametros: list[Parametro]  # nome, tipo, obrigatório
    escopo: Escopo             # AMBIENTE | FRENTE | TAREFA — de que alvo precisa
    executar: Callable[[Alvo, dict], Resultado]
Isso é um registro, não um match/case. A diferença prática: um registro é dado, então a paleta pode iterar sobre ele, filtrar por escopo, gerar o formulário de argumentos, e validar antes de executar. O match/case não pode ser lido por ninguém.

2. O parser / é um adaptador de entrada, e é fino.

Sua única responsabilidade: "/nova-tarefa campanha de verao" → ("nova-tarefa", {"nome": "campanha de verao"}). Ele não conhece regra de negócio, não sabe o que a ação faz. Um botão pula essa etapa inteira e chama a ação direto com os argumentos que já tem tipados — que é exatamente o que você queria.

E note que TD-11 (espaços quebram argumento) deixa de ser um bug espalhado por 3 classes: é um bug de uma função, com um teste.

3. Alvo explícito, em vez de "o ativo".

A ação recebe a identidade de sobre o que ela age (e aqui a Pergunta 4 se encaixa — identidade opaca e estável). "O item ativo" vira um default que o parser preenche quando você digita /, não uma verdade embutida no domínio. Assim o botão "renomear" numa lista de 5 chats consegue dizer qual dos 5.

4. Resultado tipado.

Resultado com sucesso/falha e, no caso de falha, um motivo estruturado. A TUI decide como renderizar; o modo / renderiza como mensagem de sistema (comportamento atual preservado), o botão renderiza como toast ou validação inline. A mensagem em português vira responsabilidade da interface, não do núcleo.

5. O domínio fica sem saber que comandos existem.

Frente.criar_tarefa(nome) continua existindo e continua sendo onde a invariante mora. A ação é uma casca fina que chama isso, coordena com a persistência, e traduz o resultado. Isso é consistente com o que você já decidiu na Pergunta 1B.

O que isso te dá, e o que custa
Ganha:

Uma regra, N superfícies — que é literalmente o RF-F17, agora estruturalmente garantido em vez de mantido por disciplina.
Paleta e botões geram-se a partir do mesmo catálogo. Adicionar uma ação nova = uma entrada no registro, e ela aparece na paleta automaticamente.
Testável sem TUI e sem string: executar(acao, alvo, args).
Quando o agente ganhar ferramentas, o catálogo já é a lista de ferramentas. Você não precisa inventar nada — o mesmo registro vira a tool definition.
Autorização/disponibilidade contextual (esta ação faz sentido agora?) tem um lugar único para morar.
Custa:

Mais estrutura do que match/case. Para 13 comandos, isso é honestamente umas 100–150 linhas a mais.
Uma indireção: ler "o que /nova-tarefa faz" exige olhar o registro e depois a função, em vez de um case.

#### Pergunta 8 — Política de gravação

US-05 e US-06 exigem que matar o processo não perca nada. Isso define quando a porta de
persistência é chamada.

A) **(recomendo)** Gravar ao fim de cada operação de domínio que muda estado (criar frente, criar
tarefa, turno de conversa, anotação, etapa concluída), numa transação por operação. Simples,
previsível, e "matar o processo" nunca perde mais do que o turno em andamento

B) Gravar por comando explícito do usuário (`/salvar`)

C) Gravar periodicamente em segundo plano

D) Other (please describe after [Answer]: tag below)

[Answer]:

#### Pergunta 9 — Onde mora o portão de revisão humana da escrita na wiki (US-14)

RNF-14 trata a wiki como entrada não confiável e aponta a revisão humana como uma das duas
defesas. A pergunta é quem segura a escrita.

A) **(recomendo)** A ferramenta do bibliotecário **não escreve**: ela devolve uma *proposta* de
escrita (caminho lógico, conteúdo, links). Um serviço de aplicação guarda a proposta pendente, a
TUI mostra, e a escrita só acontece na aprovação. O agente nunca tem poder de escrita direto

B) A ferramenta escreve, mas antes chama um callback de confirmação que a TUI responde

C) A ferramenta escreve em área de rascunho dentro da raiz da wiki, e a aprovação move o arquivo
para o lugar definitivo

D) Other (please describe after [Answer]: tag below)

[Answer]: A - a segurança vai ser via ferramentas que vamos disponibilizar para o bibliotecario. eu penso o bibliotecario como a camada de funcionalidades que o agente vai usar para interagir com a wiki, e para o agente interagir com a wiki ele vai utiilzar ferramentas que vai aplica regras de segurança , nesse caso sendo a regra de escrita, onde vai ser feito um processo de aprovação antes da escrita ser realizada.

### Categoria D — Dependências e comunicação

#### Pergunta 10 — Como o bibliotecário acessa a wiki

ESC-20 diz "exclusivamente pelas ferramentas do bibliotecário". Falta decidir se essas ferramentas
são as nativas do SDK com permissão restrita, ou tools nossas. **Fato relevante**: o spike mediu
permissão de tool **MCP**; permissão de ferramenta de **arquivo** nativa não foi medida. Escolher
(A) transforma uma coisa não medida em fundação da segurança da wiki.

A) Ferramentas de arquivo nativas do agente (Read/Write/Glob/Grep) com permissão restrita à raiz
da wiki, confiando na configuração do SDK

B) **(recomendo)** Tools nossas, expostas ao agente por MDP/MCP in-process (caminho já medido pelo
spike): `listar`, `ler`, `buscar`, `propor_escrita`. Ferramentas nativas de escrita **negadas**. O
confinamento de caminho é código nosso, num ponto único, testável sem credencial — e é o que
RF-F14 e RNF-10 pedem

C) Híbrido: leitura pelas nativas (Read/Grep/Glob, baratas e boas), escrita só pela nossa tool

D) Other (please describe after [Answer]: tag below)

[Answer]: B — tools nossas para a wiki, expostas por MCP in-process; ferramentas nativas de
escrita negadas.

**Precisão de vocabulário**: as tools são a *cerca* determinística sobre a wiki. Quem as usa é o
**agente** bibliotecário, que continua sendo agente de primeira classe (ele carrega o julgamento
de curadoria — Pergunta 13). Esta pergunta decide apenas a camada de acesso, não a natureza do
bibliotecário.

**A regra de decisão adotada** (vale para toda tool futura, não só para a wiki):

> Tool nossa quando o acesso carrega uma invariante que o software precisa garantir.
> Ferramenta nativa quando o acesso é genérico e o dano de um mau uso é local.

Classificação por store:

| store | tool | motivo |
|---|---|---|
| wiki | **nossa** | esquema de dois níveis, confinamento de caminho, escrita só por proposta |
| estado do ambiente / transcrição | **nossa** | invariantes de domínio; não existe equivalente nativo |
| busca na web | **nativa** | sem invariante do software; reimplementar é puro retrabalho |
| arquivos do usuário (ex.: a PPT da reunião) | **nativa** (decisão futura) | área livre por definição; classificada aqui só para registrar que a Pergunta 10 **não** decidiu que "tudo é tool nossa" |

**Por que a wiki cai do lado "nossa" — o motivo principal não é segurança, é integridade do
esquema.** ESC-17 trava a wiki em entidade=pasta / propriedade=arquivo, dois níveis. Com `Write`
nativo nada impede `wiki/clientes/acme/2024/q3/notas.md`: a regra vira instrução de prompt, ou
seja, sugestão estatística. Com tool nossa, a assinatura *é* a regra — `propor_escrita(entidade,
propriedade, conteudo, links)` não tem parâmetro para um terceiro nível, e a violação deixa de ser
representável. Isso ataca diretamente o "risco número um" registrado na Pergunta 13.

Isso **não é reinventar `Write`**: `Write` grava bytes num caminho; a tool cria uma propriedade
numa entidade, valida o esquema e devolve uma proposta. Vocabulários diferentes, níveis de
abstração diferentes.

**Por que (A) está descartada** — três motivos independentes, qualquer um suficiente:
1. **Incompatível com a Pergunta 9A**, já decidida: o agente não tem poder de escrita direto. Não
   existe configuração de permissão que transforme "escrever" em "propor".
2. **Incompatível com RNF-11**: ferramenta nativa opera com caminho real do disco, e esse caminho
   aparece na chamada de tool, que entra na transcrição persistida (Pergunta 3). Caminho absoluto
   vazaria para o banco pelo caminho lateral.
3. **Funda a segurança da wiki em algo não medido** — o spike mediu permissão de tool MCP, não
   escopo de ferramenta de arquivo nativa.

**Por que (C) está descartada**, apesar de `Grep`/`Glob` serem genuinamente bons:
- C **não escapa do risco não medido**: para leitura nativa não virar acesso ao disco inteiro, ela
  precisa exatamente da restrição de caminho nativa que não foi verificada.
- Quebra ESC-20 na letra ("exclusivamente pelas ferramentas do bibliotecário").
- **Leitura é o vetor de injeção, não escrita** (RNF-14). Com `ler`/`buscar` nossas, existe um
  ponto único para envelopar o conteúdo como dado (não instrução), truncar e marcar procedência.
  Com `Read` nativo o conteúdo entra cru no contexto, sem ponto de intervenção.
- Vaza o layout físico: sabendo que é filesystem, o agente tenta escrever como filesystem e falha,
  gastando turnos.
- O ganho de qualidade de busca é recuperável sem C: `buscar` pode usar `ripgrep` por baixo,
  confinado à raiz. Reusa-se a ferramenta **sem** reusar a exposição dela ao modelo.

**MCP é formato de exposição, não fronteira de segurança.** In-process, MCP é despacho de função.
A garantia vem do código dentro da tool (confinamento, validação de esquema, fila de aprovação) e
da negação das nativas de escrita. O valor do MCP é outro: portabilidade. O bibliotecário é
implementado como funções Python puras — testáveis sem LLM e sem credencial — e o adaptador MCP é
uma casca de schema por cima. Outro modelo no futuro = outro adaptador fino, **sem reescrever
regra**. É o mesmo padrão já aceito na Pergunta 7 (catálogo declarativo + adaptadores de entrada
finos), aplicado a uma segunda família de superfícies.

**Custo assumido**: 4 tools (~150–250 linhas); confinamento de caminho ~15 linhas mais o teste de
propriedade que RNF-10/PBT-03 já exigem em qualquer cenário; adaptador MCP em dezenas de linhas
sobre caminho já medido. O risco aberto real não é segurança, é **qualidade da busca** — item a
iterar, registrado como tal.

#### Pergunta 11 — Composição de dependências (quem monta quem)

O domínio não pode construir adaptador, senão a fronteira é decorativa.

A) **(recomendo)** Um único ponto de composição no ponto de entrada (`__main__` / entrypoint do
`uv run`), que constrói adaptadores e injeta nos serviços; a TUI recebe serviços prontos e não
sabe que SQLite ou Claude existem

B) A TUI monta suas dependências no `on_mount`, como faz hoje com `Ambiente(nome=...)`

C) Um módulo container/registry consultado por quem precisar

D) Other (please describe after [Answer]: tag below)

[Answer]: A - pois Construir e usar são responsabilidades diferentes. Empurre toda a construção para a borda do programa; o miolo só recebe.

#### Pergunta 12 — Fronteira entre os dois substratos

RNF-12 diz que o banco não guarda conteúdo nem índice da wiki, "no máximo a referência da raiz".
RNF-11 proíbe caminho absoluto persistido. As duas juntas deixam uma pergunta: o banco guarda
alguma coisa sobre a wiki?

A) O banco guarda a raiz da wiki do ambiente como **caminho relativo** a um diretório de dados
conhecido da aplicação

B) **(recomendo)** O banco não guarda **nada** sobre a wiki. A raiz é derivada por convenção da
identidade do ambiente (ex.: `<dados>/ambientes/<id>/wiki/`). Zero chance de divergência, e mover
o diretório de dados inteiro continua funcionando

C) O banco guarda um espelho de metadados da wiki (páginas existentes) para busca rápida

D) Other (please describe after [Answer]: tag below)

[Answer]:D — variante de (A): o banco guarda uma referência à raiz da wiki, e só isso. Nunca caminho absoluto, nunca nada sobre o conteúdo.

Correção da recomendação (B) do AI. A opção B derivava a raiz por convenção a partir da identidade do ambiente. Isso assume que o software é o dono da localização da wiki — verdade no modo local, falsa em qualquer outro. Se a wiki mora num drive compartilhado ou, no futuro, num serviço, a localização é escolhida por quem configurou o compartilhamento, não calculada pelo software. Uma convenção fixa não tem como representar isso: no modo nuvem a "raiz" nem é uma pasta. Convenção é boa para gerar o valor inicial da raiz no modo local; é errada como única forma de saber onde a wiki está.

O que fica em cada substrato. Substrato 1 (SQLite) guarda o ambiente: frentes, tarefas, chats, memória, transcrição — mais uma referência à raiz da wiki daquele ambiente. Substrato 2 (a wiki) guarda o conteúdo, e o arquivo continua sendo a fonte da verdade (ESC-17). O banco não guarda página, não guarda índice, não guarda espelho de estrutura. RNF-12 é cumprido na letra: "no máximo, a referência da raiz" — e é exatamente a raiz, nada além dela.

Por que apontar só para a raiz — estabilidade referencial. Só se persiste referência a coisas cujo ciclo de vida o software controla. A raiz nasce quando o ambiente é criado e morre quando o ambiente é apagado: ciclo de vida controlado, referência estável. O conteúdo dentro da raiz é o oposto — o usuário renomeia pasta no Obsidian, move arquivo, faz git pull, e o software não é avisado. Persistir referência a qualquer coisa dentro da raiz é criar dado que apodrece sozinho. Saber a raiz é suficiente: a partir dela o bibliotecário navega e descobre o resto em tempo de leitura, sempre atualizado por construção. Corolário operacional: apagar a raiz é apagar a wiki — uma operação, um efeito, sem resíduo espalhado no banco.

Por que isso não viola RNF-11. A referência persistida não é caminho absoluto de disco. Ela é relativa a uma raiz de dados que o processo resolve em tempo de execução, no ponto de composição (Pergunta 11). O banco guarda wikis/<id_ambiente>; quem transforma isso em caminho real é o adaptador, com a raiz de dados que recebeu do main. Consequência prática: mover ou sincronizar o diretório de dados inteiro continua funcionando, e nenhum caminho de máquina entra em arquivo ou banco.

Como isso se conecta ao modo do ambiente (local × nuvem). Um ambiente nasce em um de dois modos, e o modo determina a forma da referência de raiz, não a existência dela:

ambiente local (esta iteração)	ambiente na nuvem (futuro)
estado do ambiente	SQLite na máquina do usuário	serviço remoto
wiki	pasta em raiz de dados criada pelo software	drive/serviço compartilhado
referência de raiz	localizador relativo à raiz de dados	localizador do serviço
escopo	um usuário, uma máquina (D-ARQ-09)	compartilhado no ambiente (FOR-13)
No modo local, o software gera a raiz por convenção (wikis/<id_ambiente>) no momento da criação e a registra. Convenção como semente, referência como verdade — a mesma lógica de ESC-19 para o esquema da wiki. Assim o caso comum não pede configuração nenhuma do usuário, e o caso compartilhado passa a ser representável sem redesenho.

Por que (C) está descartada. Viola RNF-12 diretamente e é divergência garantida: qualquer edição feita fora do software (Obsidian, git pull) deixa o espelho velho, e com wiki compartilhada (FOR-13, RNF-13 — sem escritor único) ele estaria errado a partir do segundo usuário. Se busca rápida virar necessidade, ela se resolve dentro do substrato 2 (índice derivado, descartável, reconstruível a partir dos arquivos), nunca no banco.

O que esta decisão preserva para o futuro, sem custo hoje. O domínio e a aplicação nunca sabem onde a wiki está nem qual é o modo do ambiente: os dois chegam por porta e adaptador, montados no ponto de composição. Trocar pasta local por serviço remoto é escrever outro adaptador de wiki e outro adaptador de repositório — não é redesenhar o núcleo.

Ponta solta registrada, fora do escopo desta iteração. O modo nuvem quebra a suposição de escritor único no estado do ambiente — hoje RNF-13 cobre apenas a wiki. Nada a implementar agora; apenas nada a tornar impossível. A decisão da Pergunta 3 (transcrição em tabela separada, append-only) já sobrevive a esse futuro sem redesenho, o que é evidência a favor dela.

### Categoria E — Padrões de desenho e decisões da wiki

#### Pergunta 13 — Critério do bibliotecário entre entidade (pasta) e propriedade (arquivo)

O risco número um do desenho da wiki. Você escolheu "propriedade pode ser instância", o que é
fiel ao uso real (`clientes/dr-marcelo.md` e `clientes/criterios-de-icp.md` convivem) mas deixa o
bibliotecário sem regra: sem critério, ele decide diferente a cada vez e a wiki apodrece.
Profundidade está travada em dois níveis, então "criar entidade" é sempre uma decisão de topo.

A) **(recomendo)** Entidade nova é **decisão humana**. O bibliotecário só cria arquivo dentro de
entidade existente; quando o conteúdo não couber em nenhuma, ele **propõe** a entidade nova e
espera aprovação. O esquema-semente já dá as entidades iniciais, então o caso comum não pede
aprovação nenhuma

B) Regra explícita para o agente decidir sozinho: cria entidade quando o conteúdo é substantivo
que terá múltiplas páginas; caso contrário, arquivo dentro da entidade mais próxima

C) O esquema é fechado: entidades são só as do esquema, e criar entidade nova exige editar o
esquema fora da conversa

D) Other (please describe after [Answer]: tag below)

[Answer]:  A — com uma precisão que simplifica a regra: não há dois regimes. Toda escrita na wiki é proposta, então "criar entidade" e "criar propriedade" passam pelo mesmo mecanismo.

O critério semântico vem da abstração da wiki, não de uma regra extra. Entidade é substantivo — a coisa sobre a qual se sabe algo. Propriedade é característica que define ou restringe aquela entidade — e pode ser faceta (clientes/criterios-de-icp.md) ou instância (clientes/dr-marcelo.md). Dois níveis, travados. O bibliotecário não precisa de heurística inventada: ele pergunta "isto é um substantivo novo, ou é algo que caracteriza um substantivo que já existe?". Se o conteúdo caracteriza uma entidade existente, é propriedade. Se introduz um substantivo que não existe, é entidade.

A regra de funcionamento do bibliotecário é propor. Ele tem duas operações de escrita — propor_entidade e propor_propriedade — e nenhuma delas escreve. Ambas produzem uma proposta que o usuário aceita ou recusa (Pergunta 9A). Isso elimina a pergunta "quando ele pode decidir sozinho?": nunca. Não existe caminho de escrita sem aprovação, então não existe caso de borda onde o julgamento dele vira fato sem revisão.

Por que isso não vira atrito no uso comum. O esquema-semente (ESC-19) já entrega as entidades iniciais do domínio, então a esmagadora maioria das escritas é propriedade dentro de entidade que já existe. Propor entidade nova é evento raro — e quando acontece, é exatamente o momento em que uma decisão estrutural sobre a wiki está sendo tomada, que é o momento em que revisão humana tem mais valor.

Por que não (B). B pede ao modelo que decida sozinho por heurística ("substantivo que terá múltiplas páginas"). Heurística em prompt é sugestão estatística: ele decide diferente em dias diferentes, e o erro estrutural só aparece semanas depois, quando a wiki já tem entidade duplicada e conteúdo espalhado. O custo do erro é assimétrico — errar propriedade se corrige apagando um arquivo; errar entidade contamina a organização inteira.

Por que não (C). Esquema fechado tira o crescimento orgânico da wiki e obriga o usuário a sair da conversa para editar configuração. Contraria ESC-19, que trata o esquema como semente e não como cerca.

Onde cada parte mora. O critério semântico é prompt do bibliotecário (é julgamento — ver Pergunta 10). A profundidade de dois níveis e o confinamento de caminho são código na tool (é garantia). O agente pode errar o julgamento; não pode violar a estrutura.

#### Pergunta 14 — Qual grafo manda na recuperação

Hierarquia de pastas e links `[[...]]` são dois grafos e podem discordar.

A) A hierarquia de pastas manda; links são conveniência de leitura

B) **(recomendo)** A hierarquia manda para **localizar** (é ela que o filesystem garante) e os
links são **arestas de navegação validadas na escrita** — link para página inexistente faz a
escrita ser recusada ou vira proposta de criar a página. Nenhum dos dois "vence" porque eles não
respondem a mesma pergunta

C) Os links mandam; a pasta é só armazenamento

D) Other (please describe after [Answer]: tag below)

[Answer]: B - Os dois grafos não competem porque respondem perguntas diferentes. A hierarquia responde onde a informação mora — é estrutura, garantida pelo filesystem, e é o que torna a wiki legível fora do software. Os links respondem com o que esta informação se relaciona — é semântica, criada pelo conteúdo, e é o que permite associação livre entre propriedades de entidades diferentes. Nenhum dos dois "vence" porque nenhum substitui o outro.

A minha idea é que o index.md seja o arquivo lido obrigatoriamente quando o agente inicia a leitura da wiki. Ele é a porta de entrada obrigatória (ESC-17). O index.md lista as entidades e, dentro de cada uma, as propriedades — cada uma com seu link e uma descrição curta do que há ali. Essa descrição é o ponto central: é ela que permite ao agente decidir onde buscar sem precisar ler a wiki inteira. Sem descrição, o índice seria só uma lista de nomes de arquivo, e o agente teria que abrir tudo para descobrir o que importa — caro em contexto e pouco confiável.

A partir daí, o grafo de links assume. Dentro das propriedades existem os links [[...]], que conectam propriedades entre si livremente, inclusive atravessando entidades. Recuperação típica: index.md → localiza a propriedade candidata pela descrição → lê → segue os links relevantes. Primeiro salto por estrutura, saltos seguintes por associação.


19h
17h
16h
16h
Read
application-design-plan.md
#L60-169
Vou explicar as duas com o formato de armazenamento concreto, porque a diferença só fica visível quando você olha o que vai para o disco a cada mensagem digitada.

O que "agregado" decide na prática
Agregado = a unidade que é carregada inteira, validada inteira e salva inteira, numa transação. A pergunta não é sobre modelagem bonita: é sobre qual é o menor write possível quando o usuário manda uma mensagem para o agente.

Opção A — agregado único Ambiente
Uma linha no SQLite, mais ou menos assim:



tabela ambiente
  id TEXT PK
  documento TEXT   -- JSON com TUDO
  versao INTEGER
E o documento contendo:



json
{
  "frentes": [
    { "id": "...", "nome": "FishingRod",
      "tarefas": [
        { "id": "...", "nome": "persistencia", "etapa": "construcao",
          "memoria": { "decisao": "..." },
          "chats": [
            { "id": "...", "agente": "claude",
              "mensagens": [
                {"papel": "usuario", "texto": "..."},
                {"papel": "agente", "texto": "..."}   // <- cresce sem limite
              ] } ] } ] } ]
}
Como fica o fluxo de uma mensagem: ler a linha → parsear o JSON inteiro → adicionar 2 itens no array mensagens → serializar o JSON inteiro → UPDATE da linha inteira.

Vantagens reais:

Uma transação, uma invariante. "Toda tarefa pertence a uma frente existente", "chat aponta para tarefa viva" — isso é verdade por construção, não por código de verificação. Nunca existe estado meio-salvo.
Um único ponto de serialização. O repositório é literalmente salvar(ambiente) / carregar(). Não tem mapeamento, não tem join, não tem ordem de escrita para pensar.
O domínio não sabe que persistência existe. Você navega objetos Python normais; nada de lazy loading, nada de "esse campo ainda não foi carregado".
Refatorar o modelo é barato agora. Você está em iteração de design; mudar a forma do JSON é mudar uma função de serialização, não uma migração de esquema com FK.
Desvantagens reais:

O custo de escrita cresce com o histórico, não com a mudança. Chat com 500 mensagens ≈ algumas centenas de KB de JSON. Cada tecla-enter reescreve tudo. Isso é O(tamanho total) por turno, e o histórico só cresce.
O documento é o gargalo de concorrência. Dois chats de tarefas diferentes rodando ao mesmo tempo (e você vai querer isso — é a razão de existir "frentes") escrevem a mesma linha. Um sobrescreve o outro, a menos que você implemente versão otimista e merge. E merge de dois arrays append-only dentro de um JSON é exatamente o trabalho que a opção B te dá de graça.
Streaming fica esquisito. A resposta do agente chega em pedaços. Ou você acumula tudo em memória e salva no fim (perde a resposta se cair no meio), ou reescreve o documento inteiro a cada chunk.
Nada é consultável. "Onde eu falei sobre UUIDv7?" vira: carregar tudo, varrer em Python. Sem índice, sem LIKE, sem paginação.
Opção B — estrutura como documento, transcrição como tabela


tabela ambiente
  id TEXT PK
  documento TEXT   -- frentes, tarefas, chats: id, nome, etapa, agente, memoria
  versao INTEGER   -- SEM mensagens
 
tabela mensagem
  id TEXT PK              -- UUIDv7, ordena por tempo
  chat_id TEXT NOT NULL   -- referencia identidade de chat no documento
  papel TEXT
  texto TEXT
  criada_em TEXT
  INDEX (chat_id, id)
Como fica o fluxo de uma mensagem: INSERT INTO mensagem — duas linhas, tamanho fixo. O documento não é tocado.

O ponto central: você separou dois tipos de dado que se comportam de forma oposta.

estrutura (frentes/tarefas/chats/memória)	transcrição
tamanho	pequeno, limitado	cresce sem limite
muda quando	usuário cria/renomeia/avança etapa (raro)	cada turno (constante)
forma da mudança	edição no meio	só append
precisa de invariante entre itens	sim	não — mensagem só precisa de um chat_id
Vantagens reais:

Write O(1) por turno. Independe de o chat ter 10 ou 10.000 mensagens.
Concorrência resolvida sem esforço. Dois chats escrevendo = dois INSERT em linhas diferentes. Zero contenção. Isso importa muito no seu caso: trabalhar em várias frentes em paralelo é o propósito do produto.
Streaming natural. Pode inserir a mensagem do agente parcial e atualizar só ela, ou inserir por chunk. Queda no meio perde um turno, não corrompe a estrutura.
Paginação e busca viram SQL. WHERE chat_id = ? ORDER BY id DESC LIMIT 50 — carrega os últimos 50 turnos sem tocar no resto. Para a TUI isso é diretamente útil: abrir uma tarefa não precisa carregar o histórico todo.
UUIDv7 (Pergunta 4B) já te dá a ordenação. As duas respostas se encaixam: id ordenável por tempo = ORDER BY id é a ordem cronológica, sem coluna extra nem contador.
Desvantagens reais:

Duas escritas, duas formas de mapear. Você tem um repositório de documento e um repositório de transcrição. Mais código, mais dois testes.
Integridade referencial passa a ser sua. chat_id aponta para um id que vive dentro do JSON — o SQLite não pode ter FK para isso. Se um chat for deletado, mensagens órfãs ficam. Precisa de uma decisão explícita (limpar em cascata no serviço de aplicação, ou aceitar órfãs como lixo inofensível).
Transação atravessando os dois. Criar um chat e gravar a primeira mensagem toca as duas tabelas. Resolvível (mesma conexão, mesma transação SQLite), mas é um cuidado que A não tem.
Carregar um chat completo é uma composição. O serviço monta "chat = metadado do documento + mensagens da tabela". A entidade de domínio Chat provavelmente não deve mais carregar a lista de mensagens dentro dela — o que muda um pouco o desenho que você tinha.
O trade-off em uma frase
A troca é: A compra simplicidade e garantia de consistência pagando com custo de escrita proporcional ao histórico e contenção entre chats paralelos. B compra escrita constante, paralelismo e consultabilidade pagando com um mapeamento a mais e integridade referencial manual.

Como eu leria isso no seu contexto
Três fatos do seu software empurram para B:

Frentes paralelas são o propósito. Se o valor do produto é tocar várias frentes ao mesmo tempo, um único documento como ponto de escrita é uma contradição arquitetural com a feature principal.
A transcrição é o dado que cresce. Todo o resto (nomes, etapas, memória) é minúsculo e estável. Você está prestes a colocar o único dado ilimitado dentro do único documento que é reescrito por inteiro.
Streaming do SDK. A resposta chega em pedaços; append-only é a forma natural disso, e A é a forma mais hostil.
O argumento honesto do outro lado: se o volume real for pequeno (você é o único usuário, chats de dezenas de mensagens), A funciona bem por muito tempo e é menos código. Mas o problema de A não é performance — é a contenção de escrita entre chats paralelos, e essa é estrutural, não some com volume baixo. É o tipo de coisa que você conserta migrando para B depois, com dados em produção, em vez de agora, com o esquema ainda em papel.

Se você quiser um meio-caminho: pode fazer B e manter a integridade referencial simplificada — mensagens órfãs são toleradas e limpas por uma varredura ocasional, em vez de cascade rigoroso. Isso corta a maior parte da desvantagem de B sem perder as vantagens.







Pergunta 7 — Onde mora o roteamento de comando (/frentes, /nova-tarefa, /nome-chat)

Hoje mora no domínio. O mockup do usuário mantém paleta acionada por /, então o vocabulário de
comando sobrevive. RF-F17 exige que "a regra que a TUI aciona é a mesma que um comando aciona".


A) Manter no domínio, como hoje (_detectar_comando + _acionar_comando por andar)

B) (recomendo) Um serviço de comandos na camada de aplicação: traduz a string em uma chamada
de serviço e devolve mensagem de sistema. Domínio não conhece a sintaxe /, e a TUI ganha os
mesmos comandos sem duplicar regra


C) Na interface (TUI), que traduz o comando e chama os serviços diretamente

D) Other (please describe after [Answer]: tag below)


quero que vc me ajuda com essa proxima pergunta agora. o meu ponto de avaliacao é o seguinte - quandoeu programei os comandos no codigo eu fiz de um jeito q eu sabia fazer mas penso que nao foi o melhor jeito, eu penso que deve ter uma maneira melhor de implementar a logica dos comandos para serem usados, os comandos eu pensei nao foi apenas para ser possivel a TUI usar o ambiente, eu pensei neles para ser mais uma maneira de usar o ambiente , por exemplo, eu poderia ter botoes na interface que façam a mesma coisas que os comandos, mas eu tambem quero ter a possibilidade de comandos para um usuairo mais habiildoso poder usar. eu queria a sua avaliacao e analise para me dar uma luz de como podemos tomar a decisao nesse ponto. eu preciso conseguir explicar o caminho que temos que seguir. tenho perguntas  como , qual seria uma boa maneira de criar a soluacao de comando ? qual é o real problema que estamos resovlendo ?



Vou ancorar isso no código que você escreveu, porque o diagnóstico está lá.

Primeiro: qual é o problema real
Você já disse a resposta na sua pergunta, mas vale nomear com precisão. Você não quer "comandos". Você quer:

Um conjunto de ações sobre o ambiente, exposto por múltiplas superfícies (botão, atalho, texto /, e mais tarde: o próprio agente, ou um script), sem que a regra seja reimplementada em cada superfície.

O comando / não é a feature. Ele é uma forma de acionar uma coisa que existe independente dele. Você mesmo formulou assim: "eu poderia ter botões na interface que façam a mesma coisa que os comandos". Isso não é coincidência de design — é o sinal de que a ação é o conceito, e / é um jeito de digitar a ação.

Reformulando o problema em três partes que hoje estão coladas:

parte	pergunta que responde	hoje mora em
catálogo de ações	o que dá para fazer com o ambiente?	espalhado: enum Comando + match/case em 3 classes
sintaxe / parsing	como o texto "/nova-tarefa X" vira "quero a ação nova-tarefa com argumento X"?	mensagem.split() dentro do domínio
execução	quem realmente muda o estado?	os mesmos match/case
Enquanto essas três estiverem no mesmo lugar, um botão não tem como reusar a ação sem passar por uma string. E é exatamente aí que a duplicação nasce: ou a TUI monta "/nova-tarefa " + nome (frágil, e TD-11 já mostra que quebra com espaços), ou a TUI chama o método direto e agora existem dois caminhos com regras que vão divergir.

O que está errado no desenho atual, concretamente
Não é "está no domínio" no abstrato. São efeitos observáveis:

O roteamento depende de onde você está. Ambiente.enviar → Projeto.enviar → Sessao.enviar roteia pelo nó ativo. Então /nome-chat não age sobre "aquele chat" — age sobre o chat ativo da sessão ativa do projeto ativo. Um botão numa lista precisa dizer qual item. A cadeia não tem como receber isso: a única entrada é uma string, e o alvo é implícito.
O resultado é uma string. _acionar_comando devolve "Erro - Sessao indice [3] nao existe". A TUI não tem como saber se deu certo. Não dá para pintar de vermelho, não dá para não fechar o modal, não dá para testar sem comparar texto em português.
O catálogo não é consultável. A paleta / do seu mockup precisa listar comandos, mostrar descrição, saber quantos argumentos cada um pede, e saber quais estão disponíveis no contexto atual. Hoje isso está em match/case — que é código, não dado. Você teria que manter uma segunda lista à mão para a paleta, e ela vai dessincronizar.
Sessao é o pega-tudo. Ela assume qualquer / porque é o último andar, inclusive para dizer "não conheço". Ou seja, o erro de comando desconhecido é uma regra de interface implementada na camada mais profunda do domínio.
Repare: nenhum desses quatro problemas é resolvido só por "mover para outra camada". Isso importa para você conseguir explicar o caminho.

Avaliando as três opções
A) Manter no domínio. O domínio passa a depender da sintaxe de uma interface específica. Quando entrar botão, o botão terá que falar /. Quando entrar o agente acionando ações via ferramenta, ele também. Você acaba com uma linguagem de string como API interna do sistema — que é serialização sem ganho nenhum. E mantém os 4 problemas acima.

C) Na TUI. Resolve o acoplamento do domínio, mas coloca o catálogo de ações dentro da interface. Aí o núcleo deixa de ser usável sem TUI — você perde a possibilidade de script, de teste sem interface, e o agente não tem como acionar nada. Também viola direto o RF-F17 no espírito: a TUI vira dona da regra "o que existe para fazer".

B) Serviço de comandos na aplicação. É a direção certa, mas do jeito que está escrita a opção ainda mistura duas coisas: "traduz a string" e "devolve mensagem de sistema". Se o serviço de comandos for o caminho, o botão continua tendo que produzir uma string para passar por ele.

A forma que eu proporia
Separar B em duas peças, e essa é a ideia central que eu acho que destrava seu problema:



TUI: paleta "/"  ──► Parser (aplicação) ──┐
TUI: botão       ─────────────────────────┤
TUI: atalho      ─────────────────────────┼──► Ação (aplicação) ──► Domínio
Agente (futuro)  ─────────────────────────┘         │
                                            ┌───────┴───────┐
                                         Catálogo      Resultado
                                      (metadados)   (tipado, não string)
1. Ação como objeto de primeira classe na camada de aplicação.

Cada ação carrega o que precisa para ser executada e o que precisa para ser exibida:



python
@dataclass(frozen=True)
class Acao:
    nome: str                  # "nova-tarefa"
    descricao: str             # para a paleta e o tooltip do botão
    parametros: list[Parametro]  # nome, tipo, obrigatório
    escopo: Escopo             # AMBIENTE | FRENTE | TAREFA — de que alvo precisa
    executar: Callable[[Alvo, dict], Resultado]
Isso é um registro, não um match/case. A diferença prática: um registro é dado, então a paleta pode iterar sobre ele, filtrar por escopo, gerar o formulário de argumentos, e validar antes de executar. O match/case não pode ser lido por ninguém.

2. O parser / é um adaptador de entrada, e é fino.

Sua única responsabilidade: "/nova-tarefa campanha de verao" → ("nova-tarefa", {"nome": "campanha de verao"}). Ele não conhece regra de negócio, não sabe o que a ação faz. Um botão pula essa etapa inteira e chama a ação direto com os argumentos que já tem tipados — que é exatamente o que você queria.

E note que TD-11 (espaços quebram argumento) deixa de ser um bug espalhado por 3 classes: é um bug de uma função, com um teste.

3. Alvo explícito, em vez de "o ativo".

A ação recebe a identidade de sobre o que ela age (e aqui a Pergunta 4 se encaixa — identidade opaca e estável). "O item ativo" vira um default que o parser preenche quando você digita /, não uma verdade embutida no domínio. Assim o botão "renomear" numa lista de 5 chats consegue dizer qual dos 5.

4. Resultado tipado.

Resultado com sucesso/falha e, no caso de falha, um motivo estruturado. A TUI decide como renderizar; o modo / renderiza como mensagem de sistema (comportamento atual preservado), o botão renderiza como toast ou validação inline. A mensagem em português vira responsabilidade da interface, não do núcleo.

5. O domínio fica sem saber que comandos existem.

Frente.criar_tarefa(nome) continua existindo e continua sendo onde a invariante mora. A ação é uma casca fina que chama isso, coordena com a persistência, e traduz o resultado. Isso é consistente com o que você já decidiu na Pergunta 1B.

O que isso te dá, e o que custa
Ganha:

Uma regra, N superfícies — que é literalmente o RF-F17, agora estruturalmente garantido em vez de mantido por disciplina.
Paleta e botões geram-se a partir do mesmo catálogo. Adicionar uma ação nova = uma entrada no registro, e ela aparece na paleta automaticamente.
Testável sem TUI e sem string: executar(acao, alvo, args).
Quando o agente ganhar ferramentas, o catálogo já é a lista de ferramentas. Você não precisa inventar nada — o mesmo registro vira a tool definition.
Autorização/disponibilidade contextual (esta ação faz sentido agora?) tem um lugar único para morar.
Custa:

Mais estrutura do que match/case. Para 13 comandos, isso é honestamente umas 100–150 linhas a mais.
Uma indireção: ler "o que /nova-tarefa faz" exige olhar o registro e depois a função, em vez de um case.
O risco que eu quero apontar
Existe uma versão exagerada disso: sistema de plugins, descoberta dinâmica, middleware, undo/redo, decoradores @comando. Não faça. Isso é framework, e você tem 13 comandos e um usuário.

A linha que eu traçaria: registro é um dict literal em um módulo, escrito à mão. Se um dia forem 60 ações, você reavalia. O valor está na separação (catálogo / parsing / execução / resultado), não na maquinaria.

Como eu escreveria a justificativa da decisão
Se você precisa explicar o caminho, eu formularia assim:

Comandos não são um recurso da interface de texto — são o vocabulário de ações do ambiente. A sintaxe / é uma de várias formas de acionar esse vocabulário, ao lado de botões, atalhos e, futuramente, do próprio agente. Portanto o catálogo de ações pertence à camada de aplicação, o parser / é um adaptador de entrada descartável, e o domínio permanece sem conhecimento de qualquer sintaxe. Isso torna o RF-F17 uma propriedade da arquitetura em vez de uma convenção a ser mantida manualmente.

Ou seja: B, com a ressalva de que "serviço de comandos" deve ser lido como "catálogo de ações + parser separado", não como uma função que recebe string. Se a formulação da pergunta te obriga a escolher uma letra, é B — mas vale registrar essa qualificação na resposta, porque ela muda o que vai ser construído.







Your modified files:
application-design-plan.md
C:\Users\pedro\OneDrive\Área de Trabalho\dev\FishingRod\aidlc-docs\inception\plans
+51
-2
Pergunta 9 — Onde mora o portão de revisão humana da escrita na wiki (US-14)

RNF-14 trata a wiki como entrada não confiável e aponta a revisão humana como uma das duas
defesas. A pergunta é quem segura a escrita.


A) (recomendo) A ferramenta do bibliotecário não escreve: ela devolve uma proposta de
escrita (caminho lógico, conteúdo, links). Um serviço de aplicação guarda a proposta pendente, a
TUI mostra, e a escrita só acontece na aprovação. O agente nunca tem poder de escrita direto

B) A ferramenta escreve, mas antes chama um callback de confirmação que a TUI responde


C) A ferramenta escreve em área de rascunho dentro da raiz da wiki, e a aprovação move o arquivo
para o lugar definitivo


D) Other (please describe after [Answer]: tag below)


[Answer]: A - a segurança vai ser via ferramentas que vamos disponibilizar para o bibliotecario. eu penso o bibliotecario como a camada de funcionalidades que o agente vai usar para interagir com a wiki, e para o agente interagir com a wiki ele vai utiilzar ferramentas que vai aplica regras de segurança , nesse caso sendo a regra de escrita, onde vai ser feito um processo de aprovação antes da escrita ser realizada.

Categoria D — Dependências e comunicação

Pergunta 10 — Como o bibliotecário acessa a wiki

ESC-20 diz "exclusivamente pelas ferramentas do bibliotecário". Falta decidir se essas ferramentas
são as nativas do SDK com permissão restrita, ou tools nossas. Fato relevante: o spike mediu
permissão de tool MCP; permissão de ferramenta de arquivo nativa não foi medida. Escolher
(A) transforma uma coisa não medida em fundação da segurança da wiki.

A) Ferramentas de arquivo nativas do agente (Read/Write/Glob/Grep) com permissão restrita à raiz
da wiki, confiando na configuração do SDK


B) (recomendo) Tools nossas, expostas ao agente por MDP/MCP in-process (caminho já medido pelo
spike): listar, ler, buscar, propor_escrita. Ferramentas nativas de escrita negadas. O
confinamento de caminho é código nosso, num ponto único, testável sem credencial — e é o que
RF-F14 e RNF-10 pedem

C) Híbrido: leitura pelas nativas (Read/Grep/Glob, baratas e boas), escrita só pela nossa tool


D) Other (please describe after [Answer]: tag below)


[Answer]:



Vou separar as fibras, porque você misturou três decisões que têm respostas diferentes — e essa separação é justamente o que evita "reinventar a roda em várias tools".

1. Reformulando: a pergunta não é sobre a wiki, é sobre uma regra de classificação
Você percebeu isso sozinho quando listou os stores. Você vai ter pelo menos quatro domínios de dado:

domínio	quem escreve	tem invariante do software?	quem já resolve bem?
estado do ambiente (frentes, tarefas, chats, memória)	ações do usuário	sim, forte	ninguém — é seu
transcrição	turno de conversa	append-only, fraca	ninguém — é seu
wiki	agente, sob aprovação	sim, forte (esquema, confinamento, aprovação)	ninguém — é seu
arquivos do usuário (a PPT da reunião)	usuário/agente	não, é área livre	ferramentas nativas
mundo externo (web search)	ninguém	não	SDK/nativo
A regra que eu proporia, e que você pode aplicar para sempre:

Escreva sua própria tool quando o acesso carrega uma invariante que o software precisa garantir. Use a nativa quando o acesso é genérico e o dano de um mau uso é local.

Isso responde direto seu medo de reinventar a roda: você não vai fazer tool própria de web search, nem de manipular a PPT do usuário. Você vai fazer tool própria para os três stores onde o software tem regra. Isso é finito e pequeno — não é uma política de "tudo é nosso".

2. Por que a wiki cai claramente do lado "nossa tool" — e o motivo principal não é segurança
O argumento de segurança (confinamento de caminho, RF-F14/RNF-10) é real, mas é o segundo argumento. O primeiro é mais forte e você ainda não o nomeou:

Se o agente vê a wiki como filesystem, a abstração da wiki vaza e a wiki apodrece.

ESC-17 diz: entidade = pasta, propriedade = arquivo, profundidade travada em dois níveis, links [[...]], index.md como porta de entrada. Isso não é um layout de arquivos — é um modelo de dados que por acaso mora em arquivos.

Com Write nativo, o agente pode criar wiki/clientes/acme/2024/q3/notas/rascunho.md. Nada no filesystem impede. A regra "dois níveis" vira uma instrução no prompt — ou seja, uma sugestão estatística. Você mesmo marcou na tabela de perguntas que o critério do bibliotecário entre criar entidade e criar propriedade é o "risco número um do desenho da wiki; sem regra, a wiki apodrece em semanas". Ferramenta nativa é exatamente a decisão que torna essa regra inexequível.

Com tool própria, a assinatura é a regra:



propor_escrita(entidade: str, propriedade: str, conteudo: str, links: list[str])
Não existe parâmetro para o terceiro nível. O agente não pode violar o esquema porque a violação não é representável. Isso é a diferença entre uma regra que você pede e uma regra que você garante.

E veja: isso não é reinventar Write. Write escreve bytes num caminho. Sua tool cria uma propriedade numa entidade, valida o esquema, e devolve uma proposta pendente. São operações diferentes, num vocabulário diferente. Você não está reimplementando — está subindo o nível de abstração, que é o que a Pergunta 9A já decidiu.

3. Três fatos que eliminam A, e um que também elimina C
(a) RNF-11 é incompatível com ferramenta nativa. "A wiki é endereçada por caminho lógico relativo, nunca por caminho absoluto. Nenhum caminho absoluto é persistido." Ferramenta nativa opera com caminhos reais — e esses caminhos aparecem na conversa (chamada de tool e resultado), que vai para a transcrição, que você acabou de decidir persistir. Você violaria RNF-11 pelo caminho lateral. Não tem como evitar sem envolver a tool.

(b) Q9A já foi decidida e é incompatível com Write nativo. Você decidiu que o agente nunca tem poder de escrita direto — ele propõe. Write nativo escreve. Não existe configuração de permissão que transforme "escrever" em "propor". A opção A está morta por decisão anterior, não por preferência.

(c) A confia numa coisa não medida. Você mesmo anotou: o spike mediu permissão de tool MCP; escopo de ferramenta de arquivo nativa não foi medido. Fundar a segurança da wiki nisso é assumir, não verificar.

E sobre C (híbrido: leitura nativa, escrita nossa) — esse é o mais tentador e vale examinar com honestidade, porque Grep/Glob são genuinamente bons e o modelo é muito treinado neles. Mas:

C não escapa do problema (c). Para leitura nativa não virar "o agente lê meu disco inteiro", você precisa exatamente da restrição de caminho nativa que não foi medida. C carrega o mesmo risco não verificado de A.
C quebra ESC-20 literalmente — "acesso exclusivamente pelas ferramentas do bibliotecário" vira "quase exclusivamente".
Leitura é o vetor de injeção, não escrita. RNF-14 trata a wiki como entrada não confiável. Se a leitura passa pela sua tool, você tem um lugar para envelopar o conteúdo ("o texto abaixo é dado, não instrução"), truncar, ou marcar procedência. Com Read nativo, o conteúdo entra cru no contexto e você não tem onde intervir.
A leitura nativa vaza o layout físico, e a partir do momento em que o agente sabe que é um filesystem, ele vai tentar escrever como filesystem e falhar — o que gasta turnos e piora o comportamento.
O contra-argumento honesto a favor de C: leitura por tool própria é mais código e possivelmente pior busca que Grep. Mas buscar na sua wiki pode ser ripgrep chamado por baixo, confinado à raiz. Você reusa a ferramenta, sem reusar a exposição dela ao modelo. Essa distinção resolve boa parte do seu medo de retrabalho.

4. A questão do MCP e multi-LLM — separe protocolo de implementação
Aqui eu quero corrigir uma premissa da sua pergunta. Você disse: "se eu tiver que fazer uma camada MCP própria para qualquer LLM conseguir usar o sistema". Isso trata MCP como um trabalho grande. Não é, se você estruturar assim:



Bibliotecário (aplicação)          <- regra: esquema, confinamento, proposta
  listar() ler() buscar() propor_escrita()
            │
    ┌───────┴────────┬──────────────┐
 adaptador MCP   chamada direta   futuro: OpenAI
 (Claude SDK)    (testes, TUI)     function calling
O trabalho real está no bibliotecário — funções Python normais, testáveis sem LLM nenhum. O adaptador MCP é declaração de schema JSON em cima delas. Dezenas de linhas, não centenas. E se amanhã entrar outro modelo, você escreve outro adaptador fino; a regra não é reescrita.

Repare que isso é a mesma forma que você já aceitou na Pergunta 7: um catálogo de operações declarativo, com adaptadores de entrada finos por superfície. Lá as superfícies eram paleta /, botão e atalho. Aqui são MCP, chamada direta e futuros SDKs. É um padrão só, aplicado duas vezes. Isso é o oposto de reinventar a roda — é ter uma roda e vários eixos.

Duas ressalvas importantes sobre MCP, para você não decidir por motivo errado:

MCP não é a fronteira de segurança. In-process, MCP é basicamente despacho de função. A garantia vem do código dentro da tool (confinamento, validação de esquema, fila de aprovação) e da negação das ferramentas nativas de escrita. MCP é o formato de exposição, não o guarda. Se você justificar B dizendo "MCP é seguro", o argumento é frágil. Justifique dizendo "a regra está em código nosso, num ponto único, testável sem credencial".
Não faça MCP para tudo. Web search: use a nativa. Arquivos do usuário: quando chegar, provavelmente nativa numa raiz de workspace do usuário, porque lá não há invariante do software a proteger — é área livre por definição. Reserve o esforço para os stores com regra.
5. O que eu diria que é o custo real
Sendo concreto, para não vender fácil:

4 tools, ~150–250 linhas de aplicação.
Confinamento de caminho: ~15 linhas, e o teste de propriedade já é exigido por RNF-10/PBT-03 — ou seja, esse custo você paga em qualquer opção que tenha escrita.
Adaptador MCP: dezenas de linhas, caminho já medido pelo spike.
Custo contínuo real: qualidade da busca. Sua buscar precisa ser boa o bastante, e você vai iterar nela. Esse é o item que eu marcaria como risco aberto, não a segurança.
6. Resumo para você conseguir explicar
A escolha não é "tools próprias vs nativas" como política geral — é uma classificação por store. Onde o acesso carrega invariante do software, a tool é nossa; onde é genérico, usamos a nativa. A wiki carrega três invariantes simultâneas (esquema de dois níveis, confinamento de caminho, escrita só por proposta aprovada), e nenhuma delas é expressável como configuração de permissão de ferramenta de arquivo. Além disso, ferramenta nativa é incompatível com RNF-11 (caminho lógico) e com a decisão da Pergunta 9 (agente sem poder de escrita direto). Por isso: tools nossas, com o bibliotecário implementado como funções Python puras e o MCP como adaptador fino de exposição — o que também dá portabilidade para outros modelos sem reescrever regra.

Ou seja, B — e o híbrido C merece ser registrado como rejeitado com motivo, porque ele parece o meio-termo sensato mas não elimina o risco não medido nem o vetor de injeção.

Uma coisa que eu deixaria explicitamente fora desta decisão: o store de arquivos do usuário (a PPT). Você já disse que é assunto para outro momento, e concordo — mas vale anotar no plano como decisão futura já classificada ("área livre, sem invariante, provavelmente nativa"), para que a Pergunta 10 não seja lida depois como se tivesse decidido que tudo é tool própria.







sobre a sua explicacao resumida, eu entendi que teriamos uma ferramenta que seria o bibliotecario, ai ja me levantou uma suspeita para uma coisa que eu ja estava pensando e ja estava no meu alerta , essa coisa é sobre a questao do bibliotecario e o rod-maker serem apenas ferramentas e nao agentes proprios do sistema , vou explicar o motivo de eu ter pensado nisso e quero a sua avaliacao e vemos como responder a pergunta 10, e se essa minha explicacao de agora onde seria melhor responder.

minha explicacao - vc ao meu ver explicacou uma implementacao onde o bilbiotecario é a apliacao onde tem as funcoes e que aplica a regra e ele teria adptadores para quem for usar, me pareceu que isso é mais uma ferramenta doque realmente um agente. oq me leva a pensar uma forma de uso do software na interace muito boa que eu imagino - a forma de uso boa que imagino seria o usuario usar as ferramentas do bibliotecario e do rod-maker atravez do orquestrador, o usuario poderia digitar diretaemte falando com o orquestrador que quer registrar alguma informacao na wiki ou o proprio orquestrador sugerir armazenar alguma informacao que achou relevante ao usuario ( eu vejo esse tipo de sugestao sendo um uso muito bom para o orquestrador pois ele é para ser o ponto central que o usaurio conversa e comanda tudo, orquestra tudo, direcionado tudo , e opera o sistema, aqui é um trabalho de funcionalidade de software que pode ser otimizada com o tempo) . isso seria o mesmo para o rod-maker , onde o usuario poderia pedir para construir um agente ou o proprio orquestrador sugerir construir um agente para uma tarefa que percebeu que o usuario ja vez muitas vezes aqui  é um trabalho de funcionalidade de software que pode ser otimizada com o tempo.

deu para perceber que talvez isso ate se encaixe com a maneira de uso que eu imagino que seria a melhor para o software ? oq vc acha? como vc avalia essa questao ? onde é melhor responder essa pergunta ?



Sua suspeita está certa, e o erro foi meu — vou apontar exatamente onde.

O que eu colapsei
No resumo eu escrevi "o bibliotecário implementado como funções Python puras". Isso não descreve o bibliotecário; descreve as ferramentas que o bibliotecário usa. São coisas distintas, e eu as fundi numa frase. Repare que o próprio título da Pergunta 10 já denuncia isso: "Como o bibliotecário acessa a wiki" — a pergunta pressupõe um ator que acessa. Ferramenta não acessa; ferramenta é o acesso.

A estrutura correta tem três camadas, não duas:



Usuário ──► Orquestrador (agente, superfície de conversa)
                 │ delega
                 ▼
          Bibliotecário / Rod-maker  (agentes: JULGAMENTO)
                 │ usa
                 ▼
          Tools de wiki  (código: GARANTIA)
            listar/ler/buscar/propor_escrita
                 │
                 ▼
          Wiki no filesystem
A Pergunta 10 decide só a camada de baixo. Sua pergunta agora é sobre a camada do meio — e ela é uma decisão diferente, ainda não tomada em nenhum lugar do plano.

O teste que separa ferramenta de agente
É agente se a função exige julgamento que não se reduz a regra. É ferramenta se o comportamento é determinístico dado o input.

Aplicando ao bibliotecário, você tem a resposta escrita no seu próprio plano: a Pergunta 13 existe porque decidir entre criar entidade nova e criar propriedade dentro de entidade existente não tem regra fechada. Você chamou isso de "risco número um". Além disso: escolher o título da propriedade, redigir o markdown no estilo da wiki, decidir quais [[links]] fazem sentido, perceber que a informação nova contradiz algo já escrito. Nada disso é expressável como if.

Ou seja: o bibliotecário é irredutivelmente um agente. A parte dele que é código (confinar caminho, validar esquema, enfileirar proposta) é a cerca, não o curador. As duas coisas precisam existir, e é bom que existam separadas — a cerca garante que o julgamento errado do agente não cause dano estrutural.

O rod-maker é ainda mais claro: construir um agente é escrever prompt, escolher ferramentas, definir regras. Isso é geração de conteúdo, atividade de LLM por natureza.

E note: seu código já dizia isso. Em agente.py você tem Papel.SUB_AGENTE e NOME_SUB_AGENTE_ROD_MAKER = "rod-maker". Você modelou o rod-maker como sub-agente desde o começo. Sua intuição de agora não é uma ideia nova — é você percebendo que meu resumo contradizia uma decisão que você já tinha tomado.

Agora, a parte onde eu discordo de você
Você conectou isso ao seu modelo de uso: usuário fala com o orquestrador, o orquestrador aciona bibliotecário e rod-maker. Eu concordo que esse modelo de uso é bom — mas ele não é argumento para bibliotecário ser agente, e é importante você saber disso para não construir a justificativa em cima de areia.

Motivo: o orquestrador poderia perfeitamente receber as tools de wiki diretamente e fazer ele mesmo o julgamento de curadoria. A experiência do usuário seria idêntica — ele digita "registra isso na wiki", aparece uma proposta, ele aprova. Do lado de fora, indistinguível. Então o modelo de uso não discrimina entre as opções.

O que realmente discrimina são três coisas, e essas sim são bons argumentos:

1. Isolamento de contexto (o argumento prático). O bibliotecário precisa carregar: o esquema da wiki, o index.md, a regra entidade-vs-propriedade, convenções de redação, e o conteúdo das páginas que ele leu para decidir. Isso é muito token. Se tudo isso entra na janela do orquestrador, o orquestrador — que é o ponto central da conversa, o que você mais quer que funcione bem — fica pior a cada registro na wiki. Sub-agente resolve: ele consome contexto no próprio processo e devolve só a proposta.

2. Quarentena de conteúdo não confiável (o argumento de segurança). Este é o mais forte e o menos óbvio. RNF-14 diz que a wiki é entrada não confiável — conteúdo pode conter instrução dirigida ao modelo. Se o orquestrador lê a wiki diretamente, uma injeção entra na conversa principal, que é justamente a que tem autoridade sobre tudo. Com sub-agente, o conteúdo suspeito é absorvido por um agente com poucas ferramentas e nenhuma autoridade (ele nem pode escrever — Q9A), e o que volta para o orquestrador é uma proposta estruturada, não texto livre. Isso transforma o sub-agente numa fronteira de segurança real, não só numa organização de código.

Isso é significativo: você tem agora duas defesas em profundidade para RNF-14 — confinamento no código (cerca) e isolamento de contexto (quarentena) — em vez de uma.

3. Afinar independente. A qualidade da wiki depende do prompt do bibliotecário. Você vai iterar nele muito, medindo "a wiki apodreceu ou não?". Se esse prompt está fundido com o do orquestrador, cada ajuste na curadoria arrisca degradar a conversa, e você não consegue atribuir causa.

O custo honesto: mais uma chamada de LLM (latência e consumo), e encanamento agente-para-agente — o que significa que a porta de sessão (Pergunta 5) precisa ser reentrante ou aninhável. Isso não é trivial e você deveria decidir com consciência disso.

Um alerta sobre uma parte da sua visão
Você mencionou "o próprio orquestrador sugerir armazenar informação que achou relevante" e "sugerir construir um agente para uma tarefa que o usuário já fez muitas vezes". Esses dois são ótimos — e são proatividade, que é uma categoria diferente de tudo que discutimos.

Eu suspeito que isso cai nos cinco comportamentos diferenciais (FOR-06), que você marcou como fora desta iteração em C1. Vale conferir. Se cair, o caminho certo é: a arquitetura desta iteração permite proatividade (o orquestrador tem acesso ao catálogo de ações e às capacidades dos sub-agentes, logo pode sugerir), mas a implementação da sugestão fica para depois. Você preserva o futuro sem inflar o escopo — exatamente o padrão que você já usou com autenticação (desenhar para dois, implementar um).

Onde responder
Eu não responderia isso na Pergunta 10. Motivos:

A Pergunta 10 é sobre as tools, e a resposta é B independentemente de o bibliotecário ser agente ou não. Se ele é agente, B é ainda mais necessária (a cerca precisa existir justamente porque há julgamento acima dela). Enfiar essa discussão em D) polui a decisão e a torna difícil de rastrear depois.
Isso é identificação de componente: "bibliotecário e rod-maker são agentes de primeira classe do sistema, não módulos de aplicação". Pertence à Categoria A, ao lado das Perguntas 1, 2 e 3.
E é uma decisão com consequência em cascata: afeta a Pergunta 5 (a porta de sessão precisa suportar sessão aninhada?), a Pergunta 13 (o critério entidade-vs-propriedade é prompt do bibliotecário ou validação de código? — provavelmente ambos, em níveis diferentes), e como as tools são registradas (por agente, não globalmente).
Concretamente, eu sugeriria:

Responder a Pergunta 10 com B, acrescentando uma frase de precisão: "as tools são a cerca determinística; quem as usa é o agente bibliotecário — ver Pergunta 3-bis".
Acrescentar uma pergunta nova na Categoria A (pode ser 3-bis, para não renumerar), sobre a natureza de bibliotecário e rod-maker: agentes de primeira classe com contexto próprio × módulos de aplicação sem LLM × tools entregues direto ao orquestrador.
Registrar no plano que essa nova pergunta surgiu de uma imprecisão na minha explicação anterior — porque isso é rastreabilidade honesta, e a auditoria do AI-DLC pede isso.
Quer que eu escreva essa Pergunta 3-bis com as opções e o contexto, no formato do arquivo, para você revisar antes de eu inserir?







vc tem razao eu me precipitei com a ideia de treansformar o bibliotecario e o rod-maker em apenas ferramentas, realmente eles sao precisam ser agentes pois eles tem e precisam ter julgamento para executar as tarefas e isso se faz com os agentes. vamos votlar para responder a questao 10. vamos cosntruir uma resposta completa paraa questao 10. vamos explicar claramente a ideia de tools proprioa e nativas e explicar oq nao restringe . temos que ficar espertos com a questao de quando fazer e quando reaproveitar ferramentas nativas.


Read
application-design-plan.md
#L305-334
application-design-plan.md
cancelled
+87
-3
 
[Answer]:
 
#### Pergunta 11 — Composição de dependências (quem monta quem)
[Answer]: B — tools nossas para a wiki, expostas por MCP in-process. Abaixo o raciocínio completo,
incluindo a regra geral que evita que essa decisão vire "tudo é tool própria".
 
**Precisão de vocabulário (correção de uma imprecisão anterior).** As tools da wiki são a *cerca
determinística*; quem as usa é o **agente bibliotecário**, que tem julgamento próprio. Tool não é
agente. Esta pergunta decide apenas a camada de baixo:
 
```
Orquestrador (agente)  ──delega──►  Bibliotecário (agente: JULGAMENTO)
                                          │ usa
                                          ▼
                                    Tools de wiki (código: GARANTIA)
                                    listar / ler / buscar / propor_escrita
                                          │
                                          ▼
                                    Wiki no filesystem
```
 
A natureza do bibliotecário e do rod-maker como agentes de primeira classe é decisão separada
(Categoria A) — já sustentada pelo código atual, que tem `Papel.SUB_AGENTE` e
`NOME_SUB_AGENTE_ROD_MAKER`.
 
---
 
**A regra geral: quando fazer tool própria e quando reaproveitar a nativa**
 
> **Tool própria quando o acesso carrega invariante que o software precisa garantir.
> Tool nativa quando o acesso é genérico e o dano de um mau uso é local.**
 
Classificação dos stores do sistema por essa regra:
 
| domínio de dado | invariante do software? | decisão |
|---|---|---|
| estado do ambiente (frentes, tarefas, chats, memória) | sim, forte | acesso por ações nossas (Pergunta 7) |
| transcrição de mensagens | append-only, fraca | persistência nossa (Pergunta 3) |
| **wiki** | **sim, forte** (esquema, confinamento, proposta) | **tools nossas — esta pergunta** |
| arquivos do usuário (ex.: a PPT da reunião) | não — área livre | **nativa**, quando entrar em escopo |
| mundo externo (web search) | não | **nativa** |
 
Isto é o que impede o efeito "reinventar a roda em várias tools": não haverá tool própria de busca
web nem de manipulação de arquivo do usuário. A lista de tools nossas é finita e pequena, e é
justamente onde há regra a garantir.
 
---
 
**Por que a wiki cai do lado "nossa tool" — quatro razões, em ordem de força**
 
1. **Integridade do esquema (razão principal, não é segurança).** ESC-17 fixa entidade = pasta,
   propriedade = arquivo, **profundidade travada em dois níveis**. Com `Write` nativo, o agente
   pode criar `wiki/clientes/acme/2024/q3/notas.md` — nada no filesystem impede, e a regra vira
   uma instrução de prompt, ou seja, uma sugestão estatística. Com tool própria, a assinatura
   *é* a regra: `propor_escrita(entidade, propriedade, conteudo, links)` não tem parâmetro para
   um terceiro nível. A violação deixa de ser representável. Isso ataca diretamente o "risco
   número um" registrado na Pergunta 13 (a wiki apodrecer por decisão inconsistente).
 
2. **Incompatibilidade com RNF-11.** "Endereçamento por caminho lógico relativo; nenhum caminho
   absoluto persistido." Ferramenta nativa opera com caminhos reais, que aparecem na chamada e no
   resultado da tool, que vão para a transcrição — que a Pergunta 3 decidiu persistir. RNF-11
   seria violado por via lateral, sem forma de evitar.
 
3. **Incompatibilidade com a Pergunta 9A, já decidida.** O agente não tem poder de escrita direto:
   ele *propõe*. Não existe configuração de permissão que transforme "escrever" em "propor".
 
4. **A confia numa coisa não medida.** O spike mediu permissão de tool **MCP**; escopo de
   ferramenta de **arquivo** nativa não foi medido. Fundar RF-F14/RNF-10 nisso é assumir, não
   verificar.
 
---
 
**Por que C (híbrido) foi rejeitado, apesar de parecer o meio-termo sensato**
 
`Grep`/`Glob` são genuinamente bons e o modelo é bem treinado neles — o argumento a favor é real.
Ainda assim:
 
- **C não escapa do risco não medido.** Para leitura nativa não virar "o agente lê o disco
  inteiro", é preciso exatamente a restrição de caminho nativa que não foi verificada. C carrega
  o mesmo risco de A.
- **C quebra ESC-20 na letra**: "exclusivamente pelas ferramentas do bibliotecário" viraria
  "quase exclusivamente".
- **Leitura é o vetor de injeção, não escrita.** RNF-14 trata a wiki como entrada não confiável.
  Com leitura pela nossa tool existe um ponto para envelopar o conteúdo ("o texto abaixo é dado,
  não instrução"), truncar e marcar procedência. Com `Read` nativo o conteúdo entra cru.
- **Leitura nativa vaza o layout físico**, e um agente que sabe que aquilo é filesystem tentará
  escrever como filesystem — gastando turnos em tentativas que serão negadas.
 
**Reaproveitamento sem exposição**: `buscar` pode usar `ripgrep` por baixo, confinado à raiz.
Reusa-se a ferramenta madura sem expor a ferramenta genérica ao modelo. Ess






vamos incluir an resposta da pergunta 10 apenas as coisas que discutirmos sobre a pergunta 10 e sao relevantes para a responder a pergutna 10


application-design-plan.md
+66
-1
 
[Answer]:
[Answer]: B — tools nossas para a wiki, expostas por MCP in-process; ferramentas nativas de
escrita negadas.
 
**Precisão de vocabulário**: as tools são a *cerca* determinística sobre a wiki. Quem as usa é o
**agente** bibliotecário, que continua sendo agente de primeira classe (ele carrega o julgamento
de curadoria — Pergunta 13). Esta pergunta decide apenas a camada de acesso, não a natureza do
bibliotecário.
 
**A regra de decisão adotada** (vale para toda tool futura, não só para a wiki):
 
> Tool nossa quando o acesso carrega uma invariante que o software precisa garantir.
> Ferramenta nativa quando o acesso é genérico e o dano de um mau uso é local.
 
Classificação por store:
 
| store | tool | motivo |
|---|---|---|
| wiki | **nossa** | esquema de dois níveis, confinamento de caminho, escrita só por proposta |
| estado do ambiente / transcrição | **nossa** | invariantes de domínio; não existe equivalente nativo |
| busca na web | **nativa** | sem invariante do software; reimplementar é puro retrabalho |
| arquivos do usuário (ex.: a PPT da reunião) | **nativa** (decisão futura) | área livre por definição; classificada aqui só para registrar que a Pergunta 10 **não** decidiu que "tudo é tool nossa" |
 
**Por que a wiki cai do lado "nossa" — o motivo principal não é segurança, é integridade do
esquema.** ESC-17 trava a wiki em entidade=pasta / propriedade=arquivo, dois níveis. Com `Write`
nativo nada impede `wiki/clientes/acme/2024/q3/notas.md`: a regra vira instrução de prompt, ou
seja, sugestão estatística. Com tool nossa, a assinatura *é* a regra — `propor_escrita(entidade,
propriedade, conteudo, links)` não tem parâmetro para um terceiro nível, e a violação deixa de ser
representável. Isso ataca diretamente o "risco número um" registrado na Pergunta 13.
 
Isso **não é reinventar `Write`**: `Write` grava bytes num caminho; a tool cria uma propriedade
numa entidade, valida o esquema e devolve uma proposta. Vocabulários diferentes, níveis de
abstração diferentes.
 
**Por que (A) está descartada** — três motivos independentes, qualquer um suficiente:
1. **Incompatível com a Pergunta 9A**, já decidida: o agente não tem poder de escrita direto. Não
   existe configuração de permissão que transforme "escrever" em "propor".
2. **Incompatível com RNF-11**: ferramenta nativa opera com caminho real do disco, e esse caminho
   aparece na chamada de tool, que entra na transcrição persistida (Pergunta 3). Caminho absoluto
   vazaria para o banco pelo caminho lateral.
3. **Funda a segurança da wiki em algo não medido** — o spike mediu permissão de tool MCP, não
   escopo de ferramenta de arquivo nativa.
 
**Por que (C) está descartada**, apesar de `Grep`/`Glob` serem genuinamente bons:
- C **não escapa do risco não medido**: para leitura nativa não virar acesso ao disco inteiro, ela
  precisa exatamente da restrição de caminho nativa que não foi verificada.
- Quebra ESC-20 na letra ("exclusivamente pelas ferramentas do bibliotecário").
- **Leitura é o vetor de injeção, não escrita** (RNF-14). Com `ler`/`buscar` nossas, existe um
  ponto único para envelopar o conteúdo como dado (não instrução), truncar e marcar procedência.
  Com `Read` nativo o conteúdo entra cru no contexto, sem ponto de intervenção.
- Vaza o layout físico: sabendo que é filesystem, o agente tenta escrever como filesystem e falha,
  gastando turnos.
- O ganho de qualidade de busca é recuperável sem C: `buscar` pode usar `ripgrep` por baixo,
  confinado à raiz. Reusa-se a ferramenta **sem** reusar a exposição dela ao modelo.
 
**MCP é formato de exposição, não fronteira de segurança.** In-process, MCP é despacho de função.
A garantia vem do código dentro da tool (confinamento, validação de esquema, fila de aprovação) e
da negação das nativas de escrita. O valor do MCP é outro: portabilidade. O bibliotecário é
implementado como funções Python puras — testáveis sem LLM e sem credencial — e o adaptador MCP é
uma casca de schema por cima. Outro modelo no futuro = outro adaptador fino, **sem reescrever
regra**. É o mesmo padrão já aceito na Pergunta 7 (catálogo declarativo + adaptadores de entrada
finos), aplicado a uma segunda família de superfícies.
 
**Custo assumido**: 4 tools (~150–250 linhas); confinamento de caminho ~15 linhas mais o teste de
propriedade que RNF-10/PBT-03 já exigem em qualquer cenário; adaptador MCP em dezenas de linhas
sobre caminho já medido. O risco aberto real não é segurança, é **qualidade da busca** — item a
iterar, registrado como tal.
 

Resposta da Pergunta 10 registrada em application-design-plan.md:324-393.

Estrutura do que ficou:

Precisão de vocabulário — tools são a cerca; o bibliotecário segue sendo agente. Fecha a ambiguidade que gerou a discussão, sem trazer a decisão de "agente vs módulo" para dentro da Pergunta 10.
A regra de decisão (invariante do software → tool nossa; acesso genérico → nativa) com a tabela por store, incluindo web search e arquivos do usuário como nativos — que é exatamente o "o que não restringe" que você pediu.
Por que a wiki é nossa: integridade do esquema como argumento primário, segurança como secundário, mais o contra-argumento explícito de que isso não é reimplementar Write.
A e C descartadas com motivo, cada uma com os pontos que sobrevivem a escrutínio — em especial que C não escapa do risco não medido e que leitura é o vetor de injeção.
MCP como formato de exposição, não guarda de segurança — para a justificativa não ficar apoiada num argumento frágil.
Custo assumido e o risco aberto (qualidade da busca).
Duas coisas que deixei intencionalmente fora: a discussão sobre bibliotecário/rod-maker serem agentes (fica para a pergunta nova na Categoria A) e a proatividade do orquestrador (provável FOR-06, fora de escopo).

Quer que eu escreva agora a Pergunta 3-bis da Categoria A?







Pergunta 11 — Composição de dependências (quem monta quem)

O domínio não pode construir adaptador, senão a fronteira é decorativa.


A) (recomendo) Um único ponto de composição no ponto de entrada (__main__ / entrypoint do
uv run), que constrói adaptadores e injeta nos serviços; a TUI recebe serviços prontos e não
sabe que SQLite ou Claude existem

B) A TUI monta suas dependências no on_mount, como faz hoje com Ambiente(nome=...)


C) Um módulo container/registry consultado por quem precisar


D) Other (please describe after [Answer]: tag below)


so me faça uma esclarecidmento de aprendizado para eu aprender. eu etendo que a opcao A é claramente melhor mas nao entendo direito o motivo e como isso seria montado no codigo. eu meio que nao consigo visualizar, eu gosto de imaginzar e conseguir visuazliar fluxos ou ate mesmo partes abstratas para eu entender, e essa alternativa A eu nao consigo fazer isso. ai queria aprender. me ensine para eu virar um engenheiro de software melhor



Ótima pergunta pra fazer. Isso se chama Composition Root, e a razão de você não conseguir visualizar é que ele é um conceito sobre onde uma decisão é tomada, não sobre o que o código faz. Vou construir a imagem por partes.

1. A ideia central: existem dois tipos de código
Todo programa tem duas atividades misturadas:

Construir: decidir qual implementação vai ser usada. SQLiteRepositorio() em vez de RepositorioEmMemoria().
Usar: chamar métodos e fazer o trabalho.
A frase que me fez entender isso anos atrás: toda vez que você escreve X(), você está fazendo uma solda. Você grudou permanentemente aquele pedaço de código naquela classe concreta. Não dá pra desgrudar de fora.

Olha seu código real:



python
# tui.py:338
def on_mount(self) -> None:
    ambiente = Ambiente(nome="meu-ambiente")   # <- solda
    self.push_screen(TelaAmbiente(ambiente))
A TUI soldou em si mesma a decisão de qual ambiente existe e como ele é construído. Hoje é inofensivo, porque Ambiente é um dataclass puro. Mas depois da persistência, essa linha vira:



python
def on_mount(self) -> None:
    conexao = sqlite3.connect("...")             # solda em SQLite
    repo = RepositorioSQLite(conexao)            # solda
    porta = AdaptadorClaude(...)                 # solda no Claude SDK
    servico = ServicoAmbiente(repo, porta)       # solda
    ambiente = repo.carregar() or repo.criar(...)
    self.push_screen(TelaAmbiente(servico, ambiente))
Agora a sua camada de tela sabe o que é SQLite. A regra de camadas da Pergunta 2 ("interface não importa adaptador") acabou de morrer numa função de 6 linhas.

2. A imagem mental: a árvore de objetos
Pare de pensar em "injeção de dependência" como técnica e pense em formato. As dependências do seu sistema formam uma árvore:



          ServicoAmbiente          <- raiz do uso
           /            \
RepositorioSQLite    PortaSessao
        |                 |
   Conexao SQLite    AdaptadorClaude
        |                 |
    caminho.db      ClaudeSDKClient
Folhas = coisas concretas do mundo (arquivo, rede, SDK). Raiz = o que a interface usa.

A pergunta da Pergunta 11 é literalmente: quem monta essa árvore?

A) Uma função só, no topo do programa, monta a árvore inteira de baixo pra cima e entrega a raiz pronta.
B) Cada pedaço monta os próprios galhos quando precisa.
C) Existe um armário global; quem precisa de um galho vai lá buscar.
3. Como A fica no código
Um arquivo novo — chame de __main__.py ou composicao.py:



python
# src/fishingrod/__main__.py  — o ÚNICO lugar que conhece todo mundo
 
from fishingrod.adaptadores.sqlite import RepositorioSQLite
from fishingrod.adaptadores.claude import AdaptadorSessaoClaude
from fishingrod.adaptadores.wiki import WikiFilesystem
from fishingrod.aplicacao.servicos import ServicoAmbiente
from fishingrod.interface.tui import FishingRodTUI
 
 
def montar(caminho_db: Path, raiz_wiki: Path) -> ServicoAmbiente:
    repositorio = RepositorioSQLite(caminho_db)          # folha
    sessao      = AdaptadorSessaoClaude()                # folha
    wiki        = WikiFilesystem(raiz_wiki)              # folha
    return ServicoAmbiente(repositorio, sessao, wiki)    # raiz
 
 
def main() -> None:
    servico = montar(Path("~/.fishingrod/dados.db"), Path("~/.fishingrod/wiki"))
    FishingRodTUI(servico).run()
 
 
if __name__ == "__main__":
    main()
E a TUI vira:



python
class FishingRodTUI(App):
    def __init__(self, servico: ServicoAmbiente) -> None:   # RECEBE, não constrói
        super().__init__()
        self.servico = servico
 
    def on_mount(self) -> None:
        self.push_screen(TelaAmbiente(self.servico))
É só isso. A "técnica" toda é: nenhuma classe chama o construtor de outra; ela recebe pronto pelo __init__. A montagem inteira acontece uma vez, num lugar, e desce por parâmetro.

Repare no import da TUI: ela importa ServicoAmbiente (aplicação) e mais nada. Não existe a palavra sqlite em nenhum arquivo de interface/. A regra de camadas passa a ser verificável por grep — que era exatamente a promessa da sua resposta na Pergunta 2.

4. A imagem que talvez destrave: main fica fora das camadas
Você desenhou camadas com uma regra de importação. Mas alguém precisa importar SQLite e a TUI ao mesmo tempo, senão nada se conecta. Isso parece uma contradição — e a resolução é:



  ┌─────────────────────────────────┐
  │  __main__  (composition root)   │  importa TODO MUNDO
  └───────────────┬─────────────────┘
                  │ constrói e injeta
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
interface     aplicação     adaptadores
   └──────────────┴──────────────┘
        as camadas entre si:
        seguem a regra estrita
O main não é uma camada — é o lado de fora. É o único ponto onde a regra "não atravesse camadas" não se aplica, e é justamente por concentrar essa violação num lugar só que todo o resto fica limpo. Analogia: a fábrica parafusa motor, rodas e volante no carro; o motorista só recebe o carro montado. O motorista não sabe montar motor — e é bom que não saiba.

5. Por que B falha, concretamente
Não é estética. São coisas que doem:

Você não consegue testar a TUI. Textual chama on_mount sozinho. Se a construção está lá dentro, não existe ponto onde você diga "use um repositório em memória". Todo teste de tela abre SQLite de verdade e tenta falar com o Claude. Com A, o teste é uma linha:



python
tela = TelaAmbiente(ServicoAmbiente(RepositorioEmMemoria(), SessaoFalsa(), WikiFalsa()))
A resposta trivial de "o que esse sistema usa?" Com A: leia uma função de 5 linhas. Com B: caça ao tesouro por sqlite3.connect em todo o repositório.

Duplicação silenciosa. Quando você tiver TUI e um script CLI, cada um monta do seu jeito, e um dia eles montam diferente — CLI com check_same_thread=False, TUI sem. Bug que só aparece em uma das superfícies.

6. Por que C (container/registry) falha
Essa é a mais sedutora, porque parece resolver B sem passar parâmetros. O problema:



python
class TelaAmbiente:
    def __init__(self):
        self.servico = container.get("servico_ambiente")   # dependência invisível
A assinatura mente. TelaAmbiente() diz "não preciso de nada", e é falso. Você só descobre o que a classe precisa lendo o corpo inteiro dela. Com A, o __init__ é a documentação honesta e completa das dependências — e o type checker verifica.

Além disso: o container é estado global mutável. Testes vazam um pro outro. Ordem de inicialização vira bug fantasma. E container.get("servico") é uma string — erro de digitação vira erro em runtime, não no editor.

Existe um padrão escondido aqui que vale internalizar: C troca uma dependência explícita (parâmetro) por uma implícita (busca global). Toda vez que você faz essa troca, você ganha conveniência de escrita e perde capacidade de raciocinar sobre o código. Quase nunca vale.

7. A regra pra levar pra vida
Construir e usar são responsabilidades diferentes. Empurre toda a construção para a borda do programa; o miolo só recebe.

Um teste rápido pra aplicar em qualquer código: procure NomeDeClasse( fora do entrypoint. Cada ocorrência é uma solda. Algumas são inofensivas (Mensagem(...), datetime(...) — objetos de valor, sem I/O). As que importam são as que tocam o mundo: banco, rede, arquivo, SDK, relógio, aleatoriedade. Essas só nascem no main.

E um detalhe prático: você não precisa de biblioteca de DI. Em Python, uma função montar() com construtores em ordem resolve 95% dos casos. Frameworks de DI existem pra grafos de centenas de objetos. Você tem uns 6.

Uma última coisa que vale reparar: essa decisão é a mesma ideia das Perguntas 7 e 10, num terceiro disfarce. Em 7 você separou "o que a ação é" de "como ela é acionada". Em 10, "a regra" de "como ela é exposta ao modelo". Aqui, "o que o objeto faz" de "quem decide qual objeto é". É sempre a mesma jogada: separar a decisão do uso, e concentrar as decisões num ponto único. Quando você começar a ver esse padrão sozinho, é sinal de que virou.







Your modified files:
application-design-plan.md
C:\Users\pedro\OneDrive\Área de Trabalho\dev\FishingRod\aidlc-docs\inception\plans
+1
-1
Pergunta 12 — Fronteira entre os dois substratos

RNF-12 diz que o banco não guarda conteúdo nem índice da wiki, "no máximo a referência da raiz".
RNF-11 proíbe caminho absoluto persistido. As duas juntas deixam uma pergunta: o banco guarda
alguma coisa sobre a wiki?


A) O banco guarda a raiz da wiki do ambiente como caminho relativo a um diretório de dados
conhecido da aplicação

B) (recomendo) O banco não guarda nada sobre a wiki. A raiz é derivada por convenção da
identidade do ambiente (ex.: <dados>/ambientes/<id>/wiki/). Zero chance de divergência, e mover
o diretório de dados inteiro continua funcionando


C) O banco guarda um espelho de metadados da wiki (páginas existentes) para busca rápida

D) Other (please describe after [Answer]: tag below)
me ajude com essa proxima pergunta.


eu tenho duvidas. oq sao os dois substratos ? . como isso seria implementado ? uma questao que pensei sobre a implementacao é que se a wiki for um tipo de serviço estilo drive em um servidor onde é compartilhado ( estou falando isso pois penso que a wiki deve ser compartilhada dentro do ambiente entre dos os usuarios que estiverem assim tem valor real ) , essa forma que a opcao B descreve seria boa ? como isso influencia ? me ajude a entender melhor essa pergutna para tomarmarmos uma decisao correta com a visao do software e direcionar corretamente.



Boa pergunta, e a parte sobre wiki compartilhada é o ponto mais importante aqui — vou chegar nela, mas primeiro preciso construir o vocabulário.

1. O que são os "dois substratos"
Substrato = meio físico onde o dado repousa. Você tem dois, e isso foi decisão sua, não acidente:

substrato 1	substrato 2
o quê	SQLite	arquivos markdown no filesystem
guarda	frentes, tarefas, chats, memória, transcrição	a wiki
fonte da verdade	a linha no banco	o arquivo (ESC-17)
quem lê	só o software	humano, Obsidian, git, e o software
transação	sim	não
escopo	máquina do usuário (D-ARQ-09)	potencialmente compartilhado (FOR-13)
Por que dois e não um? Porque ESC-17 decidiu que o arquivo é a fonte da verdade da wiki. Isso não é detalhe técnico — é promessa de produto: a wiki é sua, você abre no Obsidian, versiona no git, lê sem o FishingRod aberto. Se a wiki morasse no SQLite, ela viraria refém do software. RNF-12 é a consequência lógica dessa promessa.

E o preço de ter dois substratos é sempre o mesmo problema: divergência. Quando o mesmo fato está em dois lugares que não compartilham transação, eles vão discordar. Não é "se", é "quando" — o processo morre entre a escrita no disco e o commit no banco, e pronto.

A Pergunta 12 é exatamente: quanto do fato "wiki" o banco tem permissão de saber? Quanto menor, menos superfície de divergência.

2. Como as três opções ficam no disco
A — banco guarda o caminho relativo:



tabela ambiente
  id           = "01924f..."
  nome         = "Marketing"
  caminho_wiki = "ambientes/marketing-wiki"    <- dado persistido


<dados>/
  dados.db
  ambientes/marketing-wiki/
      index.md
      clientes/
B — banco não guarda nada; a raiz é calculada:



tabela ambiente
  id     = "01924f..."
  nome   = "Marketing"
                                    (sem coluna de wiki)


python
def raiz_da_wiki(raiz_configurada: Path, id_ambiente: str) -> Path:
    return raiz_configurada / id_ambiente / "wiki"


<raiz_configurada>/
  01924f.../wiki/
      index.md
      clientes/
A diferença essencial: em A, a localização é dado persistido — pode estar errada, pode apontar para pasta que não existe, pode ser editada, precisa de migração. Em B, é função pura da identidade — não pode divergir porque não existe uma segunda cópia da informação para divergir.

C — espelho de metadados no banco: o banco guarda a lista de páginas para busca rápida. Isso viola RNF-12 na letra e é o cenário de divergência garantido — qualquer edição feita fora do software (Obsidian, git pull) deixa o espelho velho. Com wiki compartilhada, então, o espelho está errado desde o segundo usuário. Descarto.

3. Agora o ponto que você levantou: wiki compartilhada
Aqui você achou um furo real na formulação de B, e vale examinar com cuidado.

O texto de B diz <dados>/ambientes/<id>/wiki/. Isso amarra a wiki ao mesmo diretório de dados do banco. Mas os dois têm escopos opostos:

banco = privado por usuário, na máquina dele (D-ARQ-09)
wiki = potencialmente compartilhada (FOR-13, e RNF-13 já proíbe assumir escritor único)
Se a raiz da wiki é derivada de <dados>, e <dados> é onde mora o banco pessoal, então apontar a wiki para um drive compartilhado exigiria mover o banco junto. B como está escrita bloqueia FOR-13.

A correção é pequena e não muda a natureza de B: são duas raízes de configuração, não uma.



<raiz_dados>   -> ~/.fishingrod/            (privado, mora o banco)
<raiz_wikis>   -> Z:\equipe\fishingrod\     (pode ser drive compartilhado)
 
banco:  <raiz_dados>/dados.db
wiki:   <raiz_wikis>/<id_ambiente>/
Nada sobre a wiki entra no banco. RNF-12 intacto. E agora dá para apontar a wiki para um drive de rede sem tocar no banco.

E aqui vem o argumento que me convenceu de que B é melhor para o futuro compartilhado, não pior:

Sob A, o caminho da wiki é um dado dentro do banco de cada usuário. João tem "wikis/marketing", Maria tem "trabalho/mkt-wiki". Nada no sistema sabe que os dois se referem à mesma wiki. Não existe fato compartilhado — existem duas strings independentes que por acaso apontam para o mesmo lugar, mantidas em sincronia por disciplina humana.

Sob B, a localização é f(identidade do ambiente). A identidade do ambiente é o único conceito que precisa ser compartilhado — e ela é opaca e estável (RF-F16, Pergunta 4). Se João e Maria têm o mesmo id_ambiente e apontam a raiz_wikis para o mesmo drive, eles caem na mesma pasta por construção. Compartilhar vira "concordar sobre a identidade" em vez de "concordar sobre um caminho" — e concordar sobre identidade é infinitamente mais robusto, porque o caminho é local a cada máquina e a identidade não.

Ou seja: B move a informação compartilhada para o lugar certo.

4. E se a wiki virar um serviço (drive/servidor), não um filesystem?
Essa é a sua pergunta mais estratégica, e a resposta é que nem A nem B respondem isso — e não deveriam.

Se a wiki vira HTTP, "raiz" deixa de ser um caminho: vira endpoint + credencial + protocolo. O que protege você nesse cenário não é a escolha desta pergunta, é a existência de uma porta de wiki com a wiki-no-filesystem como um adaptador. Trocar para servidor = escrever outro adaptador.

E é aí que a coisa fecha bonito com o que você acabou de responder na Pergunta 11:

A localização da wiki não é dado de domínio. É configuração de implantação — e configuração de implantação nasce no composition root.



python
def montar(raiz_dados: Path, raiz_wikis: Path) -> ServicoAmbiente:
    repositorio = RepositorioSQLite(raiz_dados / "dados.db")
    wiki        = WikiFilesystem(raiz_wikis)      # ou WikiHttp(url, token) amanhã
    return ServicoAmbiente(repositorio, wiki, ...)
O domínio nunca soube onde a wiki está. O banco nunca soube. Só o main sabe, e é ele quem lê <raiz_wikis> de um arquivo de config ou variável de ambiente — não do banco. Trocar filesystem por serviço mexe em uma linha do montar().

Isso também esclarece uma coisa: A não é "mais flexível" que B. A flexibilidade que você quer (apontar a wiki para onde quiser) vem de config de implantação, e essa flexibilidade B tem igual. O que A adiciona é apenas persistir essa escolha no banco — e persistir é exatamente o que cria divergência e migração.

5. Duas coisas que essa decisão não resolve
Vale registrar, para você não achar que compartilhamento está resolvido:

Compartilhar a wiki implica, cedo ou tarde, compartilhar o estado do ambiente. Se João cria a frente "Campanha X" e a wiki tem campanhas/x.md, Maria vê o arquivo mas não vê a frente. Isso é multiusuário (B2), fora de escopo — mas é bom saber que a wiki compartilhada sozinha entrega meia experiência. B não bloqueia esse futuro; só não o entrega.
Escrita concorrente na wiki. RNF-13 já cobre: não implementar, mas não tornar impossível. Com B mais escrita por proposta aprovada (Q9A), a escrita é pontual e rara — o cenário menos hostil possível para um drive compartilhado.
6. Minha recomendação
B, com a raiz da wiki como configuração de implantação separada da raiz de dados — resolvida no composition root, nunca persistida.

Justificativa em uma frase: o banco não guarda nada sobre a wiki; a localização é função da identidade do ambiente mais uma raiz configurável, o que elimina divergência por construção, satisfaz RNF-11 e RNF-12 sem exceção, e torna a wiki compartilhada uma questão de acordo sobre identidade — não sobre caminho.

Quer que eu escreva essa resposta no arquivo, incluindo a correção das duas raízes e a nota sobre os limites que ela não resolve?







Já vão falando algumas coisas aqui pra eu esquecer, depois eu organizo melhor a ideia. Mas eu entendi a questão aqui do agora dos dois substratos, que tem um que é mais JSQLite, que teria uma base de dados que armazena umas coisas e tem o substrato 2 que é da própria Wiki, que é um sistema de arquivos. Uma questão que eu quero deixar claro aqui, que, assim, é um sistema, provavelmente ele vai ser um aplicativo desktop que eu penso, mas ele vai ter que ser na nuvem, ou seja, vai ter que ter um servidor onde eu salvei aquele ambiente. Então aqui recense SQLite, tudo o que eu estou salvando ali e criando, que é SQLite ali, é os extratos, é os subcasos do ambiente criado, né? Frentes, tarefas, chats, tudo isso está dentro do ambiente criado. Esse ambiente criado, ele está salvo no servidor. Porque pensa comigo, ele é um, ele vai ser um aplicativo desktop onde eu abro ele aqui, eu logo na minha conta, eu me conecto a esse ambiente que está na nuvem.Esse ambiente que foi compartilhado comigo e eu trabalho dentro daquele ambiente. Então todas as frentes estão salvas ali. É claro que a gente está fazendo a primeira versão aqui, a nossa primeira interação, como vai ser uso próprio, né? O single user ser SQLite salvando uma própria máquina, não tem problema, a gente já consegue testar. Mas só pra deixar claro que esse substrato tem que ser possível evoluir para esse nível, tanto como o substrato 2 também tem que evoluir para essa questão de ser um drive online para ser compartilhado nesse ambiente, viu?A questão de acesso ao Wiki, eu penso que é uma questão que eu só preciso me referenciar a raiz. Porque se eu sei onde está a raiz, eu consigo acessar todos os dados que estão lá dentro. A raiz é o lugar que não varia. Onde foi criada a Wiki. Criou-se uma Wiki, tem um lugar que ela existe. Nesse drive ou localmente. E dentro da Wiki, os conteúdos lá dentro, é muito variável. O usuário pode mexer como quiser. Então, não podemos apontar para lá. É meio ruim, porque a gente não sabe, não tem controle. Pode mudar de vários jeitos. Então, apontar só para a raiz já é o suficiente. Quando for deletado aquela raiz, deleta aquele caminho, não existe mais aquela Wiki. Mas isso já é outro processo. Isso já emenda com essa questão da ideia.A ideia é que de amarrar o mesmo diretório. Acho que a gente pode fazer uma questão assim, a gente pode fazer duas inicializações, sabe? O usuário quer inicializar local, ele é salvo numa pasta padrão criada ali. e é salvo esse caminho dessa pasta padrão localmente. Se for via nuvem, servidor, aí ele se conecta a uma base, entendeu? No caso, se ele quiser conectar a esse ambiente. Então, quando ele cria um ambiente, esse ambiente ele ou ele está conectado com o servidor ou não. Se ele for offline, vamos dizer assim, esse ambiente offline, ele vai ter uma Wik local, vai ter lá algum caminho global que vai ser criado padrão e a gente aponta para as raízes das Wiks que foram criadas nesse caminho padrão. A mesma ideia da SQLite dá pra usar assim. Ah, se eu for fazer local, single user, a gente está fazendo.Hoje a gente já está fazendo ele usar localmente o SQL, se for no futuro ele vai poder criar uma conta e criar um ambiente que seja online, que seja na nuvem, aí vai ser criado um LASP, hoje não vai ser salvo no computador, acho que a ideia é por aí, essa ideia de como resolver as questões.



Capturei. Vou devolver organizado, marcando o que fecha e o que ainda tem ponta solta.

O que você descreveu, em uma frase arquitetural
Modo de implantação (local × nuvem) é uma propriedade do ambiente, não da instalação — e ela não pode vazar para o domínio.

Isso é importante porque muda uma coisa: se fosse propriedade da instalação, seria config global e o main resolveria. Mas você disse que o usuário pode ter um ambiente local e estar conectado a um ambiente compartilhado. Então a escolha é por ambiente, e alguém precisa guardar essa informação.

A ponta solta que isso cria
Você tem três coisas, não duas:



1. Catálogo local de ambientes   <- NOVO. Sempre local, sempre SQLite pequeno.
     "que ambientes eu conheço e como chego neles"
     id | nome | modo | endpoint-ou-caminho
 
2. Dados do ambiente             <- SQLite local  OU  servidor
     frentes, tarefas, chats, transcrição
 
3. Wiki do ambiente              <- pasta local   OU  drive/serviço
     markdown
O catálogo (1) é o que resolve sua ideia das "duas inicializações". Ele é o que o app lê ao abrir, antes de saber qualquer coisa. E é ele quem guarda a raiz da wiki e o endpoint do servidor — não o banco do ambiente.

Isso preserva a Pergunta 12 intacta: o banco do ambiente continua sem saber nada sobre a wiki. RNF-12 vale. O que sabe é uma camada acima, que existe fora do ambiente.

E resolve o problema que eu tinha levantado (amarrar wiki e banco no mesmo diretório) de um jeito melhor que "duas raízes configuráveis": cada ambiente carrega a própria localização no catálogo. Ambiente A local, ambiente B na nuvem, ao mesmo tempo.

Sobre a raiz — você está certo e vale nomear por quê
Sua formulação: "a raiz é o lugar que não varia; o conteúdo dentro é muito variável, então não podemos apontar para lá".

Isso é exatamente a razão técnica de RNF-11, e você chegou nela sozinho. O nome disso é estabilidade referencial: você só persiste referência a coisas cujo ciclo de vida você controla. A raiz nasce e morre com o ambiente — você controla. Um arquivo dentro dela pode ser renomeado no Obsidian às 3h da manhã — você não controla. Persistir referência a algo instável é criar dado que apodrece sozinho.

E o corolário que você já enunciou: apagar a raiz = a wiki deixou de existir. Uma operação, um efeito. Sem lixo espalhado no banco.

O que muda na nuvem, e o que não muda
O que não muda: nada no domínio, nada na aplicação. Isso é a prova de que as portas estão no lugar certo.



              hoje                        futuro nuvem
Repositório   SQLite local        →       cliente HTTP do servidor
Wiki          pasta local         →       cliente do drive/serviço
              ↑ mesma porta, mesmo domínio, adaptador trocado no main
O que muda de verdade, e é o que eu quero que você registre agora enquanto lembra:

Nuvem compartilhada quebra a suposição de escritor único no estado do ambiente. Você já cobriu isso para a wiki (RNF-13). Para frentes/tarefas/chats, não. Se João e Maria estão no mesmo ambiente e ambos renomeiam uma tarefa, alguém perde.

Isso reforça, retroativamente, a decisão da Pergunta 3 (transcrição em tabela separada, append-only). Mensagens de dois usuários em chats diferentes são inserts independentes — o padrão sobrevive à nuvem sem redesenho. Se você tivesse escolhido documento único, o modo nuvem exigiria refazer a persistência inteira.

Não precisa implementar nada disso agora. Precisa só de uma linha nos requisitos: "o desenho não pode assumir escritor único no estado do ambiente" — o gêmeo de RNF-13. É barato agora e caríssimo depois.

Um alerta
Cuidado para "tem que evoluir para nuvem" não virar justificativa para construir abstração de nuvem agora. A defesa correta contra esse futuro é o que você já decidiu: porta de persistência em vocabulário de domínio (D-ARQ-04), porta de wiki, composition root (Q11). Com isso, você não precisa prever o servidor — você troca o adaptador quando ele existir.

O único custo que vale pagar hoje, e é pequeno: garantir que o catálogo de ambientes exista como conceito (mesmo que com uma linha só, modo=local), para que o modo nuvem seja uma opção nova e não uma reforma.

Quer que eu registre isso — o catálogo de ambientes e o requisito de não-assumir-escritor-único — como nota no plano, ou prefiro deixar você organizar primeiro e a gente formaliza depois?







Vamos focar aqui em responder a pergunta 12. Eu quero que você escreva nesse chat a pergunta, a resposta, aí eu vou colocar eu manualmente no plano, vou responder a pergunta manualmente. Vamos lá. Vamos colocar nessa pergunta as coisas importantes, explicar essas ideias, nessa questão que a gente... Vamos focar na pergunta, na questão da pergunta que o caminho da Wiki, que é a questão que a pergunta se foca, mas vamos abrangê-la e explicar essa questão importante sobre onde isso está conectado, que é a questão que a gente estava explicando sobre esse local em nuvem. Então, o caminho que ele deu ali de identidade de mente está um pouco errado. Vamos corrigir isso e explicar e conectar essa ideia.Quando eu estava com essa ideia que a gente estava explicando sobre o local, então quando eu crio um ambiente, eu posso criar ele localmente e aí vai se usar um SQLite, que é o que a gente quer fazer hoje nessa interação, nessa primeira interação, porque é para uso local mesmo, um usuário. Então ele vai usar localmente, vai ser um repositório local, SQLite, e a UI que vai ser parça local. Então vai ter um caminho absoluto que o padrão, que o próprio software cria. Ou eu posso criar um ambiente na nuvem, isso para o futuro, aí vai ser diferente. Então o caminho, e também explicar a questão do caminho, focar ali na questão do caminho, a gente percebeu que a ponta para a raiz é melhor, explicar aqui essa questão de estabilidade referencial, que é a raiz da UI que vai ter essa estabilidade. Sobre a questão que a gente, que a melhor forma que seria, acho que a gente chegou, que é...E o que está armazenado no SQ-Lite, que seria meio que as informações do ambiente ali, as frames, tarefas, chats, memórias, transcrição, não só se referenciaria ao WIKI, aonde o WIKI existe, a raiz dela, é isso que precisa. E dentro da raiz é muito, varia muito. Vamos focar em responder essa pergunta aqui, agora.



Aqui está, no formato do arquivo, pronto para você colar e ajustar.

Pergunta 12 — Fronteira entre os dois substratos
RNF-12 diz que o banco não guarda conteúdo nem índice da wiki, "no máximo a referência da raiz". RNF-11 proíbe caminho absoluto persistido. As duas juntas deixam uma pergunta: o banco guarda alguma coisa sobre a wiki?

A) O banco guarda a raiz da wiki do ambiente como caminho relativo a um diretório de dados conhecido da aplicação

B) (recomendo) O banco não guarda nada sobre a wiki. A raiz é derivada por convenção da identidade do ambiente (ex.: <dados>/ambientes/<id>/wiki/). Zero chance de divergência, e mover o diretório de dados inteiro continua funcionando

C) O banco guarda um espelho de metadados da wiki (páginas existentes) para busca rápida

D) Other (please describe after [Answer]: tag below)

[Answer]: D — variante de (A): o banco guarda uma referência à raiz da wiki, e só isso. Nunca caminho absoluto, nunca nada sobre o conteúdo.

Correção da recomendação (B) do AI. A opção B derivava a raiz por convenção a partir da identidade do ambiente. Isso assume que o software é o dono da localização da wiki — verdade no modo local, falsa em qualquer outro. Se a wiki mora num drive compartilhado ou, no futuro, num serviço, a localização é escolhida por quem configurou o compartilhamento, não calculada pelo software. Uma convenção fixa não tem como representar isso: no modo nuvem a "raiz" nem é uma pasta. Convenção é boa para gerar o valor inicial da raiz no modo local; é errada como única forma de saber onde a wiki está.

O que fica em cada substrato. Substrato 1 (SQLite) guarda o ambiente: frentes, tarefas, chats, memória, transcrição — mais uma referência à raiz da wiki daquele ambiente. Substrato 2 (a wiki) guarda o conteúdo, e o arquivo continua sendo a fonte da verdade (ESC-17). O banco não guarda página, não guarda índice, não guarda espelho de estrutura. RNF-12 é cumprido na letra: "no máximo, a referência da raiz" — e é exatamente a raiz, nada além dela.

Por que apontar só para a raiz — estabilidade referencial. Só se persiste referência a coisas cujo ciclo de vida o software controla. A raiz nasce quando o ambiente é criado e morre quando o ambiente é apagado: ciclo de vida controlado, referência estável. O conteúdo dentro da raiz é o oposto — o usuário renomeia pasta no Obsidian, move arquivo, faz git pull, e o software não é avisado. Persistir referência a qualquer coisa dentro da raiz é criar dado que apodrece sozinho. Saber a raiz é suficiente: a partir dela o bibliotecário navega e descobre o resto em tempo de leitura, sempre atualizado por construção. Corolário operacional: apagar a raiz é apagar a wiki — uma operação, um efeito, sem resíduo espalhado no banco.

Por que isso não viola RNF-11. A referência persistida não é caminho absoluto de disco. Ela é relativa a uma raiz de dados que o processo resolve em tempo de execução, no ponto de composição (Pergunta 11). O banco guarda wikis/<id_ambiente>; quem transforma isso em caminho real é o adaptador, com a raiz de dados que recebeu do main. Consequência prática: mover ou sincronizar o diretório de dados inteiro continua funcionando, e nenhum caminho de máquina entra em arquivo ou banco.

Como isso se conecta ao modo do ambiente (local × nuvem). Um ambiente nasce em um de dois modos, e o modo determina a forma da referência de raiz, não a existência dela:

ambiente local (esta iteração)	ambiente na nuvem (futuro)
estado do ambiente	SQLite na máquina do usuário	serviço remoto
wiki	pasta em raiz de dados criada pelo software	drive/serviço compartilhado
referência de raiz	localizador relativo à raiz de dados	localizador do serviço
escopo	um usuário, uma máquina (D-ARQ-09)	compartilhado no ambiente (FOR-13)
No modo local, o software gera a raiz por convenção (wikis/<id_ambiente>) no momento da criação e a registra. Convenção como semente, referência como verdade — a mesma lógica de ESC-19 para o esquema da wiki. Assim o caso comum não pede configuração nenhuma do usuário, e o caso compartilhado passa a ser representável sem redesenho.

Por que (C) está descartada. Viola RNF-12 diretamente e é divergência garantida: qualquer edição feita fora do software (Obsidian, git pull) deixa o espelho velho, e com wiki compartilhada (FOR-13, RNF-13 — sem escritor único) ele estaria errado a partir do segundo usuário. Se busca rápida virar necessidade, ela se resolve dentro do substrato 2 (índice derivado, descartável, reconstruível a partir dos arquivos), nunca no banco.

O que esta decisão preserva para o futuro, sem custo hoje. O domínio e a aplicação nunca sabem onde a wiki está nem qual é o modo do ambiente: os dois chegam por porta e adaptador, montados no ponto de composição. Trocar pasta local por serviço remoto é escrever outro adaptador de wiki e outro adaptador de repositório — não é redesenhar o núcleo.

Ponta solta registrada, fora do escopo desta iteração. O modo nuvem quebra a suposição de escritor único no estado do ambiente — hoje RNF-13 cobre apenas a wiki. Nada a implementar agora; apenas nada a tornar impossível. A decisão da Pergunta 3 (transcrição em tabela separada, append-only) já sobrevive a esse futuro sem redesenho, o que é evidência a favor dela.

Duas observações sobre o que eu fiz aí, para você decidir se concorda:

Chamei de D e não de A, porque a formulação de A fala de "caminho relativo a um diretório de dados conhecido da aplicação" — o que é verdade no modo local mas não descreve o modo nuvem. D deixa registrado que a referência é um localizador cuja forma depende do modo, e isso é mais fiel ao que você descreveu.
Deixei de fora o "catálogo local de ambientes" que discutimos. Ele é uma peça real, mas é identificação de componente (Categoria A), não fronteira de substrato — e a Pergunta 12 se sustenta sem ele. Se quiser, ele entra junto com a Pergunta 3-bis dos agentes, que também ficou pendente.






Your modified files:
application-design-plan.md
C:\Users\pedro\OneDrive\Área de Trabalho\dev\FishingRod\aidlc-docs\inception\plans
+24
-1
Pergunta 13 — Critério do bibliotecário entre entidade (pasta) e propriedade (arquivo)

O risco número um do desenho da wiki. Você escolheu "propriedade pode ser instância", o que é
fiel ao uso real (clientes/dr-marcelo.md e clientes/criterios-de-icp.md convivem) mas deixa o
bibliotecário sem regra: sem critério, ele decide diferente a cada vez e a wiki apodrece.
Profundidade está travada em dois níveis, então "criar entidade" é sempre uma decisão de topo.

A) (recomendo) Entidade nova é decisão humana. O bibliotecário só cria arquivo dentro de
entidade existente; quando o conteúdo não couber em nenhuma, ele propõe a entidade nova e
espera aprovação. O esquema-semente já dá as entidades iniciais, então o caso comum não pede
aprovação nenhuma

B) Regra explícita para o agente decidir sozinho: cria entidade quando o conteúdo é substantivo
que terá múltiplas páginas; caso contrário, arquivo dentro da entidade mais próxima


C) O esquema é fechado: entidades são só as do esquema, e criar entidade nova exige editar o
esquema fora da conversa


D) Other (please describe after [Answer]: tag below)

Já responde essa próxima pergunta 13. Acho que essa pergunta 13 a gente já respondeu aqui nesse chat, a gente já falou um pouco sobre sobre. Eu acho que o que responde essa pergunta é aquela questão que quem vai desenhar o wiki, né, que tem a abstração que eu desenhei. que a wiki ela pode ser.Ela pode ser entidades, que seriam os substantivos, e as propriedades, que seriam as características que definem o restringe um substantivo, no caso, essa entidade. Então ela só teria dois camadas, Foi a ideia que eu expliquei. Então tem uma regra que o jeito que ela funciona. Então, no caso aqui, eu acho que seria muito naquela ideia que a gente já falou que o JDBC teria uma funcionalidade, e ele teria uma funcionalidade lá que seria uma requisição, ele faria. A gente que deu o nome para isso deMas o que que propõe, né? Fazer uma proposta. Então seria uma regra de bibliotecário, então tipo, a biblioteca ele propõe escrever uma entidade, aí o usuário vê se aceita. Ah, o bibliotecário propõe escrever uma propriedade dentro de uma entidade. O usuário aceita sempre essa questão. Então, acho que aqui é só uma função de criar uma propriedade ou criar uma entidade, né, que seria escrever lá na Wiki. e ele passa por esse filtro, vamos dizer, do do bibliotecário, que é a regra dele de funcionamento, que é propor, né, Ele propõe a mudança e o usuário aceita ou não.Eu ajudei a escrever aqui a resposta a essa pergunta agora. Vamos fazer... não precisa ser tão complexo. Vamos explicar, então, de forma concícia que tenha as informações relevantes.



Aqui está, conciso.

[Answer]: A — com uma precisão que simplifica a regra: não há dois regimes. Toda escrita na wiki é proposta, então "criar entidade" e "criar propriedade" passam pelo mesmo mecanismo.

O critério semântico vem da abstração da wiki, não de uma regra extra. Entidade é substantivo — a coisa sobre a qual se sabe algo. Propriedade é característica que define ou restringe aquela entidade — e pode ser faceta (clientes/criterios-de-icp.md) ou instância (clientes/dr-marcelo.md). Dois níveis, travados. O bibliotecário não precisa de heurística inventada: ele pergunta "isto é um substantivo novo, ou é algo que caracteriza um substantivo que já existe?". Se o conteúdo caracteriza uma entidade existente, é propriedade. Se introduz um substantivo que não existe, é entidade.

A regra de funcionamento do bibliotecário é propor. Ele tem duas operações de escrita — propor_entidade e propor_propriedade — e nenhuma delas escreve. Ambas produzem uma proposta que o usuário aceita ou recusa (Pergunta 9A). Isso elimina a pergunta "quando ele pode decidir sozinho?": nunca. Não existe caminho de escrita sem aprovação, então não existe caso de borda onde o julgamento dele vira fato sem revisão.

Por que isso não vira atrito no uso comum. O esquema-semente (ESC-19) já entrega as entidades iniciais do domínio, então a esmagadora maioria das escritas é propriedade dentro de entidade que já existe. Propor entidade nova é evento raro — e quando acontece, é exatamente o momento em que uma decisão estrutural sobre a wiki está sendo tomada, que é o momento em que revisão humana tem mais valor.

Por que não (B). B pede ao modelo que decida sozinho por heurística ("substantivo que terá múltiplas páginas"). Heurística em prompt é sugestão estatística: ele decide diferente em dias diferentes, e o erro estrutural só aparece semanas depois, quando a wiki já tem entidade duplicada e conteúdo espalhado. O custo do erro é assimétrico — errar propriedade se corrige apagando um arquivo; errar entidade contamina a organização inteira.

Por que não (C). Esquema fechado tira o crescimento orgânico da wiki e obriga o usuário a sair da conversa para editar configuração. Contraria ESC-19, que trata o esquema como semente e não como cerca.

Onde cada parte mora. O critério semântico é prompt do bibliotecário (é julgamento — ver Pergunta 10). A profundidade de dois níveis e o confinamento de caminho são código na tool (é garantia). O agente pode errar o julgamento; não pode violar a estrutura.

O que eu mudei em relação ao enunciado de A: A dizia "o bibliotecário só cria arquivo dentro de entidade existente; quando não couber, propõe entidade". Isso descreve dois comportamentos diferentes — cria num caso, propõe no outro. Como você já decidiu na Pergunta 9 que ele nunca escreve, o comportamento é um só: propõe sempre. Isso é mais simples de implementar e de explicar, e remove o caso de borda.







Your modified files:
application-design-plan.md
C:\Users\pedro\OneDrive\Área de Trabalho\dev\FishingRod\aidlc-docs\inception\plans
+13
-1
Pergunta 14 — Qual grafo manda na recuperação

Hierarquia de pastas e links [[...]] são dois grafos e podem discordar.


A) A hierarquia de pastas manda; links são conveniência de leitura


B) (recomendo) A hierarquia manda para localizar (é ela que o filesystem garante) e os
links são arestas de navegação validadas na escrita — link para página inexistente faz a
escrita ser recusada ou vira proposta de criar a página. Nenhum dos dois "vence" porque eles não
respondem a mesma pergunta

C) Os links mandam; a pasta é só armazenamento


D) Other (please describe after [Answer]: tag below)


[Answer]:


nessa próxima pergunta, como que eu penso aqui a questão, a questão é a seguinte é duas hierarquias só que tem nesse seu wik, entidades, dentro das entidades tem propriedades e a raiz tem o arquivo index.wik, esse arquivo index é o wik principal quando for ler uma, toda vez que, vai ser uma regra de uso da wik, de como que se usa uma wik toda vez que vai ler, fazer uma busca no wik, primeiro passa nessa wik, nesse arquivo index.md vai passar nesse arquivo index.md, nesse arquivo index.md Tem o que que são as entidades e o que que tem dentro de cada das identidades com o link delas, falando referenciando o nome dessas propriedades e tendo uma pequena descrição do que que tem lá de informação. Por que isso? Essa descrição é a informação necessária que a IDN precisa para saber aonde buscar essa informação. Aí, dentro dessas propriedades, vão existir os outros links. Por quê? Porque dentro dessas propriedades, eles é um gráfico, eles podem se conectar com outras propriedades da forma que for, independente. Então tem uma estrutura a seguir, que vai ser seguida, uma forma de como escrever essas páginas, que já existe, eu vou reaproveitar um uso. Normalmente eu falar disso, mas no momento adequado eu explico como que vai ser essa forma que a gente vai usar. E assim tem o grafo montado.



Aqui está.

[Answer]: B — com a precisão de que a recuperação tem um passo obrigatório antes dos dois grafos: o index.md.

Os dois grafos não competem porque respondem perguntas diferentes. A hierarquia responde onde a informação mora — é estrutura, garantida pelo filesystem, e é o que torna a wiki legível fora do software. Os links respondem com o que esta informação se relaciona — é semântica, criada pelo conteúdo, e é o que permite associação livre entre propriedades de entidades diferentes. Nenhum dos dois "vence" porque nenhum substitui o outro.

A regra de uso da wiki: toda leitura começa no index.md. Ele é a porta de entrada obrigatória (ESC-17). O index.md lista as entidades e, dentro de cada uma, as propriedades — cada uma com seu link e uma descrição curta do que há ali. Essa descrição é o ponto central: é ela que permite ao agente decidir onde buscar sem precisar ler a wiki inteira. Sem descrição, o índice seria só uma lista de nomes de arquivo, e o agente teria que abrir tudo para descobrir o que importa — caro em contexto e pouco confiável.

A partir daí, o grafo de links assume. Dentro das propriedades existem os links [[...]], que conectam propriedades entre si livremente, inclusive atravessando entidades. Recuperação típica: index.md → localiza a propriedade candidata pela descrição → lê → segue os links relevantes. Primeiro salto por estrutura, saltos seguintes por associação.

Links validados na escrita. Link para página inexistente não passa: ou a escrita é recusada, ou a criação da página vira parte da proposta. Como toda escrita já é proposta (Pergunta 13), isso não adiciona mecanismo novo — o link pendente entra na mesma proposta que o usuário aprova. O efeito é que o grafo nunca tem aresta quebrada, por construção.

Existe uma forma que de como fazer a estrutura das paginas que eu ja utilizei de uma estrutura que ja existe que é a skill publica chamada WIKI LLM , onde tem uma maneira ja ensinando um agente a como se criar as paginas, a minha idea é reaproveitar ideias dessa estrutura e aplica-la aqui quando for criado arquivos dentro da wiki.

#### Pergunta 15 — Como o `index.md` se mantém atualizado

Ele é a porta de entrada de leitura do agente. Se mentir, o agente busca no lugar errado.

A) **(recomendo)** Derivado: regerado a partir da varredura do diretório depois de cada escrita
aprovada. Não pode divergir, porque não é fonte de nada — é projeção

B) Mantido pelo bibliotecário, que edita o `index.md` junto com a página

C) Híbrido: seção de estrutura derivada + seção de notas escrita pelo agente

D) Other (please describe after [Answer]: tag below)

[Answer]: D — variante de (B) na responsabilidade e de (A) no mecanismo: o bibliotecário é dono da descrição; o index.md é projeção renderizada por código. O agente nunca edita o index.md.

Por que (A) pura não serve. O index.md precisa de descrições, e descrição é julgamento — só quem entendeu o conteúdo sabe dizer o que há na página. Estrutura de pastas não produz isso.

Por que (B) pura é arriscada. Se o bibliotecário editar o index.md como texto livre, aparecem os cenários que queremos evitar: ele esquece de atualizar, reescreve o bloco errado, apaga entrada de outra entidade, ou muda o formato e o próximo agente não consegue mais ler. Isso é responsabilidade sustentada por disciplina de prompt — frágil por natureza.

A solução: transformar responsabilidade em estrutura. Duas decisões:

1. A descrição é campo obrigatório da tool de escrita.



propor_propriedade(entidade, propriedade, conteudo, descricao, links)
Não existe caminho de escrita sem descrição. O esquecimento deixa de ser possível — não por instrução ao modelo, mas porque a chamada é inválida sem o campo.

2. A descrição mora na própria página, em frontmatter de estrutura fixa.



markdown
---
descricao: Critérios de qualificação de lead usados na triagem inicial
---
# Critérios de ICP
Toda propriedade criada na wiki segue essa estrutura fixa — é garantia de código na tool, não convenção. O frontmatter é extensível: campos obrigatórios podem ser acrescentados depois (datas, procedência, tags, estado de revisão) para tornar a recuperação mais robusta, sem mudar o mecanismo do índice.

Com isso o index.md volta a ser projeção pura, renderizada por código a partir de (estrutura de pastas) + (frontmatter de cada página):



markdown
# Índice
 
## clientes
- [[clientes/criterios-de-icp]] — Critérios de qualificação de lead usados na triagem inicial
- [[clientes/dr-marcelo]] — Histórico e preferências do cliente Dr. Marcelo
 
## campanhas
- [[campanhas/lancamento-q3]] — Peças, verba e resultados da campanha de lançamento do Q3
Entidade não tem descrição. O nome da entidade (a pasta) é o título do bloco, e isso basta: o nome já diz o suficiente sobre o que há dentro, e a navegação real acontece pelas descrições das propriedades. Isso simplifica o desenho — não é preciso arquivo de metadados de entidade, nem propor_entidade carregando descrição, nem lugar convencional para guardá-la.

Consequências práticas:

Não pode divergir. O índice não é fonte de nada. Se sumir, regenera; se ficar estranho, regenera. Não existe o estado "índice desatualizado precisando de conserto".
Um só caminho de código. Não há cenários de atualização por tipo de mudança. Existe renderizar_index(raiz), executada após qualquer proposta aprovada. Um teste cobre tudo.
Formato garantido. Gerado por código, o formato nunca deriva; o agente que lê amanhã encontra exatamente o que espera.
Sem dano colateral. O agente não pode apagar nem corromper entradas de outras entidades, porque não escreve no índice.
Edição externa se resolve sozinha. Pasta renomeada no Obsidian aparece corrigida na próxima renderização. Arquivo criado à mão sem frontmatter aparece no índice sem descrição — visível, e material para o lint.
Divisão de responsabilidade, coerente com as Perguntas 10 e 13: a descrição é julgamento do bibliotecário; a montagem do índice é código. O agente pode escrever uma descrição ruim; não pode quebrar o índice.

O lint — processo separado, sob demanda, para saúde semântica da wiki

Vale registrar aqui porque completa a resposta: existem dois mecanismos de manutenção da wiki, e eles não fazem o trabalho um do outro.

mantém o quê	quando roda	natureza
renderização do índice	o index.md correto em relação aos arquivos	automático, após cada proposta aprovada	código, determinístico
lint	a qualidade semântica do conteúdo	sob demanda — o usuário pede, ou o agente sugere	agente, julgamento
O lint é uma ideia tomada da skill pública WIKI LLM (GitHub), a mesma referência que orienta a estrutura de escrita das páginas (ver Pergunta 14). Nela existe um processo em que o agente percorre a wiki inteira fazendo limpeza, atualização e verificação de coerência. A intenção é reaproveitar esse processo aqui — o detalhamento fica para o momento adequado.

Escopo esperado do lint: páginas sem descricao no frontmatter; descrições que não refletem mais o conteúdo; links quebrados ou faltantes; propriedade que deveria ter virado entidade; conteúdo duplicado entre páginas; páginas órfãs. Tudo isso é julgamento, logo tudo vira proposta e passa pela aprovação do usuário (Pergunta 9A / Pergunta 13) — o lint não tem poder de escrita próprio.

A frase que resume os dois: a escrita mantém o índice correto por construção; o lint mantém a wiki saudável por revisão.

#### Pergunta 16 — Formato do arquivo de esquema de wiki

ESC-19: o esquema é semente e precisa ser plugável sem mexer em código (RF-F15).

A) Markdown com lista aninhada (mesma linguagem do resto da wiki, legível por humano e por LLM)

B) **(recomendo)** TOML (stdlib `tomllib` no 3.13, sem dependência, erro de sintaxe explícito,
mesmo formato do `pyproject.toml` que o projeto já vai ter)

C) YAML (exige dependência)

D) JSON

E) Other (please describe after [Answer]: tag below)

[Answer]: B — TOML. O esquema é dado estruturado (lista de entidades e propriedades); o arquivo .toml é apenas sua serialização.

Esclarecimento do que a pergunta decide. Não é o formato das páginas da wiki — esse já está fixado (markdown com frontmatter e links [[...]], Perguntas 14 e 15). É o formato da maquete que materializa a wiki na criação do ambiente (ESC-19, RF-F15).

O esquema tem duas origens, e ambas convergem no mesmo dado. Na tela de criação de ambiente, o usuário ou escolhe uma maquete pronta ou digita as entidades ali mesmo. Como o formulário produz dados, o esquema é dados — e o arquivo é só a forma de guardá-lo:



maquete pronta (.toml)   ──┐
                           ├──► Esquema (dado) ──► materializa a wiki
formulário preenchido    ──┘                  └──► "salvar como maquete" (.toml)
Isso entrega de graça o reaproveitamento e o compartilhamento que se quer: o usuário monta do zero uma vez, salva como maquete, reusa e distribui.

Por que TOML. tomllib é biblioteca padrão (3.11+), então ler maquetes não custa dependência nenhuma; erro de sintaxe vem explícito com número de linha, o que importa num arquivo editado à mão; aceita comentário; e é o mesmo formato do pyproject.toml que o projeto já terá — um formato de configuração no sistema, não dois. Ressalva conhecida: tomllib só lê. Salvar maquete exige um serializador próprio (~20 linhas para esta estrutura) ou tomli-w; preferimos o serializador próprio, para manter zero dependência.

Por que não os outros. Markdown: exigiria parser de lista aninhada, que aceita variação de sintaxe e produz estrutura errada em silêncio — bom para texto humano, ruim para dado que código consome. YAML: economiza o serializador, mas cobra uma dependência e traz a fragilidade de indentação, exatamente o erro silencioso que se quer evitar. JSON: sem comentário e hostil à edição manual.

Forma do arquivo:



toml
nome = "Marketing"
descricao = "Wiki inicial para trabalho de marketing e campanhas"
 
[[entidade]]
nome = "clientes"
propriedades = [
  { nome = "criterios-de-icp", descricao = "Critérios de qualificação de lead" },
]
 
[[entidade]]
nome = "campanhas"
propriedades = []
As descricao viram frontmatter das páginas criadas (Pergunta 15), então a wiki já nasce com índice útil.

Invariante de criação. Ambiente não pode ser criado sem wiki materializada (ESC-19): exige-se ao menos uma entidade. Propriedade não é exigida — obrigar o usuário a inventar uma propriedade antes de ter conteúdo é pedir que ele adivinhe; entidade vazia é lugar legítimo para o bibliotecário propor a primeira página. A regra vale para os dois caminhos de criação, logo mora no domínio; a TUI apenas exibe a mensagem.

Onde as maquetes ficam. Embutidas (distribuídas com o software, somente leitura) e do usuário (diretório de dados, criadas por "salvar como maquete"). A tela de criação lista as duas juntas, lendo nome e descricao de cada arquivo. Compartilhar é copiar um .toml.

#### Pergunta 17 — Ordem de correção das dívidas TD-01 a TD-04

Você pediu que a correção venha depois de a arquitetura fechar. Ela fechou aqui. As dívidas são:
SDK importado no núcleo, `responder()` retornando `None`, `Memoria.anotar()` com `KeyError`,
ausência de teste.

A) **(recomendo)** Não existe "correção de dívida" como trabalho separado: cada dívida morre dentro
da unidade que reescreve aquele componente (o import do SDK morre na unidade do adaptador,
`responder()` morre na unidade da porta de sessão, `Memoria` morre na unidade de domínio). Zero
trabalho jogado fora

B) Uma unidade de saneamento primeiro, corrigindo as quatro dívidas sobre a estrutura atual, e
depois a arquitetura nova em cima

C) Corrigir só o que bloqueia (o import do SDK, porque quebra teste sem credencial) e deixar o
resto para as unidades

D) Other (please describe after [Answer]: tag below)

[Answer]: A - A fraqueza real de A não é técnica, é de rastreabilidade: dívida que "morre sozinha" é dívida que ninguém verifica se morreu. E "eu reescrevi, então acabou" não é evidência.

A correção é barata: cada dívida vira critério de aceite explícito da unidade que a mata, com um teste que provaria seu retorno. Concretamente:

TD-02 → teste que importa o pacote de domínio com o SDK desinstalado. Prova RF-F04 de forma executável, e o único jeito de esse teste voltar a falhar é alguém reintroduzir o import.
TD-01 → teste da porta de sessão que exige resposta não vazia; o adaptador falso e o real passam pelo mesmo contrato.
TD-03 → teste (e propriedade, já que PBT está ligado) de que anotar em chave nova funciona.
TD-04 → o critério de aceite é CS-01: fechar e reabrir reconstitui o ambiente.
Com isso, A deixa de ser "confia que some" e passa a ser "some, e existe um teste que impede voltar".

Minha recomendação
A, com as quatro dívidas registradas como critério de aceite nomeado das respectivas unidades, cada uma com teste de regressão.

Um detalhe pequeno: TD-03 é literalmente uma linha (setdefault ou defaultdict). Se em algum momento você precisar da memória funcionando antes da unidade que a reescreve, conserte na hora sem cerimônia — é um caso onde a regra não precisa ser rígida.

---

## 4. Plano de execução do estágio

### Parte 1 — Planejamento (este documento)

- [x] Ler `requirements.md` v2, `stories.md`, `execution-plan.md` v2 e notas retidas
- [x] Verificar no código os fatos que sustentam as perguntas (§2)
- [x] Levantar as decisões abertas herdadas de §6 e §9.8
- [x] Gerar perguntas nas cinco categorias exigidas pela regra do estágio
- [x] **Usuário respondeu 16 das 17 tags `[Answer]:`** (a Pergunta 8 ficou em branco)
- [x] Analisar respostas em busca de vagueza, contradição e critério indefinido
- [x] Ambiguidades encontradas — perguntas de acompanhamento criadas, estágio **não** prossegue
- [ ] **Rodada 2**: responder `application-design-clarification-questions.md` (7 perguntas)

> **Estado em 2026-08-23**: a análise obrigatória das respostas (regra `application-design.md`,
> passos 8 e 9) encontrou uma pergunta sem resposta e cinco pontos que precisam de decisão, sendo
> três deles conflitos com escopo já aprovado. A consolidação das 16 respostas dadas, o
> detalhamento de cada pendência e as perguntas de acompanhamento estão em
> **`application-design-clarification-questions.md`**, no mesmo diretório. Nenhum artefato de
> desenho foi gerado.
>
> **Aviso sobre este arquivo**: da linha ~509 à ~1690 há transcrição de conversa colada, com
> blocos de pergunta duplicados e tags `[Answer]:` vazias em cópias repetidas. As respostas
> canônicas são as da §1 do arquivo de clarificação. Nada foi apagado aqui.

### Parte 2 — Geração dos artefatos (só depois das respostas)

- [ ] `application-design/components.md` — componentes, propósito, responsabilidades e interfaces
  - [ ] Domínio: ambiente, frente, tarefa, chat, memória, etapa, identidade
  - [ ] Portas: persistência, sessão viva, wiki
  - [ ] Adaptadores: SQLite, Claude (`claude-agent-sdk`), wiki no filesystem
  - [ ] Wiki: esquema-semente, entidade/propriedade, `index.md`, resolução de links
  - [ ] Bibliotecário: ferramentas e confinamento de caminho
  - [ ] Interface: TUI e fronteira com os serviços
- [ ] `application-design/component-methods.md` — assinaturas, entrada e saída, propósito de cada
      método (regra de negócio detalhada fica para Functional Design)
- [ ] `application-design/services.md` — serviços de aplicação, responsabilidades e orquestração
      (ciclo de conversa, criação de ambiente com wiki semeada, promoção à wiki com revisão,
      carregar/salvar)
- [ ] `application-design/component-dependency.md` — matriz de dependência, regra de import
      permitida, padrão de comunicação e fluxo de dados; prova de que o núcleo não depende de
      `claude_agent_sdk` nem de `sqlite3`
- [ ] `application-design/application-design.md` — consolidação dos quatro documentos acima
- [ ] Rastrear cada componente às histórias da linha fina e aos RF/RNF que ele atende
- [ ] Validar sintaxe de Mermaid e alinhamento de diagrama ASCII antes de gravar, com alternativa
      textual (regra `common/content-validation.md`)
- [ ] Registrar conformidade das extensões habilitadas (`security-baseline`,
      `property-based-testing`), marcando N/A com justificativa onde não se aplica
- [ ] Atualizar `aidlc-state.md` e `audit.md`

### Extensões aplicáveis a este estágio

| Extensão | Situação | Como aparece no desenho |
|---|---|---|
| `security-baseline` | Habilitada | SECURITY-05 e SECURITY-13 (confinamento de caminho na tool de wiki, wiki como entrada não confiável), SECURITY-12 (credencial por usuário, nunca no código nem no banco), SECURITY-15 (falha do provedor e de I/O isolada na fronteira do adaptador, sem vazar detalhe interno para a tela). Regras de rede, HTTP, IAM e balanceador: N/A — processo local, sem porta de rede |
| `property-based-testing` | Habilitada (Full) | PBT-01 pede identificação de propriedades no desenho: round-trip de serialização do agregado, e nenhum caminho gerado escapa da raiz da wiki. As propriedades são **nomeadas** aqui e **especificadas** em Functional Design |
| `resiliency-baseline` | Desabilitada | Não enforçada, por decisão registrada em 2026-08-17 |

---

## 5. Critérios de conclusão do estágio

- Todas as 17 respostas presentes e sem ambiguidade não resolvida.
- Os cinco artefatos obrigatórios criados.
- As oito decisões abertas da §1 fechadas e escritas, cada uma com o motivo.
- Nenhum componente de domínio dependendo de `claude_agent_sdk`, `sqlite3` ou Textual, verificável
  pela matriz de dependência.
- Cada uma das 14 histórias da linha fina rastreada a pelo menos um componente.
- Aprovação explícita do usuário antes de Units Generation.
