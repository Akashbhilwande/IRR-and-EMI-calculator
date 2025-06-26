from flask import Flask, render_template, request
import numpy as np
from scipy.optimize import root_scalar
import logging
from math import log, pow

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
    inputs = {  # Default inputs
        'asset_cost': '',
        'rate': '',
        'tenure': '',
        'moratorium': '',
        'security_deposit_pct': '',
        'residual_pct': '',
        'advance_rentals': '',
        'upfront_fee_pct': '',
        'supplier_discount_pct': '',
        'payment_frequency': 'monthly',
        'loan_type': 'standard',
        'loan_or_lease': 'lease'
    }

    if request.method == 'POST':
        try:
            # === Input Parsing ===
            params = {
                'asset_cost': float(request.form.get('asset_cost', 0) or 0),
                'rate': float(request.form.get('interest_rate', 0) or 0),
                'tenure_months': int(request.form.get('tenure_months', 0) or 0),
                'moratorium': int(request.form.get('moratorium', 0) or 0),
                'security_deposit_pct': float(request.form.get('security_deposit_pct', 0) or 0),
                'residual_pct': float(request.form.get('residual_pct', 0) or 0),
                'advance_rentals': int(request.form.get('advance_rentals', 0) or 0),
                'upfront_fee_pct': float(request.form.get('upfront_fee_pct', 0) or 0),
                'supplier_discount_pct': float(request.form.get('supplier_discount_pct', 0) or 0),
                'payment_frequency': request.form.get('payment_frequency', 'monthly'),
                'loan_type': request.form.get('loan_type', 'standard'),
                'loan_or_lease': request.form.get('loan_or_lease', 'lease')
            }
            inputs.update(params)

            # === Validations ===
            if params['asset_cost'] <= 0 or params['tenure_months'] <= 0:
                raise ValueError("Asset cost and tenure must be positive")
            if params['advance_rentals'] > params['tenure_months']:
                raise ValueError("Advance rentals cannot exceed total tenure")
            if params['moratorium'] > params['tenure_months']:
                raise ValueError("Moratorium period cannot exceed total tenure")

            # === Core Calculations ===
            # 1. Net Cost Calculation
            net_cost = params['asset_cost'] * (1 - params['supplier_discount_pct']/100)
            
            # 2. Security Deposit & Upfront Fee
            deposit_amt = net_cost * (params['security_deposit_pct']/100)
            fee_amt = net_cost * (params['upfront_fee_pct']/100)
            
            # 3. Residual Value
            residual_amt = net_cost * (params['residual_pct']/100) if params['residual_pct'] > 0 else 0
            
            # 4. Principal Calculation
            principal = net_cost - deposit_amt + fee_amt
            
            # 5. Payment Frequency Adjustment
            freq_map = {'monthly': 1, 'quarterly': 3}
            freq_factor = freq_map.get(params['payment_frequency'], 1)
            total_periods = params['tenure_months'] // freq_factor
            periodic_rate = (params['rate']/100) * (freq_factor/12)
            
            # 6. Moratorium Handling (Interest Capitalization)
            if params['moratorium'] > 0 and periodic_rate > 0:
                principal *= pow(1 + periodic_rate, params['moratorium'])
            
            # 7. EMI Calculation
            def calc_emi(P, r, n, R=0):
                if r == 0:
                    return (P - R) / n
                discount_factor = (1 - pow(1 + r, -n))
                return (r * (P - R / pow(1 + r, n))) / discount_factor

            # 8. Cashflow Construction
            cashflows = [-principal]
            table = []
            emi = 0
            
            if params['loan_or_lease'] == 'lease':
                # Lease-specific calculations
                remaining_periods = total_periods - params['advance_rentals']
                if remaining_periods <= 0:
                    raise ValueError("Advance rentals exceed total payment periods")

                emi = calc_emi(principal, periodic_rate, remaining_periods, residual_amt)
                emi = round(emi, 2)
                
                # Add advance rentals as upfront payments
                for _ in range(params['advance_rentals']):
                    cashflows.append(emi)
                
                # Regular payments with residual
                bal = principal
                for period in range(1, remaining_periods + 1):
                    interest = round(bal * periodic_rate, 2)
                    principal_pmt = round(emi - interest, 2)
                    bal -= principal_pmt
                    
                    final_payment = emi
                    if period == remaining_periods and residual_amt > 0:
                        final_payment += residual_amt
                    
                    cashflows.append(final_payment)
                    table.append({
                        'Period': period * freq_factor,
                        'Payment': final_payment,
                        'Principal': principal_pmt,
                        'Interest': interest,
                        'Balance': max(round(bal, 2), 0)
                    })
                result = f"Lease EMI: ₹{emi:.2f}"
            else:
                # Loan-specific calculations
                remaining_periods = total_periods - params['advance_rentals']
                if params['loan_type'] == 'bullet':
                    emi = round(principal * periodic_rate, 2)
                    # Bullet payment at end
                    for _ in range(params['advance_rentals']):
                        cashflows.append(emi)
                    for period in range(1, remaining_periods):
                        cashflows.append(emi)
                    final_payment = emi + principal + (residual_amt if residual_amt else 0)
                    cashflows.append(final_payment)
                else:
                    emi = calc_emi(principal, periodic_rate, remaining_periods, residual_amt)
                    emi = round(emi, 2)
                    for _ in range(params['advance_rentals']):
                        cashflows.append(emi)
                    for _ in range(remaining_periods):
                        cashflows.append(emi)
                    if residual_amt > 0:
                        cashflows[-1] += residual_amt

                result = f"{params['loan_type'].title()} EMI: ₹{emi:.2f}"

            # 9. IRR Calculation with proper annualization
            irr_periodic = irr(cashflows)
            if irr_periodic:
                irr_monthly = round(irr_periodic * 100, 2)
                if params['payment_frequency'] == 'monthly':
                    irr_annual = round((pow(1 + irr_periodic, 12) - 1) * 100, 2)
                else:  # quarterly
                    irr_annual = round((pow(1 + irr_periodic, 4) - 1) * 100, 2)
                irr_value = irr_monthly

        except Exception as e:
            logging.exception("Calculation error")
            result = f"Error: {str(e)}"

    return render_template('test_index.html', 
                         result=result,
                         inputs=inputs,
                         irr=irr_value,
                         irr_monthly=irr_monthly,
                         irr_annual=irr_annual,
                         table=table)

if __name__ == '__main__':
    app.run(debug=True,port=8001)