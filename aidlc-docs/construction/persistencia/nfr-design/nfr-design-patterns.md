# NFR Design Patterns — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 3 de 4** · **Data:** 2026-08-27
**Decisões que originam este documento:** Q1=A, Q2=A, Q3=B, Q4=A, Q5=A, Q6=A, Q7=A, Q8=A, Q9=C,
Q10=A, Q11=A, **Q12=B**, Q13=A

Os identificadores `DP-P-nn` são estáveis e podem ser citados em revisão de código.

---

## 1. Os padrões

### DP-P-01 — Abertura por fábrica, nunca por construtor (Q1=A)

```
abrir_repositorio(caminho: Path) -> RepositorioSQLite
```

A fábrica é a **única** forma legítima de obter um repositório. Ela faz, em ordem:

1. cria o diretório com `0o700` se não existir (`DP-P-08`)
2. `sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)`
3. `chmod 0o600` no arquivo do banco (`DP-P-08`)
4. aplica os PRAGMAs (`DP-P-07`, `NFR-P-05`, `NFR-P-06`, `NFR-P-10`)
5. cria o esquema com `IF NOT EXISTS` (`NFR-P-19`)
6. verifica as duas versões (`DP-P-07`)
7. devolve `RepositorioSQLite(conexao)`

O construtor recebe uma **conexão já aberta e já pragmada**. Quem instanciar a classe à mão sem
passar pela fábrica obtém um objeto que não funciona, e descobre isso na primeira chamada — não
três telas adiante.

**Por que isso importa mais do que parece:** é este passo que faz `NFR-P-07` (banco corrompido →
falha explícita, app não inicia) acontecer **na inicialização**. Com abertura preguiçosa, o erro
apareceria depois da TUI já ter subido, e a única resposta possível seria uma caixa de diálogo
dizendo que o programa não devia ter aberto.

`fechar()` fecha a conexão. Não há `__del__`, não há finalizador: o composition root de U9 abre e
fecha, e é a única coisa que faz isso.

---

### DP-P-02 — Controle de transação explícito, não herdado do driver

A conexão é aberta com `isolation_level=None`, o que põe o `sqlite3` em
`LEGACY_TRANSACTION_CONTROL` — nenhuma transação implícita. O `BEGIN`, o `COMMIT` e o `ROLLBACK`
são emitidos por nós, num lugar só (`DP-P-03`).

**Medido nesta máquina, não presumido:**

```
python 3.14.4  ·  sqlite 3.50.4
isolation_level=None  ->  conexao.autocommit == sqlite3.LEGACY_TRANSACTION_CONTROL  (-1)
BEGIN IMMEDIATE / CREATE TABLE / COMMIT  ->  in_transaction == False
```

**Por que não deixar o driver decidir:** o modo implícito do `sqlite3` abre transação antes de
`INSERT`/`UPDATE`/`DELETE`, mas **não** antes de `SELECT` nem de DDL, e comita em pontos que variam
com a versão. `NFR-P-08` diz "uma operação = uma transação, garantida por construção". Uma garantia
que depende de qual instrução o driver considerou digna de transação não é garantia — é sorte
documentada.

---

### DP-P-03 — Dois auxiliares, não um: `_ler` e `_escrever` (Q3=B, com um ajuste)

A resposta escolheu **um** auxiliar concentrando `Lock`, `to_thread` e transação. O desenho manteve
a ideia e a partiu em duas, por um motivo que só aparece quando `NFR-P-10` e `NFR-P-11` se
encontram:

```python
async def _ler(self, fn):          # BEGIN            (transação diferida)
async def _escrever(self, fn):     # BEGIN IMMEDIATE  (trava de escrita já na abertura)
```

Ambos fazem a mesma coreografia:

```
async with self._lock:                     # NFR-P-09 — serializa dentro do processo
    return await asyncio.to_thread(...)    # NFR-P-08 — um único salto, sem await no meio
        BEGIN [IMMEDIATE]
        fn(cursor)                         # todo o SQL da operação
        COMMIT                             # ou ROLLBACK, se fn levantar
```

**O ajuste, e por que ele não é detalhe.** Em WAL, uma transação aberta com `BEGIN` simples que
**lê primeiro e escreve depois** não consegue subir para escritora se outro processo já segurou a
trava de escrita nesse meio-tempo. O SQLite devolve `SQLITE_BUSY` **na hora, sem consultar o
`busy_timeout`** — esperar ali seria arriscar impasse, já que o instantâneo de leitura desta
transação já está fixado. `salvar_ambiente` é exatamente esse formato: lê a versão em disco, compara,
e só então grava.

Ou seja: `NFR-P-10` (`busy_timeout = 5000`) **não** cobre sozinho o caso de `NFR-P-11` (duas
instâncias). Quem o faz valer é o `IMMEDIATE`, que pede a trava de escrita na abertura, onde o
tempo de espera **é** respeitado. Sem esta linha, a segunda instância do FishingRod falharia na
cara do usuário em vez de esperar meio segundo.

