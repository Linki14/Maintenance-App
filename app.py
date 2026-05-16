import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

st.title("Maintenance Prioritization Framework")

# --------------------------------------------------
# MODE
# --------------------------------------------------
mode = st.radio(
    "Select evaluation mode:",
    ["Evaluate ONE circuit breaker", "Evaluate SEVERAL circuit breakers"]
)

# --------------------------------------------------
# WEIGHTING OPTIONS (UPDATED - SAME AS ORIGINAL)
# --------------------------------------------------
st.subheader("Weighting")

# -------------------------
# CI WEIGHTING
# -------------------------
ci_weights = None

st.write("Do you want to apply custom weighting to the Condition Index?")
ci_use = st.radio("Condition Index weighting", ["No", "Yes"])

if ci_use == "Yes":

    st.write("How do you want to specify weights?")
    st.write("1 – Percentages (e.g. 50)")
    st.write("2 – Relative parts (e.g. 2 = twice as important)")

    ci_mode = st.radio("Choose 1 or 2:", ["1", "2"])

    st.write(
        "Enter weights for EACH Condition Index sub‑component:\n"
        "(Higher number = higher importance relative to others)"
    )

    ci_weights = {
        "CI1": st.number_input("CI1 – Age relative to lifetime", value=1.0),
        "CI2": st.number_input("CI2 – Number of operations", value=1.0),
        "CI3": st.number_input("CI3 – Condition assessment interval", value=1.0),
        "CI4": st.number_input("CI4 – Revision interval", value=1.0),
        "CI5": st.number_input("CI5 – Time since last operation", value=1.0),
        "CI6": st.number_input("CI6 – Specialist requirement", value=1.0),
        "CI7": st.number_input("CI7 – Outdated equipment", value=1.0),
        "CI8": st.number_input("CI8 – Distance to coastline", value=1.0),
        "CI9": st.number_input("CI9 – Minimum temperature", value=1.0),
    }


    # ✅ HER SKAL CHECKEN VÆRE (INNE I BLOKKEN)
    if ci_mode == "1":
        total_ci = sum(ci_weights.values())

        if total_ci > 100:
            st.error("Condition Index weights exceed 100%")
        elif total_ci < 100:
            st.warning(f"Condition Index weights sum to {total_ci}%, not 100%")

# -------------------------
# II WEIGHTING
# -------------------------
ii_weights = None

st.write("Do you want to apply custom weighting to the Importance Index?")
ii_use = st.radio("Importance Index weighting", ["No", "Yes"])

if ii_use == "Yes":

    st.write("How do you want to specify weights?")
    st.write("1 – Percentages (e.g. 50)")
    st.write("2 – Relative parts (e.g. 2 = twice as important)")

    ii_mode = st.radio("Choose II weighting:", ["1", "2"])

    st.write(
        "Enter weights for each II sub-index:\n"
        "(Higher number = higher importance relative to others)"
    )

    ii_weights = {
        "II10": st.number_input("II10 – Breaker function", value=1.0),
        "II11": st.number_input("II11 – Grid topology", value=1.0),
        "II12": st.number_input("II12 – Busbar arrangement", value=1.0),
        "II13": st.number_input("II13 – Redundancy", value=1.0),
        "II14": st.number_input("II14 – KILE cost", value=1.0),
        "II15": st.number_input("II15 – Customer impact", value=1.0),
        "II16": st.number_input("II16 – Priority customers", value=1.0),
    }

# ✅ CHECK FOR PERCENTAGES
if ii_mode == "1":
    total_ii = sum(ii_weights.values())

    if total_ii > 100:
        st.error("Importance Index weights exceed 100%")

    elif total_ii < 100:
        st.warning(f"Importance Index weights sum to {total_ii}%, not 100%")

# --------------------------------------------------
# SCORING
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

