# Business Rules — U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 1 de 2 (Functional Design)**
**Data:** 2026-10-02
**Prefixo:** `RN-A-nn`. As regras de U1 (`RN-nn`), U2 (`RN-P-nn`) e U3 (`RN-W-nn`) continuam
valendo; aqui só entra o que é de coordenação.

---

## 1. Fronteira

| # | Regra | Origem |
|---|---|---|
| **RN-A-01** | O serviço conhece **só** domínio e portas. Nenhum `import` de `sqlite3`, `claude_agent_sdk`, `textual`, `os`, `pathlib` ou `shutil` | critério 3; D-ARQ-04; D-ARQ-08 |
| **RN-A-02** | **A invariante é do domínio.** O serviço não repete validação que o domínio já faz (nome vazio, segundo orquestrador, papel do agente). Ele chama o domínio **antes** de qualquer I/O, e o erro do domínio chega a quem chamou sem nada ter sido gravado | critério 2 |

## 2. Estado e identidade

| # | Regra | Origem |
|---|---|---|
| **RN-A-03** | **Um objeto `Ambiente` por id, por processo.** `carregar_ambiente` de um ambiente já aberto devolve **o mesmo objeto**, sem reler o disco. Quando o serviço precisa recarregar (RN-A-09, RN-A-10), ele **atualiza o conteúdo desse objeto** em vez de trocá-lo, então quem guarda a referência ao `Ambiente` continua vendo o estado certo. Referências a objetos **de dentro** dele (uma `Frente`, uma `Tarefa`) podem ficar velhas depois de uma recarga: quem as quer atuais busca de novo pelo id | Q1=A |
| **RN-A-04** | **Abertura implícita.** Toda operação que recebe `id_ambiente` abre o ambiente se ele ainda não estiver aberto. Não é preciso chamar `carregar_ambiente` antes | Q1=A, Q2=A |
| **RN-A-05** | **Ambiente que não existe é erro tipado**: `AmbienteInexistente` (o tipo de U2), tanto em `carregar_ambiente` quanto em qualquer operação com `id_ambiente`. A porta continua devolvendo `None` (RN-P-04); quem converte é o serviço | Q12=B, D-Q12-1 |
| **RN-A-06** | **Uma operação por vez em cada ambiente.** Uma trava por ambiente serializa as operações sobre ele, inclusive a abertura; ambientes diferentes não esperam um pelo outro. Assim, dentro de um processo, duas operações nunca se intercalam no mesmo objeto, e `ConflitoDeVersao` só pode vir de **outro processo** | Q10=A |
| **RN-A-07** | **Uma gravação por operação.** Cada operação de estrutura termina com um `salvar_ambiente`; não existe gravação em lote nem `/salvar` | A/8B; `services.md` §5 |
| **RN-A-08** | **Alvo por identidade, dentro do ambiente.** Frente, tarefa e etapa são achadas pelo id, percorrendo o ambiente aberto. Não achar levanta `FrenteInexistente`, `TarefaInexistente` ou `EtapaInexistente` **antes** de qualquer mudança | Q2=A, D-Q12-2, RF-F16 |

## 3. Falha e conflito

| # | Regra | Origem |
|---|---|---|
| **RN-A-09** | **Memória nunca diverge do disco depois de uma falha.** Se a gravação falha por qualquer motivo, o serviço recarrega o ambiente da porta (RN-A-03) antes de levantar o erro, e a mudança que não foi gravada desaparece também da memória. Se a própria recarga falhar, o ambiente é **fechado** (sai dos abertos) e a próxima operação o abre de novo | Q1=A; RNF-05 |
| **RN-A-10** | **Conflito de versão: recarregar, reaplicar, salvar.** A mudança é guardada como **intenção** (uma função aplicada ao ambiente), não como objeto. Em `ConflitoDeVersao`, o serviço recarrega e aplica a intenção ao estado novo. A reaplicação passa pelas mesmas validações, então, se o alvo sumiu nesse meio-tempo, o erro é o do alvo (RN-A-08) | critério 5; RN-P-05; DP-P-13 |
| **RN-A-11** | **Até 3 tentativas.** Se a terceira gravação também der conflito, o serviço recarrega (o estado em memória fica igual ao do disco) e levanta `ConflitoDeVersao` | Q4=A |
| **RN-A-12** | **Ambiente apagado por outro processo.** Se a recarga não encontra mais o ambiente, ele é fechado e o serviço levanta `AmbienteInexistente` | RN-A-05, RN-A-09 |