**O que os auxiliares compram.** As funções `_x_sync` recebem um cursor e não sabem o que é
transação, `Lock` ou thread. Um método novo ou passa por um dos dois auxiliares, ou não tem cursor
com que trabalhar. `RN-P-03` deixa de ser disciplina e vira estrutura — que era o pedido de
`NFR-P-08`.

---

### DP-P-04 — O caminho do erro é o mesmo caminho da transação

`_x_sync` levanta; `_escrever` faz `ROLLBACK` e deixa a exceção subir intacta.

Isto é o que dá a segunda metade de `RN-P-05` ("`ConflitoDeVersao` **e nada é gravado**"). A
verificação de versão e a escrita moram na mesma função síncrona, dentro da mesma transação: quando
a comparação falha, o `UPDATE` sequer chegou a ser emitido, e o que porventura já tivesse sido
escrito volta atrás. `PBT-U2-03` verifica isso do lado de fora, sem saber de transação.

---

### DP-P-05 — Localização como função pura (Q2=A)

```
caminho_do_banco() -> Path        # só o composition root chama
RepositorioSQLite recebe o Path   # todo teste passa tmp_path
```

Nenhum teste desta unidade toca a pasta real do usuário, e nenhum precisa de monkeypatch para isso.
A resolução por sistema operacional (as ~12 linhas que `Q1a=B` preferiu a uma dependência) fica
sozinha num módulo e é testada por plataforma, sem banco nenhum envolvido.

Sem variável de ambiente de override: nenhuma história pede, e configuração criada "por precaução"
nunca é removida depois.

---

### DP-P-06 — O domínio não sabe que existe disco (Q8=A)

A conversão `Ambiente ↔ dicionário JSON` vive num módulo do adaptador. U1 **não é tocado** por esta
unidade — não ganha `to_dict`, não ganha `from_dict`, não ganha import novo.

**O risco assumido e quem o cobre:** alguém acrescenta um campo ao domínio e esquece o mapeador.
`PBT-U2-01` (round-trip para todo `Ambiente` gerado) falha, porque o campo novo não sobrevive a
salvar-e-carregar. O esquecimento é **detectado**, não confiado à memória de quem revisa.

---

### DP-P-07 — Duas versões, dois escopos (Q9=C)

| Onde | O que versiona | Valor hoje | Verificado em |
|---|---|:--:|---|
| `PRAGMA user_version` | esquema **físico**: tabelas, índices, chaves estrangeiras | `1` | abertura (`abrir_repositorio`) |
| coluna `versao_esquema` na linha do ambiente | formato do **documento JSON** | `1` | `carregar_ambiente` (`RN-P-02`) |

São perguntas diferentes e vão mudar em momentos diferentes. Acrescentar uma coluna em `anotacao`
não muda o formato do documento; renomear um campo dentro do JSON não muda tabela nenhuma. Ter uma
versão só forçaria a incrementar as duas coisas juntas — e, na prática, a não incrementar nenhuma.

Maior que a suportada, em qualquer das duas, é erro explícito na abertura ou na carga. Nunca
"tenta assim mesmo".

> `RN-P-02` recebeu emenda registrando que a coluna passa a versionar **apenas** o documento.

---

### DP-P-08 — Permissão no diretório, confirmada no arquivo (Q7=A)

```
mkdir(parents=True, exist_ok=True)  ->  chmod 0o700 no diretório
connect(...)                        ->  chmod 0o600 no arquivo do banco
```

Ambos sob `if os.name != "nt"`. Em Windows o `chmod` do Python só mexe no bit de somente-leitura e
não expressa nada disso; a raiz `%LOCALAPPDATA%` já é privada ao usuário.

Os arquivos `-wal` e `-shm` **não** recebem `chmod`: eles nascem e morrem durante a execução, então
qualquer garantia dada numa abertura não vale na seguinte. Quem os protege é o diretório `0o700`,
que ninguém além do dono atravessa. Dizer o contrário seria dar sensação de proteção onde a proteção
real está noutro lugar.

---

### DP-P-09 — Observabilidade cai no mesmo funil (`NFR-P-17`, `NFR-P-18`)

O logger `fishingrod.persistencia` é usado em **um lugar só**: o `except` de `_escrever`. Como toda
falha e todo conflito passam por ali (`DP-P-04`), "registrar apenas falha e conflito" deixa de ser
uma regra que cada método precisa lembrar de obedecer.

Nível: `WARNING` para `ConflitoDeVersao` (é esperado, U4 reabsorve), `ERROR` para o resto.
`NullHandler` no módulo; **destino nenhum é configurado aqui** — isso é do composition root de U9.

