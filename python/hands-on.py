opcao = 0
notas = []
while True:
    print("\n--- Sistema de Avaliação Interativa ---")
    print("1 - Inserir nota")
    print("2 - Exibir média")
    print("3 - Exibir quantidade de notas acima da média")
    print("4 - Exibir maior e menor nota")
    print("5 - Sair")
    
    opcao = int(input("Digite a sua opção: "))
    

    if opcao == 1:
        nota1 = float(input("Digite a sua nota para adicionar: "))
        if nota1 < 0:
            print("Nota inválida. Por favor, insira uma nota não negativa.")
        else:
            notas.append(nota1)
            print("Nota adicionada com sucesso!")
        

    elif opcao == 2:
        nota = 0
        cont = 0
        for num in notas:
            nota += num
            cont += 1
        res = nota / cont
        print(f"A média das {cont} notas é: {res:.2f}")

    elif opcao == 3:
        print("Notas acima de 6:")

    
        for nota in notas:
            if nota > 6:
                  print(nota)
                
    elif opcao == 4:
        if notas:
            print(f"Maior nota: {max(notas)}")
            print(f"Menor nota: {min(notas)}")
        else:
            print("Nenhuma nota registrada ainda.")

    elif opcao == 5:
            print("Saindo do sistema...")
            break
    
    else:
            print("Opção inválida. Por favor, escolha uma opção válida.")