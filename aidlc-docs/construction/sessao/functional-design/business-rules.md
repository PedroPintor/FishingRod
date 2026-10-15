# Business Rules — U6 `sessao`

**Fase:** CONSTRUCTION · **Unidade:** `U6 sessao` · **Portão 1 de 4 (Functional Design)**
**Data:** 2026-10-02
**Prefixo:** `RN-S-nn`. As regras de U1 (`RN-nn`), U2 (`RN-P-nn`), U3 (`RN-W-nn`), U4 (`RN-A-nn`) e
U5 (`RN-AC-nn`) continuam valendo; aqui entra só o que é de sessão e de exposição de ferramentas.

---

## 1. Fronteira

| # | Regra | Origem |
|---|---|---|
| **RN-S-01** | **Só `adaptadores/sessao/` importa `claude_agent_sdk`.** `dominio/` e `aplicacao/` importam com o SDK desinstalado | critério 2; TD-02; RF-F04 |
| **RN-S-02** | **Nenhum tipo do SDK atravessa a porta.** O que sai são `SessaoViva`, `EventoConversa` e os erros de `domain-entities.md` §7 | critério 4; RF-F04 |
| **RN-S-03** | **A sessão não grava nada e não guarda fila.** Transcrição, cadência de gravação, contexto que vai junto da mensagem, a fila de mensagens e o mapa `chat → sessão` são de U7 | fronteira; C1=B |
| **RN-S-04** | **A sessão não valida argumento de ferramenta nem pede confirmação.** Isso é de quem implementa a ferramenta: U5 para as de ambiente, U8 para as de wiki | SECURITY-05; Q4=A de U5 |

## 2. Abertura e configuração

| # | Regra | Origem |
|---|---|---|
| **RN-S-05** | **`abrir` só prepara.** Verifica e fabrica as ferramentas, e não sobe processo. Nunca falha por causa do provedor | Q2=B |
| **RN-S-06** | **Todo nome em `Agente.ferramentas` existe no registro, uma vez só.** Nome desconhecido ou repetido impede a abertura com `ConfiguracaoDeSessaoInvalida`: não existe sessão pela metade | Q14=A; SECURITY-15 |
| **RN-S-07** | **R10 na abertura:** um `Agente` com `papel = SUB_AGENTE` e qualquer ferramenta da família `AMBIENTE` tem a abertura recusada. Vale para qualquer `Agente`, inclusive o lido de um banco adulterado | critério 6; Q14=A; R-FD6-9 |
| **RN-S-08** | **As ferramentas são fabricadas uma vez, na abertura**, chamando a fábrica de cada nome com o contexto e o agente. Fábrica que levanta, ou que devolve outro nome ou um esquema que não é de objeto, impede a abertura | Q8=A; SECURITY-15 |
| **RN-S-09** | **O contexto só tem identidades.** O nome que assina o que o agente fizer vem do `Agente`. Nem quem abre nem o modelo têm onde passá-lo | Q8=A; Q3=A e Q5=A de U5; G10 |
| **RN-S-10** | **O agente enxerga só as ferramentas da sessão.** Nenhuma ferramenta nativa do CLI, para nenhum agente. Nenhuma configuração da máquina: `CLAUDE.md`, servidores MCP, hooks, plugins, permissões. O prompt é só as `regras` do `Agente`, unidas por linha em branco, e nunca o prompt do Claude Code, nem quando as regras são vazias. O processo roda na pasta de trabalho recebida no construtor. **Emenda 2026-10-13 (Code Generation, medição 8, A19): o CLI 2.1.238, em modo SDK, sempre põe antes das `regras` uma linha de identidade fixa — *"You are a Claude agent, built on Anthropic's Claude Agent SDK."* (lida no binário; o agente a citou ao ser perguntado). Não é o prompt do Claude Code, não traz ferramenta nem configuração, e não há opção que a tire. As `regras` vêm logo depois dela** | Q11=A; critério 7 generalizado; SECURITY-09 |
| **RN-S-11** | **Permissão por nome qualificado exato** das ferramentas da sessão, nunca curinga. Qualquer outro pedido de ferramenta é negado e registrado no log | SECURITY-08 |
| **RN-S-12** | **Um servidor MCP in-process por família presente na sessão**, com a família como chave. O agente vê `mcp__<familia>__<nome>`. Sessão sem ferramenta não tem servidor | critério 5; Q11=A de Units Generation |
| **RN-S-13** | **Nome de ferramenta é único no registro inteiro**, entre famílias. `Agente.ferramentas` guarda o nome sem família | R4 |
| **RN-S-14** | **O registro é verificado ao ser construído**: nome `snake_case` ASCII minúsculo (o padrão de RN-AC-07), único, família conhecida. Registro inválido levanta `RegistroInvalido`, que é erro de montagem | — |
| **RN-S-15** | **`verificar_escopo(agentes)` aplica RN-S-06 e RN-S-07 a uma coleção**, com o mesmo código de `abrir`. O teste das instâncias reais (orquestrador, bibliotecário) a chama onde elas nascem: U8 e U9 | Q14=A; R-FD6-5 |

