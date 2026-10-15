# NFR Design Plan — U2 `persistencia`

**Fase:** CONSTRUCTION · **Unidade:** `U2 persistencia` · **Portão 3 de 4** · **Data:** 2026-08-26

O portão anterior fixou **alvos** (`NFR-P-01..21`) e **tecnologia** (`TS-P-01..09`).
Este estágio decide **forma**: onde as coisas moram, com que assinatura, em quantos módulos.
Continua sem escrever código — isso é Code Generation.

---

## 1. Passos

- [x] **1.** Ler `nfr-requirements.md` (21 requisitos) e `tech-stack-decisions.md` (9 decisões)
- [x] **2.** Ler o functional design: contrato da porta, 26 regras `RN-P-nn`, 8 propriedades `PBT-U2-nn`
- [x] **3.** Inspecionar a árvore existente (`src/fishingrod/`) para saber o que U0/U1 já deixaram pronto
- [x] **4.** Registrar o achado de desenho da §2 e escrever este plano com as perguntas
- [x] **5.** Coletar as respostas e analisar ambiguidade (clarificação se houver)
- [x] **6.** Gerar `construction/persistencia/nfr-design/nfr-design-patterns.md`
- [x] **7.** Gerar `construction/persistencia/nfr-design/logical-components.md`
- [x] **8.** Marcar os checkboxes, registrar em `audit.md` e `aidlc-state.md`
- [x] **9.** Apresentar o portão 3/4

---

## 2. Um achado antes das perguntas: **NFR-P-03 não pode ser cumprido aqui**

`NFR-P-03` diz "no máximo ~2 escritas por segundo por chat: throttle de 500 ms, mais uma escrita
final obrigatória". Escrevi isso no portão anterior como se fosse requisito **desta** unidade. Ao
desenhar a forma, ele não cabe.

Se o throttle morar no `RepositorioSQLite`, então `atualizar_mensagem` passa a ser uma chamada que
**pode não fazer nada** — e três coisas quebram de uma vez:

1. **`PBT-U2-08` fica impossível de escrever com honestidade.** A propriedade exige que dublê e real
   produzam o mesmo resultado observável. Se o real descarta escritas conforme o relógio, o dublê
   precisa descartar também — e um relógio entra no teste de contrato.
2. **O contrato passa a mentir.** Quem chama `atualizar_mensagem` não tem como saber se escreveu.
3. **A "escrita final obrigatória" vira um parâmetro na porta** (`forcar=True`) que só existe por
   causa do mecanismo — exatamente o tipo de vazamento que `D-ARQ-04` proíbe ("a porta fala o
   vocabulário do domínio").

O throttle é **cadência de quem chama**, não política de armazenamento. Ele pertence a **U7
`conversa`**, que conduz o streaming e sabe quando o turno terminou. A porta continua honesta: toda
chamada escreve. Isso é a **Q5** abaixo, e se for aceito dispara emenda em `unit-of-work.md` §3 (U7)
e uma nota em `NFR-P-03`.

---

## 3. Perguntas

Responda na tag `[Answer]:` de cada pergunta. Onde eu tenho recomendação, ela está marcada.

---

### Q1 — Ciclo de vida da conexão (`NFR-P-09`)

`NFR-P-09` exige **uma conexão viva por processo** com os PRAGMAs ligados **uma vez, na abertura**.
Falta dizer quem abre.

- **A) Fábrica assíncrona** `abrir_repositorio(caminho) -> RepositorioSQLite`, mais `fechar()`.
  O construtor recebe uma conexão **já aberta e já pragmada**. Quem constrói o objeto à mão sem
  passar pela fábrica recebe um objeto que não funciona — o erro aparece na hora, não depois.
  **(Recomendado)**
- **B) Construtor recebe o caminho** e abre preguiçosamente na primeira operação. Menos cerimônia no
  composition root, mas a primeira chamada carrega o custo de criar esquema e ligar PRAGMAs, e o
  erro de banco corrompido (`NFR-P-07`) aparece **depois** da tela já ter subido, não na
  inicialização como o requisito pede.
- **C) Context manager assíncrono** (`async with abrir(...) as repo:`). Fecha sozinho, mas o
  repositório vive a aplicação inteira — o `async with` acabaria envolvendo todo o `main`, o que é o
  mesmo que (A) com mais indentação.

[Answer]: A

---

### Q2 — Como o composition root descobre onde fica o banco

`Q1a=B` (portão anterior) escolheu escrever à mão as ~12 linhas que resolvem a pasta de dados do SO,
em vez de depender de `platformdirs`.