---

### DP-P-10 — O dublê é um segundo enunciado do contrato (Q4=A, Q12=B)

`RepositorioEmMemoria` é escrito **à mão**, com dicionários e listas, reimplementando versão, ordem,
cascata e paginação. Não usa `sqlite3` em `:memory:`.

**O motivo é o propósito de `PBT-U2-08`.** Se dublê e real fossem o mesmo código, a propriedade
passaria por construção e não detectaria nada. Duas implementações independentes que discordam
revelam que o **contrato** estava ambíguo — e é isso que se quer descobrir antes de U4, U7 e U8
começarem a depender dele.

Custo assumido: ~100 linhas a mais, e o dublê pode ter bugs próprios. Um bug no dublê **falha o
teste de contrato**, que é precisamente o trabalho dele.

**Onde ele mora (Q12=B):** em `tests/dobles/`, fora do pacote instalado. Eu havia recomendado o
contrário alegando que importar de dentro de `tests/` "só funciona por acidente de `sys.path`".
Verifiquei, e a objeção era mais fraca do que eu a enunciei: `tests/` já tem `__init__.py`, o
pytest insere a raiz do projeto no `sys.path` e `import tests.dominio` funciona hoje — 41 testes
coletados. A escolha mantém o pacote instalado sem código que só existe para teste, e **a condição
que a sustenta fica registrada**: `tests/dobles/` precisa ter `__init__.py`, e `tests/` precisa
continuar sendo pacote.

---

### DP-P-11 — Os erros moram junto do contrato, não do domínio nem do adaptador (Q6=A)

Hierarquia em `aplicacao/portas/persistencia.py`, ao lado do `Protocol`:

```
ErroDePersistencia
├── ConflitoDeVersao      # RN-P-05 — dois escreveram sobre a mesma versão
├── EsquemaIncompativel   # DP-P-07 — versão maior que a suportada
├── BancoIlegivel         # NFR-P-07 — arquivo corrompido ou inacessível
├── MensagemInexistente   # atualizar_mensagem sobre id que não existe
└── AmbienteInexistente    # [emenda 2026-08-27 / CG] RN-P-27
```

> **[Emenda 2026-08-27 / Code Generation]** A hierarquia nasceu com quatro erros e tem cinco. O
> quinto não veio de revisão: `PBT-U2-04` inseriu mensagem num ambiente nunca salvo e
> `sqlite3.IntegrityError` atravessou a porta. Era o desenho vazando o driver — exatamente o que
> `DP-P-11` existe para impedir.

U4 captura `ConflitoDeVersao` importando a **porta**, nunca o adaptador. Nada disso entra em
`dominio/erros.py`: `NomeInvalido` diz que o usuário digitou algo inválido; `ConflitoDeVersao` diz
que dois processos escreveram ao mesmo tempo. Só um dos dois é assunto do domínio.

`carregar_ambiente` continua devolvendo `None` para id ausente (`RN-P-04`) — ausência é resultado,
não erro. Em `atualizar_mensagem` a ausência **é** defeito, e por isso tem exceção.

---

### DP-P-12 — O throttle não mora aqui (Q5=A)

`NFR-P-03` continua alvo desta unidade, mas o mecanismo passou para **U7 `conversa`** — que conduz
o streaming e é a única que sabe quando o turno acabou. A porta escreve **toda** chamada que recebe.

Se o adaptador descartasse escritas pelo relógio: `atualizar_mensagem` viraria uma chamada que pode
não fazer nada, `PBT-U2-08` precisaria de um relógio dentro do teste de contrato, e a "escrita final
obrigatória" viraria um `forcar=True` na assinatura — mecanismo vazando para o vocabulário, que é o
que `D-ARQ-04` proíbe.

> Emendas aplicadas: `unit-of-work.md` §3 (U7) ganhou o critério 6; `NFR-P-03` ganhou a nota.

---

### DP-P-13 — A lista do que **não** entra (Q10=A, Q13=A)

| Padrão | Por que não |
|---|---|
| Retentativa de `ConflitoDeVersao` no adaptador | O adaptador tem o `Ambiente` que lhe entregaram, **não a intenção** de quem o modificou. Recarregar e regravar por cima é a escrita cega que `RN-P-05` existe para impedir. Só o chamador sabe reaplicar |
| Retentativa com recuo exponencial | `busy_timeout = 5000` + `BEGIN IMMEDIATE` (`DP-P-03`) já é a espera, feita pelo SQLite |
| Cache de leitura | Uma conexão, um processo, um usuário. O cache inventaria uma segunda cópia da verdade e um jeito novo de `RN-P-03` quebrar |
| Pool de conexões | `NFR-P-09` pede exatamente uma. Um pool desfaria a garantia de PRAGMA único e reintroduziria o esquecimento de `foreign_keys` |
| Fila de escrita | O `Lock` já serializa. Uma fila acrescentaria um ponto onde a escrita foi aceita mas ainda não aconteceu — e é isso que `RN-P-03` recusa |
| Disjuntor (*circuit breaker*) | `resiliency-baseline` está desativada. Não há dependência remota a proteger: o disco ou está lá ou não está |
| Particionamento | 5.000 anotações são ~5 MB. O gatilho declarado (`Q2a=B`) é carga sob demanda, não partição |

