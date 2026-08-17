"""
factorization of numbers 3n+1 for odd n in interval k through n
"""

import sympy

n = int(input("n: "))
k = int(input("k: "))

for i in range(k, n + 1):
    if i % 2 == 1:  # odd
        factors = sympy.factorint(3*i+1)
        # Exclude 2 from the factor keys
        #non_two_factors = [f for f in factors if f != 2]
        #if len(non_two_factors) > 1:
        print(f"{i} -> {3*i+1} = {factors}")