- **A) Função pura** `caminho_do_banco() -> Path` num módulo próprio; o repositório **recebe o
  `Path` pronto** no construtor. A resolução do SO é testável isoladamente por plataforma, e todo
  teste passa um `tmp_path` sem chegar perto da pasta real do usuário. **(Recomendado)**
- **B) Igual a (A), e mais**: a função honra `FISHINGROD_DATA_DIR` se estiver definida no ambiente.
  Custa 3 linhas e dá uma saída para quem quer o banco noutro disco. Contra: nenhuma história pede
  isso, e é superfície de configuração que passa a existir para sempre.
- **C) O repositório resolve sozinho**, sem parâmetro. Menos peças — e nenhum teste consegue
  apontá-lo para outro lugar sem monkeypatch.

[Answer]: A

---

### Q3 — A forma que `NFR-P-08` exige

`NFR-P-08`: todo o SQL de uma operação numa única função síncrona, sob um único `to_thread`, sem
`await` no meio. A questão é se isso é **convenção** ou **estrutura**.

- **A) Par explícito por operação.** Cada método público faz `async with self._lock:` e
  `await asyncio.to_thread(self._x_sync, ...)`, e cada `_x_sync` abre e fecha a própria transação.
  Lê-se de cima a baixo sem saber de mais nada. Contra: o padrão está repetido 9 vezes e o método
  número 10 pode esquecer um pedaço — `NFR-P-08` volta a ser disciplina.
- **B) Um único auxiliar** `_executar(fn, *args)` que concentra as três coisas — `Lock`, `to_thread`
  e `BEGIN`/`COMMIT`/`ROLLBACK`. Os métodos públicos viram uma linha; os `_x_sync` recebem o cursor
  e **não sabem de transação**. `RN-P-03` deixa de depender de lembrança: um método novo ou passa
  pelo auxiliar ou não tem cursor para trabalhar. **(Recomendado)**
- **C) Decorador.** Mesmo efeito de (B), mas o `Lock` e o `to_thread` ficam invisíveis na assinatura,
  e decorador sobre método assíncrono com `self` é mais difícil de depurar do que de escrever.

[Answer]: B

---

### Q4 — O que é, de fato, o dublê em memória (`PBT-U2-08`)

`PBT-U2-08` diz: para toda sequência de operações, dublê e real produzem o mesmo resultado
observável, inclusive os mesmos erros.

- **A) Estruturas Python puras** (dicionários e listas), com a semântica — versão, ordem, cascata,
  paginação — **reimplementada à mão**. **(Recomendado)**
- **B) `sqlite3` em `:memory:`**, reaproveitando o mesmo código do repositório real. Muito menos
  código para escrever e impossível de divergir.

**O problema de (B) é que ele é bom demais**: se dublê e real são o mesmo código, `PBT-U2-08` passa
**por construção** e não detecta nada. O valor do dublê está em ser um enunciado **independente** do
contrato — duas implementações que discordam revelam que o contrato estava ambíguo. Com (B) essa
propriedade vira decoração.

O custo de (A) é honesto: ~100 linhas a mais, e o dublê pode ter bugs próprios. Só que um bug no
dublê **falha o teste de contrato**, que é precisamente o trabalho dele.

[Answer]: A

---

### Q5 — Onde mora o throttle de 500 ms (o achado da §2)

- **A) Em U7 `conversa`**, que conduz o streaming e sabe quando o turno acabou. O adaptador **sempre
  escreve** o que lhe pedem. `NFR-P-03` ganha nota dizendo que o alvo é medido no fluxo de U7, e
  `unit-of-work.md` §3 (U7) ganha o critério. **(Recomendado — ver §2)**
- **B) Dentro do `RepositorioSQLite`.** Concentra a decisão num lugar só, e nenhuma outra unidade
  precisa saber do assunto. Custo: `PBT-U2-08` precisa de relógio, e a escrita final vira parâmetro
  na porta.
- **C) Um invólucro de porta** (`PersistenciaComThrottle`) que embrulha a real. Mantém o adaptador
  honesto e não polui U7 — mas cria uma terceira implementação da porta que `PBT-U2-08` também
  passaria a ter de cobrir, e o teste de contrato falharia nela por desenho.

[Answer]: A

---

### Q6 — Onde moram `ConflitoDeVersao` e as demais exceções da porta

`U4` precisa capturar `ConflitoDeVersao` sem depender do adaptador.

