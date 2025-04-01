# -*- coding: utf-8 -*-
"""
Created on Mon Mar 31 22:06:48 2025

@author: BiaBN
"""
import numpy as np
# Criar uma matriz 100x100 com números aleatórios entre 0 e 1000
matriz = np.random.randint(0, 1000, (100, 100))

# Recortar a primeira linha e listar os valores
primeira_linha = matriz[0, :]
print("Primeira linha:", primeira_linha)

# Determinar o valor da última linha e coluna
valor_ultima = matriz[-1, -1]
print("Valor na última linha e última coluna:", valor_ultima)
