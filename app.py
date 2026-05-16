import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from io import BytesIO

st.title("Maintenance Prioritization Framework")

# -------------------------
# MODE SELECTION
# -------------------------
mode = st.radio(
    "Select evaluation mode:",
    ["Evaluate ONE circuit breaker", "Evaluate SEVERAL circuit breakers"]
)

# -------------------------
# INPUT SCHEMA
# -------------------------
INPUT_COLUMNS = [
    "Breaker_ID","Age_years","Expected_lifetime_years","Num_operations","Max_operations",
    "Years_since_condition_assessment","Condition_assessment_interval",
    "Years_since_revision","Revision_interval","Years_since_last_operation",
    "Specialist_required","Outdated_equipment","Indoor_outdoor",
    "Distance_to_coast_km","Minimum_temperature_C",
    "Breaker_function","Regional_connections",
    "Busbar_arrangement","Breaker_redundancy",
    "KILE_score_manual","Customer_impact_score_manual",
    "Feeder_critical_customer","Transformer_critical_customer",
    "Number_of_transformers"
]

# -------------------------
# SCORING FUNCTIONS
# -------------------------
def score_interval_ratio(x):
    if x >= 1: return 5
    if x >= 0.75: return 4
    if x >= 0.5: return 3
    if x >= 0.25: return 2
    return 1

def score_last_operation(y):
    if y > 5: return 5
    if y > 4: return 4
    if y > 2: return 3
    if y > 1: return 2
    return 1

def score_yes_no(v):
    return 5 if str(v).lower() == "yes" else 1

def score_CI8(io, d):
    if str(io).lower() == "indoor": return 1
    if d <= 1: return 5
    if d <= 3: return 4
    if d <= 5: return 3
    if d <= 10: return 2
    return 1

def score_CI9(io, t):
    if str(io).lower() == "indoor": return 1
    if t <= -30: return 5
    if t <= -25: return 4
    if t <= -20: return 3
    if t <= -15: return 2
    return 1

# -------------------------
# CALCULATIONS
# -------------------------
def calculate_all(df):

    df = df.fillna(0).clip(lower=0)

    # CI
    df["CI1"] = df.apply(lambda r: score_interval_ratio(r.Age_years / r.Expected_lifetime_years), axis=1)
    df["CI2"] = df.apply(lambda r: score_interval_ratio(r.Num_operations / r.Max_operations), axis=1)
    df["CI3"] = df.apply(lambda r: score_interval_ratio(r.Years_since_condition_assessment / r.Condition_assessment_interval), axis=1)
    df["CI4"] = df.apply(lambda r: score_interval_ratio(r.Years_since_revision / r.Revision_interval), axis=1)
    df["CI5"] = df["Years_since_last_operation"].apply(score_last_operation)
    df["CI6"] = df["Specialist_required"].apply(score_yes_no)
    df["CI7"] = df["Outdated_equipment"].apply(score_yes_no)
    df["CI8"] = df.apply(lambda r: score_CI8(r.Indoor_outdoor, r.Distance_to_coast_km), axis=1)
    df["CI9"] = df.apply(lambda r: score_CI9(r.Indoor_outdoor, r.Minimum_temperature_C), axis=1)

    ci_cols = [f"CI{i}" for i in range(1,10)]
    df["CI"] = df[ci_cols].sum(axis=1)
    df["CI_norm"] = df["CI"] / 45

    # II
    df["II10"] = df["Breaker_function"].astype(str).astype(int)
    df["II11"] = df["Regional_connections"]
    df["II12"] = df["Busbar_arrangement"].astype(str).astype(int)
    df["II13"] = df["Breaker_redundancy"].astype(str).astype(int)
    df["II14"] = df["KILE_score_manual"]
    df["II15"] = df["Customer_impact_score_manual"]
    df["II16"] = df["Number_of_transformers"]

    ii_cols = [f"II{i}" for i in range(10,17)]
    df["II"] = df[ii_cols].sum(axis=1)
    df["II_norm"] = df["II"] / 35

    # CRITICALITY
    def assign_level(v):
        if v < 0.4666: return 0
        if v < 0.7332: return 1
        return 2

    df["CI_level"] = df["CI_norm"].apply(assign_level)
    df["II_level"] = df["II_norm"].apply(assign_level)

    matrix={(2,2):5,(2,1):4,(2,0):3,
            (1,2):4,(1,1):3,(1,0):2,
            (0,2):3,(0,1):2,(0,0):1}

    df["Criticality_Score"] = df.apply(lambda r: matrix[(r.CI_level, r.II_level)], axis=1)

    return df

# -------------------------
# SINGLE BREAKER
# -------------------------
if mode == "Evaluate ONE circuit breaker":

    st.subheader("Manual input")

    data = {}
    for col in INPUT_COLUMNS:
        data[col] = st.text_input(col)

    if st.button("Run analysis"):
        df = pd.DataFrame([data])
        df = calculate_all(df)

        st.dataframe(df)

# -------------------------
# MULTIPLE BREAKERS
# -------------------------
else:

    st.subheader("Excel workflow")

    # Download template
    template = pd.DataFrame(columns=INPUT_COLUMNS)
    buffer = BytesIO()
    template.to_excel(buffer, index=False)

    st.download_button(
        "Download Excel template",
        data=buffer.getvalue(),
        file_name="Breaker_Input_Template.xlsx"
    )

    uploaded = st.file_uploader("Upload completed file", type=["xlsx"])

    if uploaded and st.button("Run analysis"):

        df = pd.read_excel(uploaded)

        df = calculate_all(df)

        st.dataframe(df)

        # Plot
        fig, ax = plt.subplots()
        ax.scatter(df["II_norm"], df["CI_norm"])
        st.pyplot(fig)

        # Download results
        out = BytesIO()
        df.to_excel(out, index=False)

        st.download_button(
            "Download results",
            data=out.getvalue(),
            file_name="Results.xlsx"
        )