- **A) Junto do `Protocol`**, em `aplicacao/portas/persistencia.py`. Quem importa a porta importa o
  erro; o adaptador levanta, o serviço captura, e nenhum dos dois conhece o outro. **(Recomendado)**
- **B) Em `dominio/erros.py`**, ao lado de `ErroDeDominio`. Contra: conflito de versão não é
  violação de invariante de domínio — é um fato de armazenamento. `NomeInvalido` diz que o usuário
  errou; `ConflitoDeVersao` diz que dois escreveram ao mesmo tempo.
- **C) Módulo próprio** `aplicacao/portas/erros.py`, para não misturar contrato e erro no mesmo
  arquivo.

[Answer]: A

---

### Q7 — Como `NFR-P-14` (permissões) é aplicado na prática

O `sqlite3` cria o arquivo com a permissão padrão do sistema, e cria também `-wal` e `-shm` ao lado.

- **A) Diretório com `0o700` na criação, e `chmod 0o600` no arquivo do banco depois de abrir.**
  `-wal` e `-shm` ficam protegidos por estarem dentro de um diretório que só o dono atravessa. Em
  Windows, tudo isso é ignorado — a raiz `%LOCALAPPDATA%` já é do usuário. **(Recomendado)**
- **B) Igual, e ainda `chmod` em `-wal` e `-shm` a cada abertura.** Mais explícito; mas esses
  arquivos vão e voltam durante a execução, então a garantia não se sustenta entre aberturas — dá
  sensação de proteção onde a real é o diretório.
- **C) Só o diretório.** Se o banco for copiado para fora, sai com permissão frouxa.

[Answer]: A

---

### Q8 — Quem sabe converter `Ambiente` em JSON

- **A) Um módulo de mapeamento no adaptador.** O domínio (U1) **não ganha** `to_dict`/`from_dict` e
  não é tocado por esta unidade. Se o formato em disco mudar, muda um arquivo de adaptador.
  **(Recomendado)**
- **B) `to_dict`/`from_dict` nas próprias dataclasses de domínio.** Menos código e sempre em dia com
  os campos. Contra: o domínio passa a conhecer o formato de armazenamento, e uma mudança de esquema
  vira commit em `dominio/` — a fronteira que `component-dependency.md` desenhou deixa de valer.

**Sobre o risco de (A)** — alguém acrescenta um campo ao domínio e esquece o mapeador: `PBT-U2-01`
(round-trip) falha, porque o campo novo não sobrevive a salvar-e-carregar. O esquecimento é
detectado, não presumido.

[Answer]: A 

---

### Q9 — O que exatamente `versao_esquema` versiona (`NFR-P-20`, `RN-P-02`)

`RN-P-02` pôs uma coluna `versao_esquema` na linha do ambiente. Ela versiona o **formato do JSON** —
mas as tabelas de anotação, mensagem e uso de ferramenta ficam sem versão nenhuma.

- **A) Só a coluna**, como está hoje. Uma peça só. Contra: uma mudança futura na tabela `anotacao`
  não tem onde ser anunciada, e um banco antigo abre em silêncio com o esquema errado.
- **B) Só `PRAGMA user_version`**, o idioma padrão do SQLite, que versiona o banco inteiro. Contra:
  contradiz `RN-P-02` já aprovada.
- **C) As duas, versionando coisas diferentes**: `user_version` para o esquema **físico** (tabelas,
  índices, chaves), a coluna para o **formato do documento**. Custa uma linha na abertura e
  responde as duas perguntas que vão aparecer numa migração. **(Recomendado)**

[Answer]: C

---

### Q10 — Retentativa dentro do adaptador (`resiliency-baseline` está desativada)

- **A) Nenhuma.** `busy_timeout = 5000` já cobre a espera por trava entre processos, e
  `ConflitoDeVersao` sobe para quem chamou. **(Recomendado)**
- **B) O adaptador retenta o conflito** recarregando e salvando de novo.

**(B) não é possível de fazer certo**: o adaptador tem o `Ambiente` que lhe entregaram, não a
intenção de quem o modificou. Recarregar e regravar por cima é exatamente a escrita cega que
`RN-P-05` existe para impedir. Só o chamador sabe reaplicar a mudança.

[Answer]: A

---

### Q11 — Quantos módulos, e com que fronteira

- **A) Cinco arquivos** em `adaptadores/persistencia/`: `localizacao.py` (pasta do SO),
  `esquema.py` (DDL + PRAGMAs + versões), `mapeamento.py` (`Ambiente` ↔ JSON),
  `repositorio_sqlite.py` (a porta), `repositorio_memoria.py` (o dublê). Cada arquivo tem um motivo
  para mudar. **(Recomendado)**
