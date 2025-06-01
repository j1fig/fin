import sqlite3

import streamlit as st
import pandas as pd


DATABASE_PATH = 'storage/fin.db'



st.title("Finance")
st.write("Import transactions from CGD")
path = st.file_uploader("Upload a CGD transactions file", type="tsv")

with sqlite3.connect(DATABASE_PATH) as con:
    st.text("Categories")
    df = pd.read_sql('SELECT * from "category"', con)
    st.table(df)

    st.text("Accounts")
    df = pd.read_sql('SELECT * from "account"', con)
    st.table(df)

    st.text("Transactions")
    account_id = st.selectbox("Account", df['id'])
    df = pd.read_sql('SELECT * from "transaction" WHERE account_id = ?', con, params=(account_id,))
    df['amount'] = df['amount_cents'] / 100
    st.dataframe(df)
    st.text(f"Total transacted: {df['amount'].sum():.2f}")

    st.text("Expenses VS Income (monthly)")
    df = pd.read_sql('SELECT * from "transaction" WHERE account_id = ?', con, params=(account_id,))
    df['amount'] = df['amount_cents'] / 100
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['month'] = df['created_at'].dt.to_period('M')
    df['expenses'] = -df['amount'].where(df['amount'] < 0, 0)
    df['income'] = df['amount'].where(df['amount'] > 0, 0)
    df = df.drop(columns=['amount'])
    df = df.groupby('month').agg({'expenses': 'sum', 'income': 'sum'})
    st.line_chart(df)