import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Mapa de ventas por estado", layout="wide")
st.title("🗺️ Mapa de ventas por estado")
st.caption("El color de cada estado representa sus ventas acumuladas. Usa los filtros para explorar los datos.")

DATA_FILE = Path(__file__).resolve().parents[1] / "SalidaVentas.xlsx"

@st.cache_data
def load_data(path):
    return pd.read_excel(path)

try:
    df = load_data(DATA_FILE)
except Exception as exc:
    st.error(f"No se pudo cargar el archivo de datos ({DATA_FILE.name}): {exc}")
    st.stop()

required_columns = {"State", "Sales", "Region", "Segment"}
missing_columns = required_columns.difference(df.columns)
if missing_columns:
    st.error("Faltan columnas requeridas en el archivo: " + ", ".join(sorted(missing_columns)))
    st.stop()

regions = ["Todas"] + sorted(df["Region"].dropna().unique().tolist())
segments = ["Todos"] + sorted(df["Segment"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Región", regions)
selected_segment = st.sidebar.selectbox("Segmento de cliente", segments)

filtered = df.copy()
if selected_region != "Todas":
    filtered = filtered[filtered["Region"] == selected_region]
if selected_segment != "Todos":
    filtered = filtered[filtered["Segment"] == selected_segment]

state_abbreviations = {
    "Alabama": "AL", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY",
    "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY"
}

sales_by_state = (
    filtered.groupby("State", as_index=False)["Sales"]
    .sum()
    .rename(columns={"Sales": "Ventas"})
)
sales_by_state["Abreviatura"] = sales_by_state["State"].map(state_abbreviations)
unknown_states = sorted(sales_by_state.loc[sales_by_state["Abreviatura"].isna(), "State"].dropna().unique())
sales_by_state = sales_by_state.dropna(subset=["Abreviatura"])

if sales_by_state.empty:
    st.warning("No hay ventas por estado para mostrar con los filtros seleccionados.")
else:
    fig = px.choropleth(
        sales_by_state,
        locations="Abreviatura",
        locationmode="USA-states",
        scope="usa",
        color="Ventas",
        hover_name="State",
        hover_data={"Abreviatura": False, "Ventas": ":$,.2f"},
        color_continuous_scale="YlOrRd",
        labels={"Ventas": "Ventas ($)"},
        title="Ventas acumuladas por estado"
    )
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

if unknown_states:
    st.info("No se pudieron ubicar estos nombres de estado en el mapa: " + ", ".join(unknown_states))

st.subheader("Ventas por estado")
st.dataframe(
    sales_by_state[["State", "Ventas"]].sort_values("Ventas", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={"Ventas": st.column_config.NumberColumn("Ventas", format="$%.2f")}
)
