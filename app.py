import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from io import BytesIO

st.title("Maintenance Prioritization Framework")

# --------------------------------------------------
# MODE
# --------------------------------------------------
mode = st.radio(
    "Select evaluation mode:",
    ["Evaluate ONE circuit breaker", "Evaluate SEVERAL circuit breakers"]
)

# --------------------------------------------------
# INPUT SCHEMA
# --------------------------------------------------
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

# --------------------------------------------------
# SCORING FUNCTIONS
# --------------------------------------------------
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
    if io == "Indoor": return 1
    if d <= 1: return 5
    if d <= 3: return 4
    if d <= 5: return 3
    if d <= 10: return 2
    return 1

def score_CI9(io, t):
    if io == "Indoor": return 1
    if t <= -30: return 5
    if t <= -25: return 4
    if t <= -20: return 3
    if t <= -15: return 2
    return 1

def assign_level(v):
    if v < 0.4666: return 0
    if v < 0.7332: return 1
    return 2

# --------------------------------------------------
# CALCULATION
# --------------------------------------------------
def calculate_all(df):

    df_numeric = df.copy()

    # convert only numeric columns
    numeric_cols = [
        "Age_years","Expected_lifetime_years","Num_operations","Max_operations",
        "Years_since_condition_assessment","Condition_assessment_interval",
        "Years_since_revision","Revision_interval","Years_since_last_operation",
        "Distance_to_coast_km","Minimum_temperature_C",
        "Regional_connections","KILE_score_manual",
        "Customer_impact_score_manual","Number_of_transformers"
    ]

    for col in numeric_cols:
        df_numeric[col] = pd.to_numeric(df_numeric[col], errors="coerce")

    if df_numeric[numeric_cols].isnull().any().any():
        raise ValueError("Invalid numeric input")

    df_numeric[numeric_cols] = df_numeric[numeric_cols].clip(lower=0).astype(int)

    # CI
    df["CI1"] = df_numeric["Age_years"] / df_numeric["Expected_lifetime_years"]
    df["CI1"] = df["CI1"].apply(score_interval_ratio)

    df["CI2"] = df_numeric["Num_operations"] / df_numeric["Max_operations"]
    df["CI2"] = df["CI2"].apply(score_interval_ratio)

    df["CI3"] = df_numeric["Years_since_condition_assessment"] / df_numeric["Condition_assessment_interval"]
    df["CI3"] = df["CI3"].apply(score_interval_ratio)

    df["CI4"] = df_numeric["Years_since_revision"] / df_numeric["Revision_interval"]
    df["CI4"] = df["CI4"].apply(score_interval_ratio)

    df["CI5"] = df_numeric["Years_since_last_operation"].apply(score_last_operation)

    df["CI6"] = df["Specialist_required"].apply(score_yes_no)
    df["CI7"] = df["Outdated_equipment"].apply(score_yes_no)

    df["CI8"] = df.apply(lambda r: score_CI8(r["Indoor_outdoor"], r["Distance_to_coast_km"]), axis=1)
    df["CI9"] = df.apply(lambda r: score_CI9(r["Indoor_outdoor"], r["Minimum_temperature_C"]), axis=1)

    ci_cols = [f"CI{i}" for i in range(1,10)]
    df["CI"] = df[ci_cols].sum(axis=1)
    df["CI_norm"] = df["CI"] / 45

    # II
    df["II10"] = df["Breaker_function"].astype(int)
    df["II11"] = df_numeric["Regional_connections"]
    df["II12"] = df["Busbar_arrangement"].astype(int)
    df["II13"] = df["Breaker_redundancy"].astype(int)
    df["II14"] = df_numeric["KILE_score_manual"]
    df["II15"] = df_numeric["Customer_impact_score_manual"]
    df["II16"] = df_numeric["Number_of_transformers"]

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

    # Ranking
    df["Rank_CIxII"] = (df["CI_norm"] * df["II_norm"]).rank(ascending=False).astype(int)

    return df

