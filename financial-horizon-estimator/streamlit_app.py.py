import streamlit as st
import numpy_financial as npf
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Financial Horizon Estimator", layout="wide")

# --- FINANCIAL LOGIC ENGINE ---
class FinancialEngine:
    def __init__(self, age, income, dependents, debt, savings, retire_age, inflation_rate, investment_return):
        self.age = age
        self.income = income
        self.dependents = dependents
        self.debt = debt
        self.savings = savings
        self.retire_age = retire_age
        self.inflation_rate = inflation_rate / 100.0
        self.investment_return = investment_return / 100.0
        
        # Constants
        self.SAFE_WITHDRAWAL_RATE = 0.04
        self.INCOME_REPLACEMENT_RATIO = 0.75
        self.INSURANCE_DISCOUNT_RATE = 0.03 

    def calc_insurance_gap(self):
        years_support = 20 if self.dependents > 0 else 0
        if years_support == 0: return 0, 0
        
        annual_support = self.income * 0.75
        # PV of Annuity Factor
        pv_factor = (1 - (1 + self.INSURANCE_DISCOUNT_RATE)**(-years_support)) / self.INSURANCE_DISCOUNT_RATE
        gross_need = annual_support * pv_factor
        
        total_need = gross_need + self.debt - self.savings
        return max(0, total_need), max(0, gross_need)

    def calc_retirement_target(self):
        years_to_retire = self.retire_age - self.age
        if years_to_retire <= 0: return 0, 0
        
        current_annual_need = self.income * self.INCOME_REPLACEMENT_RATIO
        # Future Value of Expenses (Inflation adjusted)
        future_annual_need = current_annual_need * ((1 + self.inflation_rate) ** years_to_retire)
        
        # The "Number"
        target_corpus = future_annual_need / self.SAFE_WITHDRAWAL_RATE
        return target_corpus, years_to_retire

    def calc_monthly_savings_req(self, target_corpus, years_to_retire):
        if years_to_retire <= 0: return 0
        
        # Use numpy_financial.pmt to calculate monthly savings
        # rate = monthly investment return
        # nper = months to retire
        # pv = -current savings (negative because it's cash already "paid" into the pot)
        # fv = target_corpus
        
        monthly_rate = self.investment_return / 12
        months = years_to_retire * 12
        
        # PMT formula returns negative for payments, so we flip sign
        monthly_req = npf.pmt(monthly_rate, months, -self.savings, target_corpus) * -1
        
        return monthly_req

    def get_risk_profile(self):
        years = self.retire_age - self.age
        debt_ratio = self.debt / (self.income if self.income > 0 else 1)
        
        score = 0
        if years > 20: score += 3
        elif years > 10: score += 2
        else: score += 1
        
        if debt_ratio < 0.3: score += 2
        elif debt_ratio < 1.0: score += 1
        else: score -= 1
        
        if score >= 4: return "High (Growth Focused)"
        elif score >= 3: return "Medium (Balanced)"
        else: return "Low (Preservation Focused)"

