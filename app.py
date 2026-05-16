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
# WEIGHTING OPTIONS
# --------------------------------------------------
st.subheader("Weighting")

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

    if ci_mode == "1":
        total_ci = sum(ci_weights.values())
        if total_ci > 100:
            st.error("Condition Index weights exceed 100%")
        elif total_ci < 100:
            st.warning(f"Condition Index weights sum to {total_ci}%, not 100%")

# II weighting
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

    if ii_mode == "1":
        total_ii = sum(ii_weights.values())
        if total_ii > 100:
            st.error("Importance Index weights exceed 100%")
        elif total_ii < 100:
            st.warning(f"Importance Index weights sum to {total_ii}%, not 100%")

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
    if str(io).lower() == "indoor":
        return 1
    if d <= 1: return 5
    if d <= 3: return 4
    if d <= 5: return 3
    if d <= 10: return 2
    return 1

def score_CI9(io, t):
    if str(io).lower() == "indoor":
        return 1
    if t <= -30: return 5
    if t <= -25: return 4
    if t <= -20: return 3
    if t <= -15: return 2
    return 1

# II scoring
def score_II11(n):
    return 5 if n <= 1 else 4 if n == 2 else 3 if n == 3 else 2 if n == 4 else 1

def score_II16(f, t, n):
    if str(f).lower() == "yes":
        return 5
    if str(t).lower() == "yes":
        return 5 if n == 1 else 3
    return 1

# --------------------------------------------------
# CALCULATION
# --------------------------------------------------
def calculate(df, ci_weights=None, ii_weights=None):

    df = df.copy()

# -------------------------
# CI CALCULATION
# -------------------------
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

# -------------------------
# II CALCULATION
# -------------------------
    df["II10"] = df["Breaker_function"]
    df["II11"] = df["Regional_connections"].apply(score_II11)
    df["II12"] = df["Busbar_arrangement"]
    df["II13"] = df["Breaker_redundancy"]
    df["II14"] = df["KILE_score_manual"]
    df["II15"] = df["Customer_impact_score_manual"]
    df["II16"] = df.apply(
        lambda r: score_II16(
            r.Feeder_critical_customer,
            r.Transformer_critical_customer,
            r.Number_of_transformers
        ), axis=1
    )

    ii_cols = [f"II{i}" for i in range(10,17)]

    if ii_weights is None:
        df["II"] = df[ii_cols].sum(axis=1)
        df["II_norm"] = df["II"]/35
    else:
        df["II"] = sum(df[c]*ii_weights[c] for c in ii_cols)
        df["II_norm"] = df["II"]/(5*sum(ii_weights.values()))

# -------------------------
# CRITICALITY
# -------------------------
    CI_LOW_MAX = 0.4666
    CI_MID_MAX = 0.7332

    def assign_level(v):
        if v < CI_LOW_MAX:
            return 0
        elif v < CI_MID_MAX:
            return 1
        else:
            return 2

    df["CI_level"] = df["CI_norm"].apply(assign_level)
    df["II_level"] = df["II_norm"].apply(assign_level)

    matrix = {
        (2,2):5,(2,1):4,(2,0):3,
        (1,2):4,(1,1):3,(1,0):2,
        (0,2):3,(0,1):2,(0,0):1
    }

    df["Criticality_Score"] = df.apply(
        lambda r: matrix[(r.CI_level, r.II_level)],
        axis=1
    )

