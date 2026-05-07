"""
Profit Leak Finder 2.0
A simple, premium AI-powered business dashboard for small business owners.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Profit Leak Finder",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

/* ── Metric cards ── */
.kpi-card {
    background: linear-gradient(145deg, #1c1c2e, #252540);
    border: 1px solid #35355a;
    border-radius: 18px;
    padding: 22px 20px 18px;
    text-align: center;
    transition: transform .2s;
}
.kpi-card:hover { transform: translateY(-3px); }
.kpi-label  { color:#8888bb; font-size:12px; text-transform:uppercase; letter-spacing:1.2px; margin-bottom:6px; }
.kpi-value  { font-size:28px; font-weight:800; margin-bottom:4px; }
.kpi-sub    { font-size:12px; color:#666688; }

/* ── Alert / leak cards ── */
.alert-card {
    background: linear-gradient(135deg,#1e1e36,#28183a);
    border-left: 4px solid #ff6b6b;
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 12px;
    color: #f0f0f8;
    font-size: 14px;
    line-height: 1.7;
}
.alert-card.warn  { border-left-color: #ffd166; }
.alert-card.info  { border-left-color: #06d6a0; }
.alert-card.tip   { border-left-color: #a78bfa; }
.alert-title { font-weight: 700; font-size: 15px; margin-bottom: 5px; }

/* ── Section headers ── */
.sec-head {
    font-size: 20px;
    font-weight: 700;
    color: #e0e0ff;
    margin: 32px 0 14px;
    padding-bottom: 6px;
    border-bottom: 2px solid #35355a;
}

/* ── Health score bar ── */
.health-wrap { text-align:center; padding: 10px 0; }
.health-score { font-size:64px; font-weight:800; line-height:1; }
.health-label { font-size:14px; color:#8888bb; margin-top:4px; }

/* ── Landing steps ── */
.step-box {
    background:#1c1c2e;
    border:1px solid #35355a;
    border-radius:14px;
    padding:20px;
    text-align:center;
    height:100%;
}
.step-num { font-size:28px; font-weight:800; color:#a78bfa; }
.step-text { font-size:13px; color:#aaaacc; margin-top:6px; line-height:1.6; }

/* ── Demo button override ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg,#6d28d9,#a78bfa);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 15px;
    width: 100%;
    transition: opacity .2s;
}
div[data-testid="stButton"] > button:hover { opacity: 0.88; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background:#14142a !important; }
section[data-testid="stSidebar"] hr { border-color:#35355a; }

/* ── Progress bar colour ── */
.stProgress > div > div { background-color:#a78bfa !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

def load_csv(path):
    return pd.read_csv(path)

def load_upload(f):
    if f is None:
        return None
    return pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)

def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def fmt_money(v):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def health_color(score):
    if score >= 75: return "#06d6a0"
    if score >= 50: return "#ffd166"
    return "#ff6b6b"

def health_label(score):
    if score >= 80: return "🟢 Your business is doing great!"
    if score >= 65: return "🟡 Good — a few things to watch."
    if score >= 45: return "🟠 Some areas need attention."
    return "🔴 Action needed — check the leaks below."

def calc_health(profit_margin, expense_ratio, loss_products, total_products, trend_pct):
    """Simple 0–100 health score."""
    score = 50
    # Profit margin (max +25)
    score += min(profit_margin / 40 * 25, 25)
    # Expense ratio (lower = better, max +15)
    score += max(0, 15 - expense_ratio / 5)
    # No losing products (+10)
    if loss_products == 0:
        score += 10
    else:
        score -= min(loss_products * 5, 15)
    # Positive trend (+10)
    if trend_pct > 0:
        score += min(trend_pct / 2, 10)
    else:
        score += max(trend_pct / 2, -10)
    return int(min(max(round(score), 0), 100))


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "demo" not in st.session_state:
    st.session_state.demo = False


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 Profit Leak Finder")
    st.markdown("*Your simple business profit assistant.*")
    st.divider()

    st.markdown("### 📂 Upload Your Files")
    sales_file    = st.file_uploader("Upload Sales CSV",
                                     type=["csv","xlsx"], key="sf")
    st.caption("Required — date, product, quantity, price, cost")

    expenses_file = st.file_uploader("Upload Expense CSV *(Optional)*",
                                     type=["csv","xlsx"], key="ef")
    st.caption("Improves spending analysis")

    products_file = st.file_uploader("Upload Product List *(Optional)*",
                                     type=["csv","xlsx"], key="pf")
    st.caption("Unlocks deeper product insights")

    st.divider()
    st.markdown("### ⚙️ Settings")
    currency    = st.selectbox("Currency Symbol", ["$","₹","€","£","¥"], index=0)
    low_margin  = st.slider("Flag products earning less than (%)", 5, 50, 20)
    top_n       = st.slider("Show top/bottom N products", 3, 10, 5)

    st.divider()
    st.markdown("### 📋 Expected CSV Columns")
    with st.expander("Sales CSV"):
        st.code("Date, Product, Quantity,\nUnit_Price, Unit_COGS")
    with st.expander("Expense CSV"):
        st.code("Date, Category, Amount")
    with st.expander("Product CSV"):
        st.code("Product, Category,\nUnit_Price, Unit_COGS, Stock")


# ─────────────────────────────────────────────
#  LANDING — HERO + STEPS
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 10px 0 4px'>
    <h1 style='font-size:42px; font-weight:800; color:#e0e0ff; margin:0'>
        💸 Profit Leak Finder
    </h1>
    <p style='color:#8888bb; font-size:17px; margin-top:8px'>
        Find hidden business losses and get smart insights from your sales data.
    </p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
steps = [
    ("1️⃣", "Upload your sales data", "Add your sales file in the sidebar on the left."),
    ("2️⃣", "View your business insights", "See sales, profit, trends, and your top products."),
    ("3️⃣", "Discover hidden profit leaks", "Find what's costing you money and fix it."),
]
for col, (num, title, desc) in zip([c1,c2,c3], steps):
    with col:
        st.markdown(f"""
        <div class="step-box">
            <div class="step-num">{num}</div>
            <div style='font-weight:700;color:#e0e0ff;margin-top:8px'>{title}</div>
            <div class="step-text">{desc}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Demo button — centered
