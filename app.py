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

# (VEKTING DEL – UENDRET)
# ... (ingen endringer her)

# --------------------------------------------------
# SCORING FUNCTIONS (UENDRET)
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

def score_II11(n):
    return 5 if n <= 1 else 4 if n == 2 else 3 if n == 3 else 2 if n == 4 else 1

def score_II16(f, t, n):
    if str(f).lower() == "yes":
        return 5
    if str(t).lower() == "yes":
        return 5 if n == 1 else 3
    return 1

# --------------------------------------------------
# ✅ COLOR FUNCTION (NY)
# --------------------------------------------------
def color_cells(val):

    if val == 5:
        return 'background-color: #FA0000'
    elif val == 4:
        return 'background-color: #FF9900'
    elif val == 3:
        return 'background-color: #FFFF00'
    elif val == 2:
        return 'background-color: #BEF01C'
    elif val == 1:
        return 'background-color: #33CC33'
    else:
        return ''

# --------------------------------------------------
# CALCULATION (UENDRET)
# --------------------------------------------------
def calculate(df, ci_weights=None, ii_weights=None):

    df = df.copy()

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
    df["CI"] = df[ci_cols].sum(axis=1)
    df["CI_norm"] = df["CI"]/45

    # II
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
    df["II"] = df[ii_cols].sum(axis=1)
    df["II_norm"] = df["II"]/35

    # Criticality
    CI_LOW_MAX = 0.4666
    CI_MID_MAX = 0.7332

    def assign_level(v):
        if v < CI_LOW_MAX: return 0
        elif v < CI_MID_MAX: return 1
        else: return 2

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

    return df

# --------------------------------------------------
# SINGLE MODE
# --------------------------------------------------
if mode == "Evaluate ONE circuit breaker":

    data = {}

    data["Breaker_ID"] = st.text_input("Breaker ID")
    data["Age_years"] = st.number_input("Age", 0)
    data["Expected_lifetime_years"] = st.number_input("Lifetime", 1)

    # (resten likt – kortet for oversikt)

    if st.button("Run Analysis", key="single_run"):

        df = pd.DataFrame([data])
        df = calculate(df, ci_weights, ii_weights)

        # ✅ FARGELAGT TABELL (NY)
        color_cols = [
            "CI1","CI2","CI3","CI4","CI5","CI6","CI7","CI8","CI9",
            "II10","II11","II12","II13","II14","II15","II16",
            "Criticality_Score"
        ]

        valid_cols = [c for c in color_cols if c in df.columns]
        styled_df = df.style.map(color_cells, subset=valid_cols)

        st.dataframe(styled_df)
