import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

# HR Analytics Dashboard 
# Sheet: Palo Alto Networks, columns A:AE

st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")

GOOGLE_CSV_URL = "https://docs.google.com/spreadsheets/d/1HDAfyuXvX7nQ8RkNIpADlTs5qT6Qtsy7GLx4zP6ZYEM/export?format=csv&gid=2853478"

EXPECTED_COLUMNS = [
    "Age", "Attrition", "BusinessTravel", "DailyRate", "Department",
    "DistanceFromHome", "Education", "EducationField", "EnvironmentSatisfaction",
    "Gender", "HourlyRate", "JobInvolvement", "JobLevel", "JobRole",
    "JobSatisfaction", "MaritalStatus", "MonthlyIncome", "MonthlyRate",
    "NumCompaniesWorked", "OverTime", "PercentSalaryHike", "PerformanceRating",
    "RelationshipSatisfaction", "StockOptionLevel", "TotalWorkingYears",
    "TrainingTimesLastYear", "WorkLifeBalance", "YearsAtCompany",
    "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager"
]

st.markdown(
    """
    <style>
    .main {background-color:#edf3fb;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg,#2d60c9,#306fe2);
        color: white;
        padding: 14px;
        border-radius: 14px;
        box-shadow: 0 5px 16px rgba(15,23,42,.08);
    }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {color: white !important;}
    .report-card {
        background: #ffffff;
        border: 1px solid #dce8f6;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(15,23,42,.06);
        margin-bottom: 14px;
    }
    .risk-low {background:#ddf8ea;color:#127a58;padding:8px 14px;border-radius:999px;font-weight:800;}
    .risk-medium {background:#fff0cf;color:#b26b00;padding:8px 14px;border-radius:999px;font-weight:800;}
    .risk-high {background:#fde2e1;color:#b42318;padding:8px 14px;border-radius:999px;font-weight:800;}
    </style>
    """,
    unsafe_allow_html=True,
)


def clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


@st.cache_data(ttl=300)
def load_from_google_sheet() -> pd.DataFrame:
    return pd.read_csv(GOOGLE_CSV_URL)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # If exported sheet has no proper headers, force the Apps Script column order.
    if len(df.columns) >= 31:
        first_31 = list(df.columns[:31])
        missing_expected = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if len(missing_expected) > 10:
            rename_map = {first_31[i]: EXPECTED_COLUMNS[i] for i in range(31)}
            df = df.rename(columns=rename_map)

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col in NUMERIC_COLUMNS else ""

    for col in TEXT_COLUMNS:
        df[col] = clean_text(df[col])
    for col in NUMERIC_COLUMNS:
        df[col] = to_number(df[col])

    df = df[(df["Age"] > 0) | (df["Department"] != "") | (df["Attrition"] != "")]
    return df[EXPECTED_COLUMNS]


TEXT_COLUMNS = [
    "Attrition", "BusinessTravel", "Department", "EducationField", "Gender",
    "JobRole", "MaritalStatus", "OverTime"
]

NUMERIC_COLUMNS = [
    "Age", "DailyRate", "DistanceFromHome", "Education", "EnvironmentSatisfaction",
    "HourlyRate", "JobInvolvement", "JobLevel", "JobSatisfaction",
    "MonthlyIncome", "MonthlyRate", "NumCompaniesWorked", "PercentSalaryHike",
    "PerformanceRating", "RelationshipSatisfaction", "StockOptionLevel",
    "TotalWorkingYears", "TrainingTimesLastYear", "WorkLifeBalance",
    "YearsAtCompany", "YearsInCurrentRole", "YearsSinceLastPromotion",
    "YearsWithCurrManager"
]


def is_attrition_yes(df: pd.DataFrame) -> pd.Series:
    return df["Attrition"].astype(str).str.lower().eq("yes")


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Major Filters")
    st.sidebar.caption("Keep All for full data")

    filtered = df.copy()
    filter_cols = [
        "Department", "Gender", "JobRole", "Attrition", "BusinessTravel",
        "OverTime", "MaritalStatus", "EducationField"
    ]

    for col in filter_cols:
        values = sorted([x for x in df[col].dropna().unique().tolist() if str(x).strip()])
        selected = st.sidebar.multiselect(col, values, default=[])
        if selected:
            filtered = filtered[filtered[col].isin(selected)]

    min_age, max_age = int(df["Age"].min()), int(df["Age"].max())
    age_range = st.sidebar.slider("Age Range", min_age, max_age, (min_age, max_age))
    filtered = filtered[(filtered["Age"] >= age_range[0]) & (filtered["Age"] <= age_range[1])]

    min_income, max_income = int(df["MonthlyIncome"].min()), int(df["MonthlyIncome"].max())
    income_range = st.sidebar.slider("Monthly Income Range", min_income, max_income, (min_income, max_income))
    filtered = filtered[(filtered["MonthlyIncome"] >= income_range[0]) & (filtered["MonthlyIncome"] <= income_range[1])]

    return filtered


