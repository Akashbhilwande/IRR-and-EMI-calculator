def calculate_emi(principal, annual_rate, years):
    r = annual_rate / 100 / 12  # Monthly interest rate
    n = int(years * 12)  # Total number of months (ensure it's an integer)
    
    if r == 0:
        monthly_payment = principal / n  # If interest rate is zero
    else:
        monthly_payment = (principal * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    
    return monthly_payment, n  # Return n as well to use it in cash flow

def npv(rate, cash_flows):
    """Calculate Net Present Value for a given rate"""
    return sum(cash_flow / ((1 + rate) ** i) for i, cash_flow in enumerate(cash_flows, start=1))

def npv_derivative(rate, cash_flows):
    """Calculate the derivative of NPV for a given rate"""
    return sum(-i * cash_flow / ((1 + rate) ** (i + 1)) for i, cash_flow in enumerate(cash_flows, start=1))

def calculate_irr_newton_raphson(principal, monthly_payment, years, guess=0.01, max_iterations=1000, tolerance=1e-6):
    """Calculate IRR using the Newton-Raphson method"""
    n = int(years * 12)  # Number of months (ensure it's an integer)
    # Build the cash flow array: -principal (initial outflow) and monthly EMI for each month
    cash_flows = [-principal] + [monthly_payment] * n

    rate = guess
    for _ in range(max_iterations):
        f = npv(rate, cash_flows)
        df = npv_derivative(rate, cash_flows)
        if df == 0:
            return None  # Avoid division by zero
        new_rate = rate - f / df
        if abs(new_rate - rate) < tolerance:
            return new_rate
        rate = new_rate

    return None  # IRR could not be calculated within the given iterations

def main():
    principal = float(input("Enter loan amount: "))
    nominal_rate = float(input("Enter nominal annual interest rate (in %): "))
    years = float(input("Enter loan tenure (in years): "))

    # Calculate monthly payment using the EMI formula
    monthly_payment, n = calculate_emi(principal, nominal_rate, years)
    print(f"Monthly EMI: {monthly_payment:.2f}")

    # Calculate IRR using Newton-Raphson method
    irr = calculate_irr_newton_raphson(principal, monthly_payment, years)
    if irr is not None:
        annual_irr = (1 + irr) ** 12 - 1  # Convert monthly IRR to annual
        print(f"Calculated IRR (annual): {annual_irr * 100:.2f}%")
    else:
        print("IRR could not be calculated.")

if __name__ == "__main__":
    main()
