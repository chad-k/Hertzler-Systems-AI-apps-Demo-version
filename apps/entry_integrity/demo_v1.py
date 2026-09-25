from common.ui import DemoStopped
# operator_data_integrity_app.py

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(
    page_title="Operator Data Integrity Checker",
    layout="wide"
)

st.title("Operator Data Integrity Checker")
from common.ui import render_guide
render_guide('entry_integrity')
st.caption(
    "Detect suspicious data-entry patterns that may indicate data entry errors, backfilling, or potential pencil whipping."
)

# -------------------------------------------------
# Helper functions
# -------------------------------------------------

@st.cache_data
def generate_demo_data():
    np.random.seed(42)

    operators = [
        "John",
        "Mike",
        "Sarah",
        "David",
        "Emily",
        "Bob_PencilWhip",
        "Tom_Backfill"
    ]

    parts = ["P100", "P200", "P300"]
    machines = ["M1", "M2", "M3"]
    tests = ["Diameter", "Length", "Weight"]

    records = []
    start_time = pd.Timestamp("2026-01-01 06:00:00")

    for i in range(5000):
        operator = np.random.choice(operators)
        part = np.random.choice(parts)
        machine = np.random.choice(machines)
        test = np.random.choice(tests)

        target_map = {
            "Diameter": 10.0,
            "Length": 50.0,
            "Weight": 100.0
        }

        target = target_map[test]

        entry_time = start_time + pd.Timedelta(
            seconds=np.random.randint(0, 60 * 60 * 24 * 30)
        )

        inspection_time = entry_time - pd.Timedelta(
            minutes=np.random.randint(0, 20)
        )

        value = np.random.normal(target, 0.25)

        if operator == "Bob_PencilWhip":
            if np.random.random() < 0.80:
                value = target
            if np.random.random() < 0.50:
                value = round(value, 0)

        if operator == "Tom_Backfill":
            inspection_time = entry_time - pd.Timedelta(
                minutes=np.random.randint(90, 240)
            )

        records.append({
            "Operator": operator,
            "EntryTime": entry_time,
            "InspectionTime": inspection_time,
            "PartNumber": part,
            "Machine": machine,
            "TestName": test,
            "MeasurementValue": round(value, 3),
            "Target": target
        })

    df = pd.DataFrame(records)

    idx = np.random.choice(df.index, 200, replace=False)
    batch_time = pd.Timestamp("2026-01-15 08:00:00")

    df.loc[idx, "Operator"] = "Tom_Backfill"
    df.loc[idx, "EntryTime"] = batch_time
    df.loc[idx, "InspectionTime"] = batch_time - pd.Timedelta(hours=3)

    return df


def read_file(uploaded_file):
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type")


