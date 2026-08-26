# Units of Work — Mapa história → unidade

**Estágio:** INCEPTION — Units Generation, Parte 2 · **Data:** 2026-08-25
**Base:** `stories.md` (linha fina, 14 histórias), `unit-of-work.md` (10 unidades)

---

## 1. Como ler este mapa

Q2=A escolheu decomposição **horizontal**, então quase nenhuma história vive em uma unidade só —
cada uma atravessa camadas. A coluna **unidade que fecha** diz qual é a última unidade a entregar:
enquanto ela não fechar, a história não está pronta, mesmo que todas as outras estejam.

Nas 14 histórias, a unidade que fecha é `U9` em 13 delas — consequência direta da decomposição
horizontal, não escolha por história.

---

## 2. Mapa completo — 14/14 histórias

| História | Unidades envolvidas | Unidade que fecha |
|---|---|---|
| **US-01** — Conversar com um agente real dentro de uma tarefa | U6, U7, U9 | U9 |
| **US-02** — Sessão autenticada por assinatura, sem API key | U6, U9 | U9 |
| **US-03** — Falha do provedor não derruba a interface | U6, U7, U9 | U9 |
| **US-04** — Anotar informação na memória da tarefa sem erro | U1 (TD-03), U4, U5, U9 | U9 |
| **US-05** — A estrutura sobrevive a fechar e reabrir | U1, U2, U4 | **U4** |
| **US-06** — Transcrição antiga continua visível ao reabrir | U2, U7, U9 | U9 |
| **US-08** — Todo ambiente novo nasce com uma wiki | U3, U4, U9 | U9 |
| **US-09** — A estrutura da wiki é definida pelo dono | U3 (`EsquemaWiki`), U4, U9 (formulário) | U9 |
| **US-13** — Promover conteúdo à wiki pelo bibliotecário | U3, U6, U8, U9 | U9 |
| **US-14** — Revisar antes de o bibliotecário escrever | U8, U9 | U9 |
| **US-15** — Criar uma frente dentro do ambiente | U1, U4, U5, U9 | U9 |
| **US-16** — Criar uma tarefa dentro de uma frente | U1, U4, U5, U9 | U9 |
| **US-17** — Descobrir as etapas conversando com o orquestrador | U5, U6, U7, U9 | U9 |
| **US-19** — Executar uma tarefa através de um chat com agente | U4, U5, U7, U9 | U9 |

**Verificação obrigatória**: 14/14 histórias da linha fina têm pelo menos uma unidade. Nenhuma
unidade ficou sem história, **com uma exceção declarada**: `U0` (`fundacao`), que é infraestrutura de
build e não sustenta história nenhuma — é o que Q3=C decidiu ao tirá-la do loop de unidades.

---

## 3. Mapa inverso — unidade → histórias

| Unidade | Histórias |
|---|---|
| U0 `fundacao` | **nenhuma** (infraestrutura de build) |
| U1 `dominio` | US-04, US-05, US-15, US-16 |
| U2 `persistencia` | US-05, US-06 |
| U3 `wiki` | US-08, US-09, US-13 |
| U4 `ambiente` | US-04, US-05, US-08, US-09, US-15, US-16, US-19 |
| U5 `acoes` | US-04, US-15, US-16, US-17, US-19 |
| U6 `sessao` | US-01, US-02, US-03, US-13, US-17 |
| U7 `conversa` | US-01, US-03, US-06, US-17, US-19 |
| U8 `bibliotecario` | US-13, US-14 |
| U9 `interface` | as 14 |

---

## 4. Escopo **sem história de origem** — declarado, não camuflado

A aprovação de ação por agente **não vem de nenhuma das 14 histórias da linha fina**. É decisão de
produto tomada durante Units Generation. Registro assim, em vez de anexá-la a US-17 ou US-19, porque
atribuí-la a uma história daria a impressão falsa de que alguém já tinha pedido — e no próximo
estágio ninguém saberia mais distinguir.

**Rodada 4 (2026-08-25) — o usuário retirou o parâmetro configurável desta iteração.** O que sobra é
menor e mais barato: uma política constante, sem estado e sem tela de configuração.

| Parte | Unidade | O que é |
|---|---|---|
| ~~O campo `aprovacao_de_agente_obrigatoria` em `Ambiente`, padrão ligado~~ → `dominio/politica.py`: constante `APROVACAO_DE_AGENTE_OBRIGATORIA = True` + `exige_aprovacao(...)` | **U1** | ~~dado~~ código, sem estado |
| ~~Compatibilidade com `Ambiente` salvo antes do campo existir~~ **removido** | ~~**U2**~~ | — |
| Ponto de consulta antes de executar ferramenta acionada por agente | **U5** e **U8** | regra |
| Fluxo de confirmação na tela ~~+ tela para desligar o parâmetro~~ | **U9** | interface — **mas já exigido por US-14**, então deixa de ser escopo sem origem |

**Consequência de rastreabilidade**: depois da rodada 4, o único item verdadeiramente sem história de
origem é a **política em si** (`U1`, algumas linhas) e o fato de as ferramentas de ambiente do
orquestrador passarem pelo fluxo (`U5`). O fluxo de confirmação da `U9` sai desta lista, porque
US-14 o pede diretamente.

**Mesma classificação, mesmo tratamento**: a tela de início que lista e cria ambientes locais (Q10=B)
também não vem de história da linha fina — vem do ponto 2 da §7 de `application-design.md`. Fica em
**U9**.

---

## 5. Histórias adiadas e fora de escopo — sem unidade, de propósito

| História | Situação | Se voltar, entra em |
|---|---|---|
| US-07 — retomar conversa com continuidade de memória do agente | ADIADA v2 | U6, U7 |
| US-10 — criar categoria da wiki conversando | ADIADA v2 | U8 |
| US-11 / US-12 — rod-maker e escolha de agente | ADIADA v2 | U6 (novo `Agente`), U9 |
| US-18 — reaproveitar tarefa feita antes | ADIADA v2 | U4, U5 |
| US-20 a US-23 | FORA DE ESCOPO (multiusuário, contrato consome/entrega) | não previsto nesta arquitetura |

A coluna "se voltar" é indicativa, não compromisso — serve para a próxima iteração saber onde olhar.

**Nota sobre US-10 e o ponto 1 da §7**: você decidiu incluir `propor_entidade` mesmo com US-10
adiada. Não há contradição — a ferramenta existe em **U8**, e o que continua adiado é a *conversa
guiada* que a US-10 descreve. A ferramenta é o mecanismo; a história era a experiência em volta dele.

---

## 6. Dívidas técnicas → unidade

| Dívida | Unidade | Critério que a mata |
|---|---|---|
| TD-01 — `responder()` devolve `None` | **U6** | Contrato da porta exige resposta não vazia; falso e real passam pelo mesmo teste |
| TD-02 — SDK importado no núcleo | **U6** | Importar `dominio/` e `aplicacao/` com o SDK desinstalado |
| TD-03 — `Memoria.anotar()` lança `KeyError` | **U1** | Anotar em chave nova funciona, com propriedade PBT |
| TD-04 — persistência inexistente | **U2** | CS-01: fechar e reabrir reconstitui o ambiente |
| TD-11 — argumento com espaço quebra comando | **U5** | `/nova-tarefa campanha de verao` interpreta o argumento inteiro |

5/5 com unidade dona e critério verificável.
