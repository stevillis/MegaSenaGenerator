from random import randint, sample
from tkinter import *
from tkinter import scrolledtext


class MegaSenaGenerator():
    def __init__(self):
        self.__window = Tk()
        self.__qtd_apostas = IntVar()

        self.__window.geometry("300x200")
        self.__window.title("Mega-Sena Generator")
        self.__window.resizable(False, False)

        Label(self.__window, text="Quantidade de apostas: ").grid(row=0, column=0)
        Entry(self.__window, textvariable=self.__qtd_apostas).grid(row=0, column=1)
        Button(self.__window, text="Gerar", command=self.__sorteia).grid(row=0, column=2)

        self.__window.mainloop()

    def __sorteia(self):
        contador = 0
        str_numeros_sorteados = ''

        while contador < self.__qtd_apostas.get():
            numeros_sorteados = self.__gerarAleatorios()
            contador += 1
            str_numeros_sorteados += f'Aposta {contador}: {str(numeros_sorteados).replace("[", "").replace("]", "")}' + '\n'

        self.__text = scrolledtext.ScrolledText(self.__window)
        self.__text.config(width=35, height=10)
        self.__text.grid(row=1, column=0, columnspan=3)
        self.__text.insert(END, str_numeros_sorteados)
        self.__text.config(state=DISABLED)

    def __gerarAleatorios(self):
        lista_sorteados = []
        while len(lista_sorteados) < 10:
            # Gera 10 números aleatórios entre 1 e 60
            numero_sorteado = randint(1, 60)
            if numero_sorteado not in lista_sorteados:
                lista_sorteados.append(numero_sorteado)
        else:
            # Seleciona, aleatoriamente, 6 dos 10 números aleatórios gerados
            lista_sorteados = sample(lista_sorteados, 6)
            lista_sorteados.sort()

        return lista_sorteados


if __name__ == '__main__':
    teste = MegaSenaGenerator()