def pct(part: float, total: float) -> float:
    return (part / total * 100) if total else 0


def build_summary(filtered: pd.DataFrame, all_rows: pd.DataFrame) -> dict:
    total = len(filtered)
    attrition = int(is_attrition_yes(filtered).sum()) if total else 0
    active = total - attrition
    return {
        "Total Employees": total,
        "Active Employees": active,
        "Attrition Employees": attrition,
        "Attrition Rate": pct(attrition, total),
        "Average Age": filtered["Age"].mean() if total else 0,
        "Avg Monthly Income": filtered["MonthlyIncome"].mean() if total else 0,
        "Avg Working Years": filtered["TotalWorkingYears"].mean() if total else 0,
        "Overall Rows": len(all_rows),
    }


def group_table(df: pd.DataFrame, field: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Name", "TotalEmployee", "Attrition", "AttritionRate"])
    temp = df.copy()
    temp["AttritionFlag"] = is_attrition_yes(temp).astype(int)
    out = temp.groupby(field, dropna=False).agg(
        TotalEmployee=(field, "size"),
        Attrition=("AttritionFlag", "sum")
    ).reset_index().rename(columns={field: "Name"})
    out["AttritionRate"] = (out["Attrition"] / out["TotalEmployee"] * 100).round(1).astype(str) + "%"
    return out.sort_values("Name")


def department_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Department", "TotalEmployee", "Active", "Attrition", "AttritionRate", "AvgAge", "AvgIncome"])
    temp = df.copy()
    temp["AttritionFlag"] = is_attrition_yes(temp).astype(int)
    out = temp.groupby("Department", dropna=False).agg(
        TotalEmployee=("Department", "size"),
        Attrition=("AttritionFlag", "sum"),
        AvgAge=("Age", "mean"),
        AvgIncome=("MonthlyIncome", "mean"),
    ).reset_index()
    out["Active"] = out["TotalEmployee"] - out["Attrition"]
    out["AttritionRate"] = (out["Attrition"] / out["TotalEmployee"] * 100).round(1).astype(str) + "%"
    out["AvgAge"] = out["AvgAge"].round(1)
    out["AvgIncome"] = out["AvgIncome"].round(0).astype(int)
    return out[["Department", "TotalEmployee", "Active", "Attrition", "AttritionRate", "AvgAge", "AvgIncome"]].sort_values("Department")


def income_band_table(df: pd.DataFrame) -> pd.DataFrame:
    bands = [
        ("0-5K", 0, 5000),
        ("5K-10K", 5001, 10000),
        ("10K-15K", 10001, 15000),
        ("15K+", 15001, 999999999),
    ]
    rows = []
    for name, low, high in bands:
        data = df[(df["MonthlyIncome"] >= low) & (df["MonthlyIncome"] <= high)]
        attr = int(is_attrition_yes(data).sum()) if len(data) else 0
        rows.append({
            "IncomeBand": name,
            "TotalEmployee": len(data),
            "Attrition": attr,
            "AttritionRate": f"{pct(attr, len(data)):.1f}%",
        })
    return pd.DataFrame(rows)


def age_band_counts(df: pd.DataFrame) -> pd.DataFrame:
    labels = ["18-25", "26-35", "36-45", "46-55", "56+"]
    bins = [0, 25, 35, 45, 55, 200]
    out = df.copy()
    out["Age Band"] = pd.cut(out["Age"], bins=bins, labels=labels, include_lowest=True)
    return out["Age Band"].value_counts().reindex(labels, fill_value=0).reset_index(name="Employee Count").rename(columns={"index": "Age Band"})


def working_years_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"Working Years Band": [], "Employee Count": []})
    max_val = int(df["TotalWorkingYears"].max())
    rows = []
    for start in range(0, max_val + 1, 5):
        end = start + 4
        rows.append({
            "Working Years Band": f"{start}-{end}",
            "Employee Count": len(df[(df["TotalWorkingYears"] >= start) & (df["TotalWorkingYears"] <= end)]),
        })
    return pd.DataFrame(rows)


