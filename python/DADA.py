itens = []
nome = input('qual o seu nome? ')
valor_carro = float(input('qual o valor do carro? '))
comissao = int(input('qual a sua comissao? '))
while True:
    opcao = int(input('voce tem itens extras?\n se nao tiver, digite 0 '))
    if opcao != 0:
        item = input('qual o nome do item?')
        preco_item = int(input('qual o preco do item?'))
        itens.append(item)
    else:
        for item in itens:
            print('-',item)
        break