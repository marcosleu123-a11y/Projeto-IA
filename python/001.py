#1 - Solicite ao usuário que insira um número
# e,  em seguida, use uma estrutura if else para determinar se o número é par ou ímpar.

numero = int(input('digite um numero '))
print('=' * 100)
if numero % 2:
    print('ele é impar ')
else:
    print('ele é par')
