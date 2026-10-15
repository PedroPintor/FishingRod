# Code Summary — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 4 de 4, Parte 2** · **Data:** 2026-08-27
**Plano executado:** `construction/plans/persistencia-code-generation-plan.md` — **16/16 passos**

---

## 1. Resultado

```
uv run pytest        ->  84 passed, 1 skipped   (era 41 antes desta unidade)
uv sync              ->  dependencies = []      (pyproject.toml e uv.lock intactos)
```

O teste pulado é `test_nfr_p_14_permissoes_restritas`, marcado para Windows: o `chmod` do Python só
mexe no bit de somente-leitura e não expressa `0o600` (`DP-P-08`).

| | |
|---|--:|
| Testes novos | **43** (41 → 84) |
| Linhas em `src/` | **1.158** |
| Linhas em `tests/` | **1.292** |
| Dependências novas | **0** |

---

## 2. Arquivos

### Criados em `src/`

| Arquivo | Linhas | Papel |
|---|--:|---|
| `aplicacao/portas/persistencia.py` | 228 | `PortaPersistencia`, os 3 tipos de fronteira, os **5** erros |
| `adaptadores/persistencia/__init__.py` | 13 | Exporta `abrir_repositorio` e `RepositorioSQLite` |
| `adaptadores/persistencia/localizacao.py` | 43 | `pasta_de_dados()` e `caminho_do_banco()` |
| `adaptadores/persistencia/esquema.py` | 119 | DDL, PRAGMAs, as duas versões |
| `adaptadores/persistencia/mapeamento.py` | 166 | `Ambiente` ↔ documento JSON |
| `adaptadores/persistencia/repositorio_sqlite.py` | 589 | Fábrica, `_ler`/`_escrever`, as 9 operações |

### Criados em `tests/`

| Arquivo | Linhas | Papel |
|---|--:|---|
| `conftest.py` | 17 | Perfil Hypothesis `deadline=None` (`NFR-P-21`) |
| `dobles/__init__.py` | 6 | A condição que sustenta `Q12=B` |
| `dobles/repositorio_memoria.py` | 308 | O segundo enunciado do contrato |
| `persistencia/estrategias.py` | 104 | Geradores e o auxiliar `executar` |
| `persistencia/test_contrato.py` | 491 | `PBT-U2-01..08`, nas duas implementações |
| `persistencia/test_sqlite.py` | 294 | PRAGMAs, versões, permissão, cascata, tempo |
| `persistencia/test_mapeamento.py` | 71 | O exemplo legível do round-trip |

### Modificados

| Arquivo | Mudança |
|---|---|
| `src/fishingrod/dominio/ambiente.py` | `versao: int = 0` como último campo (emenda pendente desde o portão 1) |
| `tests/dominio/test_ambiente.py` | Teste do padrão e da construção posicional |

**Nada foi removido.** `Ambiente/`, `model/`, `cli.py` e `tui.py` continuam onde estavam: a regra
de U1 vale — o antigo sai quando o substituto for executável, em U9.

---

## 3. O achado: um erro que o desenho não tinha

`PBT-U2-04` inseriu mensagem num ambiente nunca salvo. O adaptador real deixou
**`sqlite3.IntegrityError` atravessar a porta** — a chave estrangeira que existe para a cascata de
`RN-P-20` também torna o ambiente uma **pré-condição** de `anotar` e `inserir_mensagem`, e isso não
estava dito em lugar nenhum.

Duas coisas quebravam ao mesmo tempo:

1. **O vocabulário da porta ficava furado** (`NFR-P-16`, `DP-P-11`): quem chama teria de capturar
   uma exceção do driver, que é exatamente o vazamento que `D-ARQ-04` proíbe.
2. **As duas implementações discordavam** (`RN-P-26`): o dublê aceitava alegremente a mensagem
   órfã. `PBT-U2-08` teria pegado isso mais cedo ou mais tarde.

**Resolvido no contrato, não no teste**: nasceu `AmbienteInexistente`, verificado explicitamente
nas duas implementações. `registrar_uso_ferramenta` ganhou o mesmo tratamento com
`MensagemInexistente`, pela mesma razão.

Emendas aplicadas (texto anotado, nada apagado): `business-logic-model.md` §1 e §2 ·
`business-rules.md` (**`RN-P-27`** novo) · `nfr-design-patterns.md` `DP-P-11` ·
`logical-components.md` §1.1.

---

## 4. Decisões tomadas durante a execução

| Decisão | Motivo |
|---|---|
| **Ambiente ausente com `versao > 0` é `ConflitoDeVersao`**, não inserção | Inserir ali ressuscitaria um ambiente que outra instância removeu de propósito — a escrita cega que `RN-P-05` existe para impedir. Tem teste próprio |
| **Um repositório por teste, reaproveitado entre os exemplos gerados** | Cada exemplo cria um `Ambiente` com identidade nova, então nenhum enxerga o estado do anterior. Verificado nesta versão (CPython 3.14.4) que `asyncio.Lock` só se prende a um laço **quando há disputa** — e nestes testes nunca há. Foi medido, não presumido: sem isso, um arquivo de banco por exemplo |
| **Testes de `localizacao` e `esquema` foram para `test_sqlite.py`** | O plano pedia "+ testes" sem nomear arquivo. Um arquivo por módulo daria três arquivos de 30 linhas com o mesmo assunto |
| `_usos_por_mensagem` faz **uma** consulta por página, com `IN (?,?,…)` | Ver §5 |
| `listar_ambientes` desempata por `id DESC` | Dois ambientes gravados no mesmo instante — o que acontece em teste gerado — precisam de ordem determinista |
| Anotação de tarefa que saiu do documento é **ignorada na carga** | A tabela é append-only (`RN-P-09`): a linha fica, mas não há para onde devolvê-la |

