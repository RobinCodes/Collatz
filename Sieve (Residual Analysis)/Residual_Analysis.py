q = 1
residue_report_limit = 15
relevant_residues = [1]
surviving_residues = []
score = 0
cycles = []

def write_output(*args, filename="output.txt"):
	with open(filename, "a") as f:
		for arg in args:
			f.write(str(arg) + "\n")
		f.write("\n")

def collatz_step(n: int, score: int) -> tuple[int, int]:
	y = 3 * n + 1
	v2 = (y & -y).bit_length() - 1
	
	d = min(v2, q - score)
	return y >> d, d
	
def collatz_sim(n: int) -> bool:
	og_n = n
	score = 0;
	while score < q:
		data = collatz_step(n, score)
		n = data[0]
		score += data[1]
		
	if og_n < n:
		return True # Survives
	elif og_n > n:
		return False # Dies
	else:
		cycles.append(og_n) # Cycle
		return False # Make it die so program continues, we report cycles with the cycles list
		
while True:
	for n in relevant_residues:
		if collatz_sim(n):
			surviving_residues.append(n)
			
	report = [
		100 - (len(set(surviving_residues)) / (2**q) * 100),
		q
	]
	if q <= residue_report_limit:
		report.append(surviving_residues)
	report.append("cycles: " + (str(cycles) if cycles else "none"))

	write_output(*report)

	# Prepare for next iteration

	relevant_residues = []
	for k in surviving_residues:
		relevant_residues.append(k)
		relevant_residues.append(k + 2**q)
		
	q += 1
	surviving_residues = []
	
