"""ParserDeComando: tradutor de sintaxe da barra `/` (U5, RN-AC-39..42).

So separa o nome do texto. Nao conhece o catalogo (Q9=A) nem o alvo (R-FD5-3),
e por isso serve igual para as acoes e para os comandos da tela (`/ajuda`,
`/sair`), que sao de U9. Repartir o texto pelos parametros de uma acao e do
catalogo (argumentos.py), que e quem sabe quais parametros ela tem.

Nao importa nada do projeto: e funcao pura de texto.

"Espaco" e o que str.isspace() diz que e (R-CG5-6) - a mesma definicao de
strip() e de split(), e a mesma que o dominio usa para recusar nome vazio.
"""

from dataclasses import dataclass

PREFIXO = "/"


@dataclass(frozen=True)
class ComandoDigitado:
    """O que veio depois de `/` ate o primeiro espaco (pode ser vazio), e o
    resto da linha sem os espacos das pontas. Nao sabe se o nome e uma acao do
    catalogo ou um comando da tela."""

    nome: str
    texto: str = ""


class ParserDeComando:
    """Sem estado: os metodos sao de instancia so para U9 poder recebe-lo
    montado, como os outros componentes."""

    def detectar(self, entrada: str) -> bool:
        """RN-AC-39, G9: a barra precisa ser o PRIMEIRO caractere. Espaco antes
        dela faz a entrada ser conversa, e nao comando."""
        return entrada.startswith(PREFIXO)

    def interpretar(self, entrada: str) -> ComandoDigitado:
        """RN-AC-40. Os espacos entre o nome e o texto e os das pontas saem; os
        de DENTRO do texto ficam como foram digitados (TD-11). Maiuscula e
        acento tambem ficam: quem compara e o catalogo.

        `/` sozinho da nome vazio, que o catalogo responde com
        ACAO_DESCONHECIDA. Para toda entrada que comeca com `/`, nunca levanta;
        entrada que nao comeca e erro de quem chamou sem `detectar`.
        """
        if not self.detectar(entrada):
            raise ValueError("interpretar exige uma entrada que comece com '/'")
        corpo = entrada[len(PREFIXO):]
        for posicao, caractere in enumerate(corpo):
            if caractere.isspace():
                return ComandoDigitado(corpo[:posicao], corpo[posicao:].strip())
        return ComandoDigitado(corpo, "")

    def formatar(self, comando: ComandoDigitado) -> str:
        """RN-AC-41: a inversa de interpretar, para nome sem espaco e texto sem
        espaco nas pontas - que e tudo o que interpretar produz. Fora disso, a
        linha formatada nao volta igual, e isso nao e verificado aqui."""
        if comando.texto:
            return f"{PREFIXO}{comando.nome} {comando.texto}"
        return f"{PREFIXO}{comando.nome}"
