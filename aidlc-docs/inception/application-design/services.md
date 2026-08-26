# Application Design — Serviços e Orquestração

**Estágio:** INCEPTION — Application Design · **Profundidade:** comprehensive
**Data:** 2026-08-25 · **Base:** `components.md`, `component-methods.md`, `application-design-plan.md`

> Este documento descreve **como os serviços de aplicação orquestram** domínio, portas e
> adaptadores para cada fluxo relevante — ciclo de conversa, criação de ambiente com wiki
> semeada, promoção à wiki com revisão, carregar/salvar. Não repete assinaturas (ver
> `component-methods.md`); foca em sequência e responsabilidade de cada passo.

---

## 1. Padrão geral de orquestração

Todos os serviços de aplicação seguem a mesma forma, decidida nas Perguntas 1B, 7B e 11A:

1. A interface (TUI) nunca chama domínio ou adaptador diretamente — só serviços de aplicação e o
   `CatalogoDeAcoes`.
2. Um serviço recebe uma chamada (ação do catálogo, ou `enviar` de conversa), resolve o(s) objeto(s)
   de domínio envolvidos via `PortaPersistencia`, aciona a invariante no domínio, e persiste o
   resultado — tudo numa única unidade de trabalho por operação (Pergunta A/8B: "transação por
   operação").
3. Nenhum serviço constrói um adaptador. Todos recebem porta já pronta pelo composition root
   (Pergunta 11A).
4. Erros de infraestrutura (provedor de LLM fora do ar, disco cheio) são convertidos em
   `Resultado`/`EventoConversa` de erro na fronteira do serviço — nunca atravessam como exceção
   crua para a TUI (RNF-06, US-03).

---

## 2. Ciclo de criação de ambiente com wiki semeada

**Serviço**: `ServicoDeAmbiente.criar_ambiente`
**Histórias**: US-08, US-09 · **Rastreio**: RF-F07, RF-F08, RF-F15, ESC-07, ESC-19, RNF-09

### Sequência

1. TUI apresenta a tela de criação de ambiente (US-09): usuário escolhe uma maquete embutida
   (Pergunta C/16B) **ou** preenche o formulário com entidades/propriedades.
2. TUI monta um `EsquemaWiki`:
   - via `EsquemaWiki.carregar_toml(caminho)` se maquete escolhida;
   - via `EsquemaWiki.a_partir_do_formulario(dados)` se formulário preenchido.
3. TUI chama `ServicoDeAmbiente.criar_ambiente(nome, esquema)`.
4. O serviço valida a invariante de criação (ao menos uma entidade — Pergunta 16B). Se falhar,
   devolve `Resultado` de erro sem tocar nenhum substrato.
5. O serviço cria `Ambiente` de domínio com `Identidade.nova()`, uma `Frente` padrão (mantém
   paridade com o comportamento atual de nascer com um projeto/frente default) e um `RaizWiki` com
   localizador `dados:wikis/<id_ambiente>` (Pergunta D).
6. O serviço persiste o documento do ambiente via `PortaPersistencia.salvar_ambiente` (transação
   única).
7. O serviço chama `PortaWiki` (via `AdaptadorWikiFilesystem`) para **materializar a wiki**:
   cria uma pasta por entidade do esquema, e para cada propriedade da semente, cria a página com o
   frontmatter `descricao` (Pergunta 15D) e conteúdo inicial vazio ou o texto da maquete.
   - **Nota de decisão explícita (reconciliação §5.3 do plano)**: esta materialização **não** é
     proposta do bibliotecário. É ação do sistema a partir do esquema aprovado na tela de criação.
     O regime "toda escrita é proposta" (9A/13A) vale para o bibliotecário, não para o sistema
     semeando a partir de uma escolha que o próprio usuário acabou de fazer.
8. O serviço chama `PortaWiki.renderizar_index` para produzir o `index.md` inicial.
9. O serviço devolve `Ambiente` pronto para a TUI abrir.

### Diagrama de sequência (texto)

```
TUI → ServicoDeAmbiente.criar_ambiente(nome, esquema)
    ServicoDeAmbiente → Ambiente.criar_frente(default)      [domínio]
    ServicoDeAmbiente → PortaPersistencia.salvar_ambiente    [SQLite]
    ServicoDeAmbiente → PortaWiki.escrever (materialização)  [filesystem]
    ServicoDeAmbiente → PortaWiki.renderizar_index           [filesystem]
    ServicoDeAmbiente → TUI: Ambiente pronto
```

---

## 3. Ciclo de conversa (US-01, US-02, US-03, US-06, US-19)

**Serviço**: `ServicoConversa.enviar`
**Rastreio**: RF-F01, RF-F03, RF-F05 (transcrição), RNF-06, ESC-01, ESC-18

### Sequência (turno de conversa em um chat)

1. Usuário digita texto sem `/` numa aba. TUI chama `ServicoConversa.enviar(id_chat, mensagem)`.
2. O serviço resolve a `SessaoViva` do chat: se já existe (mapeamento `chat.id → SessaoViva`
   mantido pelo serviço, não pelo domínio — Pergunta 6A), reusa; senão, chama
   `PortaSessao.abrir(agente)`.
3. O serviço grava a mensagem do usuário via `PortaPersistencia.inserir_mensagem(papel="usuario",
   em_andamento=False)` — mensagem de usuário não tem streaming, é atômica.
4. O serviço grava uma linha para a mensagem do agente com `em_andamento=True` (Pergunta A/8B:
   *"a mensagem do agente é inserida no começo do turno e atualizada conforme o streaming
   avança"*).
5. O serviço chama `PortaSessao.enviar(sessao, mensagem)` e itera o `AsyncIterator[EventoConversa]`
   resultante:
   - **pedaço de texto** → concatena ao acumulado e chama
     `PortaPersistencia.atualizar_mensagem(id_mensagem, texto_acumulado, em_andamento=True)`;
     ao mesmo tempo, repassa o pedaço para a TUI renderizar incrementalmente (streaming visível ao
     usuário — Pergunta 5B);
   - **uso de ferramenta** → chama
     `PortaPersistencia.registrar_uso_ferramenta(id_mensagem, tool, args_resumo, resultado_resumo)`
     (Pergunta F/B: registra tool + parâmetros resumidos + resultado resumido, não o payload
     completo nem o stream de tokens parciais);
   - **fim de turno** → chama `PortaPersistencia.atualizar_mensagem(id_mensagem, texto_final,
     em_andamento=False)`, removendo a marca de "em andamento" (Pergunta A/8B: *"queda no meio
     preserva o que já chegou; o carregamento distingue turno interrompido de turno completo"*);
   - **erro de provedor** → o serviço encerra o iterador com um evento de erro; a mensagem em
     andamento permanece marcada como tal no banco (não é promovida a completa); a TUI mostra
     aviso na aba, sem afetar outras abas (US-03).
6. O serviço devolve controle à TUI ao final do iterador.

### Reabertura de aba antiga (US-06)

1. TUI chama `ServicoConversa.carregar_transcricao(id_chat, limite)`.
2. O serviço lê via `PortaPersistencia.listar_mensagens`, ordenado por identidade (UUIDv7 —
   ordenação cronológica sem coluna extra, Pergunta 4B).
3. Mensagens com `em_andamento=True` remanescentes de uma queda são exibidas como "turno
   interrompido" (marcação visível, não erro) — decisão embutida na política de gravação A/8B.

### Ciclo de conversa do bibliotecário (US-13, US-14) — mesma porta, sessão separada

1. `ServicoBibliotecario` abre a própria `SessaoViva` via `PortaSessao.abrir(agente_bibliotecario)`
   — sessão distinta da do orquestrador, suportada pelo spike (dois clients simultâneos no mesmo
   event loop).
2. O usuário aciona o bibliotecário (via ação do orquestrador ou diretamente) para promover
   conteúdo (US-13). `ServicoBibliotecario.enviar(mensagem)` segue o mesmo padrão de streaming do
   item acima, mas os eventos de "uso de ferramenta" aqui são chamadas a `propor_entidade`/
   `propor_propriedade`.
3. Cada chamada de proposta gera uma `PropostaWiki` guardada em memória/tabela de propostas
   pendentes (não persistida como transcrição de wiki — é estado transitório de aprovação).
4. TUI lista `propostas_pendentes()` e apresenta o conteúdo final para revisão (US-14, critério de
   aceite: "vejo o texto final e posso aprovar ou pedir ajuste antes da escrita se efetivar").
5. Usuário aprova → `ServicoBibliotecario.aprovar(id_proposta)` → ver §4.
   Usuário pede ajuste → nova mensagem ao bibliotecário; a proposta antiga é substituída, nunca
   promovida (US-14, segundo critério: "a versão anterior não é salva").

---

## 4. Ciclo de promoção à wiki com revisão (US-13, US-14)

**Serviço**: `ServicoBibliotecario.aprovar`
**Rastreio**: RF-F10, RF-F14, RNF-10, RNF-14, ESC-08, ESC-20

### Sequência

1. `ServicoBibliotecario.aprovar(id_proposta)` recupera a `PropostaWiki` pendente (pode conter
   várias páginas — reconciliação do plano §5.4, para que aprovar seja um ato por promoção).
2. Para cada página da proposta, o serviço valida os links `[[...]]` contra `PortaWiki.listar`/
   `ler` (Pergunta 14B):
   - se todo link resolve para página existente ou para outra página da mesma proposta, segue;
   - se um link aponta para página inexistente fora da proposta, a escrita dessa página é
     recusada, **ou** (dependendo da configuração da tool) o próprio link pendente é convertido em
     proposta de criação da página de destino, incorporada à mesma promoção.
3. O serviço chama `PortaWiki.escrever_proposta(localizador, proposta)` — que, dentro do
   `AdaptadorWikiFilesystem`, confina cada caminho à raiz da wiki do ambiente (RF-F14/RNF-10) antes
   de qualquer gravação física.
4. Após a escrita, o serviço chama `PortaWiki.renderizar_index(localizador)` — o `index.md` é
   sempre projeção derivada, nunca editado pelo agente (Pergunta 15D).
5. O serviço remove a proposta da lista de pendentes e devolve `Resultado` de sucesso à TUI.
6. Em caso de rejeição (`rejeitar`), nenhum destes passos toca o filesystem — a proposta é apenas
   descartada.

### Diagrama de sequência (texto)

```
TUI → ServicoBibliotecario.aprovar(id_proposta)
    ServicoBibliotecario → validar links (PortaWiki.listar/ler)
    ServicoBibliotecario → PortaWiki.escrever_proposta       [confinamento de caminho aqui]
    ServicoBibliotecario → PortaWiki.renderizar_index
    ServicoBibliotecario → TUI: Resultado(sucesso)
```

---

## 5. Ciclo de carregar/salvar o ambiente (US-05, US-06)

**Serviço**: `ServicoDeAmbiente.carregar_ambiente` / gravação incremental via
`ServicoDeAmbiente`/`ServicoConversa`
**Rastreio**: RF-F05, ESC-05, D-ARQ-04, RNF-05

### Abertura do programa

1. Composition root monta `RepositorioSQLite` com a raiz de dados configurada.
2. TUI (via serviço) chama `carregar_ambiente(id)` — se for a primeira execução, não há ambiente
   e a TUI direciona para o fluxo de criação (§2).
3. `RepositorioSQLite.carregar_ambiente` lê o documento (frentes, tarefas, chats: identidade, nome,
   etapas, agente, memória) e reconstitui os objetos de domínio. A leitura pode usar
   `asyncio.to_thread` internamente para não bloquear o event loop da TUI (Pergunta E1, nota sobre
   `sqlite3`).
4. A transcrição **não** é carregada aqui — cada aba busca sua própria transcrição sob demanda via
   `ServicoConversa.carregar_transcricao` quando o usuário a abre (evita carregar histórico total
   na abertura).

### Gravação incremental (durante o uso)

- Toda operação de estrutura (criar frente/tarefa/chat, concluir etapa, anotar memória) grava ao
  final da própria operação, numa transação — nunca em lote periódico nem por comando explícito
  `/salvar` (Pergunta A/8B, opção B escolhida sobre C/D descartadas na Pergunta 8 original).
- A transcrição grava por linha, conforme o ciclo de conversa (§3) — não pelo documento do
  ambiente.
- **Efeito prático de US-05**: matar o processo no meio de qualquer operação de estrutura nunca
  perde mais do que a própria operação em andamento; matar o processo no meio de um turno de
  conversa perde, no máximo, o texto que ainda não tinha chegado (o já chegado fica marcado como
  "em andamento" e visível na reabertura).

---

## 6. Ciclo de execução de etapa via agente (US-19)

**Serviços envolvidos**: `ServicoDeAmbiente` (etapas) + `ServicoConversa` (execução via chat)
**Rastreio**: RF-F12, RF-F07

### Sequência

1. Uma `Etapa` de uma `Tarefa` tem `executor = AGENTE` ou `executor = USUARIO`.
2. Se `AGENTE`: o usuário aciona o agente correspondente na aba (mesmo ciclo do §3). A conclusão
   da etapa não é automática a partir da resposta do agente nesta iteração — fica para o usuário
   confirmar via ação `concluir_etapa` (paridade com o critério de aceite de US-19 para o caso
   `USUARIO`: "quando confirmo que a fiz, então a etapa é marcada como concluída"). A distinção
   fina de automatizar isso por tipo de etapa é regra de negócio de Functional Design.
3. Se `USUARIO`: `ServicoDeAmbiente.concluir_etapa(id_etapa)`, chamada via `CatalogoDeAcoes`.

**Nota de escopo explícita**: execução dependente de ferramenta MCP externa configurada está fora
desta iteração (stories.md, nota de US-19; requirements.md FOR-04).

---

## 7. Descoberta de etapas conversando com o orquestrador (US-17)

**Serviço**: `ServicoConversa` (mesmo ciclo do §3) + `ServicoDeAmbiente` para persistir etapas
descobertas.

### Sequência

1. Usuário conversa com o orquestrador na aba padrão de uma tarefa nova.
2. O orquestrador, com acesso ao `CatalogoDeAcoes` (ação `criar_etapa`, incluída no catálogo — não
   detalhada em Application Design, cabe em Functional Design a forma exata de o agente acionar
   ações via ferramenta), propõe etapas.
3. Cada etapa proposta e aceita na conversa é persistida via `ServicoDeAmbiente` como `Etapa`
   dentro da `Tarefa`.

**Nota de fronteira com Units Generation**: a forma exata de o orquestrador "chamar" uma ação do
catálogo como ferramenta (schema exposto ao modelo, aprovação de uso) segue o mesmo padrão da
Pergunta 10 (tools próprias, MCP in-process), mas para o catálogo de ações do ambiente em vez da
wiki. Este acoplamento é sinalizado aqui para não ser esquecido em Units Generation/Functional
Design; **não é decidido nesta iteração de Application Design** porque as 14 histórias da linha
fina não exigem que o orquestrador crie etapas de forma autônoma sem revisão — o dono do domínio
(João) frequentemente já chega com o método formado (segundo critério de aceite de US-17).

> **/!\ Emenda 2026-08-25 - Units Generation.** **Este ponto deixou de ser "não decidido".** O usuário respondeu o ponto 5 da §7 de `application-design.md` e Units Generation fechou o desdobramento: mecanismo = **MCP in-process** (Q11=A); a capacidade mora na **unidade de sessão** (Q12=A, R4); o orquestrador **não** recebe ferramentas de wiki e delega criando um chat com o bibliotecário (Q14=X). Consequência para este fluxo: US-17 passa a ser o agente chamando `criar_etapa` como ferramenta de ambiente, e não o usuário digitando `/criar-etapa` depois da conversa — mais fiel à história, e mais escopo. ~~A execução é mediada pelo parâmetro `aprovacao_de_agente_obrigatoria` (CQ2/CQ3), ligado por padrão.~~ **[rodada 4, 2026-08-25]** A execução é mediada pela constante de política `exige_aprovacao(...)` (`dominio/politica.py`), que nesta iteração devolve sempre `True`: o agente propõe, você confirma. O parâmetro configurável foi retirado do escopo pelo usuário; o ponto de consulta permanece exatamente onde estava, para que a configuração futura não exija redesenho.

---

## 8. Tratamento de falha do provedor (US-03) — padrão transversal

**Rastreio**: RNF-06, RNF-15 (isolamento de exceção)

Aplica-se a `ServicoConversa` e `ServicoBibliotecario`, ambos consumidores de `PortaSessao`:

1. `AdaptadorSessaoClaude` converte qualquer exceção do SDK ou falha de rede num tipo de erro
   próprio da aplicação (nunca deixa a exceção do SDK atravessar a porta).
2. O serviço que consome o iterador de `EventoConversa` trata o evento de erro como fim de turno
   com falha — grava o que já tinha chegado como incompleto, não propaga exceção para a TUI.
3. A TUI recebe um evento de erro tipado e o renderiza como aviso **na aba onde ocorreu**,
   preservando as demais abas/tarefas funcionando (segundo critério de aceite de US-03).

---

## 9. Resumo de orquestração — serviço × porta × adaptador

| Serviço | Portas usadas | Adaptadores por trás |
|---|---|---|
| `ServicoDeAmbiente` | `PortaPersistencia`, `PortaWiki` | `RepositorioSQLite`, `AdaptadorWikiFilesystem` |
| `ServicoConversa` | `PortaPersistencia`, `PortaSessao` | `RepositorioSQLite`, `AdaptadorSessaoClaude` |
| `ServicoBibliotecario` | `PortaSessao`, `PortaWiki` | `AdaptadorSessaoClaude` (sessão própria), `AdaptadorWikiFilesystem` (via `FerramentasWiki`) |
| `CatalogoDeAcoes` | nenhuma diretamente — delega a `ServicoDeAmbiente` | — |

Nenhum serviço usa mais de duas portas. Nenhuma porta é usada por um serviço sem que essa relação
esteja listada em `component-dependency.md`.
