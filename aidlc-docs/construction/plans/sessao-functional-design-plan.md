# Functional Design Plan — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Profundidade:** comprehensive
**Data:** 2026-10-02
**Base:** `unit-of-work.md` §3 (U6, critérios 1–7, com a emenda de U5), `unit-of-work-story-map.md`,
`components.md` §2.9, §4.2, §5.2, §5.4, `component-methods.md` §3.2, §4.2 e §6.1, `services.md`
§3 e §8, `application-design-plan.md` (Perguntas 5 e 6), `unit-of-work-plan.md` (Q11, Q12, R4,
R9, R10), `stories.md` (US-01, US-02, US-03, US-13, US-17), TD-01 e TD-02 em
`code-quality-assessment.md`, as heranças de U5 (`construction/acoes/functional-design/business-logic-model.md`
§9), o código de U1 (`dominio/agente.py`, `dominio/politica.py`), de U5
(`aplicacao/catalogo/tipos.py`, `aplicacao/portas/confirmacao.py`) e o spike
`testes-de-aprendizado/spike_claudeSDK.py`.
**Estado da base de código:** U0–U5 implementadas — **691 passed, 7 skipped**, `dependencies = []`.
Não existe `adaptadores/sessao/` nem porta de sessão. O SDK **não** está no `pyproject.toml`.

---

## 1. Contexto da unidade

| Campo | Conteúdo |
|---|---|
| **Componentes** | `PortaSessao`, `AdaptadorSessaoClaude`, servidor MCP in-process, registro nome→função de ferramentas |
| **Histórias** | US-01, US-02, US-03 (o adaptador), US-13 e US-17 (a exposição de ferramentas). Nenhuma fecha aqui: todas fecham em U9 |
| **Dívidas** | **TD-01** (`responder()` devolve `None`), **TD-02** (SDK importado no núcleo) |
| **Depende de** | U1 (`Agente`, `Papel`). Ver Q9: a conversão de ação em ferramenta pode acrescentar U5 |
| **Estágios** | FD **EXECUTE** (aqui) · NFR-R **EXECUTE** · NFR-D **EXECUTE** · INFRA **SKIP** · CG **EXECUTE** |
| **Portões** | 4 (este, NFR Requirements, NFR Design e Code Generation) |

**Critérios de pronto herdados** (`unit-of-work.md` §3, U6):

1. Contrato da porta exige resposta não vazia; adaptador falso e real passam pelo mesmo teste
   (mata TD-01).
2. Importar `dominio/` e `aplicacao/` com o SDK **desinstalado** funciona (mata TD-02); este é o
   único módulo que importa `claude_agent_sdk`.
3. Duas sessões vivas simultâneas no mesmo processo (orquestrador e bibliotecário).
4. Falha do provedor vira erro tipado, sem exceção crua atravessando a porta (RNF-06).
5. Exposição via MCP in-process, um servidor por conjunto de ferramentas (Q11=A).
6. **R10**: nenhum `Agente` com `papel = SUB_AGENTE` carrega nome de ferramenta da família
   ambiente. Teste de configuração, sem LLM.
7. A sessão do bibliotecário abre com ferramentas nativas de escrita fechadas (`tools=[]`).

**Heranças de U5** (emenda de 2026-10-02): (1) a família ambiente são as **6 ações** do catálogo, e
o R10 verifica esses 6 nomes; (2) o esquema de cada ferramenta sai do `Parametro` (tipo,
obrigatório, opções, máximo, descrição); (3) **medir** se uma ferramenta MCP in-process pode esperar
uma pessoa sem tempo-limite; (4) o texto que o agente recebe é montado a partir do `Resultado`,
incluindo a posição da etapa.

## 2. Fronteira desta unidade

**Faz:** o contrato da porta de sessão (abrir, enviar, fechar) e os eventos de um turno; o ciclo de
vida de uma sessão (estados, falha, reconexão, interrupção); a tradução das mensagens do SDK em
eventos — **num ponto só**; a tradução de toda falha do provedor em falha tipada; a exposição de
ferramentas a uma sessão, respeitando o escopo do agente (R10); o isolamento da sessão em relação à
máquina (o que o agente enxerga e com que credencial ele roda).