# --- PDF GENERATOR ---
def create_pdf(engine, ins_need, ret_target, monthly_save, risk):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Financial Horizon Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Client Age: {engine.age} | Retirement Age: {engine.retire_age}", ln=True)
    pdf.cell(200, 10, txt=f"Annual Income: ${engine.income:,.0f}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="1. Insurance Analysis", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"To replace your income for your {engine.dependents} dependents and clear debts, you need approximately ${ins_need:,.0f} in coverage.")
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="2. Retirement Forecast", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Adjusting for inflation, your target 'Nest Egg' is ${ret_target:,.0f}.")
    pdf.multi_cell(0, 10, txt=f"To reach this, your required monthly savings is: ${monthly_save:,.0f}.")
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="3. Risk Profile", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Assessment: {risk}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT UI ---
def main():
    st.title("📊 Financial Horizon Estimator")
    st.markdown("A tool combining **Economic Logic** with **Financial Modeling**.")

    # SIDEBAR INPUTS
    with st.sidebar:
        st.header("Client Profile")
        age = st.slider("Current Age", 18, 70, 35)
        retire_age = st.slider("Target Retirement Age", age+1, 80, 65)
        income = st.number_input("Annual Income ($)", value=85000, step=1000)
        savings = st.number_input("Current Savings ($)", value=40000, step=1000)
        debt = st.number_input("Total Debt ($)", value=25000, step=1000)
        dependents = st.slider("Dependents", 0, 5, 2)
        
        st.markdown("---")
        st.header("Economic Assumptions")
        inflation = st.slider("Inflation Rate (%)", 1.0, 10.0, 2.5, 0.1)
        roi = st.slider("Expected Investment Return (%)", 1.0, 12.0, 7.0, 0.1)

    # CALCULATIONS
    engine = FinancialEngine(age, income, dependents, debt, savings, retire_age, inflation, roi)
    ins_gap, ins_gross = engine.calc_insurance_gap()
    ret_target, years_to_ret = engine.calc_retirement_target()
    monthly_req = engine.calc_monthly_savings_req(ret_target, years_to_ret)
    risk_profile = engine.get_risk_profile()

    # MAIN DASHBOARD
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Insurance Gap", f"${ins_gap:,.0f}", delta="Coverage Needed", delta_color="inverse")
    with col2:
        st.metric("Retirement Target", f"${ret_target:,.0f}", help=f"Adjusted for {inflation}% inflation")
    with col3:
        # Conditional formatting for savings
        color = "normal" if monthly_req < (income/12)*0.2 else "inverse" 
        st.metric("Required Monthly Savings", f"${monthly_req:,.0f}", delta=f"{years_to_ret} Years to Goal", delta_color=color)

    st.markdown("---")

    # CHARTS ROW
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🛡️ Insurance Analysis")
        # Waterfall chart for Insurance
        fig_ins = go.Figure(go.Waterfall(
            name = "20", orientation = "v",
            measure = ["relative", "relative", "relative", "total"],
            x = ["Gross Income Replacement", "Debt", "Existing Savings", "Net Insurance Need"],
            textposition = "outside",
            text = [f"${ins_gross/1000:.0f}k", f"${debt/1000:.0f}k", f"-${savings/1000:.0f}k", f"${ins_gap/1000:.0f}k"],
            y = [ins_gross, debt, -savings, ins_gap],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        fig_ins.update_layout(title="Liquidity Needs Breakdown", showlegend=False)
        st.plotly_chart(fig_ins, use_container_width=True)
        st.caption(f"**Economic Logic:** This calculates the Present Value of your future earnings stream minus current assets. It answers: 'If your human capital stops today, how much capital is needed to replace it?'")

    with c2:
        st.subheader("🚀 Retirement Trajectory")
        # Bar chart comparing current vs target
        fig_ret = go.Figure(data=[
            go.Bar(name='Current Savings', x=['Capital'], y=[savings], marker_color='lightslategray'),
            go.Bar(name='Target Needed', x=['Capital'], y=[ret_target], marker_color='crimson')
        ])
        fig_ret.update_layout(title=f"The Gap: ${ret_target - savings:,.0f}", barmode='group')
        st.plotly_chart(fig_ret, use_container_width=True)
        st.caption(f"**Economic Logic:** To maintain your lifestyle with {inflation}% inflation, your nest egg must grow significantly. The 'Required Monthly Savings' leverages compound interest to bridge this gap.")

    # RISK PROFILE
    st.info(f"### 🚦 Suggested Risk Profile: {risk_profile}")

    # EXPORT
    st.markdown("---")
    if st.button('Generate PDF Report'):
        pdf_bytes = create_pdf(engine, ins_gap, ret_target, monthly_req, risk_profile)
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="financial_plan.pdf">Download PDF Report</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()