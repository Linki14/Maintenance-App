import streamlit as st
import pandas as pd

st.title("Maintenance Prioritization Tool")

uploaded_file = st.file_uploader("Last opp Excel-fil", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("Fil lastet inn")

    st.write("Preview av data:")
    st.dataframe(df.head())

    st.write("Klar for analyse (vi legger inn full modell etterpå)")