Cada um deles resolveria um problema que esta unidade não tem, e todos custariam um caminho a mais
onde `RN-P-03` pode quebrar.

---

## 2. Cada NFR e onde ele acontece

| # | Realizado por |
|---|---|
| NFR-P-01 | `mapeamento` + índice `idx_anotacao_ambiente`; medido por teste de fumaça |
| NFR-P-02 | `_listar_ambientes_sync` seleciona colunas nomeadas; nunca lê `documento` |
| NFR-P-03 | **Fora desta unidade** — U7, critério 6 (`DP-P-12`) |
| NFR-P-04 | `idx_mensagem_chat(id_chat, id)` + `ORDER BY id DESC LIMIT ?` |
| NFR-P-05 | `esquema.aplicar_pragmas` — `journal_mode=WAL`, `synchronous=NORMAL` |
| NFR-P-06 | `esquema.aplicar_pragmas` — `foreign_keys=ON`; verificado por `PBT-U2-07` |
| NFR-P-07 | `abrir_repositorio` → `BancoIlegivel` antes de qualquer tela subir (`DP-P-01`) |
| NFR-P-08 | `DP-P-02` + `DP-P-03` |
| NFR-P-09 | `DP-P-01` (conexão única, pragmada uma vez) + `DP-P-03` (`Lock`) |
| NFR-P-10 | `busy_timeout=5000` **e** `BEGIN IMMEDIATE` — sem o segundo, o primeiro não é consultado |
| NFR-P-11 | Nenhum mecanismo novo; a proteção é `RN-P-05` + `DP-P-03` |
| NFR-P-12 | Nenhum import de terceiros em módulo algum desta unidade |
| NFR-P-13 | Todo SQL com `?`; nenhuma f-string monta consulta (verificável por inspeção em CG) |
| NFR-P-14 | `DP-P-08` |
| NFR-P-15 | Nenhuma coluna de credencial no esquema |
| NFR-P-16 | `DP-P-04` + `DP-P-11` |
| NFR-P-17 | `DP-P-09` |
| NFR-P-18 | `DP-P-09` — funil único no `except` de `_escrever` |
| NFR-P-19 | `esquema.criar_esquema`, `CREATE TABLE IF NOT EXISTS` |
| NFR-P-20 | `DP-P-07` |
| NFR-P-21 | `tests/conftest.py` — perfil Hypothesis com `deadline=None` |

Nenhum requisito ficou sem dono.

---

## 3. Conformidade das extensões

| Extensão | Estado | Onde incide neste estágio |
|---|:--:|---|
| `security-baseline` | ✅ | `DP-P-08` (permissões), `DP-P-11` (falha explícita, nunca valor de sucesso ambíguo), `DP-P-13` (nenhum componente novo, nenhuma dependência nova — `NFR-P-12` intacto) |
| `property-based-testing` (Full) | ✅ | `DP-P-10` é o desenho que torna `PBT-U2-08` capaz de falhar; `DP-P-06` liga `PBT-U2-01` ao risco que ele cobre |
| `resiliency-baseline` | N/A | Desativada na Requirements Analysis. `DP-P-13` registra explicitamente os padrões de resiliência que **não** entram e por quê |

---

## 4. Emendas aplicadas neste estágio

| Artefato | Emenda |
|---|---|
| `unit-of-work.md` §3 (U7) | **Critério 6 novo**: cadência de gravação (~500 ms + escrita final obrigatória) é de U7; a porta sempre escreve |
| `business-rules.md` (`RN-P-02`) | A coluna `versao_esquema` passa a versionar **apenas** o documento; o esquema físico vai para `PRAGMA user_version` |
| `nfr-requirements.md` (`NFR-P-03`) | Nota registrando que o alvo permanece, mas o mecanismo mora em U7 |

Texto substituído foi riscado ou anotado com a data da emenda; nada foi apagado.

---

## 5. O que fica para Code Generation

- A emenda de código pendente desde o portão 1: **`Ambiente` ganha `versao: int = 0`**, com
  serialização e teste, e `Memoria.versao` derivada na carga.
- `tests/dobles/__init__.py` precisa existir (`DP-P-10`).
- `tests/conftest.py` precisa registrar o perfil Hypothesis (`NFR-P-21`).
- A inspeção de `NFR-P-13` (nenhuma consulta montada por concatenação) é feita lá, sobre código real.
