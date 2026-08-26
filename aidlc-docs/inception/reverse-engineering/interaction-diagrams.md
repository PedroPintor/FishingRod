# Interaction Diagrams — FishingRod

**Data da análise**: 2026-08-16
**Propósito**: mostrar como cada transação de negócio é implementada **através** dos componentes.

---

## BT-02 — Criar um Projeto (frente)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant T as tui.py
    participant A as Ambiente
    participant P as Projeto
    participant S as Sessao

    U->>T: "/novo-projeto marketing"
    T->>T: guarda posicao e tamanhos ANTES
    T->>A: enviar("/novo-projeto marketing")
    A->>A: _detectar_comando_ambiente -> sim
    A->>A: criar_projeto("marketing")
    A->>P: Projeto(nome="marketing")
    P->>P: __post_init__ cria sessao padrao
    P->>S: Sessao(chats=[Chat(OrquestradorTeste)], memoria=Memoria())
    S-->>P: ok
    P-->>A: instancia
    A-->>T: [Mensagem(autor="comando", tipo="sistema")]
    T->>T: tamanhos mudaram -> recarrega sidebar
    T->>A: obter_status()
    A-->>T: status composto
    T-->>U: "Projeto [marketing] criado" + sidebar atualizada
```

**Observação de desenho**: criar projeto **não** troca o projeto ativo. O usuário fica onde
estava — decisão coerente com a cadeia, mas que a interface precisa deixar visível.

---

## BT-04 / BT-05 — Abrir um chat com um sub-agente

```mermaid
sequenceDiagram
    participant U as Usuario
    participant A as Ambiente
    participant P as Projeto
    participant S as Sessao
    participant CAT as AgenteDoSistema

    U->>A: "/novo-chat rod-maker"
    A->>A: e meu? nao
    A->>P: enviar
    P->>P: e meu? nao
    P->>S: enviar
    S->>S: comeca com barra -> e meu
    S->>CAT: buscar_agente("rod-maker")
    CAT-->>S: RodMakerTeste (instancia GLOBAL)
    S->>S: criar_chat -> papel e SUB_AGENTE, invariante nao se aplica
    S-->>U: "Novo chat criado: [1] rod-maker"
```

**⚠️ Ponto de atenção**: `buscar_agente` consulta o **catálogo global do módulo**, não uma
coleção da sessão. Duas sessões que abram chat com `rod-maker` compartilham a **mesma instância**
de agente.

---

## BT-06 — Conversar com um agente (o caminho que hoje é stub)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Sessao
    participant C as Chat
    participant G as AgenteTeste

    U->>S: "como esta o plano?"
    S->>S: nao comeca com barra
    S->>S: monta Mensagem(usuario)
    S->>C: le chat ativo
    S->>G: responder("como esta o plano?")
    G-->>S: string fixa de teste
    S->>S: monta Mensagem(agente) com autor = caixa_de_texto
    S->>C: mensagens.extend(as duas)
    S->>C: adicionar_iteracao()
    S-->>U: [Mensagem(usuario), Mensagem(agente)]
```

**Onde a implementação real entra**: substituir `AgenteTeste` por um adaptador que fale a porta
de sessão viva (`abrir` / `enviar` / `fechar`). Hoje `responder()` é **síncrono e sem estado** —
a assinatura atual não comporta sessão viva.

---

## BT-08 — Anotar no blackboard (modelado, sem caminho de uso)

```mermaid
sequenceDiagram
    participant G as Agente
    participant TOOL as Ferramenta fabricada
    participant M as Memoria

    Note over G,TOOL: caminho VALIDADO no spike, NAO ligado ao nucleo
    G->>TOOL: anotar(chave, valor)
    Note over TOOL: autor vem da CLOSURE,<br/>nao e parametro da tool
    TOOL->>M: anotacoes[chave].append(Anotacao(autor, valor))
    M->>M: versao += 1
    M-->>TOOL: True
    TOOL-->>G: "Anotado no quadro branco"
```

**Estado real**: nenhum código de produção chama `Memoria.anotar()`. A `Sessao` cria a `Memoria`
e a expõe no status, mas não fabrica ferramenta nenhuma. O spike provou que dá para fazer; o
núcleo ainda não faz.

**⚠️ Defeito**: `Memoria.anotar()` levanta `KeyError` na primeira anotação de qualquer chave —
`self.anotacoes[chave].append(...)` sem `setdefault`.

---

## BT-07 — Consultar status (composição subindo a cadeia)

```mermaid
sequenceDiagram
    participant T as Interface
    participant A as Ambiente
    participant P as Projeto
    participant S as Sessao
    participant C as Chat
    participant M as Memoria

    T->>A: obter_status()
    A->>P: obter_status()
    P->>S: obter_status()
    S->>C: le nome e iteracoes
    S->>M: le anotacoes
    S-->>P: nome_sessao, n_iteracoes, nome_chat, memoria
    P-->>A: + nome_projeto
    A-->>T: + nome_ambiente
    T-->>T: pinta a barra com o caminho completo
```

---

## BT-10 — Conversar com LLM real (**não implementada**)

```mermaid
flowchart LR
    S["Sessao.enviar<br/>sincrono"] --> G["AgenteClaude.responder"]
    G --> R["return nu<br/>devolve None"]
    R --> X["Mensagem.texto = None<br/>quebra a pintura"]
```

**Alternativa em texto**: `Sessao.enviar` chama `AgenteClaude.responder()`, que devolve `None`;
`Mensagem` recebe `texto=None`; `tui.formatar` chama `escape(None)` e falha. Ligar o
`AgenteClaude` hoje, sem mais mudanças, quebra a aplicação.

**O que falta para esta transação existir**:
1. `responder()` precisa virar assíncrono (o SDK é `async`) — hoje toda a cadeia `enviar()` é
   síncrona, do `input()` até o `Chat`.
2. Separar **definição de agente** (dados reusáveis) de **client vivo** (conexão com estado).
3. Definir a porta de sessão viva (`abrir` / `enviar` / `fechar`) e confinar os tipos do SDK ao
   adaptador — hoje `agente.py:6` importa `ClaudeAgentOptions` no núcleo.