# --------------------------------------------------
# CALCULATION
# --------------------------------------------------
def calculate(df, ci_weights=None, ii_weights=None):

    df = df.copy()

    # ensure numeric + non-negative
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].clip(lower=0)

    # CI
    df["CI1"] = (df["Age_years"]/df["Expected_lifetime_years"]).apply(score_interval_ratio)
    df["CI2"] = (df["Num_operations"]/df["Max_operations"]).apply(score_interval_ratio)
    df["CI3"] = (df["Years_since_condition_assessment"]/df["Condition_assessment_interval"]).apply(score_interval_ratio)
    df["CI4"] = (df["Years_since_revision"]/df["Revision_interval"]).apply(score_interval_ratio)
    df["CI5"] = df["Years_since_last_operation"].apply(score_last_operation)
    df["CI6"] = df["Specialist_required"].apply(score_yes_no)
    df["CI7"] = df["Outdated_equipment"].apply(score_yes_no)
    df["CI8"] = df.apply(lambda r: score_CI8(r["Indoor_outdoor"], r["Distance_to_coast_km"]), axis=1)
    df["CI9"] = df.apply(lambda r: score_CI9(r["Indoor_outdoor"], r["Minimum_temperature_C"]), axis=1)

    ci_cols = [f"CI{i}" for i in range(1,10)]

    if ci_weights is None:
        df["CI"] = df[ci_cols].sum(axis=1)
        df["CI_norm"] = df["CI"]/45
    else:
        df["CI"] = sum(df[c]*ci_weights[c] for c in ci_cols)
        df["CI_norm"] = df["CI"]/(5*sum(ci_weights.values()))

    # II
    df["II10"] = df["Breaker_function"]
    df["II11"] = df["Regional_connections"]
    df["II12"] = df["Busbar_arrangement"]
    df["II13"] = df["Breaker_redundancy"]
    df["II14"] = df["KILE_score_manual"]
    df["II15"] = df["Customer_impact_score_manual"]
    df["II16"] = df["Number_of_transformers"]

    ii_cols = [f"II{i}" for i in range(10,17)]

    if ii_weights is None:
        df["II"] = df[ii_cols].sum(axis=1)
        df["II_norm"] = df["II"]/35
    else:
        df["II"] = sum(df[c]*ii_weights[c] for c in ii_cols)
        df["II_norm"] = df["II"]/(5*sum(ii_weights.values()))

    return df

# --------------------------------------------------
# PLOT (EXACT ORIGINAL)
# --------------------------------------------------
def plot_map(df):

    fig, ax = plt.subplots(figsize=(6,6))

    matrix = np.array([[0,1,2],[3,4,5],[6,7,8]])

    colors = [
        "#33CC33","#BEF01C","#FFF000",
        "#BEF01C","#FFF000","#FF9900",
        "#FFF000","#FF9900","#FA0000"
    ]

    cmap = ListedColormap(colors)

    ax.imshow(matrix, cmap=cmap, extent=[0.2,1,0.2,1], origin="lower")

    ax.scatter(df["II_norm"], df["CI_norm"], color="black")

    for _, r in df.iterrows():
        ax.text(r["II_norm"], r["CI_norm"], str(r["Breaker_ID"]), fontsize=8)

    ax.set_xlabel("Importance Index")
    ax.set_ylabel("Condition Index")

    ax.set_xlim(0.2,1)
    ax.set_ylim(0.2,1)

    return fig

