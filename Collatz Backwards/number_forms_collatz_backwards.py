from sympy import symbols, simplify, factor

def generate_inverse_families(max_depth=4):
    """
    Generate closed-form inverse Collatz families for each depth.
    Each formula comes from choosing t_i = 2*n_i to ensure (2^t_i-1)/3 is integer.
    """
    families = {0: ["1"], 1: ["2^n"]}

    # Prepare symbolic parameters for exponents
    n_vars = symbols(f'n1:{max_depth+1}', integer=True, positive=True)

    for depth in range(2, max_depth+1):
        expr = 1
        # Apply depth-1 inverse-odd steps, each preceded by doubling 2^(2*n_i)
        for i in range(depth-1):
            expr = (expr * 2**(2*n_vars[i]) - 1) / 3

        expr_simpl = simplify(expr)
        expr_factor = factor(expr_simpl)
        families[depth] = [str(expr_factor)]

    return families


# Example: generate up to depth 4
families = generate_inverse_families(max_depth=4)

# Print formulas
for depth in families:
    print(f"Depth {depth}:")
    for f in families[depth]:
        print("   ", f)
