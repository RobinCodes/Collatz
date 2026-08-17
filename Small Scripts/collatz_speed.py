"""
compare execution times of binary shifting method to naive method
"""

import time
n = int(input("n: "))

start_time = time.perf_counter()

for i in range(1, n):
    x = i
    while x != 1:
        if x % 2 == 0:
            x //= 2
        else:
            x = 3 * x + 1
            
end_time = time.perf_counter()

naive_time = end_time - start_time
time.sleep(2)

start_time2 = time.perf_counter()
for i in range(1, n):
    x = i
    while x != 1:
        if x & 1 == 0:  # even check using bitwise AND
            x >>= 1    # equivalent to x //= 2
        else:
            x = (x << 1) + x + 1  # equivalent to 3*x + 1

end_time2 = time.perf_counter()

binary_time = end_time2 - start_time2
time.sleep(2)

start_time3 = time.perf_counter()
for i in range(1, n):
    x = i
    while x != 1:
        if x & 1 == 0:  # bitwise AND
            x >>= 1    # bitshift for even
        else:
            x = 3 * x + 1  #naive 3x+1

end_time3 = time.perf_counter()

combined_time = end_time3 - start_time3
time.sleep(2)

print(naive_time)
print(binary_time)
print(combined_time)

# print the fastest
if naive_time < binary_time and naive_time < combined_time:
    print("Naive method is fastest")
elif binary_time < naive_time and binary_time < combined_time:
    print("Binary method is fastest")
else:
    print("Combined method is fastest")

"""
results:
43.7094202041626
67.33496165275574
Naive method is faster for n < 1000001 (10^6)
0.024675846099853516
0.02283191680908203
Binary method is faster for n < 1001 (10^3) 
So:
n < 10^3 : binary
n > 10^3 : naive

Overall combined method is fastest everywhere
3.882727900054306 for n < 100001 (10^5)
"""