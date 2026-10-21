import io
import math

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Top Marine Noise Experiment",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 0.7rem; padding-bottom: 0.7rem; max-width: 100%;}
    h1 {font-size: 2.1rem !important; margin: 0.15rem 0 0.45rem 0 !important;}
    h2 {font-size: 1.45rem !important; margin: 0.15rem 0 0.35rem 0 !important;}
    h3 {font-size: 1.15rem !important; margin: 0.1rem 0 0.25rem 0 !important;}
    p, li, div {line-height: 1.25;}
    section[data-testid="stSidebar"] {min-width: 265px !important; max-width: 265px !important;}
    .tm-kpi {border: 1px solid rgba(120,120,120,.25); border-radius: 14px; padding: 12px 14px; background: rgba(255,255,255,.02); min-height: 90px;}
    .tm-kpi-label {font-size: 0.78rem; opacity: 0.72; margin-bottom: 5px;}
    .tm-kpi-value {font-size: 1.65rem; font-weight: 700; line-height: 1.0;}
    .tm-kpi-sub {font-size: 0.72rem; opacity: 0.62; margin-top: 5px;}
    .tm-request {border-left: 5px solid #5f6b7a; padding: 12px 18px; border-radius: 0 12px 12px 0; background: rgba(120,120,120,.08); font-size: 0.95rem; line-height: 1.35;}
    .tm-big {font-size: 3.3rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1;}
    .tm-center {text-align:center;}
    div[data-testid="stDataFrame"] {margin-top: 0.15rem; margin-bottom: 0.15rem;}
    .tm-slide-counter {text-align: center; font-size: 0.9rem; opacity: .7; padding-top: .55rem;}
    div[data-testid="stPlotlyChart"] {margin-top: -0.2rem; margin-bottom: -0.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

EXPECTED_COLUMNS = [
    "Dealer ID",
    "Pontoon solution",
    "Pontoon measurements",
    "Gangway measurements",
    "Booms",
    "Anchoring solution",
    "Other equipment",
    "Transport & installation EUR",
    "Total price EUR",
    "Expected difference %",
]

CUSTOMER_REQUEST = """
Hi,

I am looking for a floating pontoon to extend an existing fixed pier.
The pontoon would mainly be used for mooring one leisure boat with booms.

I am considering a T-shaped solution with a relatively long gangway,
because the existing fixed pier is approximately 1 metre above the water level.

The location is shallow and well sheltered from waves,
although strong northerly winds can occur.

I am thinking of a floating section of around 8 × 2 m,
but I am open to your recommendation.

Would additional flotation be needed near the booms?

Best regards
"""

# Requested order: old 1, 11, 5, 6, 7, 8, 9, 3, 4, 10, 2
SLIDES = [
    "Customer request",
    "All offers",
    "Pontoon solutions",
    "Pontoon measurements",
    "Gangways & booms",
    "Anchoring",
    "Other equipment",
    "Price reveal",
    "Price noise",
    "Final reveal",
    "Expected noise",
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_percent(value):
    if pd.isna(value) or value == "":
        return math.nan
    if isinstance(value, str):
        value = value.replace("%", "").replace(",", ".").strip()
    try:
        number = float(value)
    except Exception:
        return math.nan
    if 0 <= number <= 1:
        number *= 100
    return number


def format_eur(value):
    if pd.isna(value):
        return "—"
    return f"€{value:,.0f}".replace(",", " ")


def normalize_label(value):
    text = clean_text(value)
    return text if text else "Not specified"


def load_excel(file_bytes):
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Offers", header=None)
    header_row = None
    for i in range(min(len(raw), 20)):
        row_values = [clean_text(v) for v in raw.iloc[i].tolist()]
        if "Dealer ID" in row_values and "Total price EUR" in row_values:
            header_row = i
            break
    if header_row is None:
        raise ValueError("Could not find the Offers table header row.")

    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Offers", header=header_row)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("The Excel structure does not match the expected template. Missing columns: " + ", ".join(missing))

    df = df[EXPECTED_COLUMNS].copy()
    offer_fields = [c for c in EXPECTED_COLUMNS if c != "Dealer ID"]
    df = df[df[offer_fields].notna().any(axis=1)].copy()
    if df.empty:
        return df

    for i, idx in enumerate(df.index, start=1):
        if not clean_text(df.at[idx, "Dealer ID"]):
            df.at[idx, "Dealer ID"] = f"D{i:02d}"

    for col in ["Transport & installation EUR", "Total price EUR"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Expected difference %"] = df["Expected difference %"].apply(parse_percent)

    for col in ["Dealer ID", "Pontoon solution", "Pontoon measurements", "Gangway measurements", "Booms", "Anchoring solution", "Other equipment"]:
        df[col] = df[col].apply(clean_text)

    return df.reset_index(drop=True)


def kpi(label, value, sub=""):
    st.markdown(
        f'''<div class="tm-kpi"><div class="tm-kpi-label">{label}</div><div class="tm-kpi-value">{value}</div><div class="tm-kpi-sub">{sub}</div></div>''',
        unsafe_allow_html=True,
    )


def section_title(title, subtitle=None):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def categorical_chart(df, column, title):
    counts = df[column].apply(normalize_label).value_counts().rename_axis(column).reset_index(name="Dealers")
    fig = px.bar(counts, x="Dealers", y=column, orientation="h", text="Dealers", title=title)
    fig.update_layout(showlegend=False, height=430, margin=dict(l=10, r=25, t=55, b=25), yaxis_title="", xaxis_title="Number of dealers")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def nav_buttons():
    left, middle, right = st.columns([1, 4, 1])
    with left:
        if st.button("← Previous", use_container_width=True, disabled=st.session_state.slide_index <= 0):
            st.session_state.slide_index -= 1
            st.rerun()
    with middle:
        st.markdown(f'<div class="tm-slide-counter">Slide {st.session_state.slide_index + 1} / {len(SLIDES)}</div>', unsafe_allow_html=True)
    with right:
        if st.button("Next →", use_container_width=True, disabled=st.session_state.slide_index >= len(SLIDES) - 1):
            st.session_state.slide_index += 1
            st.rerun()


st.sidebar.title("Noise Experiment")
uploaded = st.sidebar.file_uploader("Upload completed Excel file", type=["xlsx"], help="Use the Top_Marine_Noise_Experiment_Offers.xlsx template.")
st.sidebar.caption("Use the arrows at the bottom of each slide to move through the presentation.")

if uploaded is None:
    st.title("Top Marine Noise Experiment")
    st.subheader("Presentation dashboard")
    st.info("Upload the completed **Top_Marine_Noise_Experiment_Offers.xlsx** file from the sidebar.")
    st.stop()

try:
    df = load_excel(uploaded.getvalue())
except Exception as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.warning("The Excel file contains no completed dealer offers yet.")
    st.stop()

price_df = df.dropna(subset=["Total price EUR"]).copy()
n_dealers = len(df)

if "slide_index" not in st.session_state:
    st.session_state.slide_index = 0
st.session_state.slide_index = max(0, min(st.session_state.slide_index, len(SLIDES) - 1))
page = SLIDES[st.session_state.slide_index]

st.sidebar.metric("Offers loaded", n_dealers)
if not price_df.empty:
    st.sidebar.metric("Offers with price", len(price_df))

if page == "Customer request":
    section_title("Same customer. Same request.", "How different will the decisions be?")
    left, right = st.columns([1.45, 1])
    with left:
        st.markdown(f'<div class="tm-request">{CUSTOMER_REQUEST.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with right:
        st.subheader("Prepare your offer")
        st.markdown("""
        - Recommended pontoon solution
        - Pontoon measurements
        - Gangway + measurements
        - Booms
        - Anchoring solution
        - Other equipment
        - Transport & installation
        - Total price, EUR excl. VAT
        """)

elif page == "All offers":
    section_title("All offers", f"{n_dealers} completed dealer offers")
    display_df = df.copy()
    display_df["Transport & installation EUR"] = display_df["Transport & installation EUR"].apply(lambda x: "" if pd.isna(x) else format_eur(x))
    display_df["Total price EUR"] = display_df["Total price EUR"].apply(lambda x: "" if pd.isna(x) else format_eur(x))
    display_df["Expected difference %"] = display_df["Expected difference %"].apply(lambda x: "" if pd.isna(x) else f"{x:.0f}%")
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=520)

elif page == "Pontoon solutions":
    section_title("What did we actually offer?", "The first source of noise may appear before pricing even begins.")
    st.plotly_chart(categorical_chart(df, "Pontoon solution", "Recommended pontoon solutions"), use_container_width=True)

elif page == "Pontoon measurements":
    section_title("Pontoon measurements", "Did we interpret the required floating section in the same way?")
    show_df = df[["Dealer ID", "Pontoon solution", "Pontoon measurements"]].copy()
    show_df["Pontoon solution"] = show_df["Pontoon solution"].apply(normalize_label)
    show_df["Pontoon measurements"] = show_df["Pontoon measurements"].apply(normalize_label)
    st.dataframe(show_df, use_container_width=True, hide_index=True, height=520)

elif page == "Gangways & booms":
    section_title("Gangways & booms", "Different interpretations of the same technical brief.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Gangway measurements")
        gang = df[["Dealer ID", "Gangway measurements"]].copy()
        gang["Gangway measurements"] = gang["Gangway measurements"].apply(normalize_label)
        st.dataframe(gang, use_container_width=True, hide_index=True, height=485)
    with c2:
        st.subheader("Booms")
        booms = df[["Dealer ID", "Booms"]].copy()
        booms["Booms"] = booms["Booms"].apply(normalize_label)
        st.dataframe(booms, use_container_width=True, hide_index=True, height=485)

elif page == "Anchoring":
    section_title("Anchoring decisions", "What did each dealer consider appropriate for the same site?")
    st.plotly_chart(categorical_chart(df, "Anchoring solution", "Anchoring solutions"), use_container_width=True)

elif page == "Other equipment":
    section_title("What else did we add?", "Additional equipment reveals different interpretations of the customer's need.")
    extras = df[["Dealer ID", "Other equipment"]].copy()
    extras["Other equipment"] = extras["Other equipment"].apply(normalize_label)
    st.dataframe(extras, use_container_width=True, hide_index=True, height=520)

elif page == "Price reveal":
    section_title("The price reveal", "Same customer request. Different total prices.")
    if price_df.empty:
        st.warning("No total prices have been entered.")
    else:
        plot_df = price_df[["Dealer ID", "Total price EUR"]].sort_values("Total price EUR")
        fig = px.bar(plot_df, x="Total price EUR", y="Dealer ID", orientation="h", text=plot_df["Total price EUR"].map(format_eur))
        fig.update_layout(height=535, showlegend=False, margin=dict(l=10, r=55, t=10, b=35), xaxis_title="Total price, EUR excl. VAT", yaxis_title="")
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

elif page == "Price noise":
    section_title("Price noise", "How far apart were the offers?")
    if price_df.empty:
        st.warning("No total prices have been entered.")
    else:
        prices = price_df["Total price EUR"]
        min_price = prices.min()
        max_price = prices.max()
        avg_price = prices.mean()
        median_price = prices.median()
        spread_eur = max_price - min_price
        spread_pct = (spread_eur / min_price * 100) if min_price > 0 else math.nan
        cv = (prices.std(ddof=1) / avg_price * 100) if len(prices) > 1 and avg_price > 0 else math.nan

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi("Lowest offer", format_eur(min_price))
        with c2: kpi("Highest offer", format_eur(max_price))
        with c3: kpi("Average offer", format_eur(avg_price))
        with c4: kpi("Median offer", format_eur(median_price))

        st.write("")
        c5, c6, c7 = st.columns(3)
        with c5: kpi("Price spread", format_eur(spread_eur), "Highest − lowest")
        with c6: kpi("Actual price noise", f"{spread_pct:.0f}%" if not math.isnan(spread_pct) else "—", "Spread vs. lowest offer")
        with c7: kpi("Coefficient of variation", f"{cv:.1f}%" if not math.isnan(cv) else "—", "Relative dispersion")

elif page == "Final reveal":
    section_title("Expected noise vs. actual noise")
    expected = df["Expected difference %"].dropna()
    if price_df.empty:
        st.warning("No total prices have been entered.")
    else:
        prices = price_df["Total price EUR"]
        min_price = prices.min()
        max_price = prices.max()
        actual_noise = ((max_price - min_price) / min_price * 100) if min_price > 0 else math.nan
        expected_mean = expected.mean() if not expected.empty else math.nan

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="tm-center">', unsafe_allow_html=True)
            st.caption("WE EXPECTED")
            st.markdown(f'<div class="tm-big">{"—" if math.isnan(expected_mean) else f"{expected_mean:.0f}%"}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="tm-center">', unsafe_allow_html=True)
            st.caption("THE ACTUAL PRICE NOISE WAS")
            st.markdown(f'<div class="tm-big">{"—" if math.isnan(actual_noise) else f"{actual_noise:.0f}%"}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div class="tm-center">
            <h2>Same information does not guarantee the same judgment.</h2>
            <p style="font-size:1rem; opacity:.75;">Which differences were justified — and which were noise?</p>
        </div>
        """, unsafe_allow_html=True)

elif page == "Expected noise":
    section_title("How much noise did we expect?", "Dealer estimates before seeing anyone else's offer.")
    expected = df["Expected difference %"].dropna()
    if expected.empty:
        st.warning("No expected-difference estimates have been entered.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: kpi("Average expected difference", f"{expected.mean():.0f}%")
        with c2: kpi("Lowest expectation", f"{expected.min():.0f}%")
        with c3: kpi("Highest expectation", f"{expected.max():.0f}%")

        exp_df = df.dropna(subset=["Expected difference %"])[["Dealer ID", "Expected difference %"]].sort_values("Expected difference %")
        fig = px.bar(exp_df, x="Expected difference %", y="Dealer ID", orientation="h", text=exp_df["Expected difference %"].map(lambda x: f"{x:.0f}%"))
        fig.update_layout(height=420, showlegend=False, margin=dict(l=10, r=45, t=10, b=35), xaxis_title="Expected difference between lowest and highest offer (%)", yaxis_title="")
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

nav_buttons()
