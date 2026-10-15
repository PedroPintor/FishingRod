# Tech Stack Decisions — U3 `wiki`

**Fase:** CONSTRUCTION · **Unidade:** `U3 wiki` · **Data:** 2026-09-23

---

## 1. Decisões

| # | Decisão | Origem | Alternativa rejeitada |
|---|---|---|---|
| **TS-W-01** | **`pathlib` da biblioteca padrão** para toda manipulação de caminho, com `Path.resolve()` e `Path.is_relative_to()` na verificação de confinamento | Q2=B, `NFR-W-05` | `os.path.realpath` + comparação de string — `is_relative_to` compara componentes, não prefixo de texto, e não confunde `/dados/wiki2` com `/dados/wiki` |
| **TS-W-02** | **`asyncio.to_thread`** atravessa a fronteira `async` → filesystem síncrono, **uma vez por operação da porta** | Q1=A, `NFR-W-03` | Chamada síncrona direta (congela a TUI durante a renderização); `aiofiles` (dependência nova, e não cobre `iterdir`/`mkdir`) |
| **TS-W-03** | **`os.replace`** publica o `index.md`, a partir de temporário no **mesmo diretório** | Q5=B, `NFR-W-11` | Escrita direta (índice truncado é falha silenciosa); marcador de fim de arquivo (protocolo inventado dentro de um markdown que humano lê) |
| **TS-W-04** | **`unicodedata.normalize("NFKD", ...)`** + descarte de combinantes implementa o slug de `RN-W-04`, precedido de uma tabela mínima de substituição (`&` → `e`) | `R-NFR3-2` | `python-slugify`, `unidecode` — dependência de runtime para 15 linhas |
| **TS-W-05** | **`open(..., encoding="utf-8", newline="\n")`** em toda escrita; leitura em **UTF-8 estrito** | `NFR-W-14`, `NFR-W-10`, Q6=A | `errors="replace"` (grava a corrupção de volta via `RN-W-26`); `newline` padrão (CRLF no Windows quebra `PBT-U3-02`) |
| **TS-W-06** | **`logging` da stdlib**, logger `fishingrod.wiki` com `NullHandler` | Q8=A, `NFR-W-16` | Sem log — deixaria `RN-W-20` invisível, que é o único evento silencioso por desenho |
| **TS-W-07** | Testes: **`pytest` + `hypothesis`** (já em `dependency-groups.dev`), com `tmp_path` como substrato e **sem duplo em memória** | Q9=A, Q3=A, `NFR-W-18`, `NFR-W-19` | `tests/dobles/wiki.py` — um duplo sem filesystem não pode reproduzir o confinamento |
| **TS-W-08** | **Zero dependências de runtime.** `dependencies = []` permanece | `R-NFR3-1`, `NFR-W-08`, herda `TS-P-09` | — |

**Nada aqui acrescenta pacote ao `pyproject.toml`.** O primeiro pacote de runtime do projeto
continua sendo o `claude-agent-sdk`, em **U6** — a mesma frase que `tech-stack-decisions.md` de U2
escreveu, e que continua verdadeira uma unidade depois.

---

## 2. A decisão que exigiu mais justificativa: `Path.resolve()` sem criar a raiz (Q2)

O Functional Design deixou uma lacuna nomeada: `RN-W-07` manda comparar o caminho resolvido com a
raiz resolvida, mas `renderizar_index` é justamente quem **cria** a raiz (`RN-W-25`). Antes disso,
ela não existe.

### O que foi verificado antes de decidir

Em Python, `Path.resolve()` sobre caminho inexistente **não levanta** — `strict=False` é o padrão
desde 3.6 — e resolve o prefixo que existe. Ou seja: a verificação não quebra com a raiz ausente;
ela apenas cobre menos do que parece cobrir.

### Por que B, e não A

A alternativa (A) — criar a raiz antes de qualquer operação — daria a garantia mais forte, e o
custo estava escondido na letra miúda: `listar` e `ler` passariam a **criar diretório**. O
Functional Design já especificou que `listar` sobre raiz inexistente devolve lista vazia sem
levantar, porque *"a wiki ainda não foi renderizada, e isso não é erro"*. Fazer uma operação de
leitura ter efeito colateral de escrita para satisfazer uma verificação de segurança é o tipo de
troca que se paga depois, em um bug que ninguém relaciona com a causa.

**B compensa a garantia menor aplicando a etapa 3 em cada caminho de arquivo, não só na raiz** —
que é onde o ataque realmente aterrissa. Um título hostil produz uma **folha**; um symlink plantado
dentro da pasta de dados também. Nenhum dos dois é prefixo.

### O que fica descoberto, dito por extenso

Enquanto a raiz não existe, a garantia é de **prefixo**, não de folha. O cenário que isso deixaria
passar exige um symlink plantado **dentro da pasta de dados do próprio usuário**, antes de a wiki
nascer — ou seja, exige que o atacante já escreva onde o app escreve. Nesse ponto ele não precisa
da wiki para nada. Risco aceito, e registrado aqui em vez de omitido.

---

## 3. A decisão que diverge de U2, e por quê: sem duplo em memória (Q9)

`Q12=B` de U2 criou `tests/dobles/` com um duplo da porta de persistência, e a decisão se provou
certa lá — eu havia objetado e a objeção não se sustentou.

Aqui o argumento **não se transfere**, e a razão é concreta: o que justificava o duplo era evitar
SQLite em teste de serviço. O substrato desta unidade é **uma pasta**, e o `tmp_path` do pytest já
entrega uma pasta descartável por teste, isolada, apagada no fim. O duplo seria o real com mais
passos.

O argumento que fecha: um duplo em memória **não tem filesystem**, logo não pode reproduzir
`resolve()`, symlink nem `is_relative_to` — ou seja, não pode reproduzir `RN-W-07`, a regra mais
importante da unidade. U4 e U8 passariam a testar contra um objeto que concorda com eles justamente
onde o real poderia discordar.

---

## 4. Riscos aceitos

| # | Risco | Decisão que o cria | Mitigação |
|---|---|---|---|
| **1** | A etapa 3 de `RN-W-07` (symlink) **não é executada no Windows**, que é a máquina do dono | Q3=A | Teste separado e nomeado, `skipif` explícito; as etapas 1 e 2 rodam em toda plataforma; cobertura real em CI Linux |
| **2** | Dois caminhos de leitura de frontmatter podem divergir | Q4=E | `NFR-W-20`: `PBT-U3-03` e `PBT-U3-04` cruzam os dois |
| **3** | Enquanto a raiz não existe, o confinamento garante prefixo, não folha | Q2=B | §2 acima; exige acesso de escrita à pasta de dados do usuário, que já é jogo perdido |
| **4** | Duas instâncias do app na mesma wiki podem se atropelar | Q7=A (Functional Design) | `NFR-W-15`: risco declarado, não suportado. `os.replace` garante que ao menos o índice nunca fica pela metade |
| **5** | Página ilegível some do índice sem aviso na tela | Q6=A + `RN-W-20` | `NFR-W-16`: `WARNING` no logger com caminho e motivo; o arquivo **não é tocado** |