---

## 5. Inspeção de `NFR-P-13` (nenhuma consulta montada por concatenação)

Varredura em `src/fishingrod/`. **Toda** consulta com valor usa `?`. Dois lugares compõem texto de
SQL, ambos sem valor externo:

| Lugar | O que compõe | Por que é seguro |
|---|---|---|
| `esquema.py:109` | `PRAGMA user_version = {VERSAO_ESQUEMA_FISICO:d}` | `PRAGMA` **não aceita** parâmetro vinculado. O valor é uma constante do módulo, formatada como inteiro. Nenhuma entrada externa alcança esta linha |
| `repositorio_sqlite.py:578` | `IN ({marcadores})`, com `marcadores = ",".join("?" * n)` | O que é gerado é o **número** de `?`, nunca conteúdo. Todos os valores continuam vinculados |

As demais f-strings do adaptador (14 ocorrências) são **mensagens de erro**, não SQL.

Verificado também: `dominio/` ganhou 8 linhas e **nenhum import novo**;
`aplicacao/portas/persistencia.py` não importa `sqlite3` nem `json`.

---

## 6. Rastreio

| Regra / propriedade | Onde é verificada |
|---|---|
| `PBT-U2-01..07` | `test_contrato.py`, **nas duas implementações** (fixture parametrizada) |
| `PBT-U2-08` | `test_pbt_u2_08_as_duas_implementacoes_concordam` — mesma sequência gerada nos dois, comparando resultado **e** tipo de erro a cada passo. *Emenda de 2026-10-02 (decisão D2=A no portão 4/4 de U3): o roteiro chamava `datetime.now()` separadamente em cada implementação e o `criada_em` das anotações diferia por microssegundos; a operação `anotar` passou a usar um instante fixo (`_INSTANTE_DO_ROTEIRO`). Só o teste mudou; o contrato verificado é o mesmo* |
| `RN-P-05`, `RN-P-06` | `test_pbt_u2_03_*` + `test_salvar_ambiente_apagado_por_outra_instancia_levanta` |
| `RN-P-07`, `RN-P-10` | `test_pbt_u2_02_*`, `test_pbt_u2_06_*` |
| `RN-P-13`, `RN-P-14` | `test_pbt_u2_04_*`, `test_pbt_u2_05_*` |
| `RN-P-17`, `RN-P-18` | `test_rn_p_17_e_rn_p_18_*` |
| `RN-P-20` | `PBT-U2-07` (observável) **e** `test_nfr_p_20_*` (contagem de linhas) |
| `RN-P-27` (novo) | `test_mensagem_inexistente_*` e o diferencial |
| `NFR-P-05`, `-06`, `-10` | `test_nfr_p_05_e_06_os_pragmas_valem_na_conexao` |
| `NFR-P-07` | `test_nfr_p_07_arquivo_corrompido_levanta_na_abertura` |
| `NFR-P-01` | `test_nfr_p_01_carga_de_cinco_mil_anotacoes` |
| `NFR-P-02` | `test_nfr_p_02_listar_nao_le_a_coluna_documento` |
| `NFR-P-19` | `test_nfr_p_19_abrir_duas_vezes_e_inofensivo` — que é também **CS-01** |
| **US-05** | `PBT-U2-01` + `test_nfr_p_19_*` (fechar e reabrir o processo) |
| **US-06** | `PBT-U2-04`, `PBT-U2-05` |
| **TD-04** | Morta: a persistência existe e está sob teste |

---

## 7. Conformidade das extensões

| Extensão | Estado | Evidência |
|---|:--:|---|
| `security-baseline` | ✅ | Inspeção de `NFR-P-13` (§5) · permissões `0o700`/`0o600` com teste · nenhuma coluna de credencial · `dependencies = []` · toda falha é exceção nomeada da porta, nunca valor de sucesso ambíguo |
| `property-based-testing` (Full) | ✅ | 8 propriedades implementadas; as 7 primeiras rodam nas duas implementações; a oitava compara uma contra a outra |
| `resiliency-baseline` | N/A | Desativada na Requirements Analysis |

---

## 8. O que fica para as próximas unidades

- **U9 (composition root)**: chamar `caminho_do_banco()`, `abrir_repositorio(...)` na subida e
  `fechar()` na saída, e configurar o destino do logger `fishingrod.persistencia` — o adaptador
  instala apenas um `NullHandler`.
- **U4 (`ServicoDeAmbiente`)**: tratar `ConflitoDeVersao` recarregando e reaplicando; apagar o
  diretório da wiki **depois** do banco (`RN-P-21`).
- **U7 (`conversa`)**: a cadência de gravação durante o streaming (~500 ms + escrita final
  obrigatória) é critério 6 daquela unidade — a porta escreve toda chamada que recebe (`DP-P-12`).
- **U3, U4, U7, U8**: importam `tests.dobles.repositorio_memoria` nos próprios testes. Se
  `tests/dobles/__init__.py` sumir, todos param de achá-lo.
