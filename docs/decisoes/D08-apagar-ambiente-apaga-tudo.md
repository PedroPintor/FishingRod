# D08 — Apagar um ambiente apaga tudo, sem lixeira, com aviso e confirmação

Status: revisada
Data do status: 2026-10-20

## O que é

Apagar um ambiente apaga tudo o que está dentro dele: frentes, tarefas, conversas, memória e a
wiki. Não há lixeira nem como desfazer. Por isso, antes de apagar, a tela avisa o perigo e pede
confirmação.

## Por quê

Nas palavras do Pedro: "quando apagarmos já vamos apagar tudo e apenas ter uma mensagem de aviso e
de confirmação antes". Acumular ambientes de teste incomodaria rápido no uso real, e uma lixeira
seria mais coisa para construir sem necessidade agora. A ordem é: primeiro o banco, depois a pasta
da wiki. Se falhar no meio, sobra no máximo uma pasta sem uso, nunca um ambiente vivo sem wiki.
A confirmação é responsabilidade da tela; o serviço só apaga.

## Onde aparece no código

- `src/fishingrod/aplicacao/servicos/servico_de_ambiente.py` (`apagar_ambiente`)
- `src/fishingrod/adaptadores/persistencia/repositorio_sqlite.py` (`apagar_ambiente`)
- `src/fishingrod/adaptadores/wiki/wiki_de_arquivos.py` (`apagar`)
