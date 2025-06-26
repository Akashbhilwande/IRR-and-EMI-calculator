from flask import Flask, render_template, request
import numpy as np
from scipy.optimize import root_scalar
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# === Financial Functions ===

def npv(rate, cashflows):
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))

def irr(cashflows):
    try:
        result = root_scalar(lambda r: npv(r, cashflows), bracket=[0.00001, 1], method='brentq')
        return result.root if result.converged else None
    except Exception as e:
        logging.warning("IRR calculation failed: %s", e)
        return None

# === Routes ===

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    irr_value = None
    irr_monthly = None
    irr_annual = None
    table = []

    inputs = {
        'amount': '',
        'rate': '',
        'tenure': '',
        'gst_rate': '',
        'loan_or_lease': 'loan',
        'loan_type': 'standard',
        'residual_value': '',
        'payment_frequency': 'monthly'
    }

    if request.method == 'POST':
        try:
            # Parse and validate inputs
            amount = float(request.form.get('loan_amount', 0) or 0)
            rate = float(request.form.get('interest_rate', 0) or 0)
            tenure = int(request.form.get('loan_tenure', 0) or 0)
            gst_rate = float(request.form.get('gst_rate', 0) or 0)
            residual_value = float(request.form.get('residual_value', 0) or 0)
            payment_frequency = request.form.get('payment_frequency', 'monthly')

            loan_or_lease = request.form.get('loan_or_lease', 'loan')
            loan_type = request.form.get('loan_type', 'standard')

            inputs.update({
                'amount': amount,
                'rate': rate,
                'tenure': tenure,
                'gst_rate': gst_rate,
                'loan_or_lease': loan_or_lease,
                'loan_type': loan_type,
                'residual_value': residual_value,
                'payment_frequency': payment_frequency
            })

            if amount <= 0 or rate < 0 or tenure <= 0:
                raise ValueError("Loan amount, interest rate, and tenure must be positive numbers.")

            financed_amount = amount * (1 + gst_rate / 100)
            freq_factor = 1 if payment_frequency == 'monthly' else 3
            rate_periodic = rate / (12 * 100 / freq_factor)
            total_periods = tenure // freq_factor
            principal_base = financed_amount
            cashflows = [-principal_base]

            # Lease type EMI
            if loan_or_lease == 'lease':
                emi = round((amount * rate_periodic) / (1 - (1 + rate_periodic) ** -total_periods), 2)
                balance = amount
                for month in range(1, total_periods + 1):
                    interest = round(balance * rate_periodic, 2)
                    principal = round(emi - interest, 2)
                    balance = round(balance - principal, 2)
                    table.append({
                        'Month': month * freq_factor,
                        'Payment': emi,
                        'Principal': principal,
                        'Interest': interest,
                        'Balance': max(balance, 0)
                    })
                    cashflows.append(emi)
                if residual_value:
                    table[-1]['Payment'] += residual_value
                    cashflows[-1] += residual_value
                result = f"Lease EMI is ₹{emi}"

            # Loan - Standard EMI
            elif loan_type == 'standard':
                emi = round((principal_base * rate_periodic) / (1 - (1 + rate_periodic) ** -total_periods), 2)
                balance = principal_base
                for month in range(1, total_periods + 1):
                    interest = round(balance * rate_periodic, 2)
                    principal = round(emi - interest, 2)
                    balance = round(balance - principal, 2)
                    payment = emi
                    if month == total_periods and residual_value:
                        payment += residual_value
                        cashflows.append(payment)
                    else:
                        cashflows.append(payment)
                    table.append({
                        'Month': month * freq_factor,
                        'Payment': payment,
                        'Principal': principal,
                        'Interest': interest,
                        'Balance': max(balance, 0)
                    })
                result = f"Loan EMI is ₹{emi}"

            # Bullet Payment
            elif loan_type == 'bullet':
                interest_payment = round(principal_base * rate_periodic, 2)
                for month in range(1, total_periods + 1):
                    if month < total_periods:
                        payment = interest_payment
                        principal = 0
                    else:
                        principal = principal_base
                        payment = round(interest_payment + principal + residual_value, 2)
                    balance = principal_base - principal
                    table.append({
                        'Month': month * freq_factor,
                        'Payment': payment,
                        'Principal': principal,
                        'Interest': interest_payment,
                        'Balance': max(balance, 0)
                    })
                    cashflows.append(payment)
                result = f"Bullet Payment: ₹{interest_payment} interest per period, principal ₹{principal_base} at end"

            # Equal Principal
            elif loan_type == 'equal_principal':
                principal_const = round(principal_base / total_periods, 2)
                balance = principal_base
                for month in range(1, total_periods + 1):
                    interest = round(balance * rate_periodic, 2)
                    payment = round(principal_const + interest, 2)
                    if month == total_periods and residual_value:
                        payment += residual_value
                        cashflows.append(payment)
                    else:
                        cashflows.append(payment)
                    balance = round(balance - principal_const, 2)
                    table.append({
                        'Month': month * freq_factor,
                        'Payment': payment,
                        'Principal': principal_const,
                        'Interest': interest,
                        'Balance': max(balance, 0)
                    })
                result = f"Equal Principal: first payment ₹{round(principal_const + principal_base * rate_periodic, 2)}"

            # IRR
            irr_monthly = irr(cashflows)
            if irr_monthly:
                irr_value = round(irr_monthly * 100, 2)
                irr_annual = round(irr_monthly * (12 / freq_factor) * 100, 2)

        except Exception as e:
            logging.exception("Error processing form inputs")
            result = f"Error: {str(e)}"

    return render_template(
        "index.html",
        result=result,
        inputs=inputs,
        irr=irr_value,
        irr_monthly=irr_value,
        irr_annual=irr_annual,
        table=table
    )

if __name__ == '__main__':
    app.run(debug=True,port=8000)