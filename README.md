
 Loan and Lease EMI Calculator with IRR Estimation

This is a Flask-based web application that helps calculate EMIs for different types of loans and leases. It supports IRR (Internal Rate of Return) calculation and multiple repayment methods including standard EMI, bullet payment, and equal principal.



 🚀 Features

- 📈 EMI calculation for loans and leases
- 🔄 Supports Standard EMI, Bullet Payment, and Equal Principal methods
- 🧮 Calculates IRR (Internal Rate of Return) from generated cash flows
- 🧾 Residual value and GST support
- 🔁 Choose monthly or quarterly payment frequency
- 📋 Tabular breakdown of payments



 🧰 Tech Stack

- Python 3
- Flask
- NumPy
- SciPy
- HTML/CSS for frontend (uses render_template and basic form)



 📂 Project Structure



loan-lease-calculator/
├── app.py               Main Flask app with calculation logic
├── templates/
│   └── index.html       UI Form and table display
├── static/
│   └── css/             (Optional) CSS stylesheets
├── requirements.txt     Python dependencies (create with pip freeze)
└── README.md            You're reading this





 ⚙️ Setup Instructions

 1. Clone the Repository

bash
git clone https://github.com/yourusername/loan-lease-calculator.git
cd loan-lease-calculator


 2. Install Dependencies

bash
pip install flask numpy scipy


Or use requirements.txt if available:

bash
pip install -r requirements.txt


 3. Run the App

bash
python app.py


Open your browser at [http://localhost:8000](http://localhost:8000)



 📌 Usage Instructions

1. Enter the loan amount, interest rate, tenure, and GST rate.
2. Choose between loan or lease, and pick the loan type:

    standard: Regular EMI
    bullet: Interest only, then lump-sum
    equal_principal: Principal divided equally
3. Optional:

    Add residual value for balloon payments
    Choose monthly or quarterly payments
4. Submit the form to see:

    EMI or payment summary
    A full amortization table
    IRR (Monthly and Annualized)



 📊 IRR Calculation

The IRR is computed using cash flows generated from the payment schedule. It represents the effective interest rate taking into account timing and residual value.



 🛠 Sample Function Snippets

Calculate EMI:

python
emi = amount  rate / (1 - (1 + rate)  -term)


Calculate IRR:

python
from scipy.optimize import root_scalar

def irr(cashflows):
    return root_scalar(lambda r: npv(r, cashflows), bracket=[0.00001, 1]).root




 👨‍💻 Author

Akash Bhilwande
GitHub: [@Akashbhilwande](https://github.com/Akashbhilwande)


![Screenshot 2025-06-26 141700](https://github.com/user-attachments/assets/098cc97d-f046-4bb4-9264-17cc58d7b03f)
![Screenshot 2025-06-26 141700](https://github.com/user-attachments/assets/098cc97d-f046-4bb4-9264-17cc58d7b03f)