**Não faz:**

- Gravar transcrição, decidir cadência de gravação, montar o contexto (memória, etapas) que vai
  junto da mensagem, ou manter o mapa `chat → sessão`: **U7**.
- Escrever o prompt do orquestrador e do bibliotecário, ou as ferramentas de wiki: **U7/U8**.
- Validar os argumentos de uma ação, consultar a política de aprovação ou pedir confirmação: é de
  **U5**, que já faz isso dentro da função da ferramenta.
- Montar o registro concreto de ferramentas, mostrar a confirmação e escrever a frase de erro que
  você lê: **U9**.

## 3. O que já sabemos do SDK

**Medido pelo spike** (`claude-agent-sdk 0.2.125`, fora do `uv.lock`):

| Fato medido | Consequência para U6 |
|---|---|
| O nome que o agente vê é `mcp__<chave em mcp_servers>__<nome>`; o `name=` do servidor é cosmético | A família vira a chave do servidor: `mcp__ambiente__criar_etapa`, `mcp__wiki__ler` |
| Ferramenta MCP não é auto-aprovada; sem `allowed_tools` nem `can_use_tool`, o CLI nega sozinho e a função nunca roda | Falha fechada já é o padrão; U6 libera exatamente as ferramentas do agente |
| `tools=[]` desliga todas as nativas e não afeta as MCP | Base da Q11 |
| `system_prompt` como texto puro substitui o prompt inteiro do Claude Code | As `regras` do `Agente` são o prompt todo |
| Dois clientes vivos no mesmo event loop funcionam; o que não se pode é mover **um** cliente entre contextos async | Critério 3 viável; regra para U7: cada sessão é usada sempre a partir do mesmo contexto |
| `connect()` volta antes de os servidores MCP subirem, e a 1ª mensagem já sai com a ferramenta | Não esperar sinal de "pronto" |
| `SystemMessage(init)` chega uma vez **por mensagem**, não por conexão | O conversor ignora `SystemMessage` |
| O resultado da ferramenta volta como `UserMessage` com `ToolResultBlock`; `ResultMessage` encerra a resposta | `ResultMessage` é o fim do turno |
| O autor amarrado por closure não aparece no esquema e o modelo não consegue forjá-lo, nem quando instruído a isso | Sustenta a Q8 e a Q3=A de U5 |

**Não medido** — vira medição obrigatória no Code Generation, com o SDK real:

1. O formato do texto chegando aos poucos (se a Q1 for B).
2. Tempo-limite de uma ferramenta que espera uma pessoa (herança 3 de U5, R-FD6-7).
3. O que acontece com uma ferramenta que está esperando quando o turno é interrompido (Q7).
4. Como o CLI sinaliza falta de login e limite de uso da assinatura (Q4).
5. O efeito de tirar a chave de API do ambiente do processo do agente (Q13).
6. O que acontece ao atingir o limite de passos (Q12).
7. O erro quando o CLI do Claude não está instalado.

---

## 4. Reconciliações declaradas (aguardam objeção; sem objeção, viram emenda na geração)

