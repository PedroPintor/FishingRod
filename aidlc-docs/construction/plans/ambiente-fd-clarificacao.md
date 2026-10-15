# Clarificação — Functional Design de U4 `ambiente`

**Fase:** CONSTRUCTION · **Unidade:** `U4 ambiente` · **Portão 1 de 2, Step 5**
**Data:** 2026-10-02
**Origem:** análise das 12 respostas em `ambiente-functional-design-plan.md`

---

## 0. Onde estamos

**11 respostas fecharam sem ambiguidade** e já valem como decisão: Q1=A, Q2=A, Q3=A, Q4=A, Q5=A,
Q6=A, Q8=A, Q9=A, Q10=A, Q11=A e **Q12=B**. As 6 reconciliações `R-FD4-1..6` não receberam
objeção.

**A Q7 abriu um conflito de escopo** com duas histórias que estão na linha fina. É a única coisa
que preciso de você antes de gerar os artefatos.

Também tirei **duas consequências da Q12=B**. Estão na §2 para você objetar; se não objetar, valem.

---

## 1. Clarificação

### C1 — Sem `criar_etapa` e `concluir_etapa`, US-17 e US-19 ficam sem caminho

Na Q7 você escolheu 8 operações e deixou `criar_etapa` e `reabrir_etapa` para depois. Concordo com
tirar `reabrir_etapa`: nenhuma história pede para desmarcar uma etapa.

Mas a lista também deixou de fora **`concluir_etapa`**, que estava entre as 6 originais. E duas
histórias da linha fina dependem dessas operações:

- **US-17** — *descobrir as etapas da tarefa conversando com o orquestrador*. O orquestrador grava
  cada etapa chamando `criar_etapa` como ferramenta (`services.md` §7, Q11/Q12/Q14). Sem a operação,
  a conversa acontece, mas nenhuma etapa fica salva.
- **US-19**, segundo critério — *"quando confirmo que fiz a etapa, ela é marcada como concluída"*.
  Isso é exatamente `concluir_etapa`. Sem `criar_etapa` também não há etapa para concluir.

O domínio já tem as duas operações prontas (`Tarefa.criar_etapa`, `Etapa.concluir`, desde U1).
Então incluí-las no serviço custa duas operações curtas, no mesmo formato de `criar_frente`.

A) **Incluir `criar_etapa` e `concluir_etapa`; deixar `reabrir_etapa` de fora.** São 10 operações
no total, e US-17 e US-19 continuam na linha fina sem mudança. **(Recomendado)**

B) **Manter as 8 operações e adiar US-17 e US-19**, que saem da linha fina (14 → 12 histórias),
como já aconteceu com US-07, US-10, US-11, US-12 e US-18. `requirements.md` §9.6, `stories.md` e o
story map são emendados, e U5/U7 perdem a parte de etapas.

C) **Manter as 8 operações e adiar só US-17**: a etapa passa a ser criada pelo usuário com
`/comando`. Mas sem `criar_etapa` no serviço nem isso funciona, então esta opção também exige
incluir `criar_etapa`. Na prática, é a A com outra história de origem.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A

---

## 2. Consequências que tirei da Q12=B (para objeção)

Você escolheu que ambiente inexistente seja um **erro tipado**, e não `None`, porque deixar a
ausência implícita gera dúvida. Apliquei o mesmo raciocínio aos casos vizinhos:

| # | Decisão derivada | Por quê |
|---|---|---|
| **D-Q12-1** | `carregar_ambiente` levanta **`AmbienteInexistente`**, o mesmo tipo que já existe em `aplicacao/portas/persistencia.py` (U2), em vez de criar um tipo novo | Já é o nome do mesmo fato em `anotar` e `inserir_mensagem`. Dois tipos para "esse ambiente não existe" fariam a TUI tratar o mesmo problema de dois jeitos. A porta continua devolvendo `None` (RN-P-04); quem converte em erro é o serviço |
| **D-Q12-2** | Alvo que não existe **dentro** de um ambiente também é erro tipado: **`FrenteInexistente`**, **`TarefaInexistente`** (e `EtapaInexistente`, se a C1 incluir etapas), em `aplicacao/servicos/` | Mesmo raciocínio da sua resposta: `criar_tarefa` numa frente que sumiu não pode falhar em silêncio. O domínio continua devolvendo `None` na busca (RN-14 de U1: não achar é resultado); quem transforma em erro é o serviço, que sabe que o alvo era obrigatório |

[Objeção, se houver]: sem objecoes. pode fazer isso tambem para os seus vizinhos, a frente e a terafa.

