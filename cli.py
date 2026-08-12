from Ambiente.sessao import (
     Mensagem
)

from Ambiente.ambiente import (
     Ambiente
)

def barra_status(status: dict) -> str:
     return f"Nome Chat: {status['nome_chat']}   Memoria: {status['memoria']}   N° de Iteracoes: {status['n_iteracoes']}"

def formatar_output(output: list[Mensagem]) -> str:
    # o terminal ja ecoou o que o usuario digitou, entao pula tipo "usuario"
    return "\n".join(
         f"[{m.autor}]: {m.texto}"
         for m in output
         if m.tipo != "usuario"
     )

def iniciar(ambiente: Ambiente):
     while ambiente.ativo:
          mensagem = input("> ")
          output = ambiente.enviar(mensagem=mensagem)

          print(formatar_output(output))
          print(barra_status(ambiente.obter_status()))
          

def menu_inicial():
     ambiente_principal = Ambiente('<NOME_AMBIENTE>')

     print("Bem vindo ao FISHING ROD")
     print("seu ambiente de trabalho com IA")
     while True:
          print("-"*20 ,"MENU INICIAL", "-"*20)
          print("[1] Criar novo    Projeto Fishing Rod")
          print("[2] Iniciar       Projeto Fishing Rod")
          print("[3] Listar        Projetos Fishing Rod")
          print("[4] Sair")

          
          mensagem = input(">")
          if mensagem == "1":
               nome = input("Digite o nome do projeto > ")
               p = ambiente_principal.criar_projeto(nome=nome)
               if p:
                    print(f"Projeto {p.nome} criado")
               else: 
                    print("Projeto ja Existe - Tente outro nome de Projeto")
          elif mensagem == "2":
               print("Lista de Projetos: ")
               print(ambiente_principal.listar_projetos())
               nome_p = input("Digite o Nome do Projeto > ")
               p = ambiente_principal.buscar_projeto(nome_p)
               if p:
                    indice, projeto = p
                    ambiente_principal.trocar_projeto(indice)
                    print(f"Projeto trocado para {projeto.nome}")
                    iniciar(ambiente=ambiente_principal)
                    break 
               else:
                    print("Projeto nao Encontrado")
          elif mensagem == "3":
               print(ambiente_principal.listar_projetos())
          else:
               break
     
def main():
     print('FISHING ROD')
     print('INICIANDO...')
     print('-'*50)
     menu_inicial()


if __name__ == "__main__":
     main()
