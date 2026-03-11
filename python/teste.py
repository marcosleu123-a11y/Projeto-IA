opcao = int(input('escolha uma opcao '))
while opcao == 1 or 2 in range(1):
    if opcao == 1:
        print('vc escolheu opcao 1')
    elif opcao == 2:
        print('vc escolher a 2')
    else:
        print(f'escreveu outro numero {opcao}')