# --------------------------------------------------
# SINGLE MODE
# --------------------------------------------------
if mode == "Evaluate ONE circuit breaker":

    st.subheader("Manual Input")

    data = {}

    data["Breaker_ID"] = st.text_input("Breaker ID")

    data["Age_years"] = st.number_input("Age (years)", min_value=0, step=1)
    data["Expected_lifetime_years"] = st.number_input("Expected lifetime", min_value=1, step=1)

    data["Num_operations"] = st.number_input("Operations", min_value=0, step=1)
    data["Max_operations"] = st.number_input("Max operations", min_value=1, step=1)

    data["Years_since_condition_assessment"] = st.number_input("Years since condition assessment", min_value=0, step=1)
    data["Condition_assessment_interval"] = st.number_input("Condition interval", min_value=1, step=1)

    data["Years_since_revision"] = st.number_input("Years since revision", min_value=0, step=1)
    data["Revision_interval"] = st.number_input("Revision interval", min_value=1, step=1)

    data["Years_since_last_operation"] = st.number_input("Years since last operation", min_value=0, step=1)

    data["Specialist_required"] = st.selectbox("Specialist required", ["No","Yes"])
    data["Outdated_equipment"] = st.selectbox("Outdated equipment", ["No","Yes"])

    io = st.selectbox("Indoor or outdoor", ["Indoor","Outdoor"])
    data["Indoor_outdoor"] = io

    if io == "Outdoor":
        data["Distance_to_coast_km"] = st.number_input("Distance to coast", min_value=0, step=1)
        data["Minimum_temperature_C"] = st.number_input("Minimum temperature", step=1)
    else:
        data["Distance_to_coast_km"] = 0
        data["Minimum_temperature_C"] = 0

    bf = st.selectbox("Breaker function",
        ["5 - Transmission","4 - Transformer","3 - Power plant","2 - Regional","1 - Distribution"])
    data["Breaker_function"] = int(bf[0])

    data["Regional_connections"] = st.number_input("Regional connections", min_value=0, step=1)

    bb = st.selectbox("Busbar arrangement",
        ["5 - Single","4 - Sectionaliser","3 - Transfer","2 - Double","1 - Triple"])
    data["Busbar_arrangement"] = int(bb[0])

    rd = st.selectbox("Redundancy",
        ["5 - None","3 - Bypass","1 - Redundancy"])
    data["Breaker_redundancy"] = int(rd[0])

    data["KILE_score_manual"] = st.number_input("KILE score (1-5)", min_value=1, max_value=5, step=1)
    data["Customer_impact_score_manual"] = st.number_input("Customer impact (1-5)", min_value=1, max_value=5, step=1)

    data["Feeder_critical_customer"] = st.selectbox("Critical feeder", ["No","Yes"])
    data["Transformer_critical_customer"] = st.selectbox("Critical transformer", ["No","Yes"])
    data["Number_of_transformers"] = st.number_input("Number of transformers", min_value=0, step=1)

    if st.button("Run Analysis"):
        try:
            df = pd.DataFrame([data])
            df = calculate_all(df)

            st.success("Analysis complete")
            st.dataframe(df)

        except:
            st.error("Error: Fill all fields correctly (only non-negative integers allowed)")

# --------------------------------------------------
# MULTIPLE MODE
# --------------------------------------------------
else:

    st.subheader("Excel Workflow")

    template = pd.DataFrame(columns=INPUT_COLUMNS)
    buffer = BytesIO()
    template.to_excel(buffer, index=False)

    st.download_button("Download template", buffer.getvalue(), "Template.xlsx")

    file = st.file_uploader("Upload completed file", type=["xlsx"])

    if file:
        try:
            df = pd.read_excel(file)

            if not all(col in df.columns for col in INPUT_COLUMNS):
                st.error("Missing columns in Excel file")
            else:
                if st.button("Run Analysis"):

                    df = calculate_all(df)

                    st.dataframe(df)

fig, ax = plt.subplots(figsize=(6,6))

# BACKGROUND MATRIX
matrix = np.array([
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5]
])

colors = [
    "#33CC33", "#BEF01C", "#FFFF00",
    "#BEF01C", "#FFFF00", "#FF9900",
    "#FFFF00", "#FF9900", "#FA0000"
]

cmap = ListedColormap(colors)

ax.imshow(matrix, cmap=cmap, extent=[0.2,1,0.2,1], origin="lower")

# SCATTER POINTS
ax.scatter(df["II_norm"], df["CI_norm"], color="black", s=50)

# LABELS (Breaker names)
if "Breaker_ID" in df.columns:
    for _, row in df.iterrows():
        ax.text(row["II_norm"], row["CI_norm"], str(row["Breaker_ID"]), fontsize=8)

# AXIS LABELS
ax.set_xlabel("Importance Index")
ax.set_ylabel("Condition Index")

ax.set_xlim(0.2, 1)
ax.set_ylim(0.2, 1)

st.pyplot(fig)

                    # Download
                    out = BytesIO()
                    df.to_excel(out, index=False)

                    st.download_button("Download results", out.getvalue(), "Results.xlsx")

        except:
            st.error("Error: Invalid file or input values")
