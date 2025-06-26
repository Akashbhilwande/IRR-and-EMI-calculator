def calculate_loan(amount, rate, term, method):
    if method == 'EMI':
        r = rate / 12 / 100
        emi = amount * r * (1 + r) ** term / ((1 + r) ** term - 1)
        return f"Monthly EMI: {round(emi, 2)}"
    elif method == 'Equal Principal':
        principal = amount / term
        return f"Monthly Principal Payment: {round(principal, 2)}"
    else:
        return "Invalid method"