| # | Divergência encontrada | Proposta |
|---|---|---|
| **R-FD6-1** | `component-methods.md` §4.2 (emenda R4): `abrir(agente)` resolve os nomes contra um registro nome→função **fixo**, entregue no construtor. Mas U5 decidiu que a ferramenta de ambiente age sempre na tarefa do chat do agente, com alvo e autor amarrados pelo sistema (Q3=A, C1=A), e deixou para U9 "amarrar `Alvo` e `Acionamento` de cada chat às ferramentas". Uma função fixa no construtor não sabe de que chat é a sessão | A forma sai da **Q8** |
| **R-FD6-2** | `component-methods.md` §3.2 diz "se `PortaSessao` **levantar** erro de provedor, o iterador emite um evento de erro" (a porta levanta, o serviço converte). §4.2 lista `ErroProvedor` como evento **da própria porta**, e o critério 4 proíbe exceção crua atravessando a porta | `enviar` **nunca levanta**: toda falha chega como o último evento do iterador. §3.2 emendado. Se `abrir` segue a mesma regra, decide a **Q2** |
| **R-FD6-3** | `component-methods.md` §6.1 lista `ToolResultBlock` entre os tipos que o adaptador converte. Desde a NFR Q6 de U2 (`resultado_resumo` removido), resultado de ferramenta não vira evento | O conversor ignora `ToolResultBlock`. `UsoDeFerramenta` significa "o agente pediu esta ferramenta", não "ela executou" — a execução é observada por quem implementa a ferramenta |
| **R-FD6-4** | O critério 3 diz "medido pelo spike". O spike rodou com uma versão do SDK que não está travada no projeto | O critério é **re-medido** no Code Generation, com a versão travada, num teste com o SDK real. O spike é evidência, não prova |
| **R-FD6-5** | O critério 6 (R10) manda percorrer "as instâncias de `Agente` configuradas", mas elas ainda não existem: os prompts nascem em U7/U8 e a montagem em U9 (R-FD5-8 deixou o lugar do teste para cá) | Depende da **Q14** |
| **R-FD6-6** | O critério 7 fala só do bibliotecário (`tools=[]`) | A **Q11** decide se vira regra de todas as sessões |
| **R-FD6-7** | Herança 3 de U5: ninguém sabe se o SDK corta uma ferramenta que fica esperando você responder | Medição obrigatória no Code Generation. Se houver limite **configurável**, U6 o põe no maior valor aceito e declara. Se não for configurável, **U5 é reaberta** (Q4 de U5) antes de U6 fechar |
| **R-FD6-8** | O critério 1 (TD-01) fala em "resposta não vazia", vocabulário do antigo `responder() -> str`. Numa porta de eventos, "vazio" precisa de definição | **Q3** |
| **R-FD6-9** | O `Chat` salvo guarda uma **cópia inteira do `Agente`** (modelo, ferramentas, prompt — `mapeamento.py` de U2). Ao reabrir um chat depois de reiniciar, a sessão pode abrir com a cópia salva ou com a configuração atual do código | Quem escolhe qual `Agente` entra em `abrir` é U7: **fica registrado para o FD de U7**. Qualquer que seja a escolha, a recusa em `abrir` (Q14=A) impede que uma cópia adulterada no banco dê ferramenta de ambiente a um sub-agente |
| **R-FD6-10** | US-07 (retomar a conversa com a memória do agente) está **adiada**. Consequência ainda não dita: **toda sessão nasce sem o histórico do chat**. Depois de reiniciar o programa, ou de uma reconexão (Q5), o agente não lembra os turnos anteriores daquele chat — embora a transcrição continue no banco e na tela | Declarado. O que vai de contexto junto da mensagem (a memória da tarefa já vai a cada chamada, decisão de 2026-08-07) é de U7 |
| **R-FD6-11** | `pyproject.toml` diz que o SDK entra em U6 | Se é dependência obrigatória ou extra opcional, com que versão, e como o teste do TD-02 simula "SDK desinstalado" são decisões de **NFR Requirements** (portão 2/4), não deste FD |

## 5. Decisões que as extensões já tomam (sem pergunta)

| Regra | O que fica decidido |
|---|---|
| **SECURITY-03** | O log `fishingrod.sessao` leva só metadados: abrir e fechar, nome do agente, nome da ferramenta pedida, categoria da falha, duração. **Nunca** o texto das mensagens, os argumentos das ferramentas ou credencial. A saída de erro do CLI só em nível DEBUG |
| **SECURITY-05** | O que o modelo passa a uma ferramenta é entrada não confiável. Quem valida é quem implementa a ferramenta (U5 para as de ambiente, U8 para as de wiki); a camada de exposição não confia que o modelo respeitou o esquema |
| **SECURITY-08** | A permissão do SDK é dada por nome qualificado **exato**, nunca por curinga. Qualquer pedido de ferramenta fora da lista do agente é negado e vai para o log |
| **SECURITY-12** | O adaptador nunca lê, guarda ou registra credencial: a autenticação é toda do CLI, pela assinatura (US-02) |
| **SECURITY-15** | Falha fechada: nome de ferramenta que não está no registro **impede a abertura** (nada de sessão pela metade). Exceção dentro de uma ferramenta vira resultado de erro genérico para o agente e vai para o log; a sessão continua. Nenhum processo do CLI fica órfão: o adaptador conhece as sessões que abriu e fecha todas no encerramento do programa |

