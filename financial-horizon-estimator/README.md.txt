# Financial Horizon Estimator

**A personalized financial planning tool built with Streamlit, Plotly, and economic logic.**  
It helps users calculate their life insurance needs, retirement targets, required monthly savings, and suggested risk profile — all in one interactive app.

---

## Problem

Most people don't know:

- How much **life insurance** they actually need
- Whether their **savings are enough** to retire comfortably
- How much they should be saving **each month**
- What **investment risk level** suits their profile

Traditional financial advice is vague or generic. This app turns **your numbers** into **real answers**.

---

## Solution

The app estimates:

### Inputs:
- Age, income, debt, savings, number of dependents
- Retirement age
- Assumptions: inflation rate and investment return

### Outputs:
- **Insurance Coverage Needed** (based on income replacement)
- **Retirement Corpus Target** (inflation-adjusted nest egg)
- **Required Monthly Savings**
- **Risk Profile** (low / medium / high)
- **PDF Report** download

All results are based on **core economic logic** like:
- Present Value of Annuity
- Future Value of Expenses
- Safe Withdrawal Rate
- Compound interest over time

---

## Example Logic Used

| Component     | Economic Model                                  |
|---------------|--------------------------------------------------|
| Insurance     | Present Value of Income Replacement (20 years)  |
| Retirement    | Future Value of Lifestyle / 4% SWR              |
| Monthly Save  | `npf.pmt()` from savings to corpus              |
| Risk Profile  | Years to retire, debt load, dependents          |

---

## How to Run It

### 1. Clone this repo

```bash
git clone https://github.com/Gm0066/financial-horizon-estimator.git
cd financial-horizon-estimator