## 3. O turno

| # | Regra | Origem |
|---|---|---|
| **RN-S-16** | **`enviar` nunca levanta.** Toda falha chega como o último evento do turno. Só o cancelamento passa, porque não é falha | critério 4; R-FD6-2; RNF-06 |
| **RN-S-17** | **Gramática do turno:** `MensagemEntregue`, depois pedaços de texto e usos de ferramenta, depois **exatamente um** evento final (`FimDeTurno` ou `FalhaDoTurno`). Uma falha antes da entrega é só `FalhaDoTurno`. Nada vem depois do evento final | D-C2-1 |
| **RN-S-18** | **`MensagemEntregue` sai quando a mensagem chegou ao provedor**, e só então. Antes dela, nada do turno existe para o agente. `conversa_nova` é `True` na primeira entrega de cada conexão | C2=A; D-C2-1; Q5=A; R-FD6-10; G2 |
| **RN-S-19** | **O texto chega aos poucos.** Cada trecho que o provedor manda vira um `PedacoDeTexto`, nunca vazio. O texto completo do bloco, que o SDK manda no fim, é a referência. Se nenhum trecho chegou, o bloco inteiro vira um pedaço. Se os trechos são o começo do bloco, sai o que falta. Se divergem, o log registra um aviso e nada mais sai para aquele bloco | Q1=B |
| **RN-S-20** | **Blocos de texto do mesmo turno são separados por uma linha em branco**, posta no começo do primeiro pedaço do bloco seguinte | G3 |
| **RN-S-21** | **O raciocínio interno do modelo não vira evento** | Q1 |
| **RN-S-22** | **Um `UsoDeFerramenta` por pedido de ferramenta da sessão**, tirado do bloco completo e não dos trechos parciais, na ordem dos blocos. Significa "o agente pediu", não "executou". Pedido de ferramenta que não é da sessão não vira evento: é negado e vai para o log | R-FD6-3; G8; G9 |
| **RN-S-23** | **Resultado de ferramenta e mensagens de sistema do SDK não viram evento** | R-FD6-3 |
| **RN-S-24** | **Resposta não vazia:** o turno só termina em `FimDeTurno` se houve ao menos um pedaço de texto **ou** um uso de ferramenta. Sem nenhum dos dois, termina em `FalhaDoTurno(RESPOSTA_VAZIA)` | critério 1; TD-01; Q3=B |
| **RN-S-25** | **Mensagem vazia (só espaços) ou com mais de 100.000 caracteres** termina em `FalhaDoTurno(MENSAGEM_INVALIDA)` sem tocar no provedor | SECURITY-05; G4 |
| **RN-S-26** | **Um turno por vez em cada sessão.** `enviar` com turno em andamento termina na hora em `FalhaDoTurno(TURNO_EM_ANDAMENTO)`, sem tocar no provedor nem no turno que está andando. É proteção contra defeito: a fila é de U7. **Emenda 2026-10-13 (NFR Design, N2): a vaga é de quem lê o turno. Depois de um ESC, enquanto o adaptador termina de interromper o provedor (até 5 s), um `enviar` novo não recebe `TURNO_EM_ANDAMENTO`: toma a vaga e espera a interrupção acabar** | C1=B; Q6=B |
| **RN-S-27** | **A vaga do turno é tomada antes de qualquer espera.** Duas chamadas ao mesmo tempo nunca começam dois turnos | RN-S-26 |

## 4. Falhas

| # | Regra | Origem |
|---|---|---|
| **RN-S-28** | **Toda falha cai numa categoria** de `domain-entities.md` §3.1, pela causa. A tabela de tradução é total: o que não está nela é `FALHA_INESPERADA` | Q4=A; critério 4 |
| **RN-S-29** | **`NAO_AUTENTICADO` e `LIMITE_DE_USO` só com sinal medido.** O que não se reconhece com certeza cai em `INDISPONIVEL`, se for falha de conexão ou de processo, ou em `FALHA_INESPERADA`. Nunca em categoria errada | Q4=A |
| **RN-S-30** | **`FALHA_INESPERADA` vai para o log** em nível ERROR, com a pilha de chamadas. Nada dela vai no evento | SECURITY-15; SECURITY-03 |
| **RN-S-31** | **O `detalhe` não carrega conteúdo**: nem texto de mensagem, nem caminho de disco, nem pilha, nem credencial. Só `problema` e `maximo` em `MENSAGEM_INVALIDA`, e `libera_em` em `LIMITE_DE_USO` quando o CLI informar | SECURITY-15 |

