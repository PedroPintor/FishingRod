# D09 — Só a assinatura do Claude, sem chave de API

Status: revisada
Data do status: 2026-10-20

## O que é

O FishingRod conversa com o Claude usando a assinatura que o usuário já paga, pelo login do
Claude. Não existe opção de usar chave de API (pagamento por uso), nem no desenho.

## Por quê

O usuário já paga a assinatura e não precisa gerenciar chave para começar. No início chegou a se
pensar em deixar o desenho pronto para os dois jeitos, mas isso foi retirado: os dois funcionam de
formas bem diferentes (a assinatura mantém uma sessão viva; a chave de API responde pedido a
pedido), e desenhar para algo que não seria construído tinha grande chance de sair errado.

## O que descobrimos

O SDK do Claude só **acrescenta** variáveis de ambiente ao processo que ele abre; ele não remove
nenhuma. Então, se a máquina tiver uma `ANTHROPIC_API_KEY` configurada (ou outra credencial, ou
outro endereço de servidor), ela vazaria para o agente, e a conversa poderia ser cobrada por uso
em vez de usar a assinatura. A solução no código é sobrescrever cada uma dessas variáveis com
texto vazio, sem nunca ler o valor. A lista tem 37 nomes, tirados do próprio programa do Claude
que vem junto com o SDK. Em 2026-10-13 isso foi testado de verdade: com uma chave falsa e um
endereço falso na máquina, a conversa respondeu pela assinatura.

## Onde aparece no código

- `src/fishingrod/adaptadores/sessao/opcoes.py` (`VARIAVEIS_DE_CREDENCIAL` e o `env` em `montar_opcoes`)
- `tests/sessao/test_opcoes.py` e `tests/sessao/test_sdk_real.py`
