def calculate_irr(cash_flows, iterations=100):
    rate = 0.1
    for _ in range(iterations):
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
        d_npv = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
        rate -= npv / d_npv
    return round(rate * 100, 2)