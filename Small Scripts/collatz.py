import time

start_time = time.time()
highest = 0
highest_achieved_by = 0
seq_len = 0
highest_seq_len = 0
longest_achieved_by = 0

# Collatz function
def collatz(n):
    global seq_len, highest, highest_seq_len, highest_achieved_by, longest_achieved_by
    seq_len = 0
    initial = n
    while n != 1: # fastest method is using bitwise operations for the /2 part
        if n & 1 == 0:  # bitwise AND
            n >>= 1    # bitshift for even
        else:
            n = 3 * n + 1
        seq_len += 1
        if n > highest:
            highest = n
            highest_achieved_by = initial
    if seq_len > highest_seq_len:
        highest_seq_len = seq_len
        longest_achieved_by = initial
    return highest, seq_len

# Test the function
for i in range(1, 10**6):
    collatz(i)

end_time = time.time()
print("Execution time:", end_time - start_time)
print("Highest number:", highest, "by", highest_achieved_by)
print("Highest sequence length:", highest_seq_len, "by", longest_achieved_by)
