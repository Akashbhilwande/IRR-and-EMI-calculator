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

    # Default input placeholders
    inputs = {
        'asset_cost': '',
        'interest_rate': '',
        'tenure_months': '',
        'moratorium': '',
        'security_deposit_pct': '',
        'residual_pct': '',
        'advance_rentals': '',
        'upfront_fee_pct': '',
        'supplier_discount_pct': '',
        'gst_pct': '',
        'payment_frequency': 'monthly'
    }

    if request.method == 'POST':
        try:
            # Parse and validate inputs
            asset_cost            = float(request.form.get('asset_cost', 0) or 0)
            rate                  = float(request.form.get('interest_rate', 0) or 0)
            tenure_months         = int(request.form.get('tenure_months', 0) or 0)
            moratorium            = int(request.form.get('moratorium', 0) or 0)
            security_deposit_pct  = float(request.form.get('security_deposit_pct', 0) or 0)
            residual_pct          = float(request.form.get('residual_pct', 0) or 0)
            advance_rentals       = int(request.form.get('advance_rentals', 0) or 0)
            upfront_fee_pct       = float(request.form.get('upfront_fee_pct', 0) or 0)
            supplier_discount_pct = float(request.form.get('supplier_discount_pct', 0) or 0)
            gst_pct               = float(request.form.get('gst_pct', 0) or 0)
            payment_frequency     = request.form.get('payment_frequency', 'monthly')

            # Update inputs for template (to preserve form values)
            inputs.update({
                'asset_cost': asset_cost,
                'interest_rate': rate,
                'tenure_months': tenure_months,
                'moratorium': moratorium,
                'security_deposit_pct': security_deposit_pct,
                'residual_pct': residual_pct,
                'advance_rentals': advance_rentals,
                'upfront_fee_pct': upfront_fee_pct,
                'supplier_discount_pct': supplier_discount_pct,
                'gst_pct': gst_pct,
                'payment_frequency': payment_frequency
            })

            # Basic validations
            if asset_cost <= 0 or rate < 0 or tenure_months <= 0:
                raise ValueError("Asset cost, rate, and tenure must be positive numbers.")

            # 1. Supplier Discount
            net_cost = asset_cost * (1 - supplier_discount_pct / 100)

            # 2. GST on net cost (GST amount added and financed)
            gst_amt = net_cost * (gst_pct / 100)
            net_cost_with_gst = net_cost + gst_amt

            # 3. Security Deposit (refundable, not financed)
            deposit_amt = net_cost_with_gst * (security_deposit_pct / 100)

            # 4. Upfront Fee (financed)
            fee_amt = net_cost_with_gst * (upfront_fee_pct / 100)

            # 5. Residual Value
            residual_amt = net_cost_with_gst * (residual_pct / 100)

            # Financed principal includes net cost + GST - deposit + upfront fee
            principal = net_cost_with_gst - deposit_amt + fee_amt

            # Frequency adjustment
            freq_map = {'monthly': 1, 'quarterly': 3}
            freq_factor = freq_map.get(payment_frequency, 1)
            total_periods = tenure_months // freq_factor or 1
            periodic_rate = rate / 100 * freq_factor / 12

            # 6. Moratorium: capitalize interest
            if moratorium > 0 and periodic_rate > 0:
                principal *= (1 + periodic_rate) ** moratorium

            # 7. Advance rentals: reduce periods
            remaining_periods = max(total_periods - advance_rentals, 1)

            # Prepare cashflows
            cashflows = [-principal]
            table = []

            # EMI formula helper
            def calc_emi(P, r, n, R=0):
                if r != 0:
                    pv_res = R / (1 + r) ** n
                    return r * (P - pv_res) / (1 - (1 + r) ** -n)
                else:
                    return (P - R) / n

            # Decide calculation
            if request.form.get('loan_or_lease') == 'lease':
                emi = round(calc_emi(principal, periodic_rate, remaining_periods, residual_amt), 2)
                bal = principal
                for i in range(1, remaining_periods + 1):
                    interest = round(bal * periodic_rate, 2)
                    princ = round(emi - interest, 2)
                    bal = round(bal - princ, 2)
                    pay = emi + (residual_amt if i == remaining_periods else 0)
                    cashflows.append(pay)
                    table.append({'Period': i * freq_factor, 'Payment': pay, 'Principal': princ, 'Interest': interest, 'Balance': max(bal, 0)})
                result = f"Lease EMI: ₹{emi:.2f}"

            else:
                loan_type = request.form.get('loan_type', 'standard')
                if loan_type == 'standard':
                    emi = round(calc_emi(principal, periodic_rate, remaining_periods, residual_amt), 2)
                elif loan_type == 'bullet':
                    emi = round(principal * periodic_rate, 2)
                else:  # equal principal
                    emi = None

                bal = principal
                for i in range(1, remaining_periods + 1):
                    interest = round(bal * periodic_rate, 2)
                    if loan_type == 'bullet':
                        princ = 0 if i < remaining_periods else principal
                        pay = interest + princ + (residual_amt if i == remaining_periods else 0)
                    elif loan_type == 'equal_principal':
                        princ = round(principal / remaining_periods, 2)
                        pay = round(princ + interest + (residual_amt if i == remaining_periods else 0), 2)
                    else:
                        princ = round(emi - interest, 2)
                        pay = emi + (residual_amt if i == remaining_periods else 0)
                    bal = round(bal - princ, 2)
                    cashflows.append(pay)
                    table.append({'Period': i * freq_factor, 'Payment': pay, 'Principal': princ, 'Interest': interest, 'Balance': max(bal, 0)})
                result = f"{loan_type.replace('_', ' ').title()} EMI: ₹{emi:.2f}" if emi else f"{loan_type.title()} schedule calculated"

            # IRR calculation
            irr_m = irr(cashflows)
            if irr_m:
                irr_monthly = round(irr_m * 100, 2)
                irr_annual = round(irr_m * 12 * 100, 2)
                irr_value = irr_monthly

        except Exception as e:
            logging.exception("Calculation error")
            result = f"Error: {e}"

    return render_template('test_index.html', result=result, inputs=inputs,
                           irr=irr_value, irr_monthly=irr_monthly, irr_annual=irr_annual,
                           table=table)


if __name__ == '__main__':
    app.run(debug=True, port=8000)
