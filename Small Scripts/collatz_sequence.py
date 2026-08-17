import sympy

n = int(input("n: "))
seq = [n]

"""
implemented binary shifting for fun
the code is for checking the seq and binary seq of an n (collatz sequence), also the
seq factorized
"""

while n != 1:
    if n % 2 == 0:
        n //= 2
    else:
        n = 3 * n + 1
    seq.append(n)
    
print("Collatz sequence:", seq)
binary_seq = [format(i, 'b') for i in seq]
print("Binary Collatz sequence:", binary_seq)
factorized_seq = [str(sympy.factorint(i)) for i in seq]
print("Factorized Collatz sequence:", " -> ".join(factorized_seq))