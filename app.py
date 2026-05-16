import streamlit as st
import pandas as pd

st.title("Maintenance Prioritization Tool")

# -------------------------
# MODE SELECTION
# -------------------------
mode = st.radio(
    "Velg analyse:",
    ["Én bryter", "Flere brytere (Excel)"]
)

# -------------------------
# MODE 1: SINGLE BREAKER
# -------------------------
if mode == "Én bryter":

    st.subheader("Input for én bryter")

    age = st.number_input("Age (years)")
    lifetime = st.number_input("Expected lifetime")
    operations = st.number_input("Number of operations")
    max_operations = st.number_input("Max operations")

    if st.button("Kjør analyse"):
        ci = age / lifetime if lifetime > 0 else 0
        op = operations / max_operations if max_operations > 0 else 0

        result = ci + op

        st.success("Analyse ferdig ✅")
        st.write("Resultat:", result)

# -------------------------
# MODE 2: MULTIPLE BREAKERS
# -------------------------
else:

    st.subheader("Flere brytere")

    # 👉 KNAPP for å laste ned template
    if st.button("Last ned Excel-mal"):
        df_template = pd.DataFrame(columns=[
            "Age_years",
            "Expected_lifetime_years",
            "Num_operations",
            "Max_operations"
        ])

        csv = df_template.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Klikk for å laste ned",
            data=csv,
            file_name="template.csv"
        )

    # 👉 Upload etterpå
    uploaded_file = st.file_uploader("Last opp ferdig Excel-fil", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.write("Preview:")
        st.dataframe(df.head())

        if st.button("Kjør analyse"):
            df["CI"] = df["Age_years"] / df["Expected_lifetime_years"]

            st.success("Ferdig ✅")
            st.dataframe(df)
