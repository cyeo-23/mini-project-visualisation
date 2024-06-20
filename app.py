import streamlit as st
import pandas as pd
import altair as alt
import geopandas as gpd
import folium
from streamlit_folium import folium_static

# Load the datasets
baby_names = pd.read_csv('dpt2020.csv', delimiter=';')
departments = gpd.read_file('departements-version-simplifiee.geojson')

# Data preprocessing
baby_names.drop(baby_names[baby_names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
baby_names.drop(baby_names[baby_names.dpt == 'XX'].index, inplace=True)

# Merge datasets
names = departments.merge(baby_names, how='right', left_on='code', right_on='dpt')

# Drop the geometry column before groupby
names_no_geom = names.drop(columns='geometry')

# Perform the groupby operation
grouped = names_no_geom.groupby(['dpt', 'preusuel', 'sexe'], as_index=False).sum()

# Merge the geometry data back in
grouped = departments.merge(grouped, how='right', left_on='code', right_on='dpt')

# Title of the app
st.title('Interactive Baby Names Visualization in France')

# Sidebar for selecting the visualization
st.sidebar.title('Select Visualization')
visualization = st.sidebar.selectbox('Choose a visualization type', 
                                     ['Baby Names Over Time', 'Regional Effect', 'Names by Sex Over Time'])

# Visualization 1: Baby Names Over Time
if visualization == 'Baby Names Over Time':
    st.header('How do baby names evolve over time?')
    names_list = st.multiselect('Select baby names', baby_names['preusuel'].unique())
    
    if names_list:
        subset = baby_names[baby_names['preusuel'].isin(names_list)]
        chart = alt.Chart(subset).mark_line().encode(
            x='annais:O',
            y='sum(nombre):Q',
            color='preusuel:N'
        ).properties(width=800, height=400)
        st.altair_chart(chart)

# Visualization 2: Regional Effect
elif visualization == 'Regional Effect':
    st.header('Regional Effect of Baby Names in France')
    name = st.selectbox('Select a baby name', baby_names['preusuel'].unique())
    
    if name:
        subset = grouped[grouped['preusuel'] == name]
        alt.chart(subset).mark_geoshape(stroke='white').encode(
            tooltip=['nom','code', 'nombre'],
            color='nombre',
        ).properties(width=800, height=600)


# Visualization 3: Names by Sex Over Time
elif visualization == 'Names by Sex Over Time':
    st.header('Proportion of First Names by Sex Over Time')
    
    male_names = st.multiselect('Select male baby names', baby_names[baby_names['sexe'] == 1]['preusuel'].unique())
    female_names = st.multiselect('Select female baby names', baby_names[baby_names['sexe'] == 2]['preusuel'].unique())
    
    if male_names and female_names:
        subset_male = baby_names[(baby_names['preusuel'].isin(male_names)) & (baby_names['sexe'] == 1)]
        subset_female = baby_names[(baby_names['preusuel'].isin(female_names)) & (baby_names['sexe'] == 2)]
        
        subset_male['proportion'] = subset_male.groupby('annais')['nombre'].transform(lambda x: x / x.sum())
        subset_female['proportion'] = subset_female.groupby('annais')['nombre'].transform(lambda x: x / x.sum())
        
        chart_male = alt.Chart(subset_male).mark_bar().encode(
            x=alt.X('annais:O', title='Year'),
            y=alt.Y('proportion:Q', title='Proportion'),
            color='preusuel:N'
        ).properties(width=400, height=400).facet(
            column='sexe:N'
        )
        
        chart_female = alt.Chart(subset_female).mark_bar().encode(
            x=alt.X('annais:O', title='Year'),
            y=alt.Y('proportion:Q', title='Proportion'),
            color='preusuel:N'
        ).properties(width=400, height=400).facet(
            column='sexe:N'
        )
        
        st.altair_chart(chart_male & chart_female)
