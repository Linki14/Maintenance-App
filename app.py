import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Maintenance Prioritization Tool")

uploaded_file = st.file_uploader("Last opp Excel-fil", type=["xlsx"])

# -------------------------
# SCORING FUNCTIONS
# -------------------------

def score_interval_ratio(x):
    if x >= 1: return 5
    if x >= 0.75: return 4
    if x >= 0.5: return 3
    if x >= 0.25: return 2
    return 1

def score_yes_no(v):
    return 5 if str(v).lower() == "yes" else 1

# -------------------------
# CALCULATIONS
# -------------------------

def calculate(df):
    df["CI1"] = (df["Age_years"] / df["Expected_lifetime_years"]).apply(score_interval_ratio)
    df["CI2"] = (df["Num_operations"] / df["Max_operations"]).apply(score_interval_ratio)

    df["CI"] = df[["CI1", "CI2"]].sum(axis=1)
    df["CI_norm"] = df["CI"] / 10

    df["II"] = df["KILE_score_manual"]
    df["II_norm"] = df["II"] / 5

    df["Criticality"] = df["CI_norm"] * df["II_norm"]

    return df

# -------------------------
# APP FLOW
# -------------------------

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.success("Fil lastet inn")
    st.dataframe(df.head())

    if st.button("Kjør analyse"):

        df = calculate(df)

        st.success("Analyse ferdig")

        st.dataframe(df)

        # Plot
        fig, ax = plt.subplots()
        ax.scatter(df["II_norm"], df["CI_norm"])
        ax.set_xlabel("Importance")
        ax.set_ylabel("Condition")

        st.pyplot(fig)

        # Download
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Last ned resultat",
            data=csv,
            file_name="results.csv"
        )
``
