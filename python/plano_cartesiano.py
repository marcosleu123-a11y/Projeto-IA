"""
Programa que identifica o quadrante de um ponto no plano cartesiano
e exibe representação visual em ASCII.
"""
import os

print('''       y
                ↑
                │
                │
                │
────────────────┼───────────────→ x
                │
                │
                │''')


def quadrante1():
    '''mostra o plano cartesiano'''
    print('''                ↑
                │
                │       x
                │
────────────────┼───────────────→ x
                │
                │
                │''')


def quadrante2():
    '''mostra o plano cartesiano'''
    print('''                y
                ↑
                │
      x         │
                │
────────────────┼───────────────→ x
                │
                │
                │''')


def quadrante3():
    '''mostra o plano cartesiano'''
    print('''                ↑
                │
                │
                │
────────────────┼───────────────→ x
                │
        x       │
                │''')


def quadrante4():
    '''mostra o plano cartesiano'''
    print('''                ↑
                │
                │
                │
────────────────┼───────────────→ x
                │
                │       x
                │''')


cord_1 = int(input('digite a primeira coordenada: '))
cord_2 = int(input('digite a segunda coordenada: '))

if cord_1 > 0 and cord_2 > 0:
    os.system('cls')
    print('primeiro quadrante\n')
    quadrante1()

elif cord_1 < 0 and cord_2 > 0:
    os.system('cls')
    print('segundo quadrante\n')
    quadrante2()
elif cord_1 < 0 and cord_2 < 0:
    os.system('cls')
    print('terceiro quadrante\n')
    quadrante3()
else:
    os.system('cls')
    print('quarto quadrante\n')
    quadrante4()
