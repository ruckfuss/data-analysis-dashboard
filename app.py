import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f1a; }
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    h1, h2, h3 { color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    url = "https://disease.sh/v3/covid-19/countries"
    response = requests.get(url, timeout=10)
    data = response.json()

    rows = []
    for country in data:
        rows.append({
            "Country":        country["country"],
            "Continent":      country.get("continent", "Unknown"),
            "Total Cases":    country["cases"],
            "Total Deaths":   country["deaths"],
            "Recovered":      country["recovered"],
            "Active":         country["active"],
            "Cases/1M Pop":   country["casesPerOneMillion"],
            "Deaths/1M Pop":  country["deathsPerOneMillion"],
            "Population":     country["population"],
            "Tests":          country["tests"],
            "Tests/1M Pop":   country["testsPerOneMillion"],
            "Death Rate (%)": round(
                country["deaths"] / country["cases"] * 100, 2
            ) if country["cases"] > 0 else 0,
        })

    df = pd.DataFrame(rows)
    df = df[df["Population"] > 100000]   # remove micro-states
    df = df[df["Total Cases"] > 0]
    return df

# ── Load ──────────────────────────────────────────────────────────────────────
with st.spinner("Fetching live data..."):
    try:
        df = load_data()
        data_ok = True
    except Exception as e:
        st.error(f"Could not fetch data: {e}")
        data_ok = False

if not data_ok:
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🦠 Global COVID-19 Data Dashboard")
st.markdown(
    f"*Live data • {len(df)} countries • "
    f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
)
st.divider()

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

continents = ["All"] + sorted(df["Continent"].dropna().unique().tolist())
selected_continent = st.sidebar.selectbox("Continent", continents)

top_n = st.sidebar.slider("Top N Countries", 5, 50, 20)
metric = st.sidebar.selectbox(
    "Primary Metric",
    ["Total Cases", "Total Deaths", "Cases/1M Pop",
     "Deaths/1M Pop", "Death Rate (%)"]
)

filtered = df.copy()
if selected_continent != "All":
    filtered = filtered[filtered["Continent"] == selected_continent]

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌍 Countries",    f"{len(filtered):,}")
c2.metric("🦠 Total Cases",  f"{filtered['Total Cases'].sum():,.0f}")
c3.metric("💀 Total Deaths", f"{filtered['Total Deaths'].sum():,.0f}")
c4.metric("📊 Avg Death Rate",
          f"{filtered['Death Rate (%)'].mean():.2f}%")

st.divider()

# ── Row 1: Bar + Pie ──────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Top {top_n} Countries by {metric}")
    top_df = filtered.nlargest(top_n, metric)
    fig_bar = px.bar(
        top_df, x="Country", y=metric,
        color=metric,
        color_continuous_scale="Viridis",
        template="plotly_dark"
    )
    fig_bar.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#0f0f1a",
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("Cases by Continent")
    cont_df = (
        df.groupby("Continent")["Total Cases"]
          .sum()
          .reset_index()
          .sort_values("Total Cases", ascending=False)
    )
    fig_pie = px.pie(
        cont_df, values="Total Cases", names="Continent",
        template="plotly_dark",
        color_discrete_sequence=px.colors.sequential.Plasma_r
    )
    fig_pie.update_layout(paper_bgcolor="#0f0f1a")
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Row 2: Scatter + Choropleth ───────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Cases vs Deaths (log scale)")
    fig_scatter = px.scatter(
        filtered,
        x="Total Cases", y="Total Deaths",
        size="Population", color="Continent",
        hover_name="Country",
        log_x=True, log_y=True,
        template="plotly_dark",
        size_max=50
    )
    fig_scatter.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#0f0f1a"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col4:
    st.subheader("Death Rate by Continent")
    box_df = df[df["Death Rate (%)"] < df["Death Rate (%)"].quantile(0.99)]
    fig_box = px.box(
        box_df, x="Continent", y="Death Rate (%)",
        color="Continent",
        template="plotly_dark"
    )
    fig_box.update_layout(
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#0f0f1a",
        showlegend=False
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ── Row 3: World map ──────────────────────────────────────────────────────────
st.subheader(f"🗺️ World Map — {metric}")
fig_map = px.choropleth(
    filtered,
    locations="Country",
    locationmode="country names",
    color=metric,
    hover_name="Country",
    color_continuous_scale="Reds",
    template="plotly_dark"
)
fig_map.update_layout(
    paper_bgcolor="#0f0f1a",
    geo=dict(bgcolor="#0f0f1a")
)
st.plotly_chart(fig_map, use_container_width=True)

# ── Row 4: Top 10 death rate table ───────────────────────────────────────────
st.subheader("📋 Data Table")
show_cols = ["Country", "Continent", "Total Cases",
             "Total Deaths", "Death Rate (%)", "Cases/1M Pop", "Population"]
st.dataframe(
    filtered[show_cols]
      .sort_values(metric, ascending=False)
      .reset_index(drop=True),
    use_container_width=True,
    height=400
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Data source: disease.sh (Johns Hopkins University)")