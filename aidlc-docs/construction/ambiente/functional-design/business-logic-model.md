# Business Logic Model — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Regras:** `business-rules.md` (`RN-A-01..26`) · **Tipos:** `domain-entities.md`

Pseudocódigo independente de tecnologia: descreve sequência e responsabilidade, não implementação.

---

## 1. Os dois auxiliares internos

Toda operação passa por um destes dois caminhos. É o que deixa as regras de falha e de conflito
num lugar só, em vez de repetidas dez vezes.

### 1.1 `abrir(id_ambiente)`, chamado já com a trava do ambiente

```
se id_ambiente está nos abertos:
    devolve o objeto aberto                          # RN-A-03: não relê o disco
ambiente = persistencia.carregar_ambiente(id_ambiente)
se ambiente é None:
    levanta AmbienteInexistente(id_ambiente)         # RN-A-05
guarda nos abertos e devolve
```

### 1.2 `mutar(id_ambiente, intencao)`: o caminho de toda operação de estrutura

`intencao` é uma função `Ambiente -> T` que acha o alvo, chama o domínio e devolve o objeto
criado ou alterado. Ela **não** faz I/O.

```
com a trava de id_ambiente:                          # RN-A-06
    ambiente = abrir(id_ambiente)
    para tentativa em 1..3:                          # RN-A-11
        resultado = intencao(ambiente)               # RN-A-02 / RN-A-08: erro aqui = nada gravado
        tente:
            persistencia.salvar_ambiente(ambiente)   # RN-A-07
            devolve resultado
        se ConflitoDeVersao:
            recarregar(ambiente)                     # RN-A-10
            se tentativa == 3: levanta ConflitoDeVersao
            (volta ao laço: reaplica a intenção no estado novo)
        se qualquer outro erro:
            recarregar(ambiente)                     # RN-A-09
            levanta o erro original
```

**`recarregar(ambiente)`**: lê da porta e copia o estado lido para dentro do **mesmo** objeto
(RN-A-03). Se a porta devolver `None`, fecha o ambiente e levanta `AmbienteInexistente`
(RN-A-12). Se a leitura falhar, fecha o ambiente (RN-A-09) e deixa o erro original seguir.

> **Por que a intenção roda antes do `try`.** Um erro do domínio, como nome vazio ou alvo
> inexistente, aparece antes de qualquer escrita. Como o domínio valida antes de mudar o objeto,
> esse erro não deixa mudança pela metade, e não há nada a recarregar.

---

## 2. Ciclo do ambiente

### 2.1 `criar_ambiente(nome, esquema)` (RN-A-13..16)

```
ambiente = Ambiente(nome)                            # valida o nome; gera id e raiz_wiki
proposta = PropostaWiki(
    entidades_novas = títulos das entidades do esquema,
    paginas = uma PaginaProposta(entidade, titulo, descricao, conteudo="")
              por propriedade de cada entidade,
)
wiki.escrever_proposta(ambiente.raiz_wiki.localizador, proposta)   # valida tudo antes de escrever
wiki.renderizar_index(ambiente.raiz_wiki.localizador, ambiente.nome)
persistencia.salvar_ambiente(ambiente)               # versao 0 -> 1
guarda nos abertos e devolve ambiente
```

Não usa trava: o id é novo e ninguém mais o conhece até a última linha. Não pode haver
`ConflitoDeVersao`, porque nenhum outro processo tem esse id.

| Falha em | Estado resultante | Erro para quem chamou |
|---|---|---|
| `Ambiente(nome)` | nada tocado | `NomeInvalido` |
| validação de `escrever_proposta` | nada tocado | `TituloInvalido` / `DescricaoObrigatoria` |
| I/O no meio de `escrever_proposta` ou em `renderizar_index` | pasta parcial órfã; banco intacto | `ErroDeWiki` |
| `salvar_ambiente` | wiki completa órfã; banco intacto | `ErroDePersistencia` |

### 2.2 `carregar_ambiente(id_ambiente)`

`abrir`, com a trava do ambiente. Devolve o objeto aberto ou levanta `AmbienteInexistente`.

### 2.3 `listar_ambientes()`

Repassa `persistencia.listar_ambientes()`, sem trava e sem abrir nada (RN-A-20).

### 2.4 `apagar_ambiente(id_ambiente)` (RN-A-17, RN-A-18)

```
com a trava de id_ambiente:
    ambiente = abrir(id_ambiente)                    # AmbienteInexistente se não houver
    persistencia.apagar_ambiente(id_ambiente)        # se falhar: erro sobe, nada mudou
    remove dos abertos
    tente:
        wiki.apagar(ambiente.raiz_wiki.localizador)
    se ErroDeWiki:
        registra WARNING em "fishingrod.ambiente" (id, tipo do erro; sem caminho)
```

