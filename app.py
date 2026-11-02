
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import ollama

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Sapphire IQ | Amazon India",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 2. PREMIUM DASHBOARD DESIGN
# =====================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #07111f, #0c1830 60%, #101d35);
    color: #f0f5ff;
}
[data-testid="stSidebar"] {
    background: #0b1527;
    border-right: 1px solid #233653;
}
h1, h2, h3 {
    color: #edf4ff !important;
}
p, label, [data-testid="stMarkdownContainer"] {
    color: #d5e0f2;
}
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #142641, #1a3150);
    border: 1px solid #2b4b70;
    border-radius: 15px;
    padding: 17px;
    box-shadow: 0 5px 22px #00000025;
}
div[data-testid="stMetricLabel"] {
    color: #a9bfdc;
}
div[data-testid="stMetricValue"] {
    color: #66e3d0;
}
div[data-testid="stPlotlyChart"] {
    background: #101f35;
    border: 1px solid #243b59;
    border-radius: 14px;
    padding: 8px;
}
.stButton button, .stDownloadButton button {
    border-radius: 9px;
    border: 1px solid #3a7799;
}
hr {
    border-color: #29415f;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. HEADER
# =====================================================
st.markdown("""
# 💎 SAPPHIRE IQ
### AMAZON INDIA · SALES INTELLIGENCE PLATFORM

Transforming sales transactions into actionable business insights.
""")

st.caption("Interactive analytics • Product intelligence • Profitability • AI-assisted insights")
st.divider()

# =====================================================
# 4. LOAD EXCEL DATA
# =====================================================
folder = Path(__file__).parent

excel_files = [
    f for f in folder.glob("*.xlsx")
    if not f.name.startswith("~$")
]

if not excel_files:
    st.error(
        "Excel file not found. Place your Amazon Sales Excel "
        "file in the same folder as app.py."
    )
    st.stop()

try:
    df = pd.read_excel(excel_files[0])
except Exception as error:
    st.error(f"Could not read Excel file: {error}")
    st.stop()

# Check required columns
required = [
    "Order_ID", "Order_Date", "Category", "Product",
    "Quantity", "Unit_Price_INR", "Discount_Pct",
    "Total_Sales_INR", "Profit_INR", "Payment_Method",
    "Fulfillment", "Order_Status", "Ship_State"
]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error(f"Required columns are missing: {missing}")
    st.write("Available columns:", df.columns.tolist())
    st.stop()

# =====================================================
# 5. CLEAN DATA SAFELY
# =====================================================
df = df.copy()
df["Order_Date"] = pd.to_datetime(
    df["Order_Date"], errors="coerce"
)

numeric_columns = [
    "Quantity", "Unit_Price_INR", "Discount_Pct",
    "Total_Sales_INR", "Profit_INR"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[
    "Order_Date", "Total_Sales_INR", "Profit_INR"
])

for col in [
    "Category", "Product", "Payment_Method",
    "Fulfillment", "Order_Status", "Ship_State"
]:
    df[col] = df[col].fillna("Unknown").astype(str)

if df.empty:
    st.error("No valid records remain after data cleaning.")
    st.stop()

# =====================================================
# 6. SIDEBAR FILTERS
# =====================================================
st.sidebar.title("🎛️ Control Center")
st.sidebar.caption("Customize your analysis")

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()

date_range = st.sidebar.date_input(
    "📅 Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = date_range

categories = st.sidebar.multiselect(
    "🛍️ Product categories",
    sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique())
)

states = st.sidebar.multiselect(
    "📍 Shipping states",
    sorted(df["Ship_State"].unique()),
    default=sorted(df["Ship_State"].unique())
)

statuses = st.sidebar.multiselect(
    "📦 Order status",
    sorted(df["Order_Status"].unique()),
    default=sorted(df["Order_Status"].unique())
)

payments = st.sidebar.multiselect(
    "💳 Payment methods",
    sorted(df["Payment_Method"].unique()),
    default=sorted(df["Payment_Method"].unique())
)

# =====================================================
# 7. APPLY FILTERS
# =====================================================
filtered = df[
    (df["Order_Date"].dt.date >= start_date)
    & (df["Order_Date"].dt.date <= end_date)
    & (df["Category"].isin(categories))
    & (df["Ship_State"].isin(states))
    & (df["Order_Status"].isin(statuses))
    & (df["Payment_Method"].isin(payments))
].copy()

if filtered.empty:
    st.warning("No records match these filters. Adjust the selections.")
    st.stop()

# =====================================================
# 8. CALCULATE BUSINESS METRICS
# =====================================================
revenue = filtered["Total_Sales_INR"].sum()
profit = filtered["Profit_INR"].sum()
units = filtered["Quantity"].sum()
orders = filtered["Order_ID"].nunique()
margin = (profit / revenue * 100) if revenue else 0
avg_order_value = revenue / orders if orders else 0

# =====================================================
# 9. EXECUTIVE SUMMARY
# =====================================================
st.header("⚡ Executive Snapshot")

st.markdown(
    f"Analysis covers **{len(filtered):,} rows** and "
    f"**{orders:,} unique order IDs** for the selected period."
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("💰 Sales Revenue", f"₹{revenue:,.0f}")
k2.metric("📈 Recorded Profit", f"₹{profit:,.0f}")
k3.metric("🛒 Unique Orders", f"{orders:,}")
k4.metric("📦 Units", f"{units:,.0f}")
k5.metric("🎯 Profit Margin", f"{margin:.1f}%")

st.caption(
    f"Average revenue per unique order ID: ₹{avg_order_value:,.2f}. "
    "This is not necessarily average basket value if order IDs "
    "represent individual line items."
)

# =====================================================
# 10. HELPER FOR CHART STYLING
# =====================================================
def polish(fig, height=360):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5efff"),
        margin=dict(l=15, r=15, t=55, b=15),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02
        )
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False
    )
    fig.update_yaxes(
        gridcolor="#263a56",
        zeroline=False
    )
    return fig

