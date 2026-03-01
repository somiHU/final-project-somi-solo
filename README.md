[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/YlfKWlZ5)
# Analysis of Red Light Tickets and Poverty Penalties
This project investigates the intersection of automated traffic enforcement and socioeconomic inequality in Chicago. While the city’s 2019 debt reforms aimed to alleviate the financial burden of parking and compliance tickets on low-income residents, red-light camera violations—carrying a flat $100 fine—were largely excluded. Our primary research question is: Does the current red-light camera enforcement system disproportionately burden low-income communities, creating a structural "Poverty Penalty" that undermines urban equity goals? We explore whether "equal" fines produce unequal outcomes through two dimensions: spatial enforcement intensity and relative economic impact.

## Setup

```bash
pip install -r requirements.txt
```

## Project Structure

```
app/
  app.py     # Streamlit app
code/
  burden.qmd   # Burden analysis on community level
  distribution.qmd  # Spatial exposure map
  enforcement intensity.qmd  #Red light camera enforcement efficiency chart
  preprocessing.py  # Preprocessing the data
  time tax.qmd  ##Burden analysis on individual level
data/
  raw-data/           # Raw data files
    ACS_5_Year_Data_by_Community_Area.csv          
    Boundaries_-_Community_Areas.csv  
    Red_Light_Camera_Violations.csv
  derived-data/       # Filtered data 
    cleaned_acs_data.csv  # Community socioeconomic data
    cleaned_communities.geojson    # Community boundaries (WGS84)
    cleaned_red_light_2023.csv  # Camera-level violations by location in 2023


```

## Data Sources
### Chicago Data Portal
1. Red Light Camera Violations, filter only 2023
2. Boundaries - Community Areas - Map

### ACS
ACS 5 Year Data by Community Area (Released 2023)



## QMD FILES TO LOAD: (in order)
1. distribution.qmd generates the primary geographic map of red-light camera locations overlaid with community poverty rates, establishing the "Spatial Illusion" (the 3.8x concentration in wealthy areas) before moving to deeper analysis.
2. enforcement intensity.qmd Conducts exploratory data analysis on camera distribution and violation frequency. This file includes the spatial visualization of camera density vs.community poverty rates and the statistical identification and removal of outliers (The Loop and Fuller Park).
3. burden.qmd Focuses on the Wealth Drain Index (WDI) for the community. It integrates community income quintiles with aggregated fine data to visualize the macro-economic burden across different socioeconomic strata in Chicago.
4. time tax.qmd Calculates and visualizes the Time Tax metric. It converts the $100 flat fine into labor hours based on community-specific hourly wages. Includes the final ranking of 75 community areas(except Loop and Fuller Park) and the comparative gap analysis (e.g., Riverdale vs. Lincoln Park)

## Usage

1. Run preprocessing to filter data:
   ```bash
   python code/preprocessing.py
   ```

2. Generate target plot(using burden plot as an example):
   ```bash
   quarto render code/burden.qmd
   ```

3. Launch the Streamlit app:
   ```bash
   streamlit run app/app.py
   ```