---

## 6. Passos do Functional Design

- [x] **Step 1** — Ler a definição da unidade, o story map, as histórias, as heranças de U5, o código de U1 e U5 e o spike
- [x] **Step 2** — Criar este plano com passos em checkbox
- [x] **Step 3** — Gerar as perguntas com tag `[Answer]:` (§7), declarar as reconciliações (§4) e as decisões forçadas (§5)
- [x] **Step 4** — Guardar o plano em `construction/plans/sessao-functional-design-plan.md`
- [x] **Step 5** — Analisar as respostas; abrir clarificação se alguma for ambígua.
      14 respostas analisadas em 2026-10-02T21:48:20Z — Q1=B, Q2=B, Q3=B, Q4=A,
      Q5=A, **Q6=B** (fila), **Q7=A + ESC devolve a mensagem ao campo**, Q8=A–Q11=A, **Q12=B** (sem
      limite), Q13=A, Q14=A; R-FD6-1..11 sem objeção. Fila e ESC juntas deixavam três pontos em aberto →
      `sessao-fd-clarificacao.md`. ~~**Aguardando C1–C3**~~ **Fechadas em 2026-10-02T22:01:38Z**:
      **C1=B** (a fila junta o texto e mora em U7), **C2=A** (ESC devolve o texto; mensagem entregue
      fica marcada como interrompida), **C3=A** (depois de falha, a fila não sai sozinha);
      D-Q12-1, D-C2-1, D-Q3-1, D-Q5-1 e D-Q7-1 sem objeção
- [x] **Step 6** — `construction/sessao/functional-design/domain-entities.md` (porta, contexto, sessão, 5 eventos e gramática do turno, 9 motivos de falha, `Familia`, `Ferramenta` neutra, registro de fábricas, projeção das ações, 4 estados, adaptador, erros)
- [x] **Step 7** — `business-rules.md` (**54 regras `RN-S-01..54`**) e `business-logic-model.md` (fluxos de abrir, turno, falha, interrupção e da ação à ferramenta; tabela de estados; **10 medições obrigatórias** no CG; **12 propriedades `PBT-U6-01..12`**; **15 decisões G1–G15** para o portão; consequências para U5, U7, U8, U9 e a próxima iteração)
- [x] **Step 8** — Emendas com texto riscado ou marcado: `unit-of-work.md` (U6 e as heranças de U7, U8, U9), `unit-of-work-dependency.md` (seta nova U6 → U5, Q9=A), `components.md` §4.2 e §5.2, `component-methods.md` §3.2, §4.2 e §6.1
- [x] **Step 9** — Apresentar a conclusão e aguardar aprovação. Conclusão apresentada em 2026-10-02T22:01:38Z; **APROVADO em 2026-10-02T22:28:28Z** ("aprovado pode continuar")

**Prévia das propriedades testáveis** (PBT-01 — a lista final sai no Step 7):

| Candidata | Categoria |
|---|---|
| Para qualquer sequência de mensagens do provedor, inclusive falha em qualquer ponto, o turno é: pedaços e usos de ferramenta, depois **exatamente um** evento final | Invariante (PBT-03) |
| A concatenação dos pedaços de texto é igual ao texto que o provedor mandou, na ordem | Invariante / oráculo (PBT-03, PBT-05) |
| `enviar` nunca levanta: qualquer exceção do provedor vira falha tipada; só o cancelamento passa | Invariante de segurança (PBT-03) |
| Nome qualificado: separar `mcp__<família>__<nome>` devolve a família e o nome originais | Round-trip (PBT-02) |
| O esquema da ferramenta tem exatamente os parâmetros da ação, com obrigatório, opções e máximo iguais | Invariante (PBT-03) |
| Ler de volta o texto que o agente recebe devolve sucesso, motivo e detalhe do `Resultado` | Round-trip (PBT-02) |
| Nenhuma configuração deixa um sub-agente abrir sessão com ferramenta de ambiente | Invariante de segurança (PBT-03) |
| Sequência aleatória de abrir, enviar, falhar, interromper e fechar contra um modelo de estados: o número de processos vivos bate com o modelo a cada passo; fechar duas vezes é o mesmo que fechar uma | Com estado + idempotência (PBT-06, PBT-04) |
| Duas sessões intercaladas nunca trocam eventos entre si | Invariante (PBT-03) |

