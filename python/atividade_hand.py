print('''            ┌───────────────────────────┐
            │      ASSISTENTE IA        │
            └───────────────────────────┘
                     ┌───────────────┐
                     │   ◉     ◉     │
                     │      ───      │
                     │   \_______/   │
                     └───────┬───────┘''')

nome = input("Digite o seu nome: ")

print('1 - Calcular média (duas notas) ')
print('2 - Verificar situação')
print('3 - Sair ')
opcao = input('escolha uma opcão: ')
if opcao == '1':
    nota1 = float(input("Digite a primeira nota: "))
    nota2 = float(input("Digite a segunda nota: "))
    nota3 = (nota1 + nota2) / 2
    print(nota3)
    opcao = input('escolha uma opcão: ')


if opcao == '2':
    if nota3 >= 6:
        print(f'Voce foi aprovado {nome} (:')
    else:
        print(f'voce foi reprovado {nome} ):')

    opcao = input("escolha uma opção: ")
if opcao == "3":
    print("Assistente de IA finalizado.")

