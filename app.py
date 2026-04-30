import streamlit as st
import pandas as pd
from database import create_db, insert_transaction, get_transactions, get_expenses_by_category, get_savings
from parser import parse_csv, parse_pdf

create_db()  # Ensure DB exists

st.title("Personal Finance Tracker")

uploaded_file = st.file_uploader("Upload bank statement (CSV or PDF)", type=['csv', 'pdf'])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        transactions = parse_csv(uploaded_file)
    elif uploaded_file.name.endswith('.pdf'):
        transactions = parse_pdf(uploaded_file)
    else:
        st.error("Unsupported file type")
        transactions = []

    if transactions:
        st.write("Parsed transactions:")
        st.dataframe(transactions)

        # Simple import to 'Other' category
        if st.button("Import all transactions to 'Other' category"):
            for t in transactions:
                insert_transaction(t['date'], t['description'], t['amount'], 'Other')
            st.success("Transactions imported!")
            st.rerun()  # Refresh

# Display existing transactions
st.header("All Transactions")
trans = get_transactions()
if trans:
    df_trans = pd.DataFrame(trans, columns=['Date', 'Description', 'Amount', 'Category'])
    st.dataframe(df_trans)
else:
    st.write("No transactions yet.")

# Expenses by category
st.header("Expenses by Category")
expenses = get_expenses_by_category()
if expenses:
    import pandas as pd
    df_exp = pd.DataFrame(expenses, columns=['Category', 'Total Expense'])
    df_exp['Total Expense'] = df_exp['Total Expense'].abs()  # Make positive
    st.bar_chart(df_exp.set_index('Category'))
else:
    st.write("No expenses recorded.")

# Savings
st.header("Total Savings")
savings = get_savings()
st.write(f"Total Savings: ${savings:.2f}")