_, btn_col, _ = st.columns([1.5, 1, 1.5])
with btn_col:
    if st.button("🎮 Try Demo Dashboard"):
        st.session_state.demo = True

st.divider()


# ─────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────
use_demo = st.session_state.demo or sales_file is None

if use_demo:
    df_sales    = load_csv(os.path.join(SAMPLE_DIR, "sample_sales.csv"))
    df_expenses = load_csv(os.path.join(SAMPLE_DIR, "sample_expenses.csv"))
    df_products = load_csv(os.path.join(SAMPLE_DIR, "sample_products.csv"))
    st.info("📊 Showing **demo data**. Upload your own files in the sidebar to analyse your business.", icon="ℹ️")
else:
    df_sales    = load_upload(sales_file)
    df_expenses = load_upload(expenses_file) if expenses_file else load_csv(os.path.join(SAMPLE_DIR, "sample_expenses.csv"))
    df_products = load_upload(products_file) if products_file else load_csv(os.path.join(SAMPLE_DIR, "sample_products.csv"))

# Clean
df_sales    = to_num(df_sales,    ["Quantity","Unit_Price","Unit_COGS"])
df_expenses = to_num(df_expenses, ["Amount"])
df_products = to_num(df_products, ["Unit_Price","Unit_COGS","Stock"])
df_sales["Date"]    = pd.to_datetime(df_sales["Date"],    errors="coerce")
df_expenses["Date"] = pd.to_datetime(df_expenses["Date"], errors="coerce")

# Derived
df_sales["Revenue"]      = df_sales["Quantity"] * df_sales["Unit_Price"]
df_sales["Cost"]         = df_sales["Quantity"] * df_sales["Unit_COGS"]
df_sales["Profit"]       = df_sales["Revenue"]  - df_sales["Cost"]
df_sales["Margin_%"]     = np.where(df_sales["Revenue"] > 0,
                                    df_sales["Profit"] / df_sales["Revenue"] * 100, 0)
df_products["Margin_%"]  = np.where(df_products["Unit_Price"] > 0,
                                    (df_products["Unit_Price"] - df_products["Unit_COGS"]) /
                                     df_products["Unit_Price"] * 100, 0)