# =====================================================
# 11. SALES TREND
# =====================================================
st.divider()
st.header("📊 Sales & Profit Intelligence")

daily = (
    filtered.set_index("Order_Date")
    .resample("D")
    .agg(
        Sales=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
    .reset_index()
)

monthly = (
    filtered.assign(
        Month=filtered["Order_Date"].dt.to_period("M").astype(str)
    )
    .groupby("Month", as_index=False)
    .agg(
        Sales=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
)

if len(monthly) > 1:
    trend = monthly
    x_col = "Month"
    x_title = "Month"
else:
    trend = daily
    x_col = "Order_Date"
    x_title = "Date"

left, right = st.columns(2)

with left:
    fig = px.line(
        trend,
        x=x_col,
        y="Sales",
        markers=True,
        title="Revenue Trend",
        labels={"Sales": "Revenue (₹)", x_col: x_title}
    )
    fig.update_traces(
        line=dict(color="#66e3d0", width=3),
        marker=dict(size=6)
    )
    st.plotly_chart(polish(fig), use_container_width=True)

with right:
    fig = px.line(
        trend,
        x=x_col,
        y="Profit",
        markers=True,
        title="Profit Trend",
        labels={"Profit": "Profit (₹)", x_col: x_title}
    )
    fig.update_traces(
        line=dict(color="#9c8cff", width=3),
        marker=dict(size=6)
    )
    st.plotly_chart(polish(fig), use_container_width=True)

# =====================================================
# 12. CATEGORY & PRODUCT PERFORMANCE
# =====================================================
st.divider()
st.header("🏆 Product Performance Lab")

left, right = st.columns(2)

category_data = (
    filtered.groupby("Category", as_index=False)
    .agg(
        Sales=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum"),
        Units=("Quantity", "sum")
    )
    .sort_values("Sales", ascending=False)
)

with left:
    fig = px.bar(
        category_data,
        x="Category",
        y="Sales",
        color="Profit",
        title="Category Revenue",
        color_continuous_scale="Tealgrn",
        labels={"Sales": "Revenue (₹)"}
    )
    fig.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(polish(fig, 430), use_container_width=True)

with right:
    top_products = (
        filtered.groupby("Product", as_index=False)
        .agg(
            Sales=("Total_Sales_INR", "sum"),
            Profit=("Profit_INR", "sum")
        )
        .nlargest(10, "Sales")
        .sort_values("Sales")
    )

    fig = px.bar(
        top_products,
        x="Sales",
        y="Product",
        orientation="h",
        color="Profit",
        title="Top 10 Products by Revenue",
        color_continuous_scale="Purples",
        labels={"Sales": "Revenue (₹)"}
    )
    st.plotly_chart(polish(fig, 430), use_container_width=True)

# =====================================================
# 13. INDIA SHIPPING STATE ANALYSIS
# =====================================================
st.divider()
st.header("🇮🇳 Regional Intelligence")

state_data = (
    filtered.groupby("Ship_State", as_index=False)
    .agg(
        Sales=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .nlargest(12, "Sales")
    .sort_values("Sales")
)

fig = px.bar(
    state_data,
    x="Sales",
    y="Ship_State",
    orientation="h",
    color="Profit",
    title="Leading Shipping States",
    color_continuous_scale="Teal",
    labels={"Sales": "Revenue (₹)", "Ship_State": "State"}
)

st.plotly_chart(polish(fig, 440), use_container_width=True)

# =====================================================
# 14. PAYMENT & ORDER STATUS
# =====================================================
st.divider()
st.header("💳 Operations & Payments")

left, right = st.columns(2)

with left:
    payment_data = (
        filtered.groupby("Payment_Method", as_index=False)
        .agg(Sales=("Total_Sales_INR", "sum"))
    )
    fig = px.pie(
        payment_data,
        names="Payment_Method",
        values="Sales",
        hole=0.58,
        title="Revenue by Payment Method"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(polish(fig), use_container_width=True)

with right:
    status_data = (
        filtered.groupby("Order_Status", as_index=False)
        .size()
        .rename(columns={"size": "Records"})
    )
    fig = px.bar(
        status_data,
        x="Order_Status",
        y="Records",
        color="Order_Status",
        title="Order Status Distribution"
    )
    st.plotly_chart(polish(fig), use_container_width=True)

fulfillment_data = (
    filtered.groupby("Fulfillment", as_index=False)
    .agg(
        Sales=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
    .sort_values("Sales", ascending=False)
)

st.subheader("Fulfillment Performance")
st.dataframe(
    fulfillment_data.style.format({
        "Sales": "₹{:,.2f}",
        "Profit": "₹{:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

# =====================================================


# =====================================================
# 15. SAPPHIRE AI - REAL LOCAL AI ASSISTANT
# =====================================================

st.divider()

st.markdown("""
<div style="
    background: linear-gradient(110deg, #10243B, #183A55);
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #34718C;
">
    <h2 style="color:#66E3D0; margin:0;">
        💎 SAPPHIRE AI ASSISTANT
    </h2>
    <p style="color:#D5E0F2; margin-bottom:0;">
        Your personal Amazon Sales Intelligence Analyst,
        powered by Llama 3.2 and Ollama.
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")

st.caption(
    "Ask questions about sales, profit, products, categories, "
    "customers' orders, payments and business performance. "
    "Answers are generated locally on your computer."
)

# Prepare a compact summary of the currently filtered data
ai_top_products = (
    filtered.groupby("Product", as_index=False)
    .agg(
        Revenue=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum"),
        Units=("Quantity", "sum")
    )
    .nlargest(10, "Revenue")
)

ai_categories = (
    filtered.groupby("Category", as_index=False)
    .agg(
        Revenue=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
    .sort_values("Revenue", ascending=False)
)

ai_states = (
    filtered.groupby("Ship_State", as_index=False)
    .agg(
        Revenue=("Total_Sales_INR", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .nlargest(10, "Revenue")
)

ai_payments = (
    filtered.groupby("Payment_Method", as_index=False)
    .agg(Revenue=("Total_Sales_INR", "sum"))
    .sort_values("Revenue", ascending=False)
)

ai_monthly = (
    filtered.assign(
        Month=filtered["Order_Date"].dt.to_period("M").astype(str)
    )
    .groupby("Month", as_index=False)
    .agg(
        Revenue=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
)

ai_status = (
    filtered.groupby("Order_Status")
    .size()
    .to_dict()
)

ai_fulfillment = (
    filtered.groupby("Fulfillment")
    .agg(
        Revenue=("Total_Sales_INR", "sum"),
        Profit=("Profit_INR", "sum")
    )
    .reset_index()
)

ai_context = f"""
You are Sapphire AI, an intelligent Amazon India sales analyst.

IMPORTANT RULES:
1. Answer using the supplied dataset summary.
2. Never invent sales figures or business facts.
3. Use Indian Rupees (INR) for monetary values.
4. Clearly distinguish revenue from recorded profit.
5. Explain findings in simple language.
6. Give practical business recommendations when appropriate.
7. If the information is unavailable, say so honestly.
8. The figures represent the currently selected dashboard filters.
9. You have aggregate summaries, not every individual transaction.

CURRENT DASHBOARD METRICS:
Filtered records: {len(filtered)}
Unique order IDs: {orders}
Total revenue: INR {revenue:,.2f}
Recorded profit: INR {profit:,.2f}
Units sold: {units:,.0f}
Profit margin: {margin:.2f}%
Average revenue per unique order ID: INR {avg_order_value:,.2f}

TOP PRODUCTS:
{ai_top_products.to_string(index=False)}

CATEGORY PERFORMANCE:
{ai_categories.to_string(index=False)}

TOP SHIPPING STATES:
{ai_states.to_string(index=False)}

PAYMENT PERFORMANCE:
{ai_payments.to_string(index=False)}

MONTHLY PERFORMANCE:
{ai_monthly.tail(12).to_string(index=False)}

ORDER STATUS:
{ai_status}

FULFILLMENT PERFORMANCE:
{ai_fulfillment.to_string(index=False)}
"""

# Initialize chat history
if "sapphire_ai_messages" not in st.session_state:
    st.session_state.sapphire_ai_messages = []

# Chat controls
chat_col1, chat_col2 = st.columns([5, 1])

with chat_col1:
    st.markdown("### 💬 Chat with Sapphire AI")

with chat_col2:
    if st.button("🗑️ Clear Chat"):
        st.session_state.sapphire_ai_messages = []
        st.rerun()

# Display previous messages
for message in st.session_state.sapphire_ai_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Suggested questions
st.markdown("**Try asking:**")

suggestions = [
    "Which product has the highest revenue?",
    "Explain my profit margin.",
    "Which category performs best?",
    "How can I improve my sales?"
]

suggestion_cols = st.columns(4)

for index, suggestion in enumerate(suggestions):
    with suggestion_cols[index]:
        if st.button(
            suggestion,
            key=f"sapphire_suggestion_{index}",
            use_container_width=True
        ):
            st.session_state.sapphire_ai_question = suggestion

# Chat input
user_question = st.chat_input(
    "Ask Sapphire AI anything about your Amazon sales..."
)

# Handle suggested questions
if "sapphire_ai_question" in st.session_state:
    user_question = st.session_state.pop("sapphire_ai_question")

# Generate AI response
if user_question:

    st.session_state.sapphire_ai_messages.append({
        "role": "user",
        "content": user_question
    })

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):

        with st.spinner("💎 Sapphire AI is analyzing your sales data..."):

            try:
                # Send current dataset context and conversation
                # to the local Ollama model.

                conversation = [
                    {
                        "role": "system",
                        "content": ai_context
                    }
                ]

                conversation.extend(
                    st.session_state.sapphire_ai_messages[-11:]
                )

                response = ollama.chat(
                    model="llama3.2:3b",
                    messages=conversation,
                    options={
                        "temperature": 0.2
                    }
                )

                ai_answer = response["message"]["content"]

                st.markdown(ai_answer)

                st.session_state.sapphire_ai_messages.append({
                    "role": "assistant",
                    "content": ai_answer
                })

            except Exception as error:

                st.error(
                    "Sapphire AI could not connect to Ollama. "
                    "Please make sure Ollama is running and "
                    "Llama 3.2 is installed."
                )

                st.code(str(error))



        
                
        

# =====================================================
# 16. DATA QUALITY & FILTERED DATA
# =====================================================
st.divider()
st.header("🔎 Data Quality & Explorer")

with st.expander("View data quality report"):
    quality = pd.DataFrame({
        "Check": [
            "Rows in original Excel data",
            "Rows after date and numeric validation",
            "Missing values in filtered data",
            "Exact duplicate rows in filtered data"
        ],
        "Result": [
            len(pd.read_excel(excel_files[0])),
            len(df),
            int(filtered.isna().sum().sum()),
            int(filtered.duplicated().sum())
        ]
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.caption(
        "Rows removed during cleaning had invalid dates or missing "
        "sales/profit values. Duplicate rows are reported, not "
        "automatically deleted."
    )

with st.expander("Explore filtered transaction records"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.download_button(
    label="⬇️ Download Filtered Sales Data (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="sapphire_iq_filtered_sales.csv",
    mime="text/csv"
)

# =====================================================
# 17. FOOTER
# =====================================================
st.divider()
st.caption(
    "💎 Sapphire IQ | Amazon India Sales Intelligence | "
    "Built with Python, Pandas, Streamlit and Plotly"
)
st.caption(
    "Business insights describe the supplied dataset. "
    "Recorded profit is not independently audited net profit. "
    "The built-in assistant uses rules, not a generative AI model."
)