# --------------------------------------------------
# SINGLE
# --------------------------------------------------
if mode == "Evaluate ONE circuit breaker":

    data = {}

    data["Breaker_ID"] = st.text_input("Breaker ID")
    data["Age_years"] = st.number_input("Age", 0)
    data["Expected_lifetime_years"] = st.number_input("Lifetime", 1)

    data["Num_operations"] = st.number_input("Operations", 0)
    data["Max_operations"] = st.number_input("Max operations", 1)

    data["Years_since_condition_assessment"] = st.number_input("Years since assessment", 0)
    data["Condition_assessment_interval"] = st.number_input("Assessment interval", 1)

    data["Years_since_revision"] = st.number_input("Years since revision", 0)
    data["Revision_interval"] = st.number_input("Revision interval", 1)

    data["Years_since_last_operation"] = st.number_input("Years since operation", 0)

    data["Specialist_required"] = st.selectbox("Specialist required", ["No","Yes"])
    data["Outdated_equipment"] = st.selectbox("Outdated", ["No","Yes"])

    io = st.selectbox("Indoor/Outdoor", ["Indoor","Outdoor"])
    data["Indoor_outdoor"] = io

    if io == "Outdoor":
        data["Distance_to_coast_km"] = st.number_input("Distance to coast", 0)
        data["Minimum_temperature_C"] = st.number_input("Temperature", 0)
    else:
        data["Distance_to_coast_km"] = 0
        data["Minimum_temperature_C"] = 0

    bf = st.selectbox("Breaker function",
                      ["5 - Connected to transmission grid","4 - Connected to transformer","3 - Connected to power plant","2 - Regional grid circuit breaker","1 - Distribution grid circuit breaker"])
    data["Breaker_function"] = int(bf)

    data["Regional_connections"] = st.number_input("Connections", 0)

    bb = st.selectbox("Busbar", ["5 - No busbar / Single busbar ","4 - Single busbar with sectionaliser","3 - Single busbar with transfer","2 - Double busbar","1 - Double busbar with transfer / Triple busbar"])
    data["Busbar_arrangement"] = int(bb)

    rd = st.selectbox("Redundancy", ["5 - No redundancy","3 - Disconnector bypass","1 - Redundancy"])
    data["Breaker_redundancy"] = int(rd)

    data["KILE_score_manual"] = st.number_input("KILE", 1,5)
    data["Customer_impact_score_manual"] = st.number_input("Customer impact", 1,5)

    data["Feeder_critical_customer"] = st.selectbox("Critical feeder", ["No","Yes"])

    # FIXED TRANSFORMER LOGIC
    if data["Feeder_critical_customer"] == "Yes":
        data["Transformer_critical_customer"] = "No"
        data["Number_of_transformers"] = 0

    else:
        data["Transformer_critical_customer"] = st.selectbox("Critical transformer", ["No","Yes"])

        if data["Transformer_critical_customer"] == "Yes":
            data["Number_of_transformers"] = st.number_input("Number of transformers", 1)
        else:
            data["Number_of_transformers"] = 0

    if st.button("Run Analysis"):

        df = pd.DataFrame([data])
        df = calculate(df, ci_weights, ii_weights)

        st.dataframe(df)
        st.pyplot(plot_map(df))

# --------------------------------------------------# ------------------------------------------------ BREAKERS (EXCEL)
# --------------------------------------------------
if mode == "Evaluate SEVERAL circuit breakers":

    st.subheader("Excel workflow")

    # ---- TEMPLATE ----
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

    template_df = pd.DataFrame(columns=INPUT_COLUMNS)

    excel_buffer = pd.ExcelWriter("template.xlsx", engine="openpyxl")
    template_df.to_excel(excel_buffer, index=False)
    excel_buffer.close()

    with open("template.xlsx", "rb") as f:
        st.download_button(
            "Download Excel template",
            f,
            file_name="Breaker_Input_Template.xlsx"
        )

    st.write("Fill in the Excel file and upload it below")

    # ---- UPLOAD ----
    uploaded_file = st.file_uploader("Upload completed file", type=["xlsx"])

    if uploaded_file:

        df = pd.read_excel(uploaded_file)

        # check columns
        missing = set(INPUT_COLUMNS) - set(df.columns)

        if missing:
            st.error(f"Missing columns: {missing}")
        else:
            if st.button("Run Analysis (Multiple)"):

                try:
                    df = calculate(df, ci_weights, ii_weights)

                    st.dataframe(df)

                    st.pyplot(plot_map(df))

                except:
                    st.error("Error in file. Only non-negative integers allowed.")