---

## 7. Perguntas

Cada pergunta traz a minha recomendação e o porquê. Responda com a letra; se nenhuma servir, use
`X` e descreva.

---

### Q1 — O texto da resposta chega de uma vez ou aos poucos?

Em qualquer opção, o raciocínio interno do modelo (*thinking*) não vira evento: não aparece na tela
nem vai para o banco.

A) **Por bloco**, como o spike mediu: cada bloco de texto da resposta chega inteiro. Uma resposta de
30 segundos aparece de uma vez no fim, com um indicador de "respondendo" até lá.

B) **Aos poucos** (palavra a palavra, como no claude.ai): o adaptador liga o modo de mensagens
parciais do SDK e entrega cada trecho assim que chega. **(Recomendado)**: é o que a Pergunta 5B
prometeu ("streaming de graça"), o critério 2 de U9 pede ("renderiza incrementalmente") e a
cadência de 500 ms de U7 já foi desenhada para atualizações frequentes. **Risco declarado:** o
formato das mensagens parciais não foi medido pelo spike; é o item 1 da medição. A regra que protege
contra texto duplicado (o SDK também manda o bloco inteiro no fim) vira propriedade: a soma dos
pedaços é igual ao texto completo.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B

---

### Q2 — Quando a conexão com o provedor acontece?

Cada sessão é um processo do CLI do Claude rodando por baixo.

A) **Na abertura**: `abrir` sobe o processo e só devolve a sessão pronta. Uma falha de conexão
aparece em `abrir`, como erro tipado; uma falha durante a conversa aparece em `enviar`, como
evento. Dois caminhos de erro para U7 e U9 tratarem.

B) **No primeiro envio**: `abrir` só prepara a sessão e nunca falha por causa do provedor; o
processo sobe na primeira mensagem. Toda falha de provedor chega do **mesmo jeito**: como o último
evento de um turno. **(Recomendado)**: um caminho só de erro, que é o que US-03 pede ("o erro fica
contido na aba"); abrir uma aba é instantâneo; um chat em que você nunca escreve não custa
processo nenhum. Custo: a primeira mensagem de cada chat demora a mais o tempo de subir o processo.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B

---

### Q3 — O que é "resposta não vazia"? *(TD-01)*

Hoje, `responder()` devolve `None` e a tela quebra. A regra nova precisa dizer quando um turno
"respondeu".

A) Um turno só termina bem se tiver **ao menos um trecho de texto não vazio**. Sem texto, termina
com a falha "resposta vazia" — mesmo que o agente tenha usado ferramentas.

B) Um turno termina bem se tiver **texto não vazio ou ao menos um uso de ferramenta**. Sem nenhum
dos dois, termina com a falha "resposta vazia". **(Recomendado)**: um orquestrador que criou três
etapas e não disse nada fez trabalho de verdade; chamar isso de falha faria você achar que nada
aconteceu. O que TD-01 proíbe é o silêncio total, e esse continua proibido.

C) Sem regra: um fim de turno vazio é válido.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B - eu penso que tem que ser assim tambem por outro motivo que vejo o uso do orquetrador pelo usuario. eu vejo o usuario falando com o orquetrador e o orquetrador pode fazer acoe como usar ferramentas, ai o orquestrador de fato nao "fez nada" mas ele diria algo como "a acao X feita, agora Y coisa esta sendo feita no chat Z, vc pode me pedir mais coisas para fazer ou acompanhar o trabalho no outro chat" . esse exemplo ilustra um uso quero quero ter , onde o orquestrador toma acoes no ambiente e eu vejo e tenho algum retorno do orquetrador, ai o usuario e o orquetrador vao tomando varias acoes. ficou claro? . 

---

### Q4 — Quão detalhado é o motivo de uma falha do provedor?

Como em U5 (Q10=A): o núcleo devolve um motivo, e a tela escreve a frase.

