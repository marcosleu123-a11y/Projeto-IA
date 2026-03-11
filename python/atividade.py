
print('''            ┌───────────────────────────┐
            │      ASSISTENTE IA        │
            └───────────────────────────┘
                     ┌───────────────┐
                     │   ◉     ◉     │
                     │      ───      │
                     │   \_______/   │
                     └───────┬───────┘''')

print("1 - Calcular média")
print("2 - Verificar situação")
print("3 - Calcular média de três notas")
print("4 - Sair")

nome = str(input("Digite o seu nome: "))

while True:
    opcao = int(input("Escolha uma opção: "))
    if opcao == 1:
        nota1 = float(input("Digite a sua primeira nota: "))
        nota2 = float(input("Digite a sua segunda nota: "))
        media = (nota1 + nota2) / 2
        print(f"A sua média é {media}")
        if 7 > media >= 6:
            print("Aprovado, Regular")
        elif 9 > media >=7:
            print("Aprovado, Bom")
        elif media >= 9:
            print("Aprovado, Excelente")
        else:
            print("Reprovado")
    elif opcao == 2:
        verificar_media = float(input("Digite a sua média: "))
        if 7 > verificar_media >= 6:
            print("Aprovado, Regular")
        elif 9 > verificar_media >=7:
            print("Aprovado, Bom")
        elif verificar_media >= 9:
            print("Aprovado, Excelente")
        else:
            print("Reprovado")
    elif opcao == 3:
        nota1 = float(input("Digite a sua primeira nota: "))
        nota2 = float(input("Digite a sua segunda nota: "))
        nota3 = float(input("Digite a sua terceira nota: "))
        res = (nota1 + nota2 + nota3) / 3
        print(f"A sua média é {res}")         
    else:
        print("Assistente Acadêmico fechada")
        print("=== Assistente Acadêmico ===")
        break