import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Maintenance Prioritization Tool")

uploaded_file = st.file_uploader("Last opp Excel-fil", type=["xlsx"])

# -------------------------
# CI FUNCTIONS
# -------------------------

def score_interval_ratio(x):
    if x >= 1: return 5
    if x >= 0.75: return 4
    if x >= 0.5: return 3
    if x >= 0.25: return 2
    return 1

def score_yes_no(v):
    return 5 if str(v).lower() == "yes" else 1

def score_last_operation(y):
    if y > 5: return 5
    if y > 4: return 4
    if y > 2: return 3
    if y > 1: return 2
    return 1

# -------------------------
# MAIN CALCULATION
# -------------------------

def calculate(df):

    # CONDITION INDEX
    df["CI1"] = (df["Age_years"] / df["Expected_lifetime_years"]).apply(score_interval_ratio)
    df["CI2"] = (df["Num_operations"] / df["Max_operations"]).apply(score_interval_ratio)
    df["CI3"] = (df["Years_since_condition_assessment"] / df["Condition_assessment_interval"]).apply(score_interval_ratio)
    df["CI4"] = (df["Years_since_revision"] / df["Revision_interval"]).apply(score_interval_ratio)
    df["CI5"] = df["Years_since_last_operation"].apply(score_last_operation)
    df["CI6"] = df["Specialist_required"].apply(score_yes_no)
    df["CI7"] = df["Outdated_equipment"].apply(score_yes_no)

    ci_cols = ["CI1","CI2","CI3","CI4","CI5","CI6","CI7"]

    df["CI"] = df[ci_cols].sum(axis=1)
    df["CI_norm"] = df["CI"] / (5 * len(ci_cols))

    # IMPORTANCE INDEX
    df["II"] = df["KILE_score_manual"] + df["Customer_impact_score_manual"]
    df["II_norm"] = df["II"] / 10

    # CRITICALITY
    df["Criticality_Score"] = df["CI_norm"] * df["II_norm"]

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

        ax.set_xlabel("Importance Index")
        ax.set_ylabel("Condition Index")

        st.pyplot(fig)

        # Download
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Last ned resultat",
            data=csv,
            file_name="results.csv"
        )