- **B) Dois arquivos**: `repositorio_sqlite.py` e `repositorio_memoria.py`, com DDL e mapeamento
  dentro do primeiro. Menos navegação; o arquivo principal passa de 400 linhas.
- **C) Um arquivo só.**

[Answer]: A

---

### Q12 — Onde o dublê em memória é publicado

Ele não serve só a esta unidade: os testes de U4, U7 e U8 vão querer uma persistência sem disco.

- **A) Código de produção**, em `adaptadores/persistencia/repositorio_memoria.py`. Qualquer teste de
  qualquer unidade importa normalmente. Ele é uma implementação legítima da porta, não um andaime.
  **(Recomendado)**
- **B) Em `tests/dobles/`.** Não vai no pacote instalado. Contra: testes de outras unidades passam a
  importar de dentro de `tests/`, o que só funciona por acidente de `sys.path`.

[Answer]: B

---

### Q13 — Padrões que **não** entram (confirmação explícita)

Pelas categorias que este estágio é obrigado a percorrer, e dado `resiliency-baseline = No`,
`Q8=A` (single-user, múltiplas instâncias toleradas) e o volume da §7 do NFR Requirements, meu
desenho **não inclui**: cache de leitura, pool de conexões, fila de escrita, disjuntor
(*circuit breaker*), retentativa com recuo exponencial, nem particionamento.

Cada um deles resolve um problema que esta unidade não tem — e todos custam um caminho a mais onde
`RN-P-03` pode quebrar.

- **A) Confirmo — nenhum deles entra nesta iteração.** **(Recomendado)**
- **B) Quero algum deles.** Diga qual e para qual problema observado.

[Answer]: A

---

## 4. O que muda conforme as respostas

| Resposta | Consequência fora desta unidade |
|---|---|
| **Q5=A** | Emenda em `unit-of-work.md` §3 (U7): critério de throttle + escrita final; nota em `NFR-P-03` |
| **Q8=B** | U1 é reaberto para ganhar `to_dict`/`from_dict`; `component-dependency.md` muda |
| **Q9=C** | `RN-P-02` ganha emenda dizendo que a coluna versiona só o documento |
| **Q12=A** | `repositorio_memoria.py` entra no pacote instalado — declarado, não acidental |

Nenhuma outra resposta sai da fronteira de U2.

---

## 5. Execução (2026-08-27)

**Respostas:** Q1=A · Q2=A · Q3=B · Q4=A · Q5=A · Q6=A · Q7=A · Q8=A · Q9=C · Q10=A · Q11=A ·
**Q12=B** · Q13=A. Nenhuma ambígua — nenhum arquivo de clarificação foi necessário.

**Q12=B foi a única divergência da recomendação, e eu estava mais errado do que ela.** Minha
objeção dizia que importar o dublê de dentro de `tests/` "só funciona por acidente de `sys.path`".
Verifiquei antes de acatar: `tests/` já tem `__init__.py`, o pytest insere a raiz do projeto no
caminho, `import tests.dominio` funciona hoje e 41 testes são coletados. A objeção não se sustentava.
A condição que faz a escolha funcionar ficou registrada em `logical-components.md` §1.3:
`tests/dobles/__init__.py` precisa existir.

**Q3=B foi acatada com um ajuste que o desenho revelou.** Um auxiliar virou dois — `_ler` com
`BEGIN` e `_escrever` com `BEGIN IMMEDIATE`. Motivo em `DP-P-03`: em WAL, uma transação diferida que
lê e depois escreve recebe `SQLITE_BUSY` **sem que o `busy_timeout` seja consultado**. Ou seja,
`NFR-P-10` sozinho não cobria `NFR-P-11` — quem o faz valer é o `IMMEDIATE`.

**Fatos medidos, não presumidos** (registrados em `DP-P-02`): Python 3.14.4, SQLite 3.50.4,
`isolation_level=None` → `autocommit == LEGACY_TRANSACTION_CONTROL`, `uuid.uuid7()` disponível.

**Emendas aplicadas:** `unit-of-work.md` §3 (U7) critério 6 · `business-rules.md` (`RN-P-02`) escopo
da versão · `nfr-requirements.md` (`NFR-P-03`) nota de que o mecanismo mora em U7.

**Artefatos:** `nfr-design-patterns.md` (13 padrões `DP-P-01..13` + mapa NFR→componente) e
`logical-components.md` (6 arquivos em `src/`, matriz de dependência sem ciclo, esquema físico).
