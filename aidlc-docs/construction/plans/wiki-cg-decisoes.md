# Decisões — Code Generation de U3 `wiki` (portão 4/4)

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Portão 4 de 4, Step 15 (aprovação)**
**Data:** 2026-10-01
**Origem:** §3 de `construction/wiki/code/code-summary.md` — as 2 falhas da suíte
(`270 passed, 7 skipped, 2 failed`) que dependem de decisão sua antes de o portão fechar.

Contexto completo, com medições, está no `code-summary.md` §3.1 e §3.2. Aqui vai só o necessário
para decidir.

---

## Pergunta D1 — O sensor `NFR-W-02` (aprovação em wiki de 500 páginas, ≤ 500 ms)

Passa sozinho 8 de 8; falha dentro da suíte 5 de 5 (521–620 ms), porque o I/O de metadados desta
máquina fica 6–7× mais lento durante a própria suíte. O código já foi otimizado até o piso imposto
por `NFR-W-05` (um `resolve()` por arquivo). Toda opção abaixo, menos a D, emenda `NFR-W-02` ou
`DP-W-11`, com texto riscado.

A) Subir o orçamento para **≤ 1 s** a 500 páginas. Todas as medições ficaram abaixo de 870 ms, até
com 700 páginas; na escala real (dezenas de páginas) a aprovação leva dezenas de ms. **(Recomendado)**

B) Manter 500 ms e medir com **100** páginas (ainda 2–4× a escala projetada; ~150 ms no regime lento).

C) Trocar o sensor por uma **razão**: renderizar páginas grandes vs. pequenas. Mede direto o que
`NFR-W-01` garante, independe da máquina, mas perde o orçamento absoluto.

D) Manter como está e aceitar a suíte vermelha nesta máquina.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A — "sobre o sensor - vamos aumentar o limite para 1s." *(respondido no chat em 2026-10-02; aplicado)*

---

## Pergunta D2 — `PBT-U2-08` de U2 (defeito latente no teste, não no código)

`_rodar_roteiro`, em `tests/persistencia/test_contrato.py`, chama `datetime.now()` separadamente na
execução real e na do duplo, e depois compara os `Ambiente` carregados. O roteiro
`[salvar, anotar, carregar]` falha sempre; o Hypothesis só agora o sorteou e guardou o
contraexemplo em `.hypothesis/`, então ele vai repetir em toda execução. U2 está fechada e nada
dela foi tocado.

A) Corrigir **agora**, como emenda registrada a U2 dentro deste portão: a operação `anotar` passa a
usar um `criada_em` fixo, igual nas duas execuções. Só o teste muda; o contrato verificado fica
intacto. **(Recomendado)**

B) Não corrigir agora; registrar como dívida técnica de U2 e marcar o teste como `xfail` com o
motivo escrito, até um momento de correção que você definir.

C) Não corrigir agora e deixar o teste falhando, registrado como pendência.

X) Outro (descreva depois da tag [Answer]: abaixo)

[Answer]: A — "vamos corrgir esse teste tambme, para nao deixar esse erro e ficarmos toda hora vendo esse teste dando erro toda vez." *(respondido no chat em 2026-10-02; aplicado)*

---

## Resultado

Suíte depois das duas correções: **272 passed, 7 skipped, 0 failed**. Arquivos alterados (só
testes): `tests/wiki/test_wiki_de_arquivos.py` (orçamento 0,5 → 1,0 s e docstring) e
`tests/persistencia/test_contrato.py` (`_INSTANTE_DO_ROTEIRO` na operação `anotar` do roteiro).