---

## 3. Estrutura (todas por `mutar`)

| Operação | Intenção aplicada ao `ambiente` |
|---|---|
| `criar_frente(id_ambiente, nome)` | `ambiente.criar_frente(nome)` |
| `criar_tarefa(id_ambiente, id_frente, nome)` | `achar_frente(id_frente).criar_tarefa(nome, self.orquestrador)` |
| `criar_chat(id_ambiente, id_tarefa, nome_agente, nome="")` | `agente = resolver(nome_agente)` (senão `AgenteDesconhecido`); `achar_tarefa(id_tarefa).criar_chat(agente, nome)` |
| `criar_etapa(id_ambiente, id_tarefa, descricao, executor)` | `achar_tarefa(id_tarefa).criar_etapa(descricao, executor)` |
| `concluir_etapa(id_ambiente, id_etapa)` | `etapa = achar_etapa(id_etapa); etapa.concluir(); devolve etapa` |

- `achar_frente` usa `Ambiente.buscar_frente`; `achar_tarefa` e `achar_etapa` percorrem as frentes
  e as tarefas do ambiente com os `buscar_*` do domínio. O `None` do domínio vira
  `FrenteInexistente`, `TarefaInexistente` ou `EtapaInexistente` (RN-A-08).
- `resolver(nome_agente)` é feito **dentro** da intenção, para que um nome desconhecido falhe antes
  de qualquer escrita, como os outros erros de validação.

---

## 4. Memória: `anotar_memoria(id_ambiente, id_tarefa, chave, valor, autor)` (RN-A-25)

Não passa por `mutar`, porque não salva o documento.

```
com a trava de id_ambiente:
    ambiente = abrir(id_ambiente)
    tarefa = achar_tarefa(id_tarefa)                 # TarefaInexistente
    anotacao = tarefa.memoria.anotar(chave, valor, autor)   # valida chave e autor
    tente:
        persistencia.anotar(id_ambiente, id_tarefa, chave, anotacao)
    se qualquer erro:
        recarregar(ambiente)                         # RN-A-09: a anotação some da memória
        levanta o erro original
    devolve anotacao
```

---

## 5. Propriedades `PBT-U4-nn`

`property-based-testing` está em modo **Full**. A especificação das estratégias `hypothesis` fica
para o Code Generation, porque NFR Requirements e NFR Design são SKIP nesta unidade.

| # | Propriedade | Regras |
|---|---|---|
| **PBT-U4-01** | **Memória ≡ disco.** Para qualquer sequência das 10 operações (com alvos válidos e inválidos), depois de cada passo o ambiente aberto é igual ao que um serviço **novo**, sobre a mesma porta, carrega | RN-A-03, RN-A-07, RN-A-09; **fecha US-05** |
| **PBT-U4-02** | **Conflito não perde mudança.** Com um segundo serviço sobre a mesma porta (o "outro processo") gravando entre as operações do primeiro, toda operação que retorna com sucesso tem o seu efeito no disco, junto com o efeito do outro | RN-A-10, RN-A-11 |
| **PBT-U4-03** | **A wiki nasce igual ao esquema.** Para qualquer `EsquemaWiki` aceito, `PortaWiki.listar` devolve exatamente os slugs das entidades e, em cada uma, os slugs das propriedades; o índice existe mesmo com esquema vazio | RN-A-13, RN-A-14; US-08, US-09 |
| **PBT-U4-04** | **Isolamento entre ambientes.** Para quaisquer dois ambientes e qualquer sequência de operações em um deles, o outro carregado do disco não muda | RN-A-06, RN-A-08; critério 4 |
| **PBT-U4-05** | **Falha não deixa rastro na memória.** Com uma porta que falha no ponto sorteado, depois do erro o ambiente aberto é igual ao do disco | RN-A-09, RN-A-16 |

Testes de exemplo cobrem o restante, sem propriedade própria: ordem das portas em criar e apagar
(RN-A-14, RN-A-17), o `WARNING` de RN-A-18, `AgenteDesconhecido`, a construção do serviço com
agentes inválidos e a trava sob duas corrotinas concorrentes (RN-A-06).

---

## 6. Rastreio