def risk_score(attrition_rate: float) -> str:
    if attrition_rate >= 25:
        return "High Risk"
    if attrition_rate >= 15:
        return "Medium Risk"
    return "Low Risk"


def build_ai_analysis(filtered: pd.DataFrame, all_rows: pd.DataFrame) -> dict:
    summary = build_summary(filtered, all_rows)
    dept = department_table(filtered).copy()
    role = group_table(filtered, "JobRole").copy()
    overtime = group_table(filtered, "OverTime").copy()

    for frame in [dept, role, overtime]:
        if not frame.empty:
            frame["RateValue"] = frame["AttritionRate"].str.replace("%", "", regex=False).astype(float)
            frame.sort_values("RateValue", ascending=False, inplace=True)
            frame.drop(columns=["RateValue"], inplace=True)

    high_dept = dept.iloc[0].to_dict() if not dept.empty else {}
    high_role = role.iloc[0].to_dict() if not role.empty else {}
    high_overtime = overtime.iloc[0].to_dict() if not overtime.empty else {}

    insights = [
        f"Selected data has {summary['Total Employees']} employees and {summary['Attrition Employees']} attrition cases. Attrition rate is {summary['Attrition Rate']:.1f}%.",
        f"Average age is {summary['Average Age']:.1f}, average monthly income is {summary['Avg Monthly Income']:.0f}, and average total working years is {summary['Avg Working Years']:.1f}.",
    ]
    if high_dept:
        insights.insert(1, f"Highest department attrition is {high_dept['Department']} with {high_dept['AttritionRate']} attrition.")
    if high_role:
        insights.insert(2, f"Highest job role attrition is {high_role['Name']} with {high_role['AttritionRate']} attrition.")
    if high_overtime:
        insights.insert(3, f"OverTime segment {high_overtime['Name']} shows attrition trend at {high_overtime['AttritionRate']}.")

    actions = [
        f"Review retention plan for {high_dept.get('Department', 'high-risk departments')}, especially employees with OverTime = Yes.",
        "Compare monthly income and job satisfaction for high attrition job roles to identify compensation or engagement gaps.",
        "Run monthly HR review using Department, JobRole, OverTime and Income filters before final management submission.",
        "Prioritize manager discussion for employees with low work-life balance, low job satisfaction and high distance from home.",
    ]

    return {
        "score": risk_score(summary["Attrition Rate"]),
        "insights": insights,
        "actions": actions,
        "top_department_risk": dept.head(5),
        "top_job_role_risk": role.head(5),
        "methodology": "Rule-based HR analysis from selected sheet data. It calculates attrition rate, employee count, monthly income, working years and major HR risk segments.",
    }