# -------------------------
# RANKING (OPPDATERT)
# -------------------------
    
    df["OR1"] = np.sqrt(
        (df["CI_norm"] - 0.2)**2 +
        (df["II_norm"] = (df["CI_norm"] * df["II_norm"]).round(2)    (df["II_norm"] - 0.2)**2
    ).round(2)


    df["OR2"] = df["CI_norm"] * df["II_norm"]

    df["Rank_OR1"] = (
        df["OR1"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    df["Rank_OR2"] = (
        df["OR2"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    return df
# --------------------------------------------------
# SAFE PLOT 
# --------------------------------------------------
def plot_map(df):

    if "II_norm" not in df.columns or "CI_norm" not in df.columns:
        return None

    fig, ax = plt.subplots(figsize=(6,6))

    matrix = np.array([[0,1,2],[3,4,5],[6,7,8]])
    colors = [
        "#33CC33","#BEF01C","#FFF000",
        "#BEF01C","#FFF000","#FF9900",
        "#FFF000","#FF9900","#FA0000"
    ]

    cmap = ListedColormap(colors)

    ax.imshow(matrix, cmap=cmap, extent=[0.2,1,0.2,1], origin="lower")

    ax.scatter(df["II_norm"], df["CI_norm"], color="black", s=60)

    for _, r in df.iterrows():
        ax.text(
            r["II_norm"],
            r["CI_norm"],
            str(r["Breaker_ID"]),
            fontsize=8,
            ha="center",
            va="bottom"
        )

    ax.set_xlim(0.2, 1)
    ax.set_ylim(0.2, 1)

    ax.set_xlabel("Importance Index")
    ax.set_ylabel("Condition Index")

    return fig

# --------------------------------------------------
# COLOR FUNCTION 
# --------------------------------------------------
def color_cells(val):

    if val == 5:
        return 'background-color: #FA0000'  # RED
    elif val == 4:
        return 'background-color: #FF9900'  # ORANGE
    elif val == 3:
        return 'background-color: #FFFF00'  # YELLOW
    elif val == 2:
        return 'background-color: #BEF01C'  # LIGHT GREEN
    elif val == 1:
        return 'background-color: #33CC33'  # GREEN
    else:
        return ''

# --------------------------------------------------
# SINGLE MODE
# --------------------------------------------------
if mode == "Evaluate ONE circuit breaker":

    data = {}

    data["Breaker_ID"] = st.text_input("Breaker ID or name")

    # CONDITION SUB-INDICES
    data["Age_years"] = st.number_input("Age of the breaker (years)", 0)
    data["Expected_lifetime_years"] = st.number_input("Expected lifetime (years)", 1)

    data["Num_operations"] = st.number_input("Total number of operations", 0)
    data["Max_operations"] = st.number_input("Maximum allowed operations", 1)

    data["Years_since_condition_assessment"] = st.number_input(
        "Years since last condition assessment", 0
    )
    data["Condition_assessment_interval"] = st.number_input(
        "Condition assessment interval (years)", 1
    )

    data["Years_since_revision"] = st.number_input(
        "Years since last revision", 0
    )
    data["Revision_interval"] = st.number_input(
        "Revision interval (years)", 1
    )

    data["Years_since_last_operation"] = st.number_input(
        "Years since last operation (integer)", 0
    )

    data["Specialist_required"] = st.selectbox(
        "Does maintenance require external personnel? (Yes/No)",
        ["No","Yes"]
    )

    data["Outdated_equipment"] = st.selectbox(
        "Is the breaker outdated? (Yes/No)",
        ["No","Yes"]
    )

    io = st.selectbox(
        "Is the breaker indoor or outdoor? (Indoor/Outdoor)",
        ["Indoor","Outdoor"]
    )
    data["Indoor_outdoor"] = io

    if io == "Outdoor":
        data["Distance_to_coast_km"] = st.number_input(
            "Distance to coastline (km)", 0
        )
        data["Minimum_temperature_C"] = st.number_input(
    "Minimum outdoor temperature during the year (°C)",
        min_value=-100,
        max_value=100,
        value=0,
        step=1
    )

    else:
        data["Distance_to_coast_km"] = 0
        data["Minimum_temperature_C"] = 0

# IMPORTANCE SUB-INDICES

    bf = st.selectbox(
        "Breaker function (choose the highest applicable)",
        [
            "5 - Connected to transmission grid",
            "4 - Connected to transformer",
            "3 - Connected to power plant",
            "2 - Regional grid circuit breaker",
            "1 - Distribution grid circuit breaker"
        ]
    )
    data["Breaker_function"] = int(bf[0])

    data["Regional_connections"] = st.number_input(
        "Number of regional connections", 0
    )

    bb = st.selectbox(
        "Busbar arrangement",
        [
            "5 - No busbar / Single busbar",
            "4 - Single busbar with sectionaliser",
            "3 - Single busbar with transfer",
            "2 - Double busbar",
            "1 - Double busbar with transfer / Triple busbar"
        ]
    )
    data["Busbar_arrangement"] = int(bb[0])

    rd = st.selectbox(
        "Breaker redundancy",
        [
            "5 - No redundancy",
            "3 - Disconnector bypass",
            "1 - Redundancy"
        ]
    )
    data["Breaker_redundancy"] = int(rd[0])

    data["KILE_score_manual"] = st.number_input(
        "KILE criticality (1–5)", 1, 5
    )
    data["Customer_impact_score_manual"] = st.number_input(
        "Customer impact (1–5)", 1, 5
    )

    data["Feeder_critical_customer"] = st.selectbox(
        "On feeder of critical customer? (Yes/No)",
        ["No","Yes"]
    )

    if data["Feeder_critical_customer"] == "Yes":
        data["Transformer_critical_customer"] = "No"
        data["Number_of_transformers"] = 0
    else:
        data["Transformer_critical_customer"] = st.selectbox(
            "Transformer breaker serving critical customer? (Yes/No)",
            ["No","Yes"]
        )

        if data["Transformer_critical_customer"] == "Yes":
            data["Number_of_transformers"] = st.number_input(
                "Number of transformers at substation", 1
            )
        else:
            data["Number_of_transformers"] = 0

    if st.button("Run Analysis", key="single_run"):

        df = pd.DataFrame([data])
        df = calculate(df, ci_weights, ii_weights)
        
# --------------------------------------------------
# COLORED AND FORMATTED OUTPUT 
# --------------------------------------------------
        color_columns = [
            "CI1","CI2","CI3","CI4","CI5","CI6","CI7","CI8","CI9",
            "II10","II11","II12","II13","II14","II15","II16",
            "Criticality_Score"
        ]

        valid_cols = [col for col in color_columns if col in df.columns]

        styled_df = (
            df.style
            .map(color_cells, subset=valid_cols)
            .format({
                "CI_norm": "{:.2f}",
                "II_norm": "{:.2f}",
                "OR_Euclidean": "{:.2f}",
                "OR_CIxII": "{:.2f}"
            })
        )

        st.dataframe(styled_df)

        fig = plot_map(df)
        if fig:
            st.pyplot(fig)

# --------------------------------------------------
# MULTIPLE MODE
# --------------------------------------------------
if mode == "Evaluate SEVERAL circuit breakers":

    st.subheader("Excel workflow")

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

    # TEMPLATE DOWNLOAD
    template_df = pd.DataFrame(columns=INPUT_COLUMNS)

    st.download_button(
        "Download Excel template",
        template_df.to_csv(index=False, sep=";"),
        file_name="breaker_template.csv",
        mime="text/csv"
    )

    # UPLOAD
    uploaded_file = st.file_uploader("Upload completed file", type=["csv","xlsx"])

    if uploaded_file:


        if uploaded_file.name.endswith(".csv"):

            df = pd.read_csv(uploaded_file)

            if len(df.columns) == 1:
                df = df.iloc[:, 0].str.replace(",", ";")
                df = df.str.split(";", expand=True)
                df.columns = INPUT_COLUMNS[:len(df.columns)]
        else:
            df = pd.read_excel(uploaded_file)

        df["Indoor_outdoor"] = (
            df["Indoor_outdoor"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        required_columns = [
            "Feeder_critical_customer",
            "Transformer_critical_customer",
            "Number_of_transformers"
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = 0

        df["Feeder_critical_customer"] = df["Feeder_critical_customer"].fillna("No")
        df["Transformer_critical_customer"] = df["Transformer_critical_customer"].fillna("No")

        df["Number_of_transformers"] = pd.to_numeric(
            df["Number_of_transformers"], errors="coerce"
        ).fillna(0)

        numeric_cols = df.columns.drop([
            "Breaker_ID",
            "Specialist_required",
            "Outdated_equipment",
            "Indoor_outdoor",
            "Feeder_critical_customer",
            "Transformer_critical_customer"
        ])

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        missing = set(INPUT_COLUMNS) - set(df.columns)
        if missing:
            st.warning(f"Missing columns in file: {missing}")

        if st.button("Run Analysis (Multiple)", key="multi_run"):

            df = calculate(df, ci_weights, ii_weights)

            color_columns = [
                "CI1","CI2","CI3","CI4","CI5","CI6","CI7","CI8","CI9",
                "II10","II11","II12","II13","II14","II15","II16",
                "Criticality_Score"
            ]

            valid_cols = [col for col in color_columns if col in df.columns]

            styled_df = (
                df.style
                .map(color_cells, subset=valid_cols)
                .format({
                    "CI_norm": "{:.2f}",
                    "II_norm": "{:.2f}",
                    "OR_Euclidean": "{:.2f}",
                    "OR_CIxII": "{:.2f}"
                })
            )

            st.dataframe(styled_df)

            fig = plot_map(df)
            if fig:
                st.pyplot(fig)