| Origem | Onde se cumpre |
|---|---|
| **US-04** anotar sem erro, sem perder a anterior | §4, RN-A-25 (TD-03 já morta em U1) |
| **US-05** estrutura sobrevive a fechar e reabrir — **U4 fecha esta história** | RN-A-07, PBT-U4-01 |
| **US-08** todo ambiente nasce com wiki, mesmo vazia | §2.1, RN-A-13/14, PBT-U4-03 |
| **US-09** a estrutura da wiki é do dono | §2.1: o esquema vem de quem chama; nenhuma entidade fixa |
| **US-15** criar frente | §3 |
| **US-16** criar tarefa, pronta para etapas e conversa | §3, RN-A-21 |
| **US-17** etapas descobertas conversando (a parte de gravar) | `criar_etapa` (C1=A) |
| **US-19** concluir etapa feita pelo usuário | `concluir_etapa`, RN-A-23 (C1=A) |
| Critérios de pronto 1–6 de U4 | 1 → §2.1 · 2 → RN-A-02 · 3 → RN-A-01 · 4 → PBT-U4-04 · 5 → RN-A-10/11, PBT-U4-02 · 6 → §2.4 |

---

## 7. Decisões tomadas nesta geração (para revisão no portão)

| # | Decisão | Por quê |
|---|---|---|
| G1 | **RN-A-18**: falha ao apagar a wiki, depois do banco, vira `WARNING`, não erro | O ambiente já não existe quando a wiki falha. Levantar erro faria a tela dizer "não foi possível apagar" sobre algo que sumiu da lista. A pasta órfã tem o mesmo status que a de RN-A-16 |
| G2 | **RN-A-03**: a recarga atualiza o **mesmo** objeto `Ambiente` em vez de trocá-lo | Sem isso, a Q1=A ("um objeto só") quebraria no primeiro conflito: a tela ficaria segurando o objeto antigo |
| G3 | **RN-A-22**: a lista `agentes_de_chat` não pode conter orquestrador | Deixa "segundo orquestrador" e "agente fora da lista" no mesmo erro, `AgenteDesconhecido`, sem depender de o domínio pegar o caso depois |
| G4 | `concluir_etapa(id_ambiente, id_etapa)` sem `id_tarefa` | O alvo imediato é a etapa (Q2=A), e a identidade é única no ambiente. Pedir também a tarefa obrigaria a tela a carregar um id que não muda nada |
| G5 | Os erros novos ficam numa raiz própria, `ErroDeServicoDeAmbiente`, e não sob `ErroDeDominio` | Não achar um alvo não é violação de invariante: no domínio, isso é `None` (RN-14). Quem decide que o alvo era obrigatório é o serviço |

---

## 8. Emendas a artefatos aprovados (texto riscado, nada apagado)

| Artefato | Emenda | Origem |
|---|---|---|
| `inception/application-design/services.md` §2 | Passo 5: ~~frente padrão~~ — o ambiente nasce sem frente. Passos 6–8: ordem invertida, **wiki antes do banco** | R-FD4-1, Q5=A |
| `inception/application-design/component-methods.md` §3.1 | Assinaturas novas das 10 operações; ~~"levanta erro se esquema sem entidade"~~; ~~`-> Resultado`~~ (Q3=A) | R-FD4-2, R-FD4-4, R-FD4-5, Q2, Q3, Q7, Q8, C1 |
| `inception/application-design/component-methods.md` §4.3 | `PortaWiki` ganha `apagar(localizador)` | Q6=A |
| `inception/application-design/components.md` §3.3 | ~~invariante: ao menos uma entidade~~; lista de operações | R-FD4-2, Q7, C1 |
| `inception/application-design/unit-of-work.md` §3 (U4) | Histórias: 5 → 7 (US-04, US-19); critério 6 cumprido por `PortaWiki.apagar`; U3 reaberta para essa operação | R-FD4-3, Q6=A |

---

## 9. Conformidade das extensões

| Extensão | Estado | Rationale |
|---|:--:|---|
| **`security-baseline`** | ✅ | SECURITY-05 (confinamento): a nova `apagar` usa o mesmo `resolver_raiz` de U3, e U4 nunca monta caminho (RN-A-01). SECURITY-13 (integridade): RN-A-09, RN-A-16 e RN-A-17 garantem que memória e disco não divergem e que nunca existe ambiente apontando para wiki inexistente. SECURITY-15 (falha segura): erros tipados, nenhum engolido além do declarado em RN-A-18, mensagens sem caminho. Escalonamento de privilégio na criação de chat fechado por RN-A-22. Demais regras (HTTP, rede, IAM, CORS): **N/A**, porque não há rede nem servidor |
| **`property-based-testing` (Full)** | ✅ | 5 propriedades nomeadas (§5), com a regra que cada uma protege. Estratégias ficam para o Code Generation, por NFR-R/NFR-D serem SKIP |
| **`resiliency-baseline`** | **N/A** | Desativada em Requirements Analysis. A nova tentativa em conflito (RN-A-11) é controle de concorrência otimista local, não resiliência distribuída |
