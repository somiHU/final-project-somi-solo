import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
from shapely.wkt import loads

script_dir = Path(__file__).parent
raw_dir = script_dir / "raw-data"
output_dir = script_dir / "derived-data"

file_path = raw_dir / "Red_Light_Camera_Violations.csv"
df_red_light = pd.read_csv(file_path)

df_clean = df_red_light.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()

camera_summary = df_clean.groupby('CAMERA ID').agg({
    'VIOLATIONS': 'sum',          
    'INTERSECTION': 'first',     
    'LATITUDE': 'first',         
    'LONGITUDE': 'first'         
}).reset_index()

camera_summary.rename(columns={'VIOLATIONS': 'TOTAL_VIOLATIONS_2023'}, inplace=True)
camera_summary.to_csv(output_dir / "cleaned_red_light_2023.csv", index=False)

print(f"Cleaning complete. There were {len(camera_summary)} active cameras in 2023.")
print(camera_summary.head())

#############

acs_path = raw_dir / "ACS_5_Year_Data_by_Community_Area.csv"
df_acs = pd.read_csv(acs_path)

income_cols = ['Under $25,000', '$25,000 to $49,999', '$50,000 to $74,999', '$75,000 to $125,000', '$125,000 +']
df_acs['Total_Households'] = df_acs[income_cols].sum(axis=1)

df_acs['Poverty_Rate'] = df_acs['Under $25,000'] / df_acs['Total_Households']

midpoints = np.array([12500, 37500, 62500, 100000, 175000]) 
df_acs['Est_Annual_Income'] = (df_acs[income_cols] * midpoints).sum(axis=1) / df_acs['Total_Households']
df_acs['Est_Monthly_Income'] = df_acs['Est_Annual_Income'] / 12

clean_acs = df_acs[[
    'Community Area', 'Poverty_Rate',
    'Est_Monthly_Income', 'Total Population'
]].copy()

clean_acs.to_csv(output_dir / "cleaned_acs_data.csv", index=False)

print("Preview of the cleaned data:")
print(clean_acs.head())

##############

geo_path = raw_dir / "Boundaries_-_Community_Areas.csv"
df_geo_raw = pd.read_csv(geo_path)

df_geo_raw['geometry'] = df_geo_raw['the_geom'].apply(loads)

gdf_community = gpd.GeoDataFrame(df_geo_raw, geometry='geometry', crs="EPSG:4326")

gdf_community = gdf_community[['COMMUNITY', 'AREA_NUMBE', 'geometry']].copy()
gdf_community['AREA_NUMBE'] = gdf_community['AREA_NUMBE'].astype(int)

gdf_community['COMMUNITY'] = gdf_community['COMMUNITY'].str.upper().str.strip()

print("Geographic data cleaning complete:")
print(gdf_community.head())

gdf_community.to_file(output_dir / "cleaned_communities.geojson", driver="GeoJSON")

print(f"All cleaned data has been successfully stored in: {output_dir}")