A) **Por categoria, uma para cada remédio diferente**: *provedor ausente* (o CLI do Claude não está
instalado — instalar), *não autenticado* (sem login na assinatura — rodar o login), *limite de uso*
(limite da assinatura atingido — esperar), *indisponível* (conexão caiu, processo morreu, serviço
fora — tentar de novo), *resposta vazia* (Q3) e *falha inesperada* (o resto, com a pilha no log).
Mais um detalhe estruturado, sem conteúdo de mensagem. Q6 e Q12 podem acrescentar uma categoria
cada. **(Recomendado)**: cada categoria pede de você uma ação diferente, e a tela não precisa
conhecer as exceções do SDK. **Risco declarado:** reconhecer "não autenticado" e "limite de uso"
depende de como o CLI avisa (item 4 da medição); o que não der para reconhecer cai em
*indisponível* ou *inesperada* — nunca em categoria errada.

B) **Só duas**: falha do provedor e falha inesperada, mais o texto do erro.

C) **Uma por exceção do SDK**, espelhando os tipos dele.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q5 — Depois que a conexão cai, a sessão continua usável?

Falhas que não derrubam a conexão (limite de uso, resposta vazia) deixam a sessão como estava, com o
histórico. A pergunta é sobre a conexão que caiu ou o processo que morreu.

A) **Reconecta na próxima mensagem**, sozinha. O primeiro turno depois da reconexão avisa, no evento
final, que **a conversa recomeçou sem o histórico** (R-FD6-10), para a tela poder te dizer isso.
**(Recomendado)**: você só manda de novo; e o aviso evita que o agente "esquecer" pareça defeito.

B) **A sessão morre**: a próxima mensagem nela falha com "sessão encerrada", e U7 abre outra. Mesmo
efeito para você, com mais código em U7.

C) **Não reconecta**: o chat fica sem agente até você reiniciar o programa.

D) Reconecta **retomando** a conversa anterior pelo mecanismo de retomada do CLI. Mantém o
histórico, mas depende de arquivos que o CLI grava na sua pasta de usuário, fora da pasta de dados
do FishingRod, não foi medido, e é exatamente a porta de entrada de US-07, que você adiou.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A - vamos seguir de A por enquanto. a opcao D que seria uma forma de retomada do historico do chat eu penso que seria o melhor pois o correto memso é retornar o historico , se nao o usuario nao consegue continuar a conversa direito. mas nessa iteracao nao vamos fazer essa parte de retomada, é um outro problema que podemo fazer depois em uma proxima iteracao. 

---

### Q6 — E se chegar uma segunda mensagem no mesmo chat enquanto o agente ainda responde?

Isso inclui o tempo em que o agente espera a sua confirmação de uma ação.

A) **Recusa na hora**: o segundo envio termina imediatamente com a falha "turno em andamento", sem
tocar no provedor, e o primeiro turno segue intacto. **(Recomendado)**: a tela já não deveria deixar
você enviar nesse momento; a regra é a grade de proteção, e falha visível é melhor que comportamento
escondido.

B) **Fila**: a segunda mensagem espera o primeiro turno acabar e então é enviada.

C) **Interrompe** o primeiro turno e envia a segunda mensagem.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B - fila é um bom uso, enquanto o usuario espera o Agente pensar ele pode digitar mai alguma informacao e enviar. sem isso eu penso que daria estranheza no uso da interface para o usuario.

---

### Q7 — Como se interrompe um turno?

Vale para o seu "parar" e para fechar a aba no meio de uma resposta. Em qualquer opção, valem duas
regras: interromper **cancela as ferramentas daquela sessão que estão em execução — inclusive a
espera pela sua confirmação**, e nada executa (RN-AC-30 de U5); e a sessão continua usável para a
próxima mensagem. A primeira regra precisa de código próprio: a função da ferramenta roda numa
tarefa interna do SDK, e cancelar quem lê a resposta **não** a alcança sozinho.

A) **Pelo cancelamento da tarefa que lê a resposta** (o jeito padrão do asyncio, que é como o
Textual cancela um trabalho em andamento). O adaptador, ao ser cancelado, avisa o provedor e cancela
as ferramentas em execução. A porta não ganha método novo. **(Recomendado)**: é o mesmo mecanismo
que U5 já usa para cancelar a confirmação, e a tela não precisa conhecer um segundo jeito de parar.

