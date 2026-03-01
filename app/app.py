import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from pathlib import Path

# --- 1. Data Initialization & Caching ---
script_dir = Path(__file__).parent
derived_dir = script_dir / "data" / "derived-data"

@st.cache_data
def load_and_process_data():
    df_acs = pd.read_csv(derived_dir / "cleaned_acs_data.csv")
    df_cameras = pd.read_csv(derived_dir / "cleaned_red_light_2023.csv")
    gdf_communities = gpd.read_file(derived_dir / "cleaned_communities.geojson")
    
    if gdf_communities.crs is None or gdf_communities.crs.to_epsg() != 4326:
        gdf_communities = gdf_communities.to_crs(epsg=4326)
    
    df_acs['Community Area'] = df_acs['Community Area'].str.upper().str.strip()
    gdf_communities['COMMUNITY'] = gdf_communities['COMMUNITY'].str.upper().str.strip()
    
    # 空间连接用于计算执法效率
    gdf_cameras_geo = gpd.GeoDataFrame(
        df_cameras, 
        geometry=gpd.points_from_xy(df_cameras.LONGITUDE, df_cameras.LATITUDE),
        crs="EPSG:4326"
    )
    cameras_with_community = gpd.sjoin(gdf_cameras_geo, gdf_communities, how="left", predicate="within")
    efficiency = cameras_with_community.groupby('COMMUNITY')['TOTAL_VIOLATIONS_2023'].mean().reset_index()
    
    df_merged = efficiency.merge(df_acs, left_on='COMMUNITY', right_on='Community Area')
    
    outliers = ['LOOP', 'FULLER PARK']
    df_filtered_camera = df_merged[~df_merged['Community Area'].isin(outliers)].copy()
    df_acs_clean = df_acs[~df_acs['Community Area'].isin(outliers)].copy()
    
    return df_filtered_camera, gdf_communities, df_acs_clean

df_camera, gdf_communities, df_acs = load_and_process_data()

# --- 2. Anchoring Metrics (基准指标) ---
# 选取对比锚点
poorest = df_acs.loc[df_acs['Est_Monthly_Income'].idxmin()]
wealthiest = df_acs.loc[df_acs['Est_Monthly_Income'].idxmax()]

# 静态不平等倍数：基于有摄像头数据的社区计算
p_poor = df_camera.loc[df_camera['Est_Monthly_Income'].idxmin()]
p_rich = df_camera.loc[df_camera['Est_Monthly_Income'].idxmax()]
pressure_multiplier = (p_poor['TOTAL_VIOLATIONS_2023'] / p_poor['Est_Monthly_Income']) / \
                    (p_rich['TOTAL_VIOLATIONS_2023'] / p_rich['Est_Monthly_Income'])

time_multiplier = wealthiest['Est_Monthly_Income'] / poorest['Est_Monthly_Income']

# --- 3. UI Layout ---
st.set_page_config(page_title="Poverty Penalty Simulator", layout="wide")
st.title("Chicago Red Light: The Poverty Penalty Simulator")

st.sidebar.header("Policy Settings")
fine_amount = st.sidebar.slider("Select Ticket Fine Amount ($)", 0, 300, 100, 10)

# --- 4. Dynamic Calculations ---
def get_work_hours(income, fine):
    hourly_wage = income / 160
    return fine / hourly_wage if hourly_wage > 0 else 0

# 核心对齐：计算全市每个社区的平均小时数，而不是计算平均收入的小时数
all_hours = df_acs['Est_Monthly_Income'].apply(lambda x: get_work_hours(x, fine_amount))
hours_city = all_hours.mean()  # 这将显示为 2.2h (当罚金为 100 时)

hours_poor = get_work_hours(poorest['Est_Monthly_Income'], fine_amount)
hours_rich = get_work_hours(wealthiest['Est_Monthly_Income'], fine_amount)

# --- 5. Metrics Display (已移除 Wealth Drain) ---
st.subheader(f"The Human Cost of a ${fine_amount} Fine")
st.write("Below is the labor required to pay for a single violation across different economic strata.")