## 5. Ciclo de vida

| # | Regra | Origem |
|---|---|---|
| **RN-S-32** | **Quatro estados**: `SEM_CONEXAO`, `OCIOSA`, `EM_TURNO`, `FECHADA`. Transições em `business-logic-model.md` §5 | Q2=B; Q5=A; Q7=A |
| **RN-S-33** | **Conexão sob demanda:** `enviar` em `SEM_CONEXAO` sobe o processo antes de entregar a mensagem. Se não subir, o turno termina em falha sem entrega | Q2=B |
| **RN-S-34** | **Reconexão sozinha.** As falhas que derrubam a conexão (`PROVEDOR_AUSENTE`, `NAO_AUTENTICADO`, `INDISPONIVEL`, `FALHA_INESPERADA`) descartam e fecham o processo, e a sessão volta a `SEM_CONEXAO`. A próxima mensagem reconecta, com `conversa_nova = True`. `LIMITE_DE_USO` e `RESPOSTA_VAZIA` mantêm a conexão e o histórico | Q5=A |
| **RN-S-35** | **Interromper é cancelar quem lê o turno**, ou abandonar o iterador. O adaptador avisa o provedor e cancela **todas** as ferramentas da sessão em execução, inclusive a espera da sua confirmação, e nada mais executa. A sessão volta a `OCIOSA`. Se o aviso ao provedor falhar, o processo é descartado e a sessão vai a `SEM_CONEXAO`. O que já executou antes continua feito | Q7=A; C2=A; RN-AC-30 |
| **RN-S-36** | **Interromper antes da entrega não deixa nada no provedor.** O processo que estava subindo é fechado. **Emenda 2026-10-13 (NFR Design, N3): "antes da entrega" é medido por quem lê: se o leitor ainda não recebeu `MensagemEntregue`, o processo é descartado, mesmo que a escrita para o CLI já tenha terminado** | C2=A |
| **RN-S-37** | **`fechar` leva a `FECHADA` a partir de qualquer estado.** Um turno em andamento termina em `FalhaDoTurno(SESSAO_FECHADA)`; as ferramentas em execução são canceladas; o processo é fechado. Fechar de novo não faz nada. `enviar` numa sessão fechada termina em `FalhaDoTurno(SESSAO_FECHADA)` | SECURITY-15; PBT-04 |
| **RN-S-38** | **Nenhum processo do CLI fica sem dono.** Nenhum caminho de erro, cancelamento ou fechamento deixa um processo vivo sem uma sessão que o use | SECURITY-15 |
| **RN-S-39** | **`encerrar()` fecha todas as sessões do adaptador.** Depois dele, `abrir` levanta `AdaptadorEncerrado` | G7; SECURITY-15 |
| **RN-S-40** | **Sessões são independentes.** Cada uma tem processo, ferramentas e eventos próprios. Falha, interrupção ou fechamento de uma não afeta outra | critério 3; US-03; RNF-06 |
| **RN-S-41** | **Toda sessão nasce sem o histórico do chat.** O agente não lembra os turnos anteriores à conexão atual; a transcrição continua no banco e na tela | R-FD6-10; US-07 adiada; D-Q5-1 |

## 6. Execução de ferramentas

| # | Regra | Origem |
|---|---|---|
| **RN-S-42** | **A ferramenta recebe os argumentos do modelo como vieram**, em cópia somente leitura. Ela valida; o adaptador não confia que o modelo respeitou o esquema. **Emenda 2026-10-13 (Code Generation, R-CG6-1, A16): o servidor in-process do SDK confere os argumentos contra o esquema ANTES de chamar a ferramenta. O que o esquema recusa não chega à ferramenta, e o agente lê o erro do SDK (`Input validation error: …`), marcado como erro. O que passa chega como veio, e a ferramenta valida de novo: o SDK é mais estrito que o catálogo, nunca mais frouxo (PBT-U6-06)** | SECURITY-05; RN-S-04 |
| **RN-S-43** | **Exceção dentro da ferramenta vira resposta de erro genérica** para o agente (`{"ok": false, "motivo": "falha_inesperada"}`) e vai para o log em ERROR, **sem os argumentos**. O turno e a sessão continuam | SECURITY-15; SECURITY-03 |
| **RN-S-44** | **Toda execução de ferramenta fica registrada na sessão enquanto roda**, para que interromper e fechar possam cancelá-la. A função da ferramenta roda numa tarefa interna do SDK, que o cancelamento de quem lê o turno não alcança sozinho | RN-S-35; Q7 |
| **RN-S-45** | **Sem limite de passos por turno.** A defesa contra um agente em laço é a interrupção e, para as ferramentas de ambiente, a confirmação. Risco aceito | Q12=B; D-Q12-1; SECURITY-11 |