def to_excel_download(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, data in df_dict.items():
            data.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    output.seek(0)
    return output


def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def classify_risk(score):
    if score >= 8:
        return "High"
    elif score >= 4:
        return "Medium"
    else:
        return "Low"


def is_rounded_value(x, decimals):
    if pd.isna(x):
        return False
    return np.isclose(x, round(x, decimals))


# -------------------------------------------------
# Data source
# -------------------------------------------------

st.sidebar.header("Data Source")

data_source = 'Use Demo Data'  # Demo-only deployment

df = generate_demo_data()
st.success(f'Loaded demo dataset with {len(df):,} records.')

if df.empty:
    st.error("The selected dataset is empty.")
    raise DemoStopped()

st.subheader("Data Preview")
st.dataframe(df.head(50), use_container_width=True)

# -------------------------------------------------
# Column mapping
# -------------------------------------------------

columns = ["None"] + list(df.columns)

st.sidebar.header("Column Mapping")

operator_col = 'Operator'
entry_time_col = 'EntryTime'
inspection_time_col = 'InspectionTime'
part_col = 'PartNumber'
machine_col = 'Machine'
test_col = 'TestName'
value_col = 'MeasurementValue'
target_col = 'Target'
st.sidebar.success('Demo columns mapped automatically.')

# -------------------------------------------------
# Detection settings
# -------------------------------------------------

st.sidebar.header("Detection Settings")

fast_entry_seconds = st.sidebar.number_input(
    "Flag entries faster than this many seconds",
    min_value=1,
    max_value=300,
    value=5
)

batch_entry_count = st.sidebar.number_input(
    "Flag batch entry count per minute",
    min_value=2,
    max_value=100,
    value=10
)

repeat_window = st.sidebar.number_input(
    "Repeated-value rolling window",
    min_value=3,
    max_value=50,
    value=10
)

low_variation_threshold = st.sidebar.number_input(
    "Low variation std threshold",
    min_value=0.0,
    value=0.001,
    format="%.6f"
)

rounded_decimal_threshold = st.sidebar.number_input(
    "Flag values rounded to this many decimals or fewer",
    min_value=0,
    max_value=6,
    value=0
)

required = {
    "Operator": operator_col,
    "Entry DateTime": entry_time_col,
    "Measurement Value": value_col
}

missing_required = [name for name, col in required.items() if col == "None"]

if missing_required:
    st.warning(f"Please map required columns: {', '.join(missing_required)}")
    raise DemoStopped()

# -------------------------------------------------
# Prepare data
# -------------------------------------------------

work = df.copy()

work["_Operator"] = work[operator_col].astype(str)
work["_EntryTime"] = pd.to_datetime(work[entry_time_col], errors="coerce")
work["_Value"] = safe_numeric(work[value_col])

if inspection_time_col != "None":
    work["_InspectionTime"] = pd.to_datetime(
        work[inspection_time_col],
        errors="coerce"
    )
else:
    work["_InspectionTime"] = pd.NaT

work["_Part"] = work[part_col].astype(str) if part_col != "None" else "ALL"
work["_Machine"] = work[machine_col].astype(str) if machine_col != "None" else "ALL"
work["_Test"] = work[test_col].astype(str) if test_col != "None" else "ALL"

if target_col != "None":
    work["_Target"] = safe_numeric(work[target_col])
else:
    work["_Target"] = np.nan

work = work.sort_values(["_Operator", "_EntryTime"]).reset_index(drop=True)

# -------------------------------------------------
# Row-level checks
# -------------------------------------------------

work["Missing Required Data"] = (
    work["_Operator"].isna() |
    work["_EntryTime"].isna() |
    work["_Value"].isna()
)

work["Exact Target"] = (
    work["_Target"].notna() &
    work["_Value"].notna() &
    np.isclose(work["_Value"], work["_Target"], equal_nan=False)
)

work["Zero Value"] = work["_Value"] == 0

work["Seconds Since Last Entry"] = (
    work.groupby("_Operator")["_EntryTime"]
    .diff()
    .dt.total_seconds()
)

work["Too Fast Entry"] = (
    work["Seconds Since Last Entry"].notna() &
    (work["Seconds Since Last Entry"] < fast_entry_seconds)
)

if inspection_time_col != "None":
    work["Entry Delay Minutes"] = (
        work["_EntryTime"] - work["_InspectionTime"]
    ).dt.total_seconds() / 60

    work["Backfilled Entry"] = work["Entry Delay Minutes"] > 60
else:
    work["Entry Delay Minutes"] = np.nan
    work["Backfilled Entry"] = False

work["_EntryMinute"] = work["_EntryTime"].dt.floor("min")

minute_counts = (
    work.groupby(["_Operator", "_EntryMinute"])
    .size()
    .reset_index(name="Entries In Same Minute")
)

work = work.merge(
    minute_counts,
    on=["_Operator", "_EntryMinute"],
    how="left"
)

work["Batch Entry"] = work["Entries In Same Minute"] >= batch_entry_count

# -------------------------------------------------
# Repeated value check
# -------------------------------------------------

group_keys = ["_Operator", "_Part", "_Machine", "_Test"]

work["Previous Value"] = (
    work.groupby(group_keys)["_Value"]
    .shift(1)
)

work["Repeated Previous Value"] = (
    work["_Value"].notna() &
    work["Previous Value"].notna() &
    np.isclose(work["_Value"], work["Previous Value"], equal_nan=False)
)

work["Rolling Repeated Value Count"] = (
    work.groupby(group_keys)["Repeated Previous Value"]
    .transform(lambda x: x.rolling(repeat_window, min_periods=1).sum())
)

work["Repeated Value Pattern"] = (
    work["Rolling Repeated Value Count"] >= (repeat_window - 1)
)

work["Rounded Value"] = work["_Value"].apply(
    lambda x: is_rounded_value(x, rounded_decimal_threshold)
)

# -------------------------------------------------
# Low variation check
# -------------------------------------------------

variation = (
    work.groupby(group_keys)["_Value"]
    .agg(["count", "mean", "std"])
    .reset_index()
    .rename(columns={
        "count": "Group Count",
        "mean": "Group Mean",
        "std": "Group Std"
    })
)

variation["Low Variation Group"] = (
    (variation["Group Count"] >= 20) &
    (variation["Group Std"].fillna(0) <= low_variation_threshold)
)

work = work.merge(
    variation[
        group_keys +
        ["Group Count", "Group Mean", "Group Std", "Low Variation Group"]
    ],
    on=group_keys,
    how="left"
)

# -------------------------------------------------
# Risk scoring
# -------------------------------------------------

work["Risk Score"] = 0

risk_rules = {
    "Missing Required Data": 3,
    "Too Fast Entry": 3,
    "Batch Entry": 3,
    "Backfilled Entry": 3,
    "Repeated Value Pattern": 2,
    "Exact Target": 2,
    "Low Variation Group": 2,
    "Rounded Value": 1,
    "Zero Value": 1
}

for col, points in risk_rules.items():
    work["Risk Score"] += work[col].astype(int) * points

work["Risk Level"] = work["Risk Score"].apply(classify_risk)

flag_cols = list(risk_rules.keys())

work["Flag Reasons"] = work[flag_cols].apply(
    lambda row: ", ".join([col for col in flag_cols if row[col]]),
    axis=1
)

flagged = work[work["Risk Score"] > 0].copy()
high_risk = work[work["Risk Level"] == "High"].copy()

# -------------------------------------------------
# Operator summary
# -------------------------------------------------

operator_summary = (
    work.groupby("_Operator")
    .agg(
        Total_Records=("_Value", "size"),
        Avg_Risk_Score=("Risk Score", "mean"),
        Max_Risk_Score=("Risk Score", "max"),
        Suspicious_Records=("Risk Score", lambda x: (x > 0).sum()),
        High_Risk_Records=("Risk Level", lambda x: (x == "High").sum()),
        Too_Fast_Entries=("Too Fast Entry", "sum"),
        Batch_Entries=("Batch Entry", "sum"),
        Backfilled_Entries=("Backfilled Entry", "sum"),
        Repeated_Value_Patterns=("Repeated Value Pattern", "sum"),
        Exact_Target_Entries=("Exact Target", "sum"),
        Rounded_Value_Entries=("Rounded Value", "sum"),
        Low_Variation_Records=("Low Variation Group", "sum"),
        Zero_Value_Records=("Zero Value", "sum")
    )
    .reset_index()
    .rename(columns={"_Operator": "Operator"})
)

operator_summary["Suspicious %"] = (
    operator_summary["Suspicious_Records"] /
    operator_summary["Total_Records"] *
    100
).round(2)

operator_summary["Operator Risk Level"] = (
    operator_summary["Avg_Risk_Score"].apply(classify_risk)
)

operator_summary = operator_summary.sort_values(
    ["High_Risk_Records", "Avg_Risk_Score", "Suspicious %"],
    ascending=False
)

# -------------------------------------------------
# Dashboard
# -------------------------------------------------

st.subheader("Dashboard")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Records", f"{len(work):,}")
c2.metric("Suspicious Records", f"{len(flagged):,}")
c3.metric("High-Risk Records", f"{len(high_risk):,}")
c4.metric("Operators", work["_Operator"].nunique())
c5.metric(
    "High-Risk Operators",
    int((operator_summary["Operator Risk Level"] == "High").sum())
)

tabs = st.tabs([
    "Suspicious Records",
    "Operator Summary",
    "Flag Breakdown",
    "Batch Entry Analysis",
    "Repeated Value Analysis",
    "Low Variation Analysis",
    "Download Results"
])

# -------------------------------------------------
# Suspicious Records
# -------------------------------------------------

with tabs[0]:
    st.subheader("Suspicious Records")

    risk_filter = st.multiselect(
        "Risk Level Filter",
        ["Low", "Medium", "High"],
        default=["Medium", "High"]
    )

    view = flagged[flagged["Risk Level"].isin(risk_filter)].copy()

    display_cols = [
        "_Operator",
        "_EntryTime",
        "_InspectionTime",
        "_Part",
        "_Machine",
        "_Test",
        "_Value",
        "_Target",
        "Seconds Since Last Entry",
        "Entry Delay Minutes",
        "Entries In Same Minute",
        "Risk Score",
        "Risk Level",
        "Flag Reasons"
    ]

    st.dataframe(
        view[display_cols].sort_values("Risk Score", ascending=False),
        use_container_width=True
    )

# -------------------------------------------------
# Operator Summary
# -------------------------------------------------

with tabs[1]:
    st.subheader("Operator Risk Summary")
    st.dataframe(operator_summary, use_container_width=True)
    st.bar_chart(operator_summary.set_index("Operator")["Avg_Risk_Score"])

# -------------------------------------------------
# Flag Breakdown
# -------------------------------------------------

with tabs[2]:
    st.subheader("Flag Breakdown")

    flag_summary = pd.DataFrame([
        {
            "Flag": col,
            "Count": int(work[col].sum()),
            "Percent": round(work[col].mean() * 100, 2)
        }
        for col in flag_cols
    ]).sort_values("Count", ascending=False)

    st.dataframe(flag_summary, use_container_width=True)
    st.bar_chart(flag_summary.set_index("Flag")["Count"])

# -------------------------------------------------
# Batch Entry Analysis
# -------------------------------------------------

with tabs[3]:
    st.subheader("Batch Entry Analysis")

    batch_view = (
        work.groupby(["_Operator", "_EntryMinute"])
        .size()
        .reset_index(name="Entries In Same Minute")
        .sort_values("Entries In Same Minute", ascending=False)
        .rename(columns={
            "_Operator": "Operator",
            "_EntryMinute": "Entry Minute"
        })
    )

    st.dataframe(batch_view, use_container_width=True)

# -------------------------------------------------
# Repeated Value Analysis
# -------------------------------------------------

with tabs[4]:
    st.subheader("Repeated Value Analysis")

    repeat_view = (
        work.groupby(["_Operator", "_Part", "_Machine", "_Test", "_Value"])
        .size()
        .reset_index(name="Repeat Count")
        .sort_values("Repeat Count", ascending=False)
        .rename(columns={
            "_Operator": "Operator",
            "_Part": "Part",
            "_Machine": "Machine",
            "_Test": "Test",
            "_Value": "Value"
        })
    )

    st.dataframe(repeat_view.head(500), use_container_width=True)

# -------------------------------------------------
# Low Variation Analysis
# -------------------------------------------------

with tabs[5]:
    st.subheader("Low Variation Analysis")

    variation_view = variation.sort_values(
        ["Low Variation Group", "Group Std"],
        ascending=[False, True]
    ).rename(columns={
        "_Operator": "Operator",
        "_Part": "Part",
        "_Machine": "Machine",
        "_Test": "Test"
    })

    st.dataframe(variation_view, use_container_width=True)

# -------------------------------------------------
# Download Results
# -------------------------------------------------

with tabs[6]:
    st.subheader("Download Results")

    export_cols = [
        c for c in work.columns
        if not c.startswith("_") or c in [
            "_Operator",
            "_EntryTime",
            "_InspectionTime",
            "_Part",
            "_Machine",
            "_Test",
            "_Value",
            "_Target"
        ]
    ]

    excel_file = to_excel_download({
        "All Records Scored": work[export_cols],
        "Flagged Records": flagged[export_cols],
        "High Risk Records": high_risk[export_cols],
        "Operator Summary": operator_summary
    })

    st.download_button(
        label="Download Excel Report",
        data=excel_file,
        file_name="operator_data_integrity_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.warning(
    "Important: This app identifies suspicious data-entry patterns. "
    "It does not prove misconduct. Use the results as a review tool."
)