# Monthly roll-ups
ms = df_sales.groupby(df_sales["Date"].dt.to_period("M")).agg(
         Revenue=("Revenue","sum"), Cost=("Cost","sum"), Profit=("Profit","sum")).reset_index()
ms["Date"] = ms["Date"].dt.to_timestamp()
me = df_expenses.groupby(df_expenses["Date"].dt.to_period("M"))["Amount"].sum().reset_index()
me["Date"] = me["Date"].dt.to_timestamp()
monthly = pd.merge(ms, me, on="Date", how="outer").fillna(0)
monthly["Net_Profit"] = monthly["Profit"] - monthly["Amount"]
monthly["Net_Margin"] = np.where(monthly["Revenue"]>0,
                                  monthly["Net_Profit"]/monthly["Revenue"]*100, 0)

# Product roll-ups
prod = df_sales.groupby("Product").agg(
        Total_Revenue=("Revenue","sum"), Total_Cost=("Cost","sum"),
        Total_Profit=("Profit","sum"),   Total_Qty=("Quantity","sum")).reset_index()
prod["Margin_%"] = np.where(prod["Total_Revenue"]>0,
                             prod["Total_Profit"]/prod["Total_Revenue"]*100, 0)

# KPIs
total_rev   = df_sales["Revenue"].sum()
total_profit= df_sales["Profit"].sum()
total_exp   = df_expenses["Amount"].sum()
net_profit  = total_profit - total_exp
avg_margin  = (total_profit / total_rev * 100) if total_rev > 0 else 0
top_product = prod.sort_values("Total_Revenue", ascending=False).iloc[0]["Product"]
top_expense = df_expenses.groupby("Category")["Amount"].sum().idxmax() if len(df_expenses) else "—"
loss_count  = (prod["Total_Profit"] < 0).sum()
exp_ratio   = (total_exp / total_rev * 100) if total_rev > 0 else 0

# Trend (last 3 months vs 3 before that)
if len(monthly) >= 6:
    recent  = monthly["Net_Profit"].iloc[-3:].mean()
    earlier = monthly["Net_Profit"].iloc[-6:-3].mean()
    trend_pct = ((recent - earlier) / abs(earlier) * 100) if earlier != 0 else 0
else:
    trend_pct = 0

health_score = calc_health(avg_margin, exp_ratio, loss_count,
                            len(prod), trend_pct)
h_color = health_color(health_score)


# ─────────────────────────────────────────────
#  SECTION 1 — KPI CARDS
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">📊 Your Business at a Glance</div>', unsafe_allow_html=True)

k1,k2,k3,k4,k5 = st.columns(5)
cards = [
    (k1, "💰 Total Sales",          fmt_money(total_rev),    "#8be9fd",
     f"{len(df_sales):,} transactions"),
    (k2, "📈 Estimated Profit",      fmt_money(net_profit),  "#06d6a0" if net_profit>=0 else "#ff6b6b",
     f"After expenses"),
    (k3, "⭐ Your Best Product",     top_product,            "#ffd166",
     "Highest total sales"),
    (k4, "💸 Biggest Spending Area", top_expense,            "#ff9f43",
     "Top expense category"),
    (k5, "🏥 Business Health Score", f"{health_score}/100",  h_color,
     health_label(health_score).split("—")[0].strip()),
]
for col, label, val, color, sub in cards:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color:{color}">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SECTION 2 — BUSINESS HEALTH SCORE DETAIL
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">🏥 Business Health Score</div>', unsafe_allow_html=True)