## 4. Ciclo do ambiente

| # | Regra | Origem |
|---|---|---|
| **RN-A-13** | **O esquema vira a primeira proposta**: uma entidade nova por `EntidadeSemente` e uma página por `PropriedadeSemente`, com a descrição da semente e **conteúdo vazio**. Esquema vazio gera proposta vazia, e isso é válido | `business-logic-model.md` §6 de U3; Parte B.3 de U1 |
| **RN-A-14** | **Ordem de `criar_ambiente`**: (1) domínio constrói o `Ambiente` (valida o nome e gera id e raiz); (2) `escrever_proposta`; (3) `renderizar_index`; (4) `salvar_ambiente`; (5) o ambiente entra nos abertos. **Wiki primeiro, banco depois** | Q5=A |
| **RN-A-15** | **O ambiente nasce sem frente.** Quem garante que o usuário tem onde trabalhar é a tela (U9) | Q1=A de U1; R-FD4-1 |
| **RN-A-16** | **Falha parcial na criação não tem compensação.** Se a wiki falhar, nada foi gravado no banco e o ambiente não existe; a pasta parcial fica órfã e é inofensiva. Se o banco falhar, sobra uma wiki órfã, também inofensiva. Em nenhum caso existe ambiente apontando para wiki que não existe | Q5=A |
| **RN-A-17** | **Ordem de `apagar_ambiente`**: verifica que o ambiente existe (senão `AmbienteInexistente`, RN-A-05) → `apagar_ambiente` da porta de persistência → `apagar` da porta de wiki → sai dos abertos. **Banco primeiro, wiki depois** | critério 6; Q6=A |
| **RN-A-18** | **Falha ao apagar a wiki, depois do banco, não é erro de quem chamou.** O ambiente já não existe, que era o pedido. O serviço registra `WARNING` no logger `fishingrod.ambiente`, com o id e sem caminho de disco, e conclui a operação. A pasta órfã é inofensiva, pela mesma razão da RN-A-16. **É o único erro que o serviço não propaga** | critério 6; decisão desta geração, ver `business-logic-model.md` §7 |
| **RN-A-19** | **Nome de ambiente repetido é permitido.** A identidade distingue; a tela inicial mostra também `atualizado_em` | Q11=A; ESC-14 |
| **RN-A-20** | `listar_ambientes` repassa a porta, na ordem dela (mais recentemente atualizado primeiro, RN-P-24), e **não abre** nenhum ambiente | Q7 |

## 5. Estrutura

| # | Regra | Origem |
|---|---|---|
| **RN-A-21** | **Toda tarefa nasce com o orquestrador do construtor.** Quem chama `criar_tarefa` não escolhe nem conhece o agente | Q8=A; RN-05 de U1 |
| **RN-A-22** | **`criar_chat` só abre chat com agente da lista fechada** (`agentes_de_chat`), resolvido pelo nome. Nome fora da lista levanta `AgenteDesconhecido`, venha o pedido da tela ou de um agente. A lista **não pode conter orquestrador** (verificado na construção), então pedir um segundo orquestrador também cai em `AgenteDesconhecido` | Q9=A; R3 de Units Generation |
| **RN-A-23** | `concluir_etapa` é **idempotente**: concluir uma etapa já concluída grava de novo e não é erro | Q5a=B de U1 |
| **RN-A-24** | Não há operação de reabrir etapa nesta iteração | Q7=X, C1=A |

## 6. Memória

| # | Regra | Origem |
|---|---|---|
| **RN-A-25** | **`anotar_memoria` não grava o documento.** O domínio cria a `Anotacao` (`Memoria.anotar`) e o serviço a entrega a `PortaPersistencia.anotar`. Nunca chama `salvar_ambiente`, nunca levanta `ConflitoDeVersao` e não muda `Ambiente.versao` | RN-P-07; RN-P-08; US-04 |
| **RN-A-26** | Anotações gravadas por **outro processo** só aparecem na memória deste quando o ambiente for recarregado (conflito, falha ou nova abertura). Não há sincronização ativa | consequência de RN-A-03 |