B) **Método explícito** `interromper(sessao)` na porta; o turno termina com um evento final
"interrompido".

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A - concordo com essa abordagem e tem mais um ponto que queria falar que eu etava pensando. ea quetao de interromper o turno pode servir para mensagens tambem. eu estou pensando isso pq estou imaginando o seguinte cenario - eu imagino eu enviando uma mensagem no chat , mas eu quero digitar mais, ou eu escrevi algo errado, nesse caso no claude code eu consigo clicar a tecla ESC para conseguir cancelar a mensagem, ai a mensagem ate volta para o chat novamente, ai consigo reescrever. entao o parar ou interromper o turno é meio que para isso tambem, vai interromper as menagens e as ferramentas, ate imagino sendo isso do memo jeito que no claude code com o usuario podendo clicar  ESC para interromper. 

---

### Q8 — Como as ferramentas chegam amarradas ao chat certo? *(R-FD6-1)*

A) **Registro de fábricas** no construtor do adaptador (cada nome aponta para a sua família e para
uma fábrica), e `abrir(agente, contexto)`: o contexto traz os ids do ambiente, da frente, da tarefa
e do chat, mais o nome do agente, e é montado por quem abre (U7) a partir do chat. O adaptador chama
a fábrica de cada ferramenta do agente com esse contexto. **(Recomendado)**: mantém R4 (o registro é
montado em U9 e resolvido pelo adaptador) e a Q3=A de U5 (o alvo vem do sistema, não do agente). O
contexto é tipo desta unidade, feito só de ids e de um nome: o adaptador não conhece `Alvo` nem o
catálogo.

B) `abrir(agente, ferramentas)`: quem abre entrega as ferramentas **já amarradas**, e o adaptador só
as expõe. O registro sai do adaptador e vai para U7, que passa a precisar de uma fábrica entregue por
U9 — revoga R4 em parte.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q9 — Quem transforma uma ação do catálogo em ferramenta?

É o trabalho das heranças 2 e 4 de U5: o esquema sai do `Parametro`, e o texto que o agente lê sai
do `Resultado`.

A) **Um módulo de aplicação desta unidade, sem SDK**: a partir de uma `Acao`, do catálogo, do alvo e
do acionamento, ele produz uma **ferramenta neutra** (nome, descrição, esquema e função). O
adaptador Claude só traduz a ferramenta neutra para o formato do SDK. **(Recomendado)**: a parte com
regra (esquema e texto) fica testável sem o SDK instalado; U8 reaproveita o mesmo tipo neutro para as
ferramentas de wiki; o adaptador continua sendo o único lugar com SDK. Consequência: U6 passa a
depender de U5, que já está pronta — a ordem sequencial não muda, e `ServicoConversa` continua sem
importar o catálogo (o motivo de Q12=A).

B) **No composition root** (U9): fica sem teste até U9 e mora na camada de interface.

C) **Dentro do adaptador Claude**: o adaptador passa a importar o catálogo, e regra de negócio
mistura com tradução de SDK.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q10 — O que o agente lê quando uma ferramenta termina?

A) **JSON compacto, sem ids**. Sucesso: `{"ok": true, ...}` com o objeto pelo nome e pela posição —
por exemplo, uma etapa como `{"posicao": 3, "descricao": "...", "executor": "usuario",
"concluida": false}`. Falha: `{"ok": false, "motivo": "recusada", "detalhe": {...}}`, marcada para
o SDK como erro da ferramenta. **(Recomendado)**: o modelo lê JSON bem; o motivo é o valor que U5 já
definiu como "o que o agente lê" (RN-AC-35); ida e volta é testável; e o agente nunca usa id (Q3=A
de U5), então mostrar id só gastaria contexto.

B) **Uma frase curta em português**, montada aqui ("Etapa 3 criada: ...").

C) JSON **com** os ids.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q11 — O que o agente enxerga além das ferramentas do FishingRod? *(R-FD6-6)*