hc1, hc2 = st.columns([1, 2])
with hc1:
    st.markdown(f"""
    <div class="kpi-card" style="padding:30px 20px">
        <div class="health-wrap">
            <div class="health-score" style="color:{h_color}">{health_score}</div>
            <div class="health-label">out of 100</div>
            <div style="margin-top:12px;font-size:15px;color:#e0e0ff;font-weight:600">
                {health_label(health_score)}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

with hc2:
    factors = {
        "Profit Margin":      min(avg_margin / 40 * 100, 100),
        "Expense Control":    max(0, 100 - exp_ratio),
        "Product Health":     100 if loss_count == 0 else max(0, 100 - loss_count * 20),
        "Sales Trend":        min(max(50 + trend_pct, 0), 100),
    }
    labels  = list(factors.keys())
    values  = list(factors.values())
    colors  = [health_color(v) for v in values]
    fig_h = go.Figure()
    for label, val, col in zip(labels, values, colors):
        fig_h.add_trace(go.Bar(x=[val], y=[label], orientation="h",
                               marker_color=col, width=0.5,
                               text=f"{val:.0f}%", textposition="inside"))
    fig_h.update_layout(
        height=200, showlegend=False, barmode="overlay",
        plot_bgcolor="#0f0f1a", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Inter", size=13),
        xaxis=dict(range=[0,100], gridcolor="#2a2a3e", ticksuffix="%"),
        yaxis=dict(gridcolor="#2a2a3e"),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_h, use_container_width=True)


# ─────────────────────────────────────────────
#  SECTION 3 — CHARTS
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">📈 Your Sales & Profit Over Time</div>', unsafe_allow_html=True)

ch1, ch2 = st.columns(2)
with ch1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["Revenue"],
        name="Sales", fill="tozeroy",
        line=dict(color="#8be9fd", width=2.5),
        fillcolor="rgba(139,233,253,0.12)"))
    fig1.add_trace(go.Scatter(
        x=monthly["Date"], y=monthly["Net_Profit"],
        name="Profit", fill="tozeroy",
        line=dict(color="#06d6a0", width=2.5),
        fillcolor="rgba(6,214,160,0.12)"))
    fig1.update_layout(
        height=300, title="Sales vs Profit by Month",
        plot_bgcolor="#0f0f1a", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Inter"),
        legend=dict(bgcolor="#1c1c2e", bordercolor="#35355a"),
        xaxis=dict(gridcolor="#2a2a3e"), yaxis=dict(gridcolor="#2a2a3e"),
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig1, use_container_width=True)

with ch2:
    top_prods = prod.nlargest(top_n, "Total_Revenue")
    fig2 = px.bar(top_prods, y="Product", x="Total_Revenue", orientation="h",
                  color="Margin_%",
                  color_continuous_scale=["#ff6b6b","#ffd166","#06d6a0"],
                  text=[fmt_money(v) for v in top_prods["Total_Revenue"]],
                  title="Your Best-Selling Products")
    fig2.update_traces(textposition="inside")
    fig2.update_layout(
        height=300, plot_bgcolor="#0f0f1a", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Inter"),
        xaxis=dict(gridcolor="#2a2a3e", title="Total Sales"),
        yaxis=dict(gridcolor="#2a2a3e"),
        coloraxis_colorbar=dict(title="Margin %"),
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

ch3, ch4 = st.columns(2)
with ch3:
    exp_cat = df_expenses.groupby("Category")["Amount"].sum().reset_index()
    fig3 = px.pie(exp_cat, names="Category", values="Amount",
                  hole=0.52,
                  color_discrete_sequence=px.colors.qualitative.Pastel,
                  title="Where Your Money Goes")
    fig3.update_traces(textinfo="label+percent", pull=[0.04]*len(exp_cat))
    fig3.update_layout(
        height=320, plot_bgcolor="#0f0f1a", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Inter"),
        legend=dict(bgcolor="#1c1c2e"),
        margin=dict(t=40, b=20),
        annotations=[dict(text=fmt_money(total_exp), x=0.5, y=0.5,
                          font=dict(size=16, color="#e0e0ff"), showarrow=False)]
    )
    st.plotly_chart(fig3, use_container_width=True)

with ch4:
    net_colors = ["#06d6a0" if v>=0 else "#ff6b6b" for v in monthly["Net_Profit"]]
    fig4 = go.Figure(go.Bar(
        x=monthly["Date"], y=monthly["Net_Profit"],
        marker_color=net_colors,
        text=[fmt_money(v) for v in monthly["Net_Profit"]],
        textposition="outside",
    ))
    fig4.add_hline(y=0, line_dash="dash", line_color="#aaaacc", line_width=1)
    fig4.update_layout(
        height=320, title="Monthly Profit",
        plot_bgcolor="#0f0f1a", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0ff", family="Inter"),
        xaxis=dict(gridcolor="#2a2a3e"), yaxis=dict(gridcolor="#2a2a3e"),
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig4, use_container_width=True)


# ─────────────────────────────────────────────
#  SECTION 4 — HIDDEN PROFIT LEAKS
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">🔍 Hidden Profit Leaks</div>', unsafe_allow_html=True)
st.markdown("*These are the areas that may be quietly costing your business money.*")

leaks_found = []

# 1. Products losing money
losing = prod[prod["Total_Profit"] < 0]
if not losing.empty:
    for _, r in losing.iterrows():
        leaks_found.append(("🔴", "danger",
            f"**{r['Product']}** is losing money",
            f"Every sale of {r['Product']} costs you more than you earn. "
            f"Total loss so far: **{fmt_money(abs(r['Total_Profit']))}**. "
            f"Consider raising the price or stopping this product."))

# 2. Products making very little profit
low_m = prod[(prod["Margin_%"] < low_margin) & (prod["Total_Profit"] >= 0)]
for _, r in low_m.iterrows():
    leaks_found.append(("⚠️", "warn",
        f"**{r['Product']}** sells well but earns low profit",
        f"It earns only **{r['Margin_%']:.1f}%** profit per sale. "
        f"That's below your {low_margin}% target. A small price increase could make a big difference."))

# 3. Expense spikes month-over-month
me2 = me.copy()
me2["MoM_%"] = me2["Amount"].pct_change() * 100
spikes = me2[me2["MoM_%"] > 20].dropna()
if not spikes.empty:
    for _, r in spikes.iterrows():
        leaks_found.append(("📈", "warn",
            f"Your spending jumped up in {r['Date'].strftime('%B %Y')}",
            f"Total expenses rose by **{r['MoM_%']:.1f}%** in that month. "
            f"Check what caused this increase — it may be a one-off or a recurring leak."))

# 4. One product dominates revenue (risk)
top_share = prod["Total_Revenue"].max() / prod["Total_Revenue"].sum() * 100
if top_share > 50:
    top_name = prod.sort_values("Total_Revenue", ascending=False).iloc[0]["Product"]
    leaks_found.append(("⚡", "warn",
        f"**{top_name}** makes up most of your sales",
        f"It accounts for **{top_share:.1f}%** of your total sales. "
        f"This is risky — if demand for this product drops, your whole business is affected. "
        f"Consider growing other product lines."))

# 5. Advertising spending high
if "Advertising" in df_expenses["Category"].values:
    ad_total = df_expenses[df_expenses["Category"]=="Advertising"]["Amount"].sum()
    ad_pct = ad_total / total_rev * 100 if total_rev > 0 else 0
    if ad_pct > 15:
        leaks_found.append(("💸", "danger",
            "Your advertising spending is very high",
            f"You're spending **{fmt_money(ad_total)}** on advertising — "
            f"that's **{ad_pct:.1f}%** of your total sales. "
            f"Aim to keep this below 10–15% for a healthy business."))

# 6. Declining profit trend
if trend_pct < -10:
    leaks_found.append(("📉", "danger",
        "Your profits have been going down recently",
        f"Compared to earlier months, your profit is down by **{abs(trend_pct):.1f}%**. "
        f"Review your costs and check if any expenses have quietly increased."))

if not leaks_found:
    st.markdown("""
    <div class="alert-card info">
        <div class="alert-title">✅ No major profit leaks found!</div>
        Your business looks healthy. Keep an eye on your expenses and product margins monthly.
    </div>""", unsafe_allow_html=True)
else:
    lc1, lc2 = st.columns(2)
    for i, (icon, kind, title, body) in enumerate(leaks_found):
        col = lc1 if i % 2 == 0 else lc2
        with col:
            st.markdown(f"""
            <div class="alert-card {kind}">
                <div class="alert-title">{icon} {title}</div>
                {body}
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SECTION 5 — SMART SUGGESTIONS
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">💡 Smart Suggestions</div>', unsafe_allow_html=True)
st.markdown("*Simple actions that can improve your business profit.*")

suggestions = []

if not losing.empty:
    names = ", ".join(losing["Product"].tolist())
    suggestions.append(("🔴", "tip",
        f"Review your pricing for: {names}",
        "These products are losing money. Try raising the price slightly or talk to your supplier about reducing costs."))

if not low_m.empty:
    names2 = low_m.sort_values("Margin_%").iloc[0]["Product"]
    suggestions.append(("💰", "tip",
        f"Consider increasing the price of {names2}",
        f"Even a small price increase of 5–10% on {names2} could noticeably improve your overall profit."))

top5_prod = prod.nlargest(1, "Total_Profit")["Product"].values[0]
suggestions.append(("⭐", "info",
    f"Focus more on {top5_prod} — it's your most profitable product",
    "Put more marketing attention on your best performers. Growing your winners is faster than fixing your losers."))

if exp_ratio > 60:
    suggestions.append(("✂️", "warn",
        "Try to reduce your overall expenses",
        f"Your expenses are {exp_ratio:.1f}% of your sales. Look for subscriptions or services you no longer use."))

if top_share > 50:
    suggestions.append(("🌱", "info",
        "Grow your other products",
        "Having one product carry your business is risky. Try promoting your other products to spread the risk."))

suggestions.append(("📅", "info",
    "Review your numbers every month",
    "Small problems become big ones when ignored. A 30-minute monthly review can save you thousands per year."))

sc1, sc2 = st.columns(2)
for i, (icon, kind, title, body) in enumerate(suggestions):
    col = sc1 if i % 2 == 0 else sc2
    with col:
        st.markdown(f"""
        <div class="alert-card {kind}">
            <div class="alert-title">{icon} {title}</div>
            {body}
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SECTION 6 — DOWNLOAD REPORT
# ─────────────────────────────────────────────
st.markdown('<div class="sec-head">📥 Download Your Business Report</div>', unsafe_allow_html=True)

lines = [
    "PROFIT LEAK FINDER — BUSINESS REPORT",
    "=" * 40,
    "",
    "SUMMARY",
    f"  Total Sales:           {fmt_money(total_rev)}",
    f"  Estimated Profit:      {fmt_money(net_profit)}",
    f"  Total Expenses:        {fmt_money(total_exp)}",
    f"  Average Profit Margin: {avg_margin:.1f}%",
    f"  Business Health Score: {health_score}/100",
    f"  Best-Selling Product:  {top_product}",
    f"  Biggest Expense:       {top_expense}",
    "",
    "PROFIT LEAKS FOUND",
]
if not leaks_found:
    lines.append("  No major leaks found.")
else:
    for icon, _, title, body in leaks_found:
        lines.append(f"  {icon} {title}")
        lines.append(f"     → {body}")
        lines.append("")

lines += ["", "SMART SUGGESTIONS"]
for icon, _, title, body in suggestions:
    lines.append(f"  {icon} {title}")
    lines.append(f"     → {body}")
    lines.append("")

lines += ["", "PRODUCT PERFORMANCE TABLE", "-"*40]
for _, r in prod.sort_values("Total_Profit", ascending=False).iterrows():
    flag = " ⚠ LOW MARGIN" if r["Margin_%"] < low_margin else ""
    flag = " 🔴 LOSING MONEY" if r["Total_Profit"] < 0 else flag
    lines.append(f"  {r['Product']:20s}  Revenue: {fmt_money(r['Total_Revenue']):>10}  "
                 f"Profit: {fmt_money(r['Total_Profit']):>10}  Margin: {r['Margin_%']:5.1f}%{flag}")

report_text = "\n".join(lines)

dc1, dc2 = st.columns(2)
with dc1:
    st.download_button(
        "⬇️ Download Business Report (.txt)",
        data=report_text,
        file_name="profit_leak_report.txt",
        mime="text/plain",
        use_container_width=True,
    )

prod_csv = prod.copy()
prod_csv.columns = ["Product","Total Sales","Total Cost","Total Profit","Units Sold","Profit Margin %"]
with dc2:
    st.download_button(
        "⬇️ Download Product Analysis (.csv)",
        data=prod_csv.to_csv(index=False),
        file_name="product_analysis.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; color:#44446a; font-size:13px; padding:20px 0'>
    💸 Profit Leak Finder &nbsp;·&nbsp; Built with Streamlit &nbsp;·&nbsp;
    Simple. Useful. Yours.
</div>""", unsafe_allow_html=True)
