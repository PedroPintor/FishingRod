# D22 — A conversa continua pela memória do próprio Claude

Status: revisada
Data do status: 2026-10-21

## O que é

Quando volto a um chat depois de fechar o programa (ou de desligar o chat), o agente retoma a
conversa pela memória do próprio Claude: o Claude guarda a conversa na pasta dele
(`~/.claude/projects/`), o FishingRod guarda só o código dela para cada chat e, ao religar, pede
ao Claude para continuar dali (a opção `resume` do SDK).

As mensagens também ficam no banco do FishingRod. Cada cópia tem um uso:

- **A do banco** é a que a tela mostra. Ela é nossa e funciona com qualquer IA.
- **A do Claude** é a que o agente usa para lembrar. Ela é do Claude e só serve para ele.

Se o Claude não achar a conversa (a pasta foi apagada, é outro computador), o chat mostra um aviso,
a conversa recomeça do zero e o texto antigo continua na tela.

Esta decisão derruba a proibição do AI-DLC de deixar o Claude guardar a conversa (DP-S-13, a opção
`no-session-persistence`, conferida pela medição 15), que nunca tinha sido revisada.

## Por quê

Foram comparados dois caminhos, na conversa sobre o card 002:

- **O FishingRod reenvia o histórico do banco** a cada vez que um chat religa. Dá controle total e
  funciona com qualquer IA, mas gasta muito mais: uma conversa longa seria mandada inteira de novo
  a cada vez que o programa reabrisse.
- **O Claude retoma pela memória dele.** É mais barato, porque o Claude aproveita o cache da
  conversa e guarda até as ferramentas usadas, e não reinventa o que o Claude Code já faz.

A ideia do Pedro juntou os dois: o adaptador do Claude usa o que o Claude já faz, como um
adaptador de software usa o que cada sistema já oferece, e o FishingRod continua com a própria
cópia para a tela. O núcleo não fica preso ao Claude ([D19](D19-nucleo-nao-depende-do-claude.md)):
a porta só diz "abre este chat retomando de onde parou", e um adaptador de outra IA pode cumprir
isso reenviando o histórico.

## Onde aparece no código

Entra com o [card 002](../cards/002-conversar-com-o-agente.md):

- `src/fishingrod/adaptadores/sessao/opcoes.py` (sai o `no-session-persistence`; entra o `resume`)
- `src/fishingrod/aplicacao/portas/sessao.py` (abrir retomando, com um marcador opaco)
- `tests/sessao/test_opcoes.py`, `tests/sessao/test_sdk_real.py` (a medição 15 se inverte)

## Pode melhorar

- **Retomar quando a conversa do Claude sumiu:** hoje recomeça do zero, com um aviso; dá para
  conferir a instalação e a pasta do Claude e reenviar o histórico do nosso banco — por quê: o
  usuário não perde o contexto. Ideia: [conferir o Claude e retomar sem ele](../ideias/conferir-o-claude-e-retomar-sem-ele.md).