## 7. Ações do catálogo como ferramentas

| # | Regra | Origem |
|---|---|---|
| **RN-S-46** | **Só ações que aceitam o chamador `AGENTE` viram ferramenta**, na família `AMBIENTE`, com o nome e a descrição da ação | D-Q2-1 de U5; R9 |
| **RN-S-47** | **O esquema sai dos `Parametro`**: um objeto com uma propriedade por parâmetro, `required` com os obrigatórios e nada além deles (`additionalProperties: false`). `TEXTO` vira texto com `maxLength` igual ao máximo e, se obrigatório, `minLength: 1`. `ESCOLHA` vira texto com `enum` igual às opções. `POSICAO` vira inteiro com mínimo 1. A descrição vai junto. O esquema orienta o modelo; quem decide é o catálogo. **Emenda 2026-10-13 (Code Generation, R-CG6-4): `TEXTO` obrigatório leva também `pattern: "\S"` (texto só de espaços é ausente para U5, R-CG5-6), e `POSICAO` leva também `maximum: 999999999` (o teto de U5). Como o SDK confere o esquema antes da ferramenta (R-CG6-1), o esquema nunca pode ser mais frouxo que a conferência de forma do catálogo. A lista fechada de agentes de U4 não cabe no esquema: é regra de domínio, e o agente lê `fora_da_lista`** | herança 2 de U5; G14 |
| **RN-S-48** | **A fábrica amarra o alvo e quem aciona**: `Alvo(id_ambiente, id_frente, id_tarefa)` vem do contexto e `Acionamento.agente(agente.nome)` vem do `Agente`. O modelo não tem onde passar id nem autor | Q3=A, C1=A e Q5=A de U5; Q8=A |
| **RN-S-49** | **Toda execução passa por `CatalogoDeAcoes.executar`**, o único caminho de U5. A política de aprovação e a confirmação continuam lá | RN-AC-38; critério 5 de U5 |
| **RN-S-50** | **O agente lê JSON compacto.** Sucesso: `{"ok": true, …}`. Falha: `{"ok": false, "motivo": …, "detalhe": {…}}`, com `erro = True`. Texto com acento sai como acento. **Emenda 2026-10-13 (Code Generation, R-CG6-1): a única exceção é o argumento recusado pelo esquema no SDK (A16), que nunca chega ao catálogo: nesse caso raro, o agente lê o texto de erro do próprio SDK, marcado como erro, e tenta de novo. Ferramenta interrompida pelo ESC responde `{"ok":false,"motivo":"interrompida"}` (N4)** | Q10=A; herança 4 de U5 |
| **RN-S-51** | **A projeção não tem id** e cobre os 5 tipos de `dado` das 6 ações (`domain-entities.md` §4.4). Um `dado` de tipo desconhecido vira `{"ok": true}` e um aviso no log | Q10=A; G12 |

## 8. Isolamento e credencial

| # | Regra | Origem |
|---|---|---|
| **RN-S-52** | **O processo do agente não recebe variáveis que fazem o CLI usar outra credencial ou outro endereço**: chave de API, token, URL base, provedores alternativos. O adaptador não lê o valor; só deixa de repassar. A sessão roda sempre pela assinatura. A lista exata é conferida contra a documentação da versão travada no Code Generation | Q13=A; US-02; FOR-09; SECURITY-12 |
| **RN-S-53** | **O adaptador nunca lê, guarda nem registra credencial.** A autenticação é toda do CLI | SECURITY-12 |

## 9. Log

| # | Regra | Origem |
|---|---|---|
| **RN-S-54** | **O log `fishingrod.sessao` leva só metadados**: abrir, conectar, fechar, encerrar; nome do agente e id da sessão; nome da ferramenta pedida ou negada; categoria da falha; duração do turno. **Nunca** o texto das mensagens, os argumentos das ferramentas ou credencial. A saída de erro do CLI só em nível DEBUG. O destino do log é de U9 | SECURITY-03 |