O CLI do Claude, por padrão, traz ferramentas nativas (ler e escrever arquivo, terminal, web) e
carrega a configuração do Claude Code da máquina: `CLAUDE.md`, servidores MCP, hooks, plugins e
permissões.

A) **Nada**: nenhuma ferramenta nativa para nenhum agente, nenhuma configuração da máquina; o prompt
é só o das `regras` do `Agente`, e o processo roda numa pasta neutra. **(Recomendado)**: um
orquestrador com terminal ou acesso a arquivos faria qualquer coisa na sua máquina sem passar pela
confirmação; web traz conteúdo não confiável (instrução injetada) para o contexto de quem tem as
ferramentas de ambiente; e sem isolamento o agente se comportaria diferente na máquina do João e na
sua — o seu `CLAUDE.md` do AI-DLC e os seus servidores MCP entrariam no orquestrador. O critério 7
vira regra de todas as sessões.

B) Como A, mas o **orquestrador ganha busca e leitura na web**.

C) **Herda** a configuração do Claude Code da máquina e as ferramentas nativas de leitura.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q12 — Existe limite de passos num turno?

Num turno, o agente pode usar ferramentas várias vezes (criar 4 etapas são 4 chamadas). O SDK tem
um limite de rodadas por turno; o spike usou 6.

A) **Limite fixo e folgado** (proposta: 25 rodadas; o número exato fica para o NFR). Ao atingir, o
turno termina com a falha "limite de passos", e o que já foi feito permanece. **(Recomendado)**: é o
caso de abuso que SECURITY-11 pede para considerar — um agente com instrução injetada em laço.
As ferramentas de ambiente já esbarram na sua confirmação, mas as de leitura da wiki não, e cada
rodada gasta a sua assinatura.

B) **Sem limite.**

C) **Limite por agente**, num campo novo de `Agente` (mexe em U1 e U2).

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: B

---

### Q13 — E se houver uma chave de API nas variáveis de ambiente da máquina? *(US-02, FOR-09)*

Se `ANTHROPIC_API_KEY` estiver definida (por causa de outro projeto, por exemplo), o CLI usa a chave
em vez da assinatura — e cobra na conta da API.

A) **O adaptador tira do processo do agente as variáveis de credencial de API** (a chave, o token e
as de provedores alternativos), e a sessão roda sempre pela assinatura. O adaptador nunca lê o
valor; só não o repassa. **(Recomendado)**: é o que US-02 e FOR-09 dizem, e evita uma cobrança que
você não esperava. **Risco declarado:** item 5 da medição.

B) **Deixa como está**: se houver chave, ela é usada.

C) **Recusa abrir a sessão** enquanto houver chave no ambiente, com aviso.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

### Q14 — Onde o invariante R10 é garantido? *(R-FD6-5)*

R10: nenhum sub-agente carrega ferramenta da família ambiente.

A) **Em duas camadas**: (1) `abrir` **recusa** a sessão de um sub-agente que tenha ferramenta de
ambiente, e recusa nome de ferramenta que não existe no registro — falha de configuração tipada,
nenhuma sessão pela metade; (2) uma função de verificação de configuração, testada aqui com
configurações geradas, que o teste das instâncias reais chama onde elas nascem (U8 e U9).
**(Recomendado)**: defesa em camadas (SECURITY-11); a recusa em `abrir` vale até para um `Agente`
lido de um banco adulterado (R-FD6-9), coisa que um teste de configuração não pega.

B) **Só o teste de configuração**, como o enunciado literal de R10.

C) **Só a recusa em `abrir`.**

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

## 8. Adiado para NFR Requirements (portão 2/4)

Registrado aqui para não parecer esquecido; nenhuma destas decisões é de regra de negócio.

- O SDK como dependência obrigatória ou extra opcional; versão travada e convivência com
  `exclude-newer = 2026-08-25` (R-FD6-11).
- Como o teste do TD-02 simula "SDK desinstalado".
- Quando roda o teste com o SDK real: ele gasta assinatura e exige login, então não pode ser parte
  da suíte padrão.
- Valores: tempo de conexão, número exato do limite de passos (Q12), máximo de sessões vivas ao
  mesmo tempo (cada uma é um processo do CLI).
- Destino e nível do log `fishingrod.sessao` (o destino é de U9).
