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
# INPUT COLUMNS
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

def assign_level(v):
    if v < 0: return 0
    if v < 0.4666: return 0
    if v < 0.7332: return 1
    return 2

# -------------------------
# MAIN CALCULATION
# -------------------------
def calculate_all(df):

    # Clean data
    df = df.fillna(0)
    df = df.clip(lower=0)

    # Force integers everywhere
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)

    # CI
    df["CI1"] = df.apply(lambda r: score_interval_ratio(r.Age_years / max(r.Expected_lifetime_years,1)), axis=1)
    df["CI2"] = df.apply(lambda r: score_interval_ratio(r.Num_operations / max(r.Max_operations,1)), axis=1)
    df["CI3"] = df.apply(lambda r: score_interval_ratio(r.Years_since_condition_assessment / max(r.Condition_assessment_interval,1)), axis=1)
    df["CI4"] = df.apply(lambda r: score_interval_ratio(r.Years_since_revision / max(r.Revision_interval,1)), axis=1)
    df["CI5"] = df["Years_since_last_operation"].apply(score_last_operation)
    df["CI6"] = df["Specialist_required"].apply(score_yes_no)
    df["CI7"] = df["Outdated_equipment"].apply(score_yes_no)
    df["CI8"] = df.apply(lambda r: score_CI8(r.Indoor_outdoor, r.Distance_to_coast_km), axis=1)
    df["CI9"] = df.apply(lambda r: score_CI9(r.Indoor_outdoor, r.Minimum_temperature_C), axis=1)

    ci_cols = [f"CI{i}" for i in range(1,10)]
    df["CI"] = df[ci_cols].sum(axis=1)
    df["CI_norm"] = df["CI"] / 45

    # II
    df["II10"] = df["Breaker_function"].astype(int)
    df["II11"] = df["Regional_connections"]
    df["II12"] = df["Busbar_arrangement"].astype(int)
    df["II13"] = df["Breaker_redundancy"].astype(int)
    df["II14"] = df["KILE_score_manual"]
    df["II15"] = df["Customer_impact_score_manual"]
    df["II16"] = df["Number_of_transformers"]

    ii_cols = [f"II{i}" for i in range(10,17)]
    df["II"] = df[ii_cols].sum(axis=1)
    df["II_norm"] = df["II"] / 35

    # Criticality
    df["CI_level"] = df["CI_norm"].apply(assign_level)
    df["II_level"] = df["II_norm"].apply(assign_level)

    matrix={(2,2):5,(2,1):4,(2,0):3,
            (1,2):4,(1,1):3,(1,0):2,
            (0,2):3,(0,1):2,(0,0):1}

    df["Criticality_Score"] = df.apply(lambda r: matrix[(r.CI_level, r.II_level)], axis=1)

    return df

# -------------------------
# SINGLE BREAKER MODE
# -------------------------
if mode == "Evaluate ONE circuit breaker":

    st.subheader("Manual Input")

    try:
        data = {}

        data["Breaker_ID"] = st.text_input("Breaker ID")

        data["Age_years"] = st.number_input("Age (years)", min_value=0, step=1)
        data["Expected_lifetime_years"] = st.number_input("Expected lifetime (years)", min_value=1, step=1)

        data["Num_operations"] = st.number_input("Number of operations", min_value=0, step=1)
        data["Max_operations"] = st.number_input("Maximum operations", min_value=1, step=1)

        data["Years_since_condition_assessment"] = st.number_input("Years since condition assessment", min_value=0, step=1)
        data["Condition_assessment_interval"] = st.number_input("Condition interval", min_value=1, step=1)

        data["Years_since_revision"] = st.number_input("Years since revision", min_value=0, step=1)
        data["Revision_interval"] = st.number_input("Revision interval", min_value=1, step=1)

        data["Years_since_last_operation"] = st.number_input("Years since last operation", min_value=0, step=1)

        data["Specialist_required"] = st.selectbox("External specialist required?", ["No","Yes"])
        data["Outdated_equipment"] = st.selectbox("Outdated equipment?", ["No","Yes"])

        io = st.selectbox("Indoor or Outdoor", ["Indoor","Outdoor"])
        data["Indoor_outdoor"] = io

        if io == "Outdoor":
            data["Distance_to_coast_km"] = st.number_input("Distance to coast (km)", min_value=0, step=1)
            data["Minimum_temperature_C"] = st.number_input("Minimum temperature °C", step=1)
        else:
            data["Distance_to_coast_km"] = 0
            data["Minimum_temperature_C"] = 0

        bf = st.selectbox("Breaker function", [
            "5 - Transmission grid",
            "4 - Transformer",
            "3 - Power plant",
            "2 - Regional grid",
            "1 - Distribution grid"
        ])
        data["Breaker_function"] = int(bf[0])

        data["Regional_connections"] = st.number_input("Regional connections", min_value=0, step=1)

        bb = st.selectbox("Busbar arrangement", [
            "5 - Single busbar",
            "4 - Sectionaliser",
            "3 - Transfer",
            "2 - Double",
            "1 - Triple"
        ])
        data["Busbar_arrangement"] = int(bb[0])

        rd = st.selectbox("Redundancy", [
            "5 - No redundancy",
            "3 - Bypass",
            "1 - Redundancy"
        ])
        data["Breaker_redundancy"] = int(rd[0])

        data["KILE_score_manual"] = st.number_input("KILE score (1–5)", min_value=1, max_value=5, step=1)
        data["Customer_impact_score_manual"] = st.number_input("Customer impact (1–5)", min_value=1, max_value=5, step=1)

        data["Feeder_critical_customer"] = st.selectbox("Critical feeder?", ["No","Yes"])
        data["Transformer_critical_customer"] = st.selectbox("Critical transformer?", ["No","Yes"])
        data["Number_of_transformers"] = st.number_input("Number of transformers", min_value=0, step=1)

        if st.button("Run Analysis"):

            df = pd.DataFrame([data])
            df = calculate_all(df)

            st.success("Analysis complete ✅")
            st.dataframe(df)

    except:
        st.error("Invalid input detected. Only non-negative integers allowed.")

# -------------------------
# MULTI MODE
# -------------------------
else:

    st.subheader("Excel Workflow")

    template = pd.DataFrame(columns=INPUT_COLUMNS)
    buffer = BytesIO()
    template.to_excel(buffer, index=False)

    st.download_button("Download Excel template", buffer.getvalue(), file_name="Template.xlsx")

    file = st.file_uploader("Upload completed file", type=["xlsx"])

    if file:
        try:
            df = pd.read_excel(file)

            if not all(col in df.columns for col in INPUT_COLUMNS):
                st.error("Missing columns in Excel file.")
            else:

                if st.button("Run Analysis"):

                    df = calculate_all(df)

                    st.dataframe(df)

                    # Plot
                    fig, ax = plt.subplots()
                    ax.scatter(df["II_norm"], df["CI_norm"])
                    st.pyplot(fig)

                    # Download
                    out = BytesIO()
                    df.to_excel(out, index=False)

                    st.download_button("Download results", out.getvalue(), "Results.xlsx")

        except:
            st.error("Error reading file. Ensure correct format and non-negative integers.")