def show_dashboard(filtered: pd.DataFrame, all_rows: pd.DataFrame) -> None:
    summary = build_summary(filtered, all_rows)

    cols = st.columns(8)
    metrics = [
        ("Total Employees", f"{summary['Total Employees']:,}"),
        ("Active Employees", f"{summary['Active Employees']:,}"),
        ("Attrition Employees", f"{summary['Attrition Employees']:,}"),
        ("Attrition Rate", f"{summary['Attrition Rate']:.1f}%"),
        ("Average Age", f"{summary['Average Age']:.1f}"),
        ("Avg Monthly Income", f"{summary['Avg Monthly Income']:,.0f}"),
        ("Avg Working Years", f"{summary['Avg Working Years']:.1f}"),
        ("Overall Rows", f"{summary['Overall Rows']:,}"),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

    c1, c2 = st.columns(2)
    dept_counts = filtered["Department"].value_counts().reset_index()
    dept_counts.columns = ["Department", "Employee Count"]
    c1.subheader("Department Wise Employees")
    fig = px.bar(dept_counts, x="Department", y = "Employee Count")
    c1.plotly_chart(fig, use_container_width=True)

    c2.subheader("Department Wise Employee Share (%)")
    c2.plotly_chart(px.pie(dept_counts, names="Department", values="Employee Count", hole=0.45), use_container_width=True)

    c3, c4 = st.columns(2)
    c3.subheader("Age Band - Employee Count")
    fig = px.bar(age_band_counts(filtered), y="Age Band", x="Employee Count", orientation="h", text="Employee Count")
    c3.plotly_chart(fig)
    c4.subheader("Total Working Years - Employee Count")
    c4.plotly_chart(px.line(working_years_counts(filtered), x="Working Years Band", y="Employee Count", markers=True, text="Employee Count"), use_container_width=True)

    t1, t2 = st.columns(2)
    t1.subheader("Department Summary")
    t1.dataframe(department_table(filtered), use_container_width=True, hide_index=True)

    t2.subheader("Job Role Summary")
    t2.dataframe(group_table(filtered, "JobRole"), use_container_width=True, hide_index=True)

    t3, t4 = st.columns(2)
    t3.subheader("OverTime Summary")
    t3.dataframe(group_table(filtered, "OverTime"), use_container_width=True, hide_index=True)

    t4.subheader("Monthly Income Band Summary")
    t4.dataframe(income_band_table(filtered), use_container_width=True, hide_index=True)


def show_ai_report(filtered: pd.DataFrame, all_rows: pd.DataFrame) -> None:
    ai = build_ai_analysis(filtered, all_rows)
    css_class = {"High Risk": "risk-high", "Medium Risk": "risk-medium", "Low Risk": "risk-low"}[ai["score"]]

    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    st.subheader("Report AI Analysis")
    st.markdown(f"Risk Status: <span class='{css_class}'>{ai['score']}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown("### Current Status")
    c1.write(ai["insights"][0] if ai["insights"] else "No summary available.")

    c2.markdown("### Risk Focus")
    if not ai["top_department_risk"].empty:
        row = ai["top_department_risk"].iloc[0]
        c2.write(f"Top Department: {row['Department']} ({row['AttritionRate']})")
    if not ai["top_job_role_risk"].empty:
        row = ai["top_job_role_risk"].iloc[0]
        c2.write(f"Top Job Role: {row['Name']} ({row['AttritionRate']})")

    c3.markdown("### Immediate Action")
    for action in ai["actions"][:2]:
        c3.write("• " + action)

    a1, a2, a3 = st.columns(3)
    a1.subheader("Key Insights")
    for item in ai["insights"]:
        a1.info(item)

    a2.subheader("Recommended Actions")
    for item in ai["actions"]:
        a2.success(item)

    a3.subheader("AI Summary Blocks")
    summary = build_summary(filtered, all_rows)
    a3.info(f"Forecasting: Based on current attrition of {summary['Attrition Employees']} employees from {summary['Total Employees']} employees, HR should track month-wise attrition trend and plan replacement hiring early.")
    a3.warning("Predictive: Risk focus is identified from department, job role and overtime attrition indicators. High attrition areas need HR attention and manager review.")
    a3.success("Prescriptive: Recommended action is stay interview, workload review, salary/career discussion and department-wise retention plan.")

    r1, r2 = st.columns(2)
    r1.subheader("Top Department Risk")
    r1.dataframe(ai["top_department_risk"], use_container_width=True, hide_index=True)
    r2.subheader("Top Job Role Risk")
    r2.dataframe(ai["top_job_role_risk"], use_container_width=True, hide_index=True)

    st.subheader("Analysis Method")
    st.write(ai["methodology"])
    st.caption("Submission Note: Connected to sheet Palo Alto Networks, columns A to AE. Department summary uses Department column E, Attrition column B, Age column A, Total Working Years column Y and Monthly Income column Q.")


st.title("Palo Alto Networks - HR Analytics Dashboard")
st.caption("Attrition, Department, Age, Monthly Income and Web Model Analysis")

source = st.sidebar.radio("Data Source", ["Google Sheet CSV link", "Upload Excel/CSV"], index=0)

try:
    if source == "Google Sheet CSV link":
        raw_df = load_from_google_sheet()
    else:
        uploaded = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "xls", "csv"])
        if uploaded is None:
            st.info("Upload an Excel/CSV file, or switch to Google Sheet CSV link.")
            st.stop()
        raw_df = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)

    df = normalize_dataframe(raw_df)
except Exception as exc:
    st.error("Could not load data. If using Google Sheet, share it as Anyone with the link can view, or use the upload option.")
    st.exception(exc)
    st.stop()

filtered_df = filter_dataframe(df)

tab1, tab2, tab3 = st.tabs(["Dashboard", "Report AI Analysis", "Raw Data"])
with tab1:
    show_dashboard(filtered_df, df)
with tab2:
    show_ai_report(filtered_df, df)
with tab3:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