col1, col2, col3 = st.columns(3)
col1.metric("City-wide Avg Labor", f"{hours_city:.1f}h")
col2.metric(f"Poorest: {poorest['Community Area']}", f"{hours_poor:.1f}h", 
            delta=f"{hours_poor - hours_city:.1f}h vs Avg", delta_color="inverse")
col3.metric(f"Wealthiest: {wealthiest['Community Area']}", f"{hours_rich:.1f}h", 
            delta=f"{hours_rich - hours_city:.1f}h vs Avg", delta_color="inverse")

st.divider()

# --- 6. The Dynamic Map ---
st.subheader("Geographical Distribution of the 'Time Tax'")
map_acs = df_acs[["Community Area", "Est_Monthly_Income"]].copy()
map_acs["Dynamic_Hours"] = map_acs["Est_Monthly_Income"].apply(
    lambda x: get_work_hours(x, fine_amount)
)
map_gdf = gdf_communities.merge(
    map_acs[["Community Area", "Dynamic_Hours"]],
    left_on="COMMUNITY",
    right_on="Community Area",
    how="left",
)
map_gdf["geometry"] = map_gdf.geometry.simplify(0.001)

m = folium.Map(location=[41.85, -87.65], zoom_start=10, tiles="CartoDB positron")
folium.Choropleth(
    geo_data=map_gdf,
    data=map_gdf,
    columns=["COMMUNITY", "Dynamic_Hours"],
    key_on="feature.properties.COMMUNITY",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Hours of labor to pay one ticket",
    bins=[0, 1, 2, 3, 5, 10, 20, 40],
    nan_fill_color="lightgray",
    highlight=True,
).add_to(m)

col_map, col_label = st.columns([3, 1])
with col_map:
    st.components.v1.html(m._repr_html_(), height=420)
    st.markdown(f"""
    <p style='margin-top: -20px;'>
    By observing the map, we can see how the South and West sides of Chicago enter the 'High Pressure' (dark red) zone 
    far earlier than the North side as the fine increases. The seemingly fair fine of <b>${fine_amount}</b> 
    is actually a regressive tax on time and labor.
    </p>
    """, unsafe_allow_html=True)
with col_label:
    st.markdown(f"""
    **Color scale (Hours of labor)**
    
    Each community is colored by the **labor sacrifice** required to pay a **${fine_amount}** fine. 
    
    * **Dark Red Areas**: Represent a 'High Poverty Penalty'. Residents here must work significantly longer to satisfy the same legal debt.
    * **Lighter Areas**: Represent lower time costs relative to income.
    """)
# --- 7. Static Multipliers (已增强解释) ---
st.divider()

st.subheader("Structural Inequity Multipliers")

m1, m2 = st.columns(2)

with m1:
    st.metric("Systemic Pressure Gap", f"{pressure_multiplier:.1f}x")
    # 使用 LaTeX 格式列出清晰的计算公式
    st.markdown(r"**Calculation Formula:**")
    st.latex(r"\frac{\text{Violations}_{\text{the poorest}} / \text{Income}_{\text{the poorest}}}{\text{Violations}_{\text{the richest}} / \text{Income}_{\text{the richest}}}")
    
    st.write("""
    This metric quantifies the 'Double Jeopardy' effect where systemic factors compound to penalize 
    poverty. It measures the total economic drain by comparing the enforcement intensity (citations 
    per camera) relative to income levels between the city's poorest and wealthiest communities. A higher 
    multiplier reveals that low-income residents are not only burdened by their limited financial 
    capacity but are also subjected to more frequent automated surveillance, creating a reinforcing 
    cycle of wealth extraction.
    """)
with m2:
    st.metric("Individual Labor Gap", f"{time_multiplier:.1f}x")
    st.write("**The 'Time Tax' Gap**: This is a pure measure of income inequality. It shows that a resident in the poorest neighborhood must sacrifice this many times more hours of their life to pay the same ticket as a wealthy resident.")
st.info("**Note on Structural Underestimation:** The current system stress differential is likely **underestimated**. Many low-income communities currently lack surveillance cameras; if future law enforcement efforts cover these areas, their wealth loss index will far exceed current observations.")


##输入查看：/opt/miniconda3/bin/streamlit run "/Users/somihu/Desktop/研二/PPHA 30538/Final project